from PIL import Image, ImageDraw
import os

os.makedirs('static/core', exist_ok=True)
for size in (192, 512):
    img = Image.new('RGBA', (size, size), (70, 213, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.ellipse((0, 0, size, size), fill=(255, 255, 255, 255))
    draw.text((size // 3, size // 3), 'P', fill=(70, 40, 120, 255))
    img.save(f'static/core/icon-{size}.png')
