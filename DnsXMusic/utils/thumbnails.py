import os
import re
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFont
from youtubesearchpython.__future__ import VideosSearch

# Fonts
title_font = ImageFont.truetype("assets/font3.ttf", 50)
channel_font = ImageFont.truetype("assets/font2.ttf", 36)
duration_font = ImageFont.truetype("assets/font.ttf", 32)

# Dark overlay function
def apply_dark_overlay(image, opacity=0.7):
    black_overlay = Image.new("RGBA", image.size, (0, 0, 0, int(255 * opacity)))
    return Image.alpha_composite(image.convert("RGBA"), black_overlay)

# Generate thumbnail with dark overlay, text, and control image
async def generate_simple_thumb(videoid, filename):
    if os.path.isfile(filename):
        return filename

    # Get YouTube metadata
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

    # Load and resize thumbnail
    base = Image.open(f"cache/thumb_{videoid}.jpg").convert("RGBA").resize((1280, 720))
    dark_image = apply_dark_overlay(base)
    draw = ImageDraw.Draw(dark_image)

    # Draw text
    draw.text((640, 250), title, font=title_font, fill="white", anchor="mm")
    draw.text((640, 310), channel, font=channel_font, fill="white", anchor="mm")
    draw.text((640, 370), f"Duration: {duration}", font=duration_font, fill="white", anchor="mm")

    # Add control UI image in center
    try:
        control_img = Image.open("assets/cntrol.png").convert("RGBA")
        control_img = control_img.resize((500, 500))  # adjust size as needed
        cx = (1280 - control_img.width) // 2
        cy = (720 - control_img.height) // 2
        dark_image.paste(control_img, (cx, cy), mask=control_img)
    except Exception as e:
        print(f"Error loading control image: {e}")

    # Save final image
    dark_image.save(filename)
    return filename

# ✅ Quick thumbnail (gen_qthumb)
async def gen_qthumb(videoid):
    return await generate_simple_thumb(videoid, f"cache/{videoid}_qv4.png")

# ✅ Full thumbnail (gen_thumb)
async def gen_thumb(videoid):
    return await generate_simple_thumb(videoid, f"cache/{videoid}_v4.png")
