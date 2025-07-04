import os
import re
import aiohttp
import aiofiles
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from youtubesearchpython.__future__ import VideosSearch

title_font = ImageFont.truetype("assets/font3.ttf", 35)
channel_font = ImageFont.truetype("assets/font2.ttf", 25)
duration_font = ImageFont.truetype("assets/font.ttf", 10)
watermark_font = ImageFont.truetype("assets/font.ttf", 20)

def apply_black_fog(image, opacity=0.0):
    fog = Image.new("RGBA", image.size, (0, 0, 0, int(255 * opacity)))
    return Image.alpha_composite(image.convert("RGBA"), fog)

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
    background = apply_black_fog(base, opacity=0.5)
    draw = ImageDraw.Draw(background)

    try:
        rect_width = 600
        rect_height = 500
        cx = (1280 - rect_width) // 2
        cy = (720 - rect_height) // 2

        back_img = Image.open("assets/back.png").convert("RGBA").resize((rect_width, rect_height))
        background.paste(back_img, (cx, cy), back_img)

        song_thumb = Image.open(f"cache/thumb_{videoid}.jpg").convert("RGBA").resize((300, 245))
        thumb_x = cx + (rect_width - 300) // 2
        thumb_y = cy + 30
        background.paste(song_thumb, (thumb_x, thumb_y), song_thumb)

        control_img = Image.open("assets/cntrol.png").convert("RGBA").resize((rect_width, rect_height))
        background.paste(control_img, (cx, cy), control_img)

    except Exception as e:
        print(f"Error loading images: {e}")
        return None

    max_chars = 10
    title_words = title.split()
    short_title = ""
    total_chars = 0

    for word in title_words:
        if total_chars + len(word) + (1 if short_title else 0) <= max_chars:
            short_title += (" " if short_title else "") + word
            total_chars += len(word) + (1 if short_title else 0)
        else:
            break

    short_title = short_title.strip()
    if short_title != title:
        short_title += "..."

    draw.text((500, 380), short_title, font=title_font, fill="black")
    draw.text((500, 430), channel, font=channel_font, fill="black")
    draw.text((800, 480), f"{duration}", font=duration_font, fill="black")
    draw.text((590, 112), "DnsXmusic", font=watermark_font, fill="black")

    background.save(filename)
    return filename

async def gen_qthumb(videoid):
    return await generate_simple_thumb(videoid, f"cache/{videoid}_qv4.png")

async def gen_thumb(videoid):
    return await generate_simple_thumb(videoid, f"cache/{videoid}_v4.png")
