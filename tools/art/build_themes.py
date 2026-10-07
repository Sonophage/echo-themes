# Draws the art for the store's first-party themes (PSP, Wild, Ryoku, ECHO) into themes/<Name>/: every icon
# slot, a console icon per console, the wallpaper and its preview, and theme.json. All art is original: the
# PSP and Wild themes are drawn in the spirit of those menus, not from their assets. Sounds, README.md and
# Preview/ are kept as they are, except ECHO's sounds, which are made here.
# usage: python3 build_themes.py <echo-themes/themes> [Name ...]
import json, math, os, random, struct, sys, wave
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont
import glyphs

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = {
    # ECHO's own font, read from an echo-launcher checkout beside this repo (ECHO_LAUNCHER to point elsewhere)
    "sora": os.path.join(os.environ.get("ECHO_LAUNCHER", os.path.join(HERE, "..", "..", "..", "echo-launcher")),
                         "core", "core-ui", "src", "main", "res", "font", "sora_variable.ttf"),
    "mono": "/usr/share/fonts/TTF/JetBrainsMonoNerdFontMono-Bold.ttf",
    "kanji": "/usr/share/fonts/noto-cjk/NotoSerifCJK-Black.ttc",
}

CONSOLES = {
    "allgames": "ALL", "android": "AND", "atari2600": "2600", "atari5200": "5200", "atari7800": "7800",
    "atarilynx": "LYNX", "c64": "C64", "dreamcast": "DC", "gamegear": "GG", "gb": "GB", "gba": "GBA", "gbc": "GBC",
    "gc": "GC", "mame": "MAME", "mastersystem": "SMS", "megadrive": "MD", "n3ds": "3DS", "n64": "N64", "nds": "DS",
    "neogeo": "NEO", "nes": "NES", "ngp": "NGP", "pcengine": "PCE", "ps2": "PS2", "ps3": "PS3", "psp": "PSP",
    "psvita": "VITA", "psx": "PS1", "saturn": "SAT", "sega32x": "32X", "segacd": "SCD", "snes": "SNES",
    "switch": "NSW", "virtualboy": "VB", "wii": "WII", "wiiu": "WIIU", "windows": "PC", "wonderswan": "WS",
    "wonderswancolor": "WSC", "x360": "360",
}

KANJI = {
    "catbar_games": "遊", "catbar_music": "音", "catbar_video": "映", "catbar_photos": "写", "catbar_settings": "設",
    "catbar_network": "網", "catbar_appstore": "店", "catbar_favorites": "愛", "catbar_library": "書",
    "item_add": "加", "item_missing": "無", "item_memcard_games": "遊", "item_memcard_music": "音",
    "item_memcard_video": "映", "item_memcard_photos": "写", "item_settings": "工", "item_video_folder": "函",
    "item_video_library": "庫", "item_video_recent": "新", "item_video_favorites": "好", "item_video_collections": "集",
    "item_video_file": "片", "item_photo_folder": "綴", "item_photo_file": "画", "item_photo_albums": "帳",
    "item_library_shelves": "棚", "item_library_reader": "読", "item_library_folder": "束", "item_library_book": "本",
    "item_library_series": "巻", "item_camera": "撮", "item_search": "探", "item_music_track": "曲",
    "item_music_artists": "奏", "item_music_albums": "盤", "item_playlist": "列", "status_battery_full": "満",
    "status_battery_high": "高", "status_battery_medium": "中", "status_battery_low": "低",
    "status_battery_charging": "充", "status_bluetooth": "青",
}


def font(name, size, index=0, weight=None):
    f = ImageFont.truetype(FONTS[name], size, index=index)
    if weight and name == "sora":
        try: f.set_variation_by_axes([weight])
        except Exception: pass
    return f


def slot_size(key):
    return 128 if key.startswith("status") else 256


def glow(img, radius, strength=1.0, tint=None):
    a = img.split()[3].filter(ImageFilter.GaussianBlur(radius))
    if strength != 1.0: a = a.point(lambda v: min(255, int(v * strength)))
    col = Image.new("RGBA", img.size, tint or (255, 255, 255, 255)); col.putalpha(a)
    out = Image.new("RGBA", img.size, (0, 0, 0, 0)); out.alpha_composite(col); out.alpha_composite(img)
    return out


