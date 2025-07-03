import os
import re
from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageFilter
import aiohttp
import aiofiles
from youtubesearchpython.__future__ import VideosSearch

async def gen_thumb(videoid):
    if os.path.isfile(f"cache/{videoid}_musicui.png"):
        return f"cache/{videoid}_musicui.png"

    # Search YouTube video
    url = f"https://www.youtube.com/watch?v={videoid}"
    results = VideosSearch(url, limit=1)
    for result in (await results.next())["result"]:
        title = re.sub(r"\W+", " ", result.get("title", "Unknown Title")).title()
        duration = result.get("duration", "Unknown")
        thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        channel = result.get("channel", {}).get("name", "Unknown Artist")

    # Download thumbnail image
    async with aiohttp.ClientSession() as session:
        async with session.get(thumbnail) as resp:
            if resp.status == 200:
                f = await aiofiles.open(f"cache/thumb_temp_{videoid}.png", mode="wb")
                await f.write(await resp.read())
                await f.close()

    # Open images
    yt_thumb = Image.open(f"cache/thumb_temp_{videoid}.png").resize((1280, 720)).convert("RGBA")
    city_bg = Image.open("/mnt/data/IMG_20250703_235841_453.jpg").resize((1280, 720)).convert("RGBA")

    # Blur YouTube thumbnail for background
    blurred = yt_thumb.filter(ImageFilter.BoxBlur(8))
    enhancer = ImageEnhance.Brightness(blurred)
    blurred = enhancer.enhance(0.6)

    # Blend the blurred background with the city image
    final_bg = Image.blend(blurred, city_bg, alpha=0.4)
    draw = ImageDraw.Draw(final_bg)

    # Fonts
    title_font = ImageFont.truetype("assets/font3.ttf", 50)
    artist_font = ImageFont.truetype("assets/font2.ttf", 35)
    arial = ImageFont.truetype("assets/font2.ttf", 30)

    # Paste the YouTube thumbnail on left side
    yt_box = yt_thumb.resize((260, 160))
    final_bg.paste(yt_box, (80, 150))

    # Create a black bar at the bottom
    black_bar = Image.new("RGBA", (1280, 180), (0, 0, 0, 200))
    final_bg.paste(black_bar, (0, 500), black_bar)

    # Write the song title and artist
    draw.text((360, 520), title, font=title_font, fill=(255, 255, 255))
    draw.text((360, 580), channel, font=artist_font, fill=(200, 200, 200))

    # Progress bar
    bar_y = 610
    draw.line([(360, bar_y), (880, bar_y)], fill="white", width=6)  # full bar
    draw.line([(360, bar_y), (560, bar_y)], fill="red", width=6)    # progress
    draw.ellipse([(553, bar_y - 7), (567, bar_y + 7)], fill="red")  # knob

    # Write duration and timestamp
    draw.text((360, 580), "1:00", font=arial, fill=(255, 255, 255))
    draw.text((880, 580), duration, font=arial, fill=(255, 255, 255))

    # Add play controls icon (if available)
    try:
        controls = Image.open("assets/play_icons.png").resize((300, 50))
        final_bg.paste(controls, (490, 630), controls)
    except:
        draw.text((540, 640), "▶ || ⏭", font=title_font, fill=(255, 255, 255))

    # Clean up and save the generated image
    try:
        os.remove(f"cache/thumb_temp_{videoid}.png")
    except:
        pass
    final_path = f"cache/{videoid}_musicui.png"
    final_bg.save(final_path)
    return final_path
