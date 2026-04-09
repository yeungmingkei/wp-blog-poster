"""
WordPress REST API 发布模块
支持创建文章、上传媒体、管理分类和标签
"""
import os
import json
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

SITE_URL = os.getenv('WP_SITE_URL', 'https://www.acdesign.com.hk')
WP_USER = os.getenv('WP_USER', 'admin')
WP_APP_PASSWORD = os.getenv('WP_APP_PASSWORD', '')
API_BASE = f'{SITE_URL}/wp-json/wp/v2'

auth = HTTPBasicAuth(WP_USER, WP_APP_PASSWORD)


def get_categories():
    """获取所有分类"""
    resp = requests.get(f'{API_BASE}/categories', params={'per_page': 100}, auth=auth)
    resp.raise_for_status()
    return {c['name']: c['id'] for c in resp.json()}


def get_or_create_category(name: str, slug: str = '') -> int:
    """获取或创建分类，返回分类 ID"""
    cats = get_categories()
    if name in cats:
        return cats[name]

    data = {'name': name}
    if slug:
        data['slug'] = slug
    resp = requests.post(f'{API_BASE}/categories', json=data, auth=auth)
    resp.raise_for_status()
    return resp.json()['id']


def get_or_create_tag(name: str) -> int:
    """获取或创建标签，返回标签 ID"""
    resp = requests.get(f'{API_BASE}/tags', params={'search': name, 'per_page': 10}, auth=auth)
    resp.raise_for_status()
    tags = resp.json()
    for t in tags:
        if t['name'] == name:
            return t['id']

    resp = requests.post(f'{API_BASE}/tags', json={'name': name}, auth=auth)
    resp.raise_for_status()
    return resp.json()['id']


def upload_media(image_path: str, alt_text: str = '', title: str = '') -> int:
    """上传图片到 WordPress 媒体库，返回 media ID"""
    filename = os.path.basename(image_path)
    content_type = 'image/png' if filename.endswith('.png') else 'image/jpeg'

    with open(image_path, 'rb') as f:
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': content_type,
        }
        resp = requests.post(
            f'{API_BASE}/media',
            headers=headers,
            data=f.read(),
            auth=auth,
        )
    resp.raise_for_status()
    media_id = resp.json()['id']

    if alt_text or title:
        update_data = {}
        if alt_text:
            update_data['alt_text'] = alt_text
        if title:
            update_data['title'] = title
        requests.post(f'{API_BASE}/media/{media_id}', json=update_data, auth=auth)

    return media_id


def create_post(
    title: str,
    content: str,
    category_ids: list = None,
    tag_ids: list = None,
    featured_media_id: int = None,
    status: str = 'publish',
    excerpt: str = '',
) -> dict:
    """创建 WordPress 文章"""
    data = {
        'title': title,
        'content': content,
        'status': status,
    }
    if category_ids:
        data['categories'] = category_ids
    if tag_ids:
        data['tags'] = tag_ids
    if featured_media_id:
        data['featured_media'] = featured_media_id
    if excerpt:
        data['excerpt'] = excerpt

    resp = requests.post(f'{API_BASE}/posts', json=data, auth=auth)
    resp.raise_for_status()
    result = resp.json()
    return {
        'id': result['id'],
        'url': result['link'],
        'title': result['title']['rendered'],
        'status': result['status'],
    }


def test_connection() -> bool:
    """测试 WordPress API 连接"""
    try:
        resp = requests.get(f'{API_BASE}/users/me', auth=auth)
        if resp.status_code == 200:
            user = resp.json()
            print(f"Connected as: {user.get('name', 'unknown')}")
            return True
        print(f"Auth failed: {resp.status_code}")
        return False
    except Exception as e:
        print(f"Connection error: {e}")
        return False


if __name__ == '__main__':
    if test_connection():
        print("WordPress API connection OK")
        cats = get_categories()
        print(f"Categories: {cats}")