def text_img(size, label, fnt, color, box=0.62):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    f = fnt
    while d.textlength(label, font=f) > size * box and f.size > 8:
        f = f.font_variant(size=f.size - 2)
    d.text((size / 2, size / 2), label, font=f, fill=color, anchor="mm")
    return img


def noise(w, h, amount, seed=1):
    random.seed(seed)
    small = Image.new("L", (w // 4, h // 4))
    small.putdata([random.randint(128 - amount, 128 + amount) for _ in range(small.width * small.height)])
    return small.resize((w, h), Image.BICUBIC)


def vgrad(w, h, stops):
    img = Image.new("RGB", (w, h)); px = img.load()
    for y in range(h):
        t = y / (h - 1)
        for i in range(len(stops) - 1):
            (t0, c0), (t1, c1) = stops[i], stops[i + 1]
            if t0 <= t <= t1:
                k = (t - t0) / (t1 - t0); col = tuple(int(c0[j] + (c1[j] - c0[j]) * k) for j in range(3)); break
        for x in range(w): px[x, y] = col
    return img


def save_wallpaper(theme_dir, img):
    os.makedirs(f"{theme_dir}/Wallpaper", exist_ok=True)
    img.convert("RGB").save(f"{theme_dir}/Wallpaper/wallpaper.png", optimize=True)
    img.convert("RGB").resize((480, 270), Image.LANCZOS).save(f"{theme_dir}/Wallpaper/preview.png", optimize=True)


def write_icons(theme_dir, make_icon, make_console):
    for key in glyphs.GLYPHS:
        make_icon(key, slot_size(key)).save(f"{theme_dir}/Icons/{key}.png", optimize=True)
    for cid, label in CONSOLES.items():
        make_console(label, 256).save(f"{theme_dir}/Icons/Consoles/{cid}.png", optimize=True)


def manifest(theme_dir, **kv):
    path = f"{theme_dir}/theme.json"
    m = json.load(open(path)) if os.path.exists(path) else {}
    m.update({"manifest": "echo-theme", "schemaVersion": 3, "iconColor": "auto", "textColor": "auto", "layout": None,
              "source": {"type": "user-created", "file": None, "firmware": None}, "created": "2026-10-07"})
    m.update(kv)
    json.dump(m, open(path, "w"), indent=4, ensure_ascii=False)


# --- PSP: the crossbar's own look. White glyphs with a soft glow on the classic blue gradient, with the wave
# drawn into the wallpaper: ECHO hides its own wave over a wallpaper unless Wave over wallpaper is on -----------
def psp(d):
    def icon(key, size):
        g = glyphs.glyph(key, size, size * (0.040 if key.startswith("catbar") else 0.036), (255, 255, 255, 245))
        return glow(g, size * 0.035, 1.3, (190, 220, 255, 255))

    def console(label, size):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0)); dr = ImageDraw.Draw(img)
        dr.rounded_rectangle([size * .16, size * .30, size * .84, size * .70], radius=size * .08, outline=(255, 255, 255, 235), width=int(size * .025))
        img.alpha_composite(text_img(size, label, font("sora", 72, weight=600), (255, 255, 255, 245), 0.56))
        return glow(img, size * 0.03, 1.2, (190, 220, 255, 255))

    write_icons(d, icon, console)
    w, h = 1920, 1080
    bg = vgrad(w, h, [(0, (6, 26, 78)), (0.5, (18, 70, 160)), (1, (44, 118, 206))])
    light = Image.new("L", (w, h), 0); ImageDraw.Draw(light).ellipse([w * .45, h * .35, w * 1.4, h * 1.5], fill=90)
    light = light.filter(ImageFilter.GaussianBlur(260))
    bg = Image.composite(Image.new("RGB", (w, h), (70, 150, 236)), bg, light)
    vign = Image.new("L", (w, h), 0); ImageDraw.Draw(vign).rectangle([0, 0, w, h], fill=0)
    ImageDraw.Draw(vign).ellipse([-w * .2, -h * .3, w * 1.2, h * 1.3], fill=255); vign = vign.filter(ImageFilter.GaussianBlur(200))
    bg = Image.composite(bg, Image.new("RGB", (w, h), (4, 14, 44)), vign).convert("RGBA")
    # the wave: a soft broad band and a sheaf of thin lines that cross it, below the crossbar's icon row
    band = Image.new("RGBA", (w, h)); bd = ImageDraw.Draw(band)
    for k in range(18):
        ph, amp, off = k * 0.21, 70 + k * 3, k * 4
        pts = [(x, h * .60 + off + amp * math.sin(x * 0.0029 + ph) * math.sin(x * 0.0011 + 1.3)) for x in range(-20, w + 20, 6)]
        bd.line(pts, fill=(255, 255, 255, 34 if k % 4 else 70), width=2)
    wide = Image.new("RGBA", (w, h)); wd = ImageDraw.Draw(wide)
    pts = [(x, h * .62 + 80 * math.sin(x * 0.0029 + 1.4) * math.sin(x * 0.0011 + 1.3)) for x in range(-20, w + 20, 6)]
    wd.line(pts, fill=(200, 230, 255, 70), width=90)
    bg.alpha_composite(wide.filter(ImageFilter.GaussianBlur(50)))
    bg.alpha_composite(glow(band, 4, 1.2, (210, 235, 255, 255)))
    save_wallpaper(d, bg)
    manifest(d, name="PSP", accentColor="#8FB8FF", waveStyle="animated", waveDesign="PSP",
             gameBootStyle="DISC", launchDiscStyle="DISC", buttonSet="PLAYSTATION")


