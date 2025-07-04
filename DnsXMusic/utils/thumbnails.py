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

# Apply soft black fog overlay
def apply_black_fog(image, opacity=0.3):
    fog = Image.new("RGBA", image.size, (0, 0, 0, int(255 * opacity)))
    return Image.alpha_composite(image.convert("RGBA"), fog)

# Main function
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

    # Load base image (YouTube thumbnail)
    base = Image.open(f"cache/thumb_{videoid}.jpg").convert("RGBA").resize((1280, 720))

    # Add soft black fog
    background = apply_black_fog(base, opacity=0.3)
    draw = ImageDraw.Draw(background)

    try:
        # Rectangle size
        rect_width = 600
        rect_height = 500

        # Center coordinates
        cx = (1280 - rect_width) // 2
        cy = (720 - rect_height) // 2

        # Back rectangle
        back_img = Image.open("assets/back.png").convert("RGBA").resize((rect_width, rect_height))
        background.paste(back_img, (cx, cy), back_img)

        # Song thumbnail on left inside rectangle
        song_thumb = Image.open(f"cache/thumb_{videoid}.jpg").convert("RGBA").resize((290, 260))
        thumb_x = cx + (rect_width - 290 ) // 2
        thumb_y = cy + 30
        background.paste(song_thumb, (thumb_x, thumb_y), song_thumb)

        # Overlay control.png on rectangle
        control_img = Image.open("assets/cntrol.png").convert("RGBA").resize((rect_width, rect_height))
        background.paste(control_img, (cx, cy), control_img)

    except Exception as e:
        print(f"Error loading images: {e}")
        return None

    # Title
    first_word = title.split()[0] if title else ""
    draw.text((thumb_x + 180, thumb_y), first_word, font=title_font, fill="red")

    # Channel
    draw.text((thumb_x + 180, thumb_y + 60), channel, font=channel_font, fill="red")

    # Duration
    draw.text((thumb_x + 180, thumb_y + 120), f"{duration}", font=duration_font, fill="red")

    # Watermark
    draw.text((640, 60), "DnsXmusic", font=watermark_font, fill=(255, 255, 255, 180), anchor="mm")

    background.save(filename)
    return filename

# Shortcut functions
async def gen_qthumb(videoid):
    return await generate_simple_thumb(videoid, f"cache/{videoid}_qv4.png")

async def gen_thumb(videoid):
    return await generate_simple_thumb(videoid, f"cache/{videoid}_v4.png")
