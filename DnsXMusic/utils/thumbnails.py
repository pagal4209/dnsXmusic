import os
import re
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from youtubesearchpython.__future__ import VideosSearch

# Fonts
title_font = ImageFont.truetype("assets/font3.ttf", 42)
channel_font = ImageFont.truetype("assets/font2.ttf", 34)
duration_font = ImageFont.truetype("assets/font.ttf", 30)
watermark_font = ImageFont.truetype("assets/font.ttf", 20)

# Dark overlay with red tint and blur
def apply_red_blur_overlay(image, opacity=0.6):
    blurred = image.filter(ImageFilter.GaussianBlur(25))
    red_overlay = Image.new("RGBA", image.size, (255, 49, 99, int(90 * opacity)))
    return Image.alpha_composite(blurred.convert("RGBA"), red_overlay)

# Multiline text wrapper and centered drawing
def draw_multiline_centered_text(draw, text, font, image_width, y_start, line_spacing=10, max_width=1100):
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = current_line + " " + word if current_line else word
        w, _ = draw.textsize(test_line, font=font)
        if w <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)

    y = y_start
    for line in lines:
        draw.text((image_width // 2, y), line, font=font, fill="white", anchor="mm")
        y += font.getsize(line)[1] + line_spacing

# Main thumbnail generator
async def generate_simple_thumb(videoid, filename):
    if os.path.isfile(filename):
        return filename

    url = f"https://www.youtube.com/watch?v={videoid}"
    results = VideosSearch(url, limit=1)
    result = (await results.next())["result"][0]

    title = re.sub(r"\W+", " ", result.get("title", "Unknown Title")).title()
    channel = result.get("channel", {}).get("name", "Unknown Channel")
    duration = result.get("duration", "0:00")
    thumbnail_url = result["thumbnails"][0]["url"].split("?")[0]

    async with aiohttp.ClientSession() as session:
        async with session.get(thumbnail_url) as resp:
            if resp.status == 200:
                async with aiofiles.open(f"cache/thumb_{videoid}.jpg", "wb") as f:
                    await f.write(await resp.read())

    base = Image.open(f"cache/thumb_{videoid}.jpg").convert("RGBA").resize((1280, 720))
    background = apply_red_blur_overlay(base)
    draw = ImageDraw.Draw(background)

    # Load and paste control overlay
    try:
        control_img = Image.open("assets/cntrol.png").convert("RGBA")
        control_img = control_img.resize((600, 600))
        cx = (1280 - control_img.width) // 2
        cy = (720 - control_img.height) // 2
        background.paste(control_img, (cx, cy), mask=control_img)
    except Exception as e:
        print(f"Error loading control image: {e}")
        cx, cy = 0, 0

    # Center thumbnail (medium size) inside control
    center_thumb = Image.open(f"cache/thumb_{videoid}.jpg").convert("RGBA").resize((200, 150))
    thumb_cx = 500 - center_thumb.width // 2
    thumb_cy = 360 - center_thumb.height // 2
    background.paste(center_thumb, (thumb_cx, thumb_cy))

    # Draw Title, Channel, and Duration
    draw_multiline_centered_text(draw, title, title_font, 1280, cy + 350)
    draw.text((640, cy + 440), channel, font=channel_font, fill="white", anchor="mm")
    draw.text((640, cy + 490), f"Duration: {duration}", font=duration_font, fill="white", anchor="mm")

    # Bottom-right watermark
    watermark_text = "DnsXmusic"
    text_width = draw.textlength(watermark_text, font=watermark_font)
    text_height = watermark_font.getsize(watermark_text)[1]
    padding = 20
    x = 1280 - text_width - padding
    y = 720 - text_height - padding
    draw.text((x, y), watermark_text, fill=(255, 255, 255, 200), font=watermark_font)

    background.save(filename)
    return filename

# Shortcut functions
async def gen_qthumb(videoid):
    return await generate_simple_thumb(videoid, f"cache/{videoid}_qv4.png")

async def gen_thumb(videoid):
    return await generate_simple_thumb(videoid, f"cache/{videoid}_v4.png")