# --- Wild: dark slate tiles with cyan line glyphs over a dusk landscape -----------------------------------------
CYAN, GOLD = (96, 226, 232), (232, 198, 106)


def slate_tile(size):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0)); dr = ImageDraw.Draw(img)
    m = size * 0.08
    dr.rounded_rectangle([m, m, size - m, size - m], radius=size * 0.12, fill=(24, 36, 38, 235))
    dr.rounded_rectangle([m * 1.7, m * 1.7, size - m * 1.7, size - m * 1.7], radius=size * 0.09, outline=CYAN + (130,), width=max(2, int(size * .012)))
    c, L = m * 1.2, size * 0.13
    for (x, y, sx, sy) in ((c, c, 1, 1), (size - c, c, -1, 1), (c, size - c, 1, -1), (size - c, size - c, -1, -1)):
        dr.line([(x, y + sy * L), (x, y), (x + sx * L, y)], fill=CYAN + (220,), width=max(2, int(size * .018)))
    return img


def wild(d):
    def icon(key, size):
        tile = slate_tile(size)
        g = glyphs.glyph(key, int(size * 0.62), size * 0.62 * 0.045, CYAN + (255,))
        g = glow(g, size * 0.03, 1.4, CYAN + (255,))
        tile.alpha_composite(g, (int(size * 0.19), int(size * 0.19)))
        return tile

    def console(label, size):
        tile = slate_tile(size)
        tile.alpha_composite(glow(text_img(size, label, font("sora", 80, weight=700), CYAN + (255,), 0.56), size * .025, 1.2, CYAN + (255,)))
        return tile

    write_icons(d, icon, console)
    w, h = 1920, 1080
    sky = vgrad(w, h, [(0, (14, 40, 58)), (0.38, (64, 112, 120)), (0.58, (226, 176, 110)), (0.66, (240, 200, 140)), (1, (40, 60, 40))])
    img = sky.convert("RGBA"); dr = ImageDraw.Draw(img)
    random.seed(7)
    for _ in range(140):
        x, y = random.uniform(0, w), random.uniform(0, h * .3); r = random.uniform(.6, 1.8)
        dr.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 240, random.randint(60, 180)))
    sun = Image.new("RGBA", (w, h)); ImageDraw.Draw(sun).ellipse([w * .62, h * .48, w * .70, h * .62], fill=(255, 226, 160, 255))
    img.alpha_composite(glow(sun, 60, 1.5, (255, 210, 140, 255)))

    def ridge(base, amp, freq, seed, color, mist=0):
        random.seed(seed); ph = [random.uniform(0, 6.28) for _ in range(4)]
        pts = [(0, h)]
        for x in range(0, w + 8, 8):
            y = base - amp * (0.55 * math.sin(x * freq + ph[0]) + 0.3 * math.sin(x * freq * 2.3 + ph[1]) + 0.15 * math.sin(x * freq * 5.1 + ph[2]))
            pts.append((x, y))
        pts.append((w, h))
        layer = Image.new("RGBA", (w, h)); ImageDraw.Draw(layer).polygon(pts, fill=color)
        if mist:
            fog = Image.new("RGBA", (w, h)); fd = ImageDraw.Draw(fog)
            for i in range(30):
                fd.rectangle([0, base - amp + i * 6, w, base - amp + i * 6 + 6], fill=(230, 210, 170, max(0, mist - i * 3)))
            layer.alpha_composite(fog.filter(ImageFilter.GaussianBlur(20)))
        img.alpha_composite(layer)

    # a far snowy mountain
    random.seed(21); peak_x, peak_y, base_y = w * .34, h * .33, h * .64
    left, right = [], []
    for i in range(41):
        t = i / 40
        jag = random.uniform(-1, 1) * 14 * math.sin(math.pi * t)
        left.append((peak_x - t * w * .30, peak_y + t * (base_y - peak_y) + jag))
        right.append((peak_x + t * w * .26, peak_y + t * (base_y - peak_y) * 1.05 + jag))
    lay = Image.new("RGBA", (w, h)); ld = ImageDraw.Draw(lay)
    ld.polygon(list(reversed(left)) + right, fill=(96, 116, 136, 220))
    ld.polygon([(peak_x, peak_y)] + right + [(peak_x + w * .03, base_y)], fill=(74, 92, 112, 170))  # the shaded right flank
    snow = [(x, y) for x, y in left[:11]][::-1] + [(peak_x, peak_y)] + right[:10]
    snow += [(right[9][0] - w * .02, right[9][1] + 26), (peak_x, peak_y + h * .07), (left[10][0] + w * .02, left[10][1] + 22)]
    ld.polygon(snow, fill=(236, 240, 244, 225))
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(1.5)))
    ridge(h * .64, 40, 0.004, 1, (70, 98, 92, 255), mist=60)
    ridge(h * .72, 50, 0.003, 2, (46, 74, 58, 255), mist=40)
    ridge(h * .82, 60, 0.0025, 3, (30, 52, 36, 255))
    ridge(h * .93, 50, 0.005, 4, (18, 34, 24, 255))
    grass = Image.new("RGBA", (w, h)); gd = ImageDraw.Draw(grass); random.seed(11)
    for _ in range(900):
        x = random.uniform(0, w); y0 = h - random.uniform(0, 60); lean = random.uniform(-14, 14)
        gd.line([(x, h), (x + lean, y0 - random.uniform(10, 50))], fill=(12, 24, 16, 255), width=2)
    img.alpha_composite(grass)
    img = Image.blend(img.convert("RGB"), Image.merge("RGB", [noise(w, h, 18)] * 3), 0.05)
    save_wallpaper(d, img)
    manifest(d, name="Wild", accentColor="#E8C66A", waveStyle="reduced", waveDesign="ECHO_ARCS",
             gameBootStyle="LENS", launchDiscStyle="DISC", buttonSet="NINTENDO")


