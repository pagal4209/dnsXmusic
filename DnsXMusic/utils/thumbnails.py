import os
import re
from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageFilter
import aiohttp
import aiofiles
from youtubesearchpython.__future__ import VideosSearch


async def gen_thumb(videoid):
    if os.path.isfile(f"cache/{videoid}_musicui.png"):
        return f"cache/{videoid}_musicui.png"

    url = f"https://www.youtube.com/watch?v={videoid}"
    results = VideosSearch(url, limit=1)
    for result in (await results.next())["result"]:
        title = re.sub(r"\W+", " ", result.get("title", "Unknown Title")).title()
        duration = result.get("duration", "Unknown")
        thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        channel = result.get("channel", {}).get("name", "Unknown Artist")

    async with aiohttp.ClientSession() as session:
        async with session.get(thumbnail) as resp:
            if resp.status == 200:
                f = await aiofiles.open(f"cache/thumb_temp_{videoid}.png", mode="wb")
                await f.write(await resp.read())
                await f.close()

    yt_thumb = Image.open(f"cache/thumb_temp_{videoid}.png").resize((1280, 720)).convert("RGBA")
    city_bg = Image.open("assets/bg.jpg").resize((1280, 720)).convert("RGBA")  # Use your uploaded background

    blurred = yt_thumb.filter(ImageFilter.BoxBlur(8))
    enhancer = ImageEnhance.Brightness(blurred)
    blurred = enhancer.enhance(0.6)

    final_bg = Image.blend(blurred, city_bg, alpha=0.4)
    draw = ImageDraw.Draw(final_bg)

    title_font = ImageFont.truetype("assets/font3.ttf", 50)
    artist_font = ImageFont.truetype("assets/font2.ttf", 35)
    arial = ImageFont.truetype("assets/font2.ttf", 30)

    yt_box = yt_thumb.resize((260, 160))
    final_bg.paste(yt_box, (80, 150))

    black_bar = Image.new("RGBA", (1280, 180), (0, 0, 0, 200))
    final_bg.paste(black_bar, (0, 500), black_bar)

    draw.text((360, 520), title, font=title_font, fill=(255, 255, 255))
    draw.text((360, 580), channel, font=artist_font, fill=(200, 200, 200))

    bar_y = 610
    draw.line([(360, bar_y), (880, bar_y)], fill="white", width=6)
    draw.line([(360, bar_y), (560, bar_y)], fill="red", width=6)
    draw.ellipse([(553, bar_y - 7), (567, bar_y + 7)], fill="red")

    draw.text((360, 580), "1:00", font=arial, fill=(255, 255, 255))
    draw.text((880, 580), duration, font=arial, fill=(255, 255, 255))

    try:
        controls = Image.open("assets/play_icons.png").resize((300, 50))
        final_bg.paste(controls, (490, 630), controls)
    except:
        draw.text((540, 640), "▶ || ⏭", font=title_font, fill=(255, 255, 255))

    try:
        os.remove(f"cache/thumb_temp_{videoid}.png")
    except:
        pass

    final_path = f"cache/{videoid}_musicui.png"
    final_bg.save(final_path)
    return final_path


# 🔁 Dummy wrappers for compatibility
async def gen_thumb(videoid):
    return await gen_music_ui_thumb(videoid)

async def gen_qthumb(videoid):
    return await gen_music_ui_thumb(videoid)
