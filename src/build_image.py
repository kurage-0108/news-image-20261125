#!/usr/bin/env python3
"""Build the 'world news in one page' broadsheet image (1024x1024 PNG).

Renders at 2x (2048x2048) and downscales with LANCZOS for crisp small text.
Deterministic: same inputs -> same bytes.
"""
import json, os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
S = 2
W = H = 1024 * S

PAPER = (246, 241, 229)
INK = (24, 22, 18)
INK_SOFT = (58, 53, 44)
MUTED = (110, 101, 84)
RED = (158, 27, 27)
RED_D = (122, 20, 20)
RULE = (24, 22, 18)
HAIR = (196, 188, 168)

F = {
    "black": "/usr/share/fonts/truetype/noto/NotoSerif-Black.ttf",
    "serif_b": "/usr/share/fonts/truetype/noto/NotoSerif-Bold.ttf",
    "serif": "/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf",
    "serif_it": "/usr/share/fonts/truetype/noto/NotoSerif-Italic.ttf",
    "times_b": "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    "sans_cb": "/usr/share/fonts/truetype/noto/NotoSans-CondensedBold.ttf",
    "sans_c": "/usr/share/fonts/truetype/noto/NotoSans-Condensed.ttf",
}
_fonts = {}
def font(name, size):
    key = (name, size)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(F[name], size)
    return _fonts[key]

img = Image.new("RGB", (W, H), PAPER)
dr = ImageDraw.Draw(img, "RGBA")

def text_w(s, f):
    return dr.textlength(s, font=f)

def wrap(text, f, max_w):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if text_w(t, f) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur); cur = w_
    if cur: lines.append(cur)
    return lines

def tracked(x, y, s, f, fill, tracking=6, anchor_right=None):
    widths = [text_w(ch, f) for ch in s]
    total = sum(widths) + tracking * (len(s) - 1)
    if anchor_right is not None:
        x = anchor_right - total
    cx = x
    for ch, wch in zip(s, widths):
        dr.text((cx, y), ch, font=f, fill=fill)
        cx += wch + tracking
    return total

def hline(x0, x1, y, wdt=2, fill=RULE):
    dr.line([(x0, y), (x1, y)], fill=fill, width=wdt)

MX = 62
CW = W - 2 * MX
data = json.load(open(os.path.join(HERE, "news.json")))
leads = data["leads"]

# ---------------------------------------------------------------- masthead
y = 42
f_k = font("sans_cb", 24)
tracked(MX, y, "ONE PAGE · ONE DAY · THE WHOLE WORLD", f_k, INK_SOFT, 5)
tracked(0, y, "A SINGLE-IMAGE NEWSPAPER", f_k, INK_SOFT, 5, anchor_right=W - MX)
y += 40
hline(MX, W - MX, y, 7)
y += 12
title = "THE WORLD IN ONE PAGE"
f_t = font("black", 104)
tw = text_w(title, f_t)
dr.text(((W - tw) / 2, y), title, font=f_t, fill=INK)
y += 128
hline(MX, W - MX, y, 2)
y += 8
f_dl = font("sans_cb", 26)
dr.text((MX, y), "Wednesday, 25 November 2026", font=f_dl, fill=INK)
mid = "ALL THE DAY'S WORLD NEWS, SUMMED UP IN A SINGLE IMAGE"
mw = text_w(mid, f_dl)
dr.text(((W - mw) / 2, y), mid, font=f_dl, fill=RED_D)
n_stories = len(leads) + sum(len(c["items"]) for c in data["columns"]) + len(data["sport"])
rt = "%d STORIES · No. 329" % n_stories
dr.text((W - MX - text_w(rt, f_dl), y), rt, font=f_dl, fill=INK)
y += 40
hline(MX, W - MX, y, 5)
y += 20

# ---------------------------------------------------------------- lead zone
lead_top = y
left_w = 1152
right_x = MX + left_w + 44
right_w = W - MX - right_x
lx = MX

tracked(lx, y, "THE DAY'S TOP STORY — " + leads[0]["kicker"], font("sans_cb", 25), RED, 4)
y += 36
f_lead = font("times_b", 64)
for ln in wrap(leads[0]["headline"], f_lead, left_w):
    dr.text((lx, y), ln, font=f_lead, fill=INK); y += 74
