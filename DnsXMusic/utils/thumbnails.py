import os
import re
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFont
from youtubesearchpython.__future__ import VideosSearch

# Fonts
title_font = ImageFont.truetype("assets/font3.ttf", 42)      # Smaller for wrapped lines
channel_font = ImageFont.truetype("assets/font2.ttf", 34)
duration_font = ImageFont.truetype("assets/font.ttf", 30)

# Dark overlay function
def apply_dark_overlay(image, opacity=0.7):
    black_overlay = Image.new("RGBA", image.size, (0, 0, 0, int(255 * opacity)))
    return Image.alpha_composite(image.convert("RGBA"), black_overlay)

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

    # Draw all lines centered
    y = y_start
    for line in lines:
        draw.text((image_width // 2, y), line, font=font, fill="white", anchor="mm")
        y += font.getsize(line)[1] + line_spacing

# Main thumbnail generator
async def generate_simple_thumb(videoid, filename):
    if os.path.isfile(filename):
        return filename

    # Get metadata
    url = f"https://www.youtube.com/watch?v={videoid}"
    results = VideosSearch(url, limit=1)
    result = (await results.next())["result"][0]

    title = re.sub(r"\W+", " ", result.get("title", "Unknown Title")).title()
    channel = result.get("channel", {}).get("name", "Unknown Channel")
    duration = result.get("duration", "0:00")
    thumbnail_url = result["thumbnails"][0]["url"].split("?")[0]

    # Download thumbnail
    async with aiohttp.ClientSession() as session:
        async with session.get(thumbnail_url) as resp:
            if resp.status == 200:
                async with aiofiles.open(f"cache/thumb_{videoid}.jpg", "wb") as f:
                    await f.write(await resp.read())

    # Load and prepare base image
    base = Image.open(f"cache/thumb_{videoid}.jpg").convert("RGBA").resize((1280, 720))
    dark_image = apply_dark_overlay(base)
    draw = ImageDraw.Draw(dark_image)

    # Load and paste control UI image
    try:
        control_img = Image.open("assets/cntrol.png").convert("RGBA")
        control_img = control_img.resize((600, 600))  # Increased size
        cx = (1280 - control_img.width) // 2
        cy = (720 - control_img.height) // 2
        dark_image.paste(control_img, (cx, cy), mask=control_img)
    except Exception as e:
        print(f"Error loading control image: {e}")

    # Draw title (wrapped & centered)
    draw_multiline_centered_text(draw, title, title_font, 1280, cy + 70)

    # Draw channel and duration below title
    draw.text((640, cy + 170), channel, font=channel_font, fill="white", anchor="mm")
    draw.text((640, cy + 220), f"Duration: {duration}", font=duration_font, fill="white", anchor="mm")
    draw.text((285, cy + 180), "DnsXmusic", (192, 192, 192), font=title_font, fill=" white", anchor="mn")
    # Save thumbnail
    dark_image.save(filename)
    return filename

# Shortcut functions
async def gen_qthumb(videoid):
    return await generate_simple_thumb(videoid, f"cache/{videoid}_qv4.png")

async def gen_thumb(videoid):
    return await generate_simple_thumb(videoid, f"cache/{videoid}_v4.png")
