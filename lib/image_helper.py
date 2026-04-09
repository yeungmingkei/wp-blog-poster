"""
AI 配图生成模块
使用 Imagen 4.0 生成室内设计相关配图
"""
import os
import base64
import requests
import tempfile
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
IMAGEN_MODEL = 'imagen-4.0-generate-001'
API_URL = f'https://generativelanguage.googleapis.com/v1beta/models/{IMAGEN_MODEL}:predict'


def generate_image(
    topic: str,
    aspect_ratio: str = '16:9',
    style: str = 'Professional interior design photography',
    output_dir: str = None,
) -> str:
    """
    根据话题生成配图，返回图片文件路径

    Args:
        topic: 文章话题（用于生成 prompt）
        aspect_ratio: 图片比例
        style: 风格描述
        output_dir: 输出目录，默认临时目录
    """
    prompt = (
        f"{style}, {topic}, "
        "modern Hong Kong apartment interior, "
        "bright natural lighting, clean composition, "
        "editorial quality, 8K resolution, "
        "warm color palette, minimalist aesthetic"
    )

    payload = {
        'instances': [{'prompt': prompt}],
        'parameters': {
            'sampleCount': 1,
            'aspectRatio': aspect_ratio,
        },
    }

    headers = {'Content-Type': 'application/json'}
    resp = requests.post(
        f'{API_URL}?key={GEMINI_API_KEY}',
        json=payload,
        headers=headers,
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()

    predictions = data.get('predictions', [])
    if not predictions:
        raise ValueError(f"No image generated. Response: {data}")

    image_bytes = base64.b64decode(predictions[0]['bytesBase64Encoded'])

    if output_dir is None:
        output_dir = tempfile.mkdtemp()
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, 'featured_image.png')
    with open(output_path, 'wb') as f:
        f.write(image_bytes)

    return output_path


if __name__ == '__main__':
    path = generate_image('modern living room design')
    print(f'Image saved to: {path}')