y += 2
f_sum = font("serif", 26)
for ln in wrap(leads[0]["summary"], f_sum, left_w):
    dr.text((lx, y), ln, font=f_sum, fill=INK_SOFT); y += 35
y += 12
hline(lx, lx + left_w, y, 2, MUTED)
y += 14
col_w2 = (left_w - 36) // 2
sec_y, max_sec_y = y, y
for i, lead in enumerate(leads[1:]):
    cx = lx + i * (col_w2 + 36)
    cy = sec_y
    tracked(cx, cy, lead["kicker"], font("sans_cb", 22), RED, 4); cy += 32
    f_sh = font("times_b", 34)
    for ln in wrap(lead["headline"], f_sh, col_w2):
        dr.text((cx, cy), ln, font=f_sh, fill=INK); cy += 40
    cy += 2
    f_ss = font("serif", 22)
    for ln in wrap(lead["summary"], f_ss, col_w2):
        dr.text((cx, cy), ln, font=f_ss, fill=INK_SOFT); cy += 29
    max_sec_y = max(max_sec_y, cy)
vx = lx + col_w2 + 18
dr.line([(vx, sec_y + 4), (vx, max_sec_y - 6)], fill=MUTED, width=2)
lead_left_bottom = max_sec_y

# ---- world map
def draw_map(x0, y0, wdt, hgt):
    # drawn on its own layer and pasted, so polygons that extend past the
    # panel (e.g. Antarctica) are clipped instead of spilling onto the page
    layer = Image.new("RGB", (wdt, hgt), (233, 228, 211))
    md = ImageDraw.Draw(layer)
    geo = json.load(open(os.path.join(HERE, "world.geo.json")))
    lat_top, lat_bot = 84.0, -58.0
    def proj(lon, lat):
        return ((lon + 180.0) / 360.0 * wdt,
                (lat_top - lat) / (lat_top - lat_bot) * hgt)
    land = (74, 68, 56)
    def ring(coords):
        pts = [proj(lon, lat) for lon, lat in coords]
        if len(pts) >= 3:
            md.polygon(pts, fill=land)
    for feat in geo["features"]:
        g = feat["geometry"]
        if not g: continue
        if g["type"] == "Polygon":
            for r in g["coordinates"]: ring(r)
        elif g["type"] == "MultiPolygon":
            for poly in g["coordinates"]:
                for r in poly: ring(r)
    # pins only where the page actually carries a story
    cities = [(57.1, 26.6), (30.5, 50.4), (34.3, 31.5), (46.7, 24.6), (32.5, 15.6),
              (7.5, 9.1), (37.6, 55.8), (13.4, 52.5), (-0.1, 51.5), (6.1, 46.2),
              (12.5, 41.9), (-77.0, 38.9), (-74.0, 40.7), (-96.8, 32.8), (-75.5, 10.4),
              (-46.6, -23.5), (77.2, 28.6), (106.8, -6.2), (116.4, 39.9), (127.0, 37.6),
              (139.7, 35.7), (149.1, -35.3)]
    for lon, lat in cities:
        cx, cy = proj(lon, lat)
        r = 7
        md.ellipse([cx - r, cy - r, cx + r, cy + r], fill=RED, outline=(246, 241, 229), width=2)
    # a few key pins get name labels so the map reads as a news map, not decoration
    f_lab = ImageFont.truetype(F["sans_cb"], 17)
    panel_bg = (233, 228, 211)
    labels = [((-74.0, 40.7), "NEW YORK", 14, -9),
              ((57.1, 26.6), "HORMUZ", -26, 16),
              ((139.7, 35.7), "TOKYO", 14, -9),
              ((149.1, -35.3), "CANBERRA", -88, -8)]
    for (lon, lat), name, dx, dy in labels:
        cx, cy = proj(lon, lat)
        md.text((cx + dx, cy + dy), name, font=f_lab, fill=(58, 53, 44),
                stroke_width=2, stroke_fill=panel_bg)
    img.paste(layer, (x0, y0))

f_cap = font("serif_it", 21)
map_h = 258
draw_map(right_x, lead_top, right_w, map_h)
cap_y = lead_top + map_h + 7
for ln in wrap("Where Wednesday happened — from Washington to Canberra.", f_cap, right_w):
    dr.text((right_x, cap_y), ln, font=f_cap, fill=INK_SOFT); cap_y += 28

