import os
import re
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from youtubesearchpython.__future__ import VideosSearch

# Fonts
title_font = ImageFont.truetype("assets/font3.ttf", 42)
channel_font = ImageFont.truetype("assets/font2.ttf", 34)
duration_font = ImageFont.truetype("assets/font.ttf", 30)
watermark_font = ImageFont.truetype("assets/font.ttf", 20)

# Full red blur overlay
def apply_red_blur_overlay(image, opacity=0.6):
    image = image.convert("RGBA")
    blurred = image.filter(ImageFilter.GaussianBlur(25))
    red_overlay = Image.new("RGBA", image.size, (255, 49, 99, int(255 * opacity)))
    red_blurred = Image.alpha_composite(blurred, red_overlay)
    red_blurred = ImageEnhance.Brightness(red_blurred).enhance(0.9)
    return red_blurred

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

    # Base background
    base = Image.open(f"cache/thumb_{videoid}.jpg").convert("RGBA").resize((1280, 720))
    background = apply_red_blur_overlay(base)
    draw = ImageDraw.Draw(background)

    # Centered back.png, song thumbnail, and control overlay
    try:
        # Load and center back.png
        back_img = Image.open("assets/back.png").convert("RGBA").resize((720, 400))
        cx = (1280 - back_img.width) // 2
        cy = (720 - back_img.height) // 2
        background.paste(back_img, (cx, cy), back_img)

        # Load and center song thumbnail on back.png
        song_thumb = Image.open(f"cache/thumb_{videoid}.jpg").convert("RGBA").resize((160, 160))
        thumb_x = cx + (back_img.width - 160) // 2
        thumb_y = cy + (back_img.height - 160) // 2
        background.paste(song_thumb, (thumb_x, thumb_y), song_thumb)

        # Load and overlay cntrol.png
        control_img = Image.open("assets/cntrol.png").convert("RGBA").resize((720, 400))
        background.paste(control_img, (cx, cy), control_img)

    except Exception as e:
        print(f"Error loading back/control images: {e}")
        return None

    # Title text
    first_word = title.split()[0] if title else ""
    draw.text((thumb_x + 180, thumb_y + 10), first_word, font=title_font, fill="white")

    # Channel name
    draw.text((thumb_x + 180, thumb_y + 70), channel, font=channel_font, fill="white")

    # Duration
    draw.text((thumb_x + 180, thumb_y + 120), f"Duration: {duration}", font=duration_font, fill="white")

    # Optional watermark at top
    draw.text((640, 60), "DnsXmusic", font=watermark_font, fill=(255, 255, 255, 180), anchor="mm")

    background.save(filename)
    return filename

# Shortcuts
async def gen_qthumb(videoid):
    return await generate_simple_thumb(videoid, f"cache/{videoid}_qv4.png")

async def gen_thumb(videoid):
    return await generate_simple_thumb(videoid, f"cache/{videoid}_v4.png")
