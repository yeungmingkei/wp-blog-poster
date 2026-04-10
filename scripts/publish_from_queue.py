"""
Publish queued articles to WordPress.

Reads JSON files from publish-queue/ directory, publishes each to WordPress via REST API,
then removes the file. Image data is expected as base64 in the JSON.
"""
import os
import json
import base64
import sys
import glob
import requests
from requests.auth import HTTPBasicAuth

QUEUE_DIR = "publish-queue"
WP_BASE = "https://www.acdesign.com.hk/wp-json/wp/v2"
WP_USER = os.environ["WP_USER"]
WP_PASS = os.environ["WP_APP_PASSWORD"]
FB_PAGE_ID = os.environ.get("FB_PAGE_ID", "")
FB_PAGE_TOKEN = os.environ.get("FB_PAGE_TOKEN", "")

auth = HTTPBasicAuth(WP_USER, WP_PASS)


def get_or_create_category(name: str) -> int:
    r = requests.get(f"{WP_BASE}/categories", params={"search": name}, auth=auth, timeout=30)
    r.raise_for_status()
    for c in r.json():
        if c["name"] == name:
            return c["id"]
    r = requests.post(f"{WP_BASE}/categories", json={"name": name}, auth=auth, timeout=30)
    r.raise_for_status()
    return r.json()["id"]


def get_or_create_tag(name: str) -> int:
    r = requests.get(f"{WP_BASE}/tags", params={"search": name}, auth=auth, timeout=30)
    r.raise_for_status()
    for t in r.json():
        if t["name"] == name:
            return t["id"]
    r = requests.post(f"{WP_BASE}/tags", json={"name": name}, auth=auth, timeout=30)
    r.raise_for_status()
    return r.json()["id"]


def upload_media(image_b64: str, filename: str = "featured.png") -> int:
    image_bytes = base64.b64decode(image_b64)
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": "image/png",
    }
    r = requests.post(f"{WP_BASE}/media", headers=headers, data=image_bytes, auth=auth, timeout=120)
    r.raise_for_status()
    return r.json()["id"]


def publish_article(article: dict) -> str:
    title = article["title"]
    content = article["content"]
    excerpt = article.get("excerpt", "")
    category_name = article.get("category", "裝修知識")
    tags = article.get("tags", [])
    image_b64 = article.get("image_base64")

    media_id = None
    if image_b64:
        media_id = upload_media(image_b64)
        print(f"  uploaded image, media_id={media_id}")

    cat_id = get_or_create_category(category_name)
    tag_ids = [get_or_create_tag(t) for t in tags]

    payload = {
        "title": title,
        "content": content,
        "status": "publish",
        "categories": [cat_id],
        "tags": tag_ids,
        "excerpt": excerpt,
    }
    if media_id:
        payload["featured_media"] = media_id

    r = requests.post(f"{WP_BASE}/posts", json=payload, auth=auth, timeout=60)
    r.raise_for_status()
    return r.json()["link"]


def post_to_facebook(caption: str, image_b64: str) -> dict:
    if not FB_PAGE_TOKEN or not FB_PAGE_ID:
        return {"skipped": "facebook credentials not set"}
    image_bytes = base64.b64decode(image_b64)
    r = requests.post(
        f"https://graph.facebook.com/v24.0/{FB_PAGE_ID}/photos",
        files={"source": ("featured.png", image_bytes, "image/png")},
        data={"caption": caption, "access_token": FB_PAGE_TOKEN, "published": "true"},
        timeout=120,
    )
    return r.json()


def main():
    os.makedirs(QUEUE_DIR, exist_ok=True)
    files = sorted(glob.glob(f"{QUEUE_DIR}/*.json"))
    if not files:
        print("No articles in queue.")
        return 0

    print(f"Found {len(files)} article(s) to publish.")
    for path in files:
        print(f"\nProcessing {path}...")
        with open(path, "r", encoding="utf-8") as f:
            article = json.load(f)

        try:
            url = publish_article(article)
            print(f"  published: {url}")

            if article.get("post_to_facebook") and article.get("fb_caption"):
                fb_result = post_to_facebook(
                    article["fb_caption"].replace("{article_url}", url),
                    article.get("image_base64", ""),
                )
                print(f"  facebook: {fb_result}")

            os.remove(path)
            print(f"  removed {path} from queue")
        except Exception as e:
            print(f"  ERROR: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"  response: {e.response.status_code} {e.response.text[:500]}")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