# ---- scene: Strait of Hormuz at dawn (drawn on its own layer, then pasted, so
# smoke/glow can never spill outside the panel)
sc_y = cap_y + 12
sc_h = 218
x0, y0, x1, y1 = right_x, sc_y, right_x + right_w, sc_y + sc_h
scn = Image.new("RGB", (right_w, sc_h), (0, 0, 0))
sd = ImageDraw.Draw(scn, "RGBA")
horizon = int(sc_h * 0.58)
sky_top, sky_mid, sky_bot = (38, 44, 74), (122, 82, 92), (232, 148, 84)
for yy in range(0, horizon):
    t = yy / max(1, horizon)
    if t < 0.55: a, b, tt = sky_top, sky_mid, t / 0.55
    else: a, b, tt = sky_mid, sky_bot, (t - 0.55) / 0.45
    sd.line([(0, yy), (right_w, yy)], fill=tuple(int(a[i] + (b[i] - a[i]) * tt) for i in range(3)))
sun_x, sun_y = int(right_w * 0.60), horizon - 6
for r, alpha in [(104, 26), (72, 40), (48, 60)]:
    sd.ellipse([sun_x - r, sun_y - r, sun_x + r, sun_y + r], fill=(255, 190, 110, alpha))
sd.ellipse([sun_x - 26, sun_y - 26, sun_x + 26, sun_y + 26], fill=(255, 214, 150))
sea_top, sea_bot = (52, 54, 78), (18, 22, 38)
for yy in range(horizon, sc_h):
    t = (yy - horizon) / max(1, sc_h - horizon)
    sd.line([(0, yy), (right_w, yy)], fill=tuple(int(sea_top[i] + (sea_bot[i] - sea_top[i]) * t) for i in range(3)))
for i in range(22):
    yy = horizon + 5 + i * 8
    half = max(8, 58 - i * 1.6)
    sd.line([(sun_x - half, yy), (sun_x + half, yy)], fill=(255, 176, 102, 120), width=3)
sil = (16, 15, 22)
sd.polygon([(0, horizon), (0, horizon - 82), (84, horizon - 110), (172, horizon - 72),
            (244, horizon - 92), (300, horizon)], fill=sil)
sd.polygon([(right_w, horizon), (right_w, horizon - 76), (right_w - 100, horizon - 102),
            (right_w - 190, horizon - 62), (right_w - 244, horizon)], fill=sil)
bx, by = int(right_w * 0.80), horizon - 4
sd.polygon([(bx - 48, by), (bx + 54, by), (bx + 40, by + 11), (bx - 36, by + 11)], fill=(10, 9, 12))
sd.rectangle([bx + 14, by - 11, bx + 31, by], fill=(10, 9, 12))
for i in range(11):
    r = 9 + i * 3.0
    sd.ellipse([bx + 16 - r + i * 3, by - 22 - i * 10 - r, bx + 16 + r + i * 3, by - 22 - i * 10 + r],
               fill=(30, 28, 30, 120))
sd.polygon([(bx + 0, by - 12), (bx + 13, by - 44), (bx + 25, by - 12)], fill=(255, 122, 40))
sd.polygon([(bx + 5, by - 12), (bx + 13, by - 32), (bx + 20, by - 12)], fill=(255, 196, 84))
tx, ty = int(right_w * 0.30), horizon + 56
sd.polygon([(tx - 134, ty), (tx + 144, ty), (tx + 116, ty + 23), (tx - 106, ty + 23)], fill=(8, 8, 11))
sd.rectangle([tx - 98, ty - 14, tx + 106, ty], fill=(8, 8, 11))
sd.rectangle([tx + 70, ty - 40, tx + 104, ty - 14], fill=(8, 8, 11))
sd.rectangle([tx + 82, ty - 50, tx + 91, ty - 40], fill=(8, 8, 11))
# the foreground tanker burns too — the headline says two ships caught fire
for fx, fh in [(tx - 30, 46), (tx + 34, 34)]:
    sd.polygon([(fx - 13, ty - 14), (fx, ty - 14 - fh), (fx + 13, ty - 14)], fill=(255, 122, 40))
    sd.polygon([(fx - 7, ty - 14), (fx, ty - 14 - fh * 0.62), (fx + 7, ty - 14)], fill=(255, 196, 84))