# --- Ryoku: a kanji for every slot on ink, a red sun, sumi-e mountains -------------------------------------------
INK, BONE, RED = (13, 13, 15), (232, 226, 214), (214, 64, 47)


def ryoku(d):
    def icon(key, size):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0)); dr = ImageDraw.Draw(img)
        ch = KANJI[key]
        if key.startswith("catbar"):
            dr.ellipse([size * .12, size * .12, size * .88, size * .88], fill=RED + (255,))
            dr.text((size / 2, size * .53), ch, font=font("kanji", int(size * .50)), fill=BONE + (255,), anchor="mm")
        elif key.startswith("item_memcard"):
            dr.rectangle([size * .2, size * .14, size * .8, size * .86], outline=BONE + (230,), width=max(2, int(size * .02)))
            dr.rectangle([size * .2, size * .74, size * .8, size * .86], fill=RED + (230,))
            dr.text((size / 2, size * .45), ch, font=font("kanji", int(size * .40)), fill=BONE + (255,), anchor="mm")
        else:
            dr.text((size / 2, size * .47), ch, font=font("kanji", int(size * .58)), fill=BONE + (255,), anchor="mm")
            dr.line([(size * .30, size * .86), (size * .70, size * .86)], fill=RED + (255,), width=max(2, int(size * .03)))
        return img

    def console(label, size):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0)); dr = ImageDraw.Draw(img)
        dr.line([(size * .18, size * .30), (size * .18, size * .70)], fill=RED + (255,), width=int(size * .035))
        img.alpha_composite(text_img(size, label, font("mono", 80), BONE + (255,), 0.56))
        return img

    write_icons(d, icon, console)
    w, h = 1920, 1080
    img = Image.new("RGBA", (w, h), INK + (255,))
    paper = Image.merge("RGBA", [noise(w, h, 22, 5)] * 3 + [Image.new("L", (w, h), 14)])
    img.alpha_composite(paper)
    # the sun sits below the crossbar's icon row, right of the menus
    sun = Image.new("RGBA", (w, h)); ImageDraw.Draw(sun).ellipse([w * .66, h * .34, w * .80, h * .34 + w * .14], fill=RED + (255,))
    img.alpha_composite(glow(sun, 40, 0.6, RED + (255,)))
    big = Image.new("RGBA", (w, h)); ImageDraw.Draw(big).text((w * .16, h * .48), "力", font=font("kanji", 760), fill=BONE + (16,), anchor="mm")
    img.alpha_composite(big)

    def sumi(base, amp, seed, shade, blur):
        random.seed(seed); ph = [random.uniform(0, 6.28) for _ in range(5)]; pts = [(0, h)]
        for x in range(0, w + 4, 4):
            v = (0.50 * math.sin(x * 0.0032 + ph[0]) + 0.28 * math.sin(x * 0.0071 + ph[1])
                 + 0.14 * abs(math.sin(x * 0.0150 + ph[2])) + 0.05 * math.sin(x * 0.041 + ph[3]))
            pts.append((x, base - amp * v))
        pts.append((w, h))
        layer = Image.new("RGBA", (w, h)); ImageDraw.Draw(layer).polygon(pts, fill=(shade, shade, shade + 2, 255))
        grad = Image.new("L", (w, h)); gd = ImageDraw.Draw(grad)
        for yy in range(h): gd.line([(0, yy), (w, yy)], fill=max(0, min(255, int(255 - (yy - base + amp) * 0.7))))
        layer.putalpha(ImageChops.multiply(layer.split()[3], grad))
        img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(blur)))

    sumi(h * .60, 120, 3, 74, 10)
    sumi(h * .70, 110, 4, 50, 6)
    sumi(h * .82, 90, 5, 28, 3)
    rule = ImageDraw.Draw(img); rule.line([(w * .92, h * .18), (w * .92, h * .82)], fill=BONE + (90,), width=2)
    rule.text((w * .935, h * .20), "力\n場", font=font("kanji", 34), fill=BONE + (150,), spacing=14)
    save_wallpaper(d, img)
    manifest(d, name="Ryoku", accentColor="#D6402F", iconColor="#E8E2D6", textColor="#E8E2D6", waveStyle="static",
             waveDesign="ECHO_RINGS", gameBootStyle="LENS", launchDiscStyle="DISC", buttonSet="GENERIC")


