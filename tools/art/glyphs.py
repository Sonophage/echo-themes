# Line-art pictograms for every ECHO icon slot, drawn from primitives so every theme can style them.
# Each glyph draws into a square of side S (units 0..1), with a pen of the given width, at 4x for smoothing.
import math
from PIL import Image, ImageDraw

SS = 4  # supersampling


class Pen:
    def __init__(self, size, width, color=(255, 255, 255, 255)):
        self.S = size * SS
        self.w = max(1, int(width * SS))
        self.c = color
        self.img = Image.new("RGBA", (self.S, self.S), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def p(self, x, y):
        return (x * self.S, y * self.S)

    def line(self, *pts):
        q = [self.p(*pt) for pt in pts]
        self.d.line(q, fill=self.c, width=self.w, joint="curve")
        r = self.w / 2
        for x, y in (q[0], q[-1]):
            self.d.ellipse([x - r, y - r, x + r, y + r], fill=self.c)

    def rect(self, x0, y0, x1, y1, r=0.06, fill=False):
        box = [*self.p(x0, y0), *self.p(x1, y1)]
        if fill:
            self.d.rounded_rectangle(box, radius=r * self.S, fill=self.c)
        else:
            self.d.rounded_rectangle(box, radius=r * self.S, outline=self.c, width=self.w)

    def circle(self, cx, cy, r, fill=False):
        box = [*self.p(cx - r, cy - r), *self.p(cx + r, cy + r)]
        if fill:
            self.d.ellipse(box, fill=self.c)
        else:
            self.d.ellipse(box, outline=self.c, width=self.w)

    def arc(self, cx, cy, r, a0, a1):
        self.d.arc([*self.p(cx - r, cy - r), *self.p(cx + r, cy + r)], a0, a1, fill=self.c, width=self.w)

    def poly(self, pts, fill=True):
        q = [self.p(*pt) for pt in pts]
        if fill:
            self.d.polygon(q, fill=self.c)
        else:
            self.d.line(q + [q[0]], fill=self.c, width=self.w, joint="curve")

    def done(self, size):
        return self.img.resize((size, size), Image.LANCZOS)


# --- base pictograms -----------------------------------------------------------------------------------
def controller(p):
    p.line((0.30, 0.36), (0.70, 0.36))
    p.d.rounded_rectangle([*p.p(0.16, 0.34), *p.p(0.84, 0.66)], radius=0.16 * p.S, outline=p.c, width=p.w)
    p.line((0.30, 0.45), (0.30, 0.57)); p.line((0.24, 0.51), (0.36, 0.51))
    p.circle(0.66, 0.47, 0.03, fill=True); p.circle(0.72, 0.54, 0.03, fill=True)


def note(p, x=0.5):
    p.circle(x - 0.10, 0.70, 0.08, fill=True)
    p.line((x - 0.03, 0.70), (x - 0.03, 0.24), (x + 0.18, 0.30))


def film(p):
    p.rect(0.18, 0.28, 0.82, 0.72, r=0.05)
    for x in (0.27, 0.40, 0.53, 0.66):
        p.rect(x, 0.31, x + 0.06, 0.35, r=0.01, fill=True); p.rect(x, 0.65, x + 0.06, 0.69, r=0.01, fill=True)
    p.poly([(0.44, 0.42), (0.44, 0.58), (0.58, 0.50)])


def photo(p):
    p.rect(0.18, 0.26, 0.82, 0.74, r=0.06)
    p.line((0.24, 0.66), (0.42, 0.46), (0.54, 0.58), (0.64, 0.50), (0.76, 0.64))
    p.circle(0.66, 0.38, 0.05, fill=True)


def gear(p):
    cx, cy = 0.5, 0.5
    for i in range(8):
        a = i * math.pi / 4
        p.line((cx + 0.20 * math.cos(a), cy + 0.20 * math.sin(a)), (cx + 0.30 * math.cos(a), cy + 0.30 * math.sin(a)))
    p.circle(cx, cy, 0.20); p.circle(cx, cy, 0.07)


def globe(p):
    p.circle(0.5, 0.5, 0.28)
    p.d.ellipse([*p.p(0.38, 0.22), *p.p(0.62, 0.78)], outline=p.c, width=p.w)
    p.line((0.22, 0.5), (0.78, 0.5)); p.line((0.27, 0.36), (0.73, 0.36)); p.line((0.27, 0.64), (0.73, 0.64))


def bag(p):
    p.poly([(0.22, 0.38), (0.78, 0.38), (0.74, 0.80), (0.26, 0.80)], fill=False)
    p.arc(0.5, 0.38, 0.14, 180, 360)


def star(p, cx=0.5, cy=0.52, r=0.30, fill=False):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    p.poly(pts, fill=fill)


def books(p):
    for x, h in ((0.22, 0.50), (0.36, 0.56), (0.50, 0.46)):
        p.rect(x, 0.78 - h, x + 0.11, 0.78, r=0.02)
    p.line((0.66, 0.34), (0.80, 0.76)); p.line((0.60, 0.36), (0.66, 0.34))
    p.line((0.18, 0.80), (0.84, 0.80))


def plus(p):
    p.circle(0.5, 0.5, 0.30); p.line((0.5, 0.36), (0.5, 0.64)); p.line((0.36, 0.5), (0.64, 0.5))


def question(p):
    p.circle(0.5, 0.5, 0.30); p.arc(0.5, 0.42, 0.09, 200, 380)
    p.line((0.58, 0.45), (0.5, 0.52), (0.5, 0.57)); p.circle(0.5, 0.66, 0.025, fill=True)


def card(p, inner):
    p.poly([(0.30, 0.18), (0.64, 0.18), (0.74, 0.28), (0.74, 0.82), (0.30, 0.82)], fill=False)
    for x in (0.38, 0.47, 0.56):
        p.rect(x, 0.70, x + 0.05, 0.78, r=0.01, fill=True)
    small(p, inner, 0.52, 0.44, 0.42)


def wrench(p):
    # an open-end wrench: a shaft to a jaw open at the top right
    p.line((0.26, 0.74), (0.56, 0.44))
    p.arc(0.64, 0.36, 0.13, 100, 350)
    p.line((0.68, 0.24), (0.62, 0.36), (0.74, 0.40))


def folder(p, inner=None):
    p.poly([(0.16, 0.30), (0.40, 0.30), (0.46, 0.36), (0.84, 0.36), (0.84, 0.76), (0.16, 0.76)], fill=False)
    if inner: small(p, inner, 0.5, 0.57, 0.40)


def clock(p):
    p.circle(0.5, 0.5, 0.28); p.line((0.5, 0.34), (0.5, 0.5), (0.62, 0.58))


def stack(p, inner):
    p.rect(0.30, 0.22, 0.80, 0.64, r=0.05); p.line((0.22, 0.32), (0.22, 0.72), (0.70, 0.72))
    small(p, inner, 0.55, 0.43, 0.36)


def page(p, inner):
    p.poly([(0.26, 0.18), (0.60, 0.18), (0.74, 0.32), (0.74, 0.82), (0.26, 0.82)], fill=False)
    p.line((0.60, 0.18), (0.60, 0.32), (0.74, 0.32))
    small(p, inner, 0.50, 0.58, 0.40)


def shelves(p):
    for y in (0.46, 0.78):
        p.line((0.16, y), (0.84, y))
        for x, h in ((0.22, 0.20), (0.32, 0.24), (0.42, 0.18), (0.60, 0.22)):
            p.rect(x, y - h, x + 0.07, y - 0.03, r=0.01)


def open_book(p):
    p.line((0.5, 0.30), (0.5, 0.76))
    p.poly([(0.5, 0.30), (0.18, 0.26), (0.18, 0.72), (0.5, 0.76)], fill=False)
    p.poly([(0.5, 0.30), (0.82, 0.26), (0.82, 0.72), (0.5, 0.76)], fill=False)


def book(p):
    p.rect(0.28, 0.20, 0.74, 0.80, r=0.04); p.line((0.36, 0.20), (0.36, 0.80)); p.line((0.46, 0.34), (0.66, 0.34))


def series(p):
    for i, x in enumerate((0.20, 0.38, 0.56)):
        p.rect(x, 0.24 + i * 0.04, x + 0.22, 0.78, r=0.03)


def camera(p):
    p.rect(0.16, 0.34, 0.84, 0.74, r=0.07); p.poly([(0.36, 0.34), (0.42, 0.24), (0.58, 0.24), (0.64, 0.34)], fill=False)
    p.circle(0.5, 0.54, 0.12)


def magnifier(p):
    p.circle(0.44, 0.44, 0.20); p.line((0.58, 0.58), (0.78, 0.78))


def person(p):
    p.circle(0.5, 0.36, 0.12); p.arc(0.5, 0.82, 0.30, 200, 340)


def disc(p):
    p.circle(0.5, 0.5, 0.30); p.circle(0.5, 0.5, 0.07)


def playlist(p):
    for y in (0.30, 0.44, 0.58):
        p.line((0.18, y), (0.54, y))
    p.circle(0.64, 0.72, 0.07, fill=True); p.line((0.71, 0.72), (0.71, 0.40), (0.84, 0.44))


def battery(p, level, bolt=False):
    p.rect(0.14, 0.34, 0.80, 0.66, r=0.05); p.rect(0.80, 0.44, 0.86, 0.56, r=0.01, fill=True)
    if level > 0:
        p.rect(0.19, 0.40, 0.19 + 0.56 * level, 0.60, r=0.02, fill=True)
    if bolt:
        p.poly([(0.52, 0.22), (0.36, 0.52), (0.48, 0.52), (0.42, 0.78), (0.62, 0.44), (0.50, 0.44)])


def bluetooth(p):
    p.line((0.34, 0.34), (0.66, 0.64), (0.5, 0.78), (0.5, 0.22), (0.66, 0.36), (0.34, 0.66))


def small(p, fn, cx, cy, scale):
    # draws another glyph at [scale] of the square, centred on (cx, cy)
    sub = Pen(p.S // SS, p.w / SS / scale * 0.85, p.c)
    fn(sub)
    im = sub.img.resize((int(p.S * scale), int(p.S * scale)), Image.LANCZOS)
    p.img.alpha_composite(im, (int(cx * p.S - im.width / 2), int(cy * p.S - im.height / 2)))


GLYPHS = {
    "catbar_games": controller, "catbar_music": note, "catbar_video": film, "catbar_photos": photo,
    "catbar_settings": gear, "catbar_network": globe, "catbar_appstore": bag, "catbar_favorites": star,
    "catbar_library": books,
    "item_add": plus, "item_missing": question,
    "item_memcard_games": lambda p: card(p, controller), "item_memcard_music": lambda p: card(p, note),
    "item_memcard_video": lambda p: card(p, film), "item_memcard_photos": lambda p: card(p, photo),
    "item_settings": wrench,
    "item_video_folder": lambda p: folder(p, film), "item_video_library": lambda p: stack(p, film),
    "item_video_recent": clock, "item_video_favorites": lambda p: star(p, fill=False),
    "item_video_collections": lambda p: stack(p, star), "item_video_file": lambda p: page(p, film),
    "item_photo_folder": lambda p: folder(p, photo), "item_photo_file": lambda p: page(p, photo),
    "item_photo_albums": lambda p: stack(p, photo),
    "item_library_shelves": shelves, "item_library_reader": open_book, "item_library_folder": lambda p: folder(p, book),
    "item_library_book": book, "item_library_series": series,
    "item_camera": camera, "item_search": magnifier,
    "item_music_track": note, "item_music_artists": person, "item_music_albums": disc, "item_playlist": playlist,
    "status_battery_full": lambda p: battery(p, 1.0), "status_battery_high": lambda p: battery(p, 0.7),
    "status_battery_medium": lambda p: battery(p, 0.45), "status_battery_low": lambda p: battery(p, 0.15),
    "status_battery_charging": lambda p: battery(p, 0.6, bolt=True), "status_bluetooth": bluetooth,
}


def glyph(key, size, width, color=(255, 255, 255, 255)):
    pen = Pen(size, width, color)
    GLYPHS[key](pen)
    return pen.done(size)