for i in range(8):
    r = 4 + i * 2.3
    sd.ellipse([tx + 86 - r + i * 4, ty - 57 - i * 7 - r, tx + 86 + r + i * 4, ty - 57 - i * 7 + r],
               fill=(200, 196, 190, 66))
for i in range(9):
    r = 5 + i * 2.6
    sd.ellipse([tx - 28 - r + i * 3, ty - 66 - i * 8 - r, tx - 28 + r + i * 3, ty - 66 - i * 8 + r],
               fill=(30, 28, 30, 110))
sd.line([(tx - 106, ty + 30), (tx + 116, ty + 30)], fill=(255, 190, 120, 90), width=3)
img.paste(scn, (x0, y0))
dr.rectangle([x0, y0, x1, y1], outline=INK, width=3)
sc_cap_y = y1 + 7
for ln in wrap("The Strait of Hormuz at dawn — two tankers burn after striking mines in the night.", f_cap, right_w):
    dr.text((right_x, sc_cap_y), ln, font=f_cap, fill=INK_SOFT); sc_cap_y += 28

lead_bottom = max(lead_left_bottom, sc_cap_y + 2)
y = lead_bottom + 14

# ---------------------------------------------------------------- ticker
dr.rectangle([MX, y, W - MX, y + 48], fill=INK)
TK_COL = {"down": (255, 128, 118), "up": (126, 216, 148), "flat": (246, 241, 229)}
tk_size = 26
while tk_size > 20:
    f_tk = font("sans_cb", tk_size)
    total = text_w("MARKETS", f_tk)
    for txt, _cls in data["ticker"]:
        total += text_w("  ·  " + txt, f_tk)
    if total <= CW - 36:
        break
    tk_size -= 1
f_tk = font("sans_cb", tk_size)
txp = MX + 18
dr.text((txp, y + 9), "MARKETS", font=f_tk, fill=(246, 241, 229))
txp += text_w("MARKETS", f_tk)
for txt, cls in data["ticker"]:
    seg = "  ·  " + txt
    dr.text((txp, y + 9), seg, font=f_tk, fill=TK_COL[cls])
    txp += text_w(seg, f_tk)
y += 48 + 14

# ------------------------------------------------------- timeline (west to east,
# each city with its local time at 12:00 UTC on the day)
tracked(MX, y, "AROUND THE WORLD IN A DAY — WEST TO EAST · LOCAL TIME AT 12:00 UTC", font("sans_cb", 24), RED, 4)
y += 34
cities = data["datelines"]
n = len(cities)
step = CW / (n - 1)
dr.line([(MX, y + 8), (W - MX, y + 8)], fill=MUTED, width=2)
f_city = font("sans_cb", 18)
f_time = font("sans_cb", 19)
prev_right = None
for i, (cname, ctime) in enumerate(cities):
    cx = MX + i * step
    dr.ellipse([cx - 6, y + 2, cx + 6, y + 14], fill=RED)
    cwid = text_w(cname.upper(), f_city)
    txp = min(max(cx - cwid / 2, MX), W - MX - cwid)
    if prev_right is not None and txp < prev_right + 6:
        txp = prev_right + 6  # keep neighbouring city names from colliding
    dr.text((txp, y + 19), cname.upper(), font=f_city, fill=INK)
    prev_right = txp + cwid
    twid = text_w(ctime, f_time)
    txp2 = min(max(cx - twid / 2, MX), W - MX - twid)
    dr.text((txp2, y + 43), ctime, font=f_time, fill=RED_D)
y += 72
hline(MX, W - MX, y, 5)
y += 16

# ---------------------------------------------------------------- columns (auto-fit)
cols_top = y
cols_bottom = 1876
ncol = 4
gap = 34
colw = (CW - gap * (ncol - 1)) // ncol

def column_height(col, hs, hlh, bs, blh, gap_i):
    f_h, f_b, f_p = font("times_b", hs), font("serif", bs), font("sans_cb", bs - 1)
    total = 40 + 13
    for item in col["items"]:
        total += len(wrap(item["headline"], f_h, colw)) * hlh + 1
        place = item["place"] + " — "
        words, lines, cur, first = item["summary"].split(), 0, "", True
        for w_ in words:
            cand = (cur + " " + w_).strip()
            limit = colw - (text_w(place, f_p) if first else 0)
            if text_w(cand, f_b) <= limit or not cur: cur = cand
            else: lines += 1; cur = w_; first = False
        total += (lines + 1) * blh + gap_i
    return total