# --- ECHO: the brand. Ice-cyan line glyphs inside echo rings on the night base, the mark in its rings ---------
BASE, ICE, MIST = (4, 6, 12), (159, 220, 236), (238, 242, 246)


def echo_mark(size, color=MIST):
    # the mark from EchoMarkPaths: crescents are a disc of r26 less the r30 disc at the ring's centre
    S = size * 4; k = S / 132; img = Image.new("L", (S, S), 0); dr = ImageDraw.Draw(img)
    def disc(cx, cy, r, fill):
        cx, cy = (cx - 22) * k, (cy + 12) * k; dr.ellipse([cx - r * k, cy - r * k, cx + r * k, cy + r * k], fill=fill)
    disc(52, 40, 26, 255); disc(124, 40, 26, 255); disc(88, 40, 30, 0)
    cx, cy = (88 - 22) * k, (40 + 12) * k
    dr.ellipse([cx - 21 * k, cy - 21 * k, cx + 21 * k, cy + 21 * k], outline=255, width=int(5 * k))
    disc(88, 86, 8, 255)
    out = Image.new("RGBA", (S, S), color + (255,)); out.putalpha(img)
    return out.resize((size, size), Image.LANCZOS)


def echo(d):
    def rings(size):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0)); dr = ImageDraw.Draw(img)
        for r, a in ((0.44, 110), (0.49, 45)):
            dr.ellipse([size * (0.5 - r), size * (0.5 - r), size * (0.5 + r), size * (0.5 + r)], outline=ICE + (a,), width=max(2, int(size * .012)))
        return img

    def icon(key, size):
        img = rings(size)
        g = glyphs.glyph(key, int(size * 0.64), size * 0.64 * 0.042, MIST + (255,))
        img.alpha_composite(glow(g, size * 0.02, 0.9, ICE + (255,)), (int(size * .18), int(size * .18)))
        return img

    def console(label, size):
        img = rings(size)
        img.alpha_composite(text_img(size, label, font("sora", 76, weight=600), MIST + (255,), 0.54))
        return img

    write_icons(d, icon, console)
    w, h = 1920, 1080
    img = Image.new("RGBA", (w, h), BASE + (255,))
    cx, cy = w * .70, h * .46
    halo = Image.new("RGBA", (w, h)); ImageDraw.Draw(halo).ellipse([cx - 360, cy - 360, cx + 360, cy + 360], fill=ICE + (40,))
    img.alpha_composite(halo.filter(ImageFilter.GaussianBlur(160)))
    ring = Image.new("RGBA", (w, h)); rd = ImageDraw.Draw(ring)
    for i in range(1, 14):
        r = 120 + i * i * 9
        rd.ellipse([cx - r, cy - r, cx + r, cy + r], outline=ICE + (max(10, 120 - i * 9),), width=2)
    img.alpha_composite(ring)
    m = Image.new("RGBA", (500, 500)); m.alpha_composite(echo_mark(300), (100, 100))
    img.alpha_composite(glow(m, 18, 0.8, ICE + (255,)), (int(cx - 250), int(cy - 250)))
    img = Image.blend(img.convert("RGB"), Image.merge("RGB", [noise(w, h, 10, 9)] * 3), 0.03)
    save_wallpaper(d, img)
    manifest(d, name="ECHO", accentColor="#9FDCEC", waveStyle="animated", waveDesign="ECHO_RINGS",
             gameBootStyle="LENS", launchDiscStyle="DISC")
    # soft, short sounds: a two-partial sine ping for each interface sound
    sounds = {"sound_scroll": (50, 1568), "sound_select": (110, 1175), "sound_system_browse": (80, 988),
              "sound_back": (130, 784), "sound_confirm": (240, 1319), "sound_error": (260, 330),
              "sound_launch": (1100, 523), "sound_notification": (520, 1760)}
    os.makedirs(f"{d}/Sounds", exist_ok=True)
    for key, (ms, f0) in sounds.items():
        rate = 44100; n = int(rate * ms / 1000); frames = bytearray()
        for i in range(n):
            t = i / rate; env = min(1, t * 400) * math.exp(-5 * t / (ms / 1000))
            s = 0.7 * math.sin(2 * math.pi * f0 * t) + 0.3 * math.sin(2 * math.pi * f0 * 2.01 * t)
            frames += struct.pack("<h", int(12000 * env * s))
        with wave.open(f"{d}/Sounds/{key}.wav", "wb") as wv:
            wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(rate); wv.writeframes(bytes(frames))


BUILDERS = {"PSP": psp, "Wild": wild, "Ryoku": ryoku, "ECHO": echo}

if __name__ == "__main__":
    root = sys.argv[1]
    for name in sys.argv[2:] or BUILDERS:
        d = os.path.join(root, name)
        os.makedirs(f"{d}/Icons/Consoles", exist_ok=True)
        BUILDERS[name](d)
        print("built", name)