fits = [(28, 33, 23, 29, 12), (27, 32, 22, 28, 11), (26, 31, 21, 27, 10), (25, 30, 20, 26, 9),
        (24, 29, 19, 25, 8), (23, 28, 18, 24, 7)]
chosen = fits[-1]
for cand in fits:
    if all(column_height(c, *cand) <= cols_bottom - cols_top for c in data["columns"]):
        chosen = cand; break
hs, hlh, bs, blh, gap_i = chosen
print("column fit:", chosen, "available:", cols_bottom - cols_top,
      "heights:", [column_height(c, *chosen) for c in data["columns"]])

f_sec = font("sans_cb", 26)
f_head = font("times_b", hs)
f_body = font("serif", bs)
f_place = font("sans_cb", bs - 1)
for ci, col in enumerate(data["columns"]):
    cx = MX + ci * (colw + gap)
    cy = cols_top
    dr.rectangle([cx, cy, cx + colw, cy + 40], fill=RED)
    dr.text((cx + 10, cy + 7), col["section"], font=f_sec, fill=(246, 241, 229))
    cy += 53
    for item in col["items"]:
        for ln in wrap(item["headline"], f_head, colw):
            dr.text((cx, cy), ln, font=f_head, fill=INK); cy += hlh
        cy += 1
        place = item["place"] + " — "
        words, lines, cur, first = item["summary"].split(), [], "", True
        for w_ in words:
            cand = (cur + " " + w_).strip()
            limit = colw - (text_w(place, f_place) if first else 0)
            if text_w(cand, f_body) <= limit or not cur: cur = cand
            else: lines.append(cur); cur = w_; first = False
        if cur: lines.append(cur)
        for li, ln in enumerate(lines):
            if li == 0:
                dr.text((cx, cy), place, font=f_place, fill=RED_D)
                dr.text((cx + text_w(place, f_place), cy + 1), ln, font=f_body, fill=INK_SOFT)
            else:
                dr.text((cx, cy), ln, font=f_body, fill=INK_SOFT)
            cy += blh
        cy += gap_i
        if item is not col["items"][-1]:
            hline(cx, cx + colw, cy - gap_i + 3, 1, HAIR)
    if ci < ncol - 1:
        vx = cx + colw + gap // 2
        dr.line([(vx, cols_top + 2), (vx, cols_bottom)], fill=HAIR, width=2)

# ---------------------------------------------------------------- sport strip
# two lines, split at an item boundary so nothing is auto-shrunk into mush
y = cols_bottom + 12
hline(MX, W - MX, y, 3)
y += 9
f_sp_l = font("sans_cb", 24)
dr.text((MX, y), "SPORT IN BRIEF", font=f_sp_l, fill=RED_D)
sx = MX + text_w("SPORT IN BRIEF", f_sp_l) + 24
f_sp = font("serif", 21)
avail = W - MX - sx
items = data["sport"]
best_k, best_score = 1, None
for k in range(1, len(items)):
    w1 = text_w(" · ".join(items[:k]), f_sp)
    w2 = text_w(" · ".join(items[k:]), f_sp)
    if w1 <= avail and w2 <= avail:
        score = abs(w1 - w2)
        if best_score is None or score < best_score:
            best_k, best_score = k, score
dr.text((sx, y - 1), " · ".join(items[:best_k]), font=f_sp, fill=INK_SOFT)
dr.text((sx, y + 27), " · ".join(items[best_k:]), font=f_sp, fill=INK_SOFT)
y += 62

# ---------------------------------------------------------------- footer
hline(MX, W - MX, y, 2)
y += 7
f_ft = font("serif", 21)
for ln in wrap(data["sources"], f_ft, CW):
    dr.text((MX, y), ln, font=f_ft, fill=INK_SOFT); y += 27
print("page bottom:", y)

img = img.resize((1024, 1024), Image.LANCZOS)
out = os.path.join(HERE, "entry.png")
img.save(out, optimize=True)
print("saved", out, os.path.getsize(out), "bytes")
