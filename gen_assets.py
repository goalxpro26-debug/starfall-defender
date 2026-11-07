#!/usr/bin/env python3
"""Starfall Defender — original asset generator (PIL + numpy, no stock art).

Generates, in this folder:
  background.png  (1280x720 nebula starfield)
  player.png      (96x96 starfighter)
  enemy1..enemy12.png (96x96, one DISTINCT ship model per level)
  boss.png        (240x180 boss dreadnought)
  powerup_shield.png / powerup_double.png / powerup_health.png (64x64)
  shoot.wav destroy.wav hit.wav win.wav lose.wav powerup.wav thrust.wav ambient.wav
  thumb-512x384.jpg thumb-512x512.jpg thumb-512x340.jpg (portal thumbnails)
All art is drawn in code from primitives — original, no copied/stock art.
"""
import math, os, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
random.seed(20261106)
np.random.seed(20261106)

def save(img, name):
    p = os.path.join(HERE, name)
    img.save(p)
    print(f"{name}: {img.size} {os.path.getsize(p)} bytes")

# ---------------------------------------------------------------- background
def background():
    W, H = 1280, 720
    # vertical deep-space gradient
    top = np.array([8, 10, 38], float); bot = np.array([24, 6, 46], float)
    yy = np.linspace(0, 1, H)[:, None, None]
    base = top[None, None, :] * (1 - yy) + bot[None, None, :] * yy
    img = np.repeat(np.repeat(base, W, axis=1), 1, axis=2).astype(np.uint8)
    im = Image.fromarray(img, "RGB").convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    # nebulae: soft radial blobs
    nebulae = [
        (300, 200, 260, (150, 60, 190)), (950, 150, 220, (40, 120, 200)),
        (1050, 520, 280, (200, 70, 90)), (180, 560, 200, (30, 140, 130)),
        (640, 380, 300, (90, 50, 160)), (820, 620, 180, (200, 130, 40)),
    ]
    for cx, cy, r, col in nebulae:
        blob = Image.new("RGBA", (r * 2, r * 2), (0, 0, 0, 0))
        bd = ImageDraw.Draw(blob)
        for i in range(r, 0, -6):
            a = int(26 * (1 - i / r) ** 2)
            bd.ellipse([r - i, r - i, r + i, r + i], fill=col + (a,))
        ov.alpha_composite(blob, (cx - r, cy - r))
    # distant planet (bottom-left) + ringed planet (top-right)
    d.ellipse([60, 520, 260, 700], fill=(90, 60, 140, 255))
    d.ellipse([90, 545, 190, 620], fill=(130, 90, 180, 255))
    d.ellipse([1080, 60, 1220, 190], fill=(200, 120, 60, 255))
    d.ellipse([1105, 95, 1195, 155], fill=(230, 170, 90, 255))
    for k in range(3):
        d.arc([1030, 90 + k * 6, 1270, 170 - k * 6], 200, 340, fill=(220, 200, 140, 180), width=3)
    im.alpha_composite(ov)
    d = ImageDraw.Draw(im)
    # stars: layered sizes + a few cross sparkles
    for _ in range(520):
        x, y = random.randint(0, W - 1), random.randint(0, H - 1)
        r = random.choice([1, 1, 1, 2, 2, 3])
        b = random.randint(140, 255)
        col = (b, b, min(255, b + 20), 255) if random.random() < 0.7 else (b, int(b * 0.85), int(b * 0.7), 255)
        d.ellipse([x - r, y - r, x + r, y + r], fill=col)
    for _ in range(14):
        x, y = random.randint(40, W - 40), random.randint(40, H - 40)
        L = random.randint(6, 12)
        d.line([x - L, y, x + L, y], fill=(255, 255, 255, 220), width=1)
        d.line([x, y - L, x, y + L], fill=(255, 255, 255, 220), width=1)
    im = im.filter(ImageFilter.GaussianBlur(0.4))
    save(im.convert("RGB"), "background.png")
    return im.convert("RGB")

# ------------------------------------------------------------------- helpers
def ship_canvas(s=96):
    return Image.new("RGBA", (s, s), (0, 0, 0, 0))

def outline(d, pts, fill, oc=(10, 12, 24, 255), w=3):
    d.polygon(pts, fill=fill, outline=oc, width=w)

def cockpit(d, x, y, r, col=(140, 230, 255, 255)):
    d.ellipse([x - r, y - r, x + r, y + r], fill=col, outline=(255, 255, 255, 255), width=2)

def engine_glow(d, x, y, r, col):
    d.ellipse([x - r, y - r, x + r, y + r], fill=col)

# ------------------------------------------------------------- player ship
def player():
    s = 96
    im = ship_canvas(s); d = ImageDraw.Draw(im)
    # twin wings + fuselage, pointing UP (player flies upward)
    outline(d, [(48, 4), (58, 40), (88, 78), (60, 70), (54, 88), (42, 88), (36, 70), (8, 78), (38, 40)],
            (40, 180, 220, 255))
    outline(d, [(48, 10), (56, 44), (52, 84), (44, 84), (40, 44)], (220, 240, 255, 255))
    d.polygon([(48, 4), (54, 30), (42, 30)], fill=(120, 220, 255, 255))
    cockpit(d, 48, 42, 7)
    engine_glow(d, 40, 84, 5, (255, 170, 40, 255))
    engine_glow(d, 56, 84, 5, (255, 170, 40, 255))
    d.line([48, 4, 48, 16], fill=(255, 255, 255, 255), width=2)
    save(im, "player.png")

# ------------------------------------------------------------- enemy ships
# Each level gets a DIFFERENT model: distinct silhouette + palette + details.
def enemy1():  # L1 Starling Drone — small green dart
    im = ship_canvas(); d = ImageDraw.Draw(im)
    outline(d, [(48, 88), (38, 52), (14, 30), (40, 40), (48, 14), (56, 40), (82, 30), (58, 52)], (80, 200, 90, 255))
    cockpit(d, 48, 52, 7, (200, 255, 170, 255))
    engine_glow(d, 48, 80, 4, (255, 80, 60, 255))
    save(im, "enemy1.png")

def enemy2():  # L2 Void Beetle — wide purple hexagon shell
    im = ship_canvas(); d = ImageDraw.Draw(im)
    outline(d, [(48, 90), (78, 70), (86, 36), (62, 14), (34, 14), (10, 36), (18, 70)], (150, 80, 210, 255))
    d.ellipse([30, 30, 66, 66], fill=(90, 40, 140, 255), outline=(220, 170, 255, 255), width=3)
    cockpit(d, 48, 48, 6, (255, 120, 220, 255))
    for x in (24, 72):
        d.line([x, 70, x, 86], fill=(255, 220, 80, 255), width=4)
    save(im, "enemy2.png")

def enemy3():  # L3 Ember Wasp — orange diamond, striped wings
    im = ship_canvas(); d = ImageDraw.Draw(im)
    outline(d, [(48, 92), (70, 55), (48, 8), (26, 55)], (240, 130, 30, 255))
    d.polygon([(48, 8), (90, 44), (70, 55)], fill=(255, 200, 60, 255))
    d.polygon([(48, 8), (6, 44), (26, 55)], fill=(255, 200, 60, 255))
    d.line([38, 30, 58, 30], fill=(60, 20, 0, 255), width=4)
    d.line([34, 46, 62, 46], fill=(60, 20, 0, 255), width=4)
    cockpit(d, 48, 58, 6, (255, 240, 150, 255))
    save(im, "enemy3.png")

def enemy4():  # L4 Crimson Cruiser — red arrowhead cruiser (boss escorts)
    im = ship_canvas(); d = ImageDraw.Draw(im)
    outline(d, [(48, 92), (84, 60), (88, 26), (60, 34), (48, 10), (36, 34), (8, 26), (12, 60)], (210, 50, 50, 255))
    d.rectangle([40, 30, 56, 74], fill=(120, 20, 20, 255))
    cockpit(d, 48, 46, 6, (255, 180, 120, 255))
    for x in (20, 76):
        d.rectangle([x - 3, 58, x + 3, 78], fill=(255, 220, 60, 255))
    save(im, "enemy4.png")

def enemy5():  # L5 Tide Squid — teal squid with tentacles
    im = ship_canvas(); d = ImageDraw.Draw(im)
    d.ellipse([26, 10, 70, 58], fill=(40, 180, 170, 255), outline=(10, 12, 24, 255), width=3)
    for i, x in enumerate((28, 40, 52, 64)):
        d.line([x, 52, x + (-6 if i % 2 else 6), 88], fill=(40, 180, 170, 255), width=6)
        d.ellipse([x - 4, 82, x + 4, 90], fill=(140, 255, 230, 255))
    cockpit(d, 48, 32, 8, (10, 40, 50, 255))
    d.ellipse([40, 28, 47, 36], fill=(255, 255, 255, 255))
    d.ellipse([49, 28, 56, 36], fill=(255, 255, 255, 255))
    save(im, "enemy5.png")

def enemy6():  # L6 Thorn Mantis — magenta mantis, bladed arms
    im = ship_canvas(); d = ImageDraw.Draw(im)
    outline(d, [(48, 90), (60, 55), (58, 20), (38, 20), (36, 55)], (200, 60, 160, 255))
    d.polygon([(36, 40), (8, 78), (20, 84), (40, 52)], fill=(160, 30, 130, 255))
    d.polygon([(60, 40), (88, 78), (76, 84), (56, 52)], fill=(160, 30, 130, 255))
    d.ellipse([38, 8, 58, 26], fill=(255, 120, 220, 255), outline=(10, 12, 24, 255), width=2)
    cockpit(d, 48, 44, 5, (255, 255, 255, 255))
    save(im, "enemy6.png")

def enemy7():  # L7 Solar Hornet — yellow/black hornet, swept wings
    im = ship_canvas(); d = ImageDraw.Draw(im)
    outline(d, [(48, 92), (58, 50), (92, 18), (60, 34), (48, 12), (36, 34), (4, 18), (38, 50)], (250, 210, 40, 255))
    d.line([36, 40, 60, 40], fill=(20, 20, 20, 255), width=5)
    d.line([38, 54, 58, 54], fill=(20, 20, 20, 255), width=5)
    cockpit(d, 48, 62, 6, (255, 120, 40, 255))
    d.line([48, 12, 48, 2], fill=(20, 20, 20, 255), width=3)
    save(im, "enemy7.png")

def enemy8():  # L8 Abyss Destroyer — dark blue battleship slab
    im = ship_canvas(); d = ImageDraw.Draw(im)
    outline(d, [(20, 88), (76, 88), (84, 40), (64, 12), (32, 12), (12, 40)], (50, 90, 200, 255))
    d.rectangle([28, 30, 68, 72], fill=(25, 45, 110, 255), outline=(140, 180, 255, 255), width=2)
    for y in (24, 44, 64):
        d.ellipse([44, y, 52, y + 8], fill=(255, 80, 80, 255))
    d.rectangle([44, 80, 52, 92], fill=(255, 220, 80, 255))
    save(im, "enemy8.png")

def enemy9():  # L9 Web Spider — lime spider, 8 legs
    im = ship_canvas(); d = ImageDraw.Draw(im)
    for y in (26, 40, 54, 68):
        d.line([30, y, 8, y - 12], fill=(140, 200, 50, 255), width=4)
        d.line([66, y, 88, y - 12], fill=(140, 200, 50, 255), width=4)
    d.ellipse([28, 34, 68, 74], fill=(170, 230, 60, 255), outline=(10, 12, 24, 255), width=3)
    d.ellipse([34, 12, 62, 38], fill=(120, 180, 40, 255), outline=(10, 12, 24, 255), width=3)
    for x in (42, 54):
        d.ellipse([x - 4, 18, x + 4, 26], fill=(255, 60, 60, 255))
    cockpit(d, 48, 54, 5, (30, 60, 10, 255))
    save(im, "enemy9.png")

def enemy10():  # L10 Mist Jelly — pink jellyfish dome
    im = ship_canvas(); d = ImageDraw.Draw(im)
    d.pieslice([18, 8, 78, 62], 180, 360, fill=(240, 120, 190, 255), outline=(10, 12, 24, 255), width=3)
    for x in (28, 40, 52, 64):
        d.arc([x - 6, 50, x + 6, 92], 0, 180, fill=(255, 180, 220, 255), width=4)
    for x, y in ((38, 30), (58, 30)):
        d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(255, 255, 255, 255))
        d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(20, 10, 30, 255))
    d.ellipse([42, 42, 54, 50], fill=(255, 150, 200, 255))
    save(im, "enemy10.png")

def enemy11():  # L11 Ghost Phantom — pale ghost ship, translucent
    im = ship_canvas(); d = ImageDraw.Draw(im)
    outline(d, [(48, 90), (30, 60), (22, 26), (48, 6), (74, 26), (66, 60)], (210, 220, 235, 220))
    d.polygon([(48, 6), (48, 90), (30, 60)], fill=(170, 190, 220, 180))
    cockpit(d, 48, 44, 7, (120, 80, 200, 255))
    d.ellipse([40, 74, 56, 86], fill=(150, 100, 255, 255))
    save(im, "enemy11.png")

def enemy12():  # L12 Gold Dreadnought — gold final-wave capital ship
    im = ship_canvas(); d = ImageDraw.Draw(im)
    outline(d, [(48, 92), (80, 66), (86, 30), (66, 16), (30, 16), (10, 30), (16, 66)], (220, 170, 40, 255))
    d.rectangle([36, 28, 60, 76], fill=(140, 100, 20, 255), outline=(255, 230, 130, 255), width=2)
    for y in (34, 52, 70):
        d.rectangle([44, y, 52, y + 6], fill=(255, 240, 160, 255))
    d.polygon([(48, 16), (56, 30), (40, 30)], fill=(255, 240, 160, 255))
    save(im, "enemy12.png")

def boss():  # Boss dreadnought 240x180, pointing DOWN toward player
    W, H = 240, 180
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    outline(d, [(120, 172), (200, 120), (228, 50), (170, 40), (150, 12), (90, 12), (70, 40), (12, 50), (40, 120)],
            (180, 40, 60, 255))
    d.rectangle([90, 40, 150, 130], fill=(90, 15, 20, 255), outline=(255, 150, 120, 255), width=3)
    d.ellipse([95, 60, 145, 110], fill=(255, 90, 60, 255), outline=(255, 220, 180, 255), width=3)
    d.ellipse([110, 75, 130, 95], fill=(255, 240, 200, 255))
    for x in (40, 200):
        d.rectangle([x - 6, 90, x + 6, 130], fill=(255, 210, 60, 255))
    for x in (70, 170):
        d.ellipse([x - 8, 130, x + 8, 146], fill=(255, 80, 80, 255))
    d.polygon([(120, 172), (132, 140), (108, 140)], fill=(255, 220, 90, 255))
    save(im, "boss.png")

def powerups():
    # shield — blue ring orb
    im = ship_canvas(64); d = ImageDraw.Draw(im)
    d.ellipse([6, 6, 58, 58], fill=(40, 140, 255, 255), outline=(200, 230, 255, 255), width=4)
    d.ellipse([20, 20, 44, 44], fill=(180, 220, 255, 255))
    save(im, "powerup_shield.png")
    # double shot — orange twin bolts
    im = ship_canvas(64); d = ImageDraw.Draw(im)
    d.ellipse([6, 6, 58, 58], fill=(255, 150, 30, 255), outline=(255, 230, 160, 255), width=4)
    d.polygon([(22, 14), (30, 14), (24, 32), (32, 32), (20, 50), (24, 34), (16, 34)], fill=(255, 255, 255, 255))
    d.polygon([(40, 14), (48, 14), (42, 32), (50, 32), (38, 50), (42, 34), (34, 34)], fill=(255, 255, 255, 255))
    save(im, "powerup_double.png")
    # health — green cross heart
    im = ship_canvas(64); d = ImageDraw.Draw(im)
    d.ellipse([6, 6, 58, 58], fill=(60, 200, 90, 255), outline=(210, 255, 220, 255), width=4)
    d.rectangle([28, 16, 36, 48], fill=(255, 255, 255, 255))
    d.rectangle([16, 28, 48, 36], fill=(255, 255, 255, 255))
    save(im, "powerup_health.png")

# --------------------------------------------------------------------- audio
def wav(name, data, sr=22050):
    import wave, struct
    p = os.path.join(HERE, name)
    with wave.open(p, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(struct.pack("<%dh" % len(data), *data))
    print(f"{name}: {len(data)/sr:.2f}s {os.path.getsize(p)} bytes")

def tone(freq0, freq1, dur, sr=22050, vol=0.5, shape="sine", noise=0.0):
    n = int(sr * dur); t = np.arange(n) / sr
    f = np.linspace(freq0, freq1, n)
    ph = 2 * np.pi * np.cumsum(f) / sr
    if shape == "sine":
        s = np.sin(ph)
    elif shape == "square":
        s = np.sign(np.sin(ph)) * 0.6
    else:
        s = np.sin(ph) + 0.4 * np.sin(2 * ph)
    if noise:
        s = s * (1 - noise) + noise * np.random.randn(n)
    env = np.minimum(1, np.arange(n) / (0.01 * sr)) * np.exp(-3 * t / dur)
    return (np.clip(s * env * vol, -1, 1) * 32767).astype(np.int16)

def audio():
    sr = 22050
    wav("shoot.wav", tone(880, 220, 0.14, vol=0.45, shape="square"))
    # destroy: noise burst with falling pitch
    n = int(sr * 0.5); t = np.arange(n) / sr
    s = np.random.randn(n) * np.exp(-6 * t) + np.sin(2 * np.pi * np.linspace(300, 50, n) * t) * np.exp(-4 * t)
    wav("destroy.wav", (np.clip(s * 0.6, -1, 1) * 32767).astype(np.int16))
    wav("hit.wav", tone(200, 90, 0.18, vol=0.5, shape="square", noise=0.3))
    # win: rising arpeggio C E G C
    parts = [tone(f, f, 0.16, vol=0.45) for f in (523, 659, 784, 1047)]
    wav("win.wav", np.concatenate(parts))
    wav("lose.wav", np.concatenate([tone(f, f * 0.94, 0.3, vol=0.45) for f in (392, 330, 262, 196)]))
    wav("powerup.wav", tone(440, 1320, 0.25, vol=0.45))
    wav("thrust.wav", tone(120, 320, 0.4, vol=0.3, shape="sine", noise=0.4))
    # ambient: 24s gentle pad (two detuned sines + slow swell), loops
    n = int(sr * 24); t = np.arange(n) / sr
    swell = 0.55 + 0.45 * np.sin(2 * np.pi * t / 8)
    s = (np.sin(2 * np.pi * 110 * t) * 0.5 + np.sin(2 * np.pi * 164.8 * t) * 0.3
         + np.sin(2 * np.pi * 220 * t) * 0.25 + 0.08 * np.random.randn(n))
    # crossfade ends so the loop is seamless
    fade = int(sr * 2)
    s[:fade] *= np.linspace(0, 1, fade); s[-fade:] *= np.linspace(1, 0, fade)
    wav("ambient.wav", (np.clip(s * swell * 0.4, -1, 1) * 32767).astype(np.int16))

# ---------------------------------------------------------------- thumbnails
def thumbnails(bg):
    try:
        font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 64)
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
    except Exception:
        font_big = ImageFont.load_default(); font_sm = ImageFont.load_default()
    def make(w, h, name):
        im = bg.resize((w, h)).convert("RGB")
        d = ImageDraw.Draw(im)
        d.rectangle([0, h - 110, w, h], fill=(6, 8, 24))
        d.text((24, h - 100), "STARFALL DEFENDER", font=font_big, fill=(120, 220, 255))
        d.text((24, h - 34), "12 levels  •  Boss battles  •  Save your progress", font=font_sm, fill=(255, 220, 90))
        p = os.path.join(HERE, name)
        im.save(p, quality=90)
        print(f"{name}: {im.size} {os.path.getsize(p)} bytes")
    make(512, 384, "thumb-512x384.jpg")
    make(512, 512, "thumb-512x512.jpg")
    make(512, 340, "thumb-512x340.jpg")

if __name__ == "__main__":
    bg = background()
    player()
    for fn in (enemy1, enemy2, enemy3, enemy4, enemy5, enemy6, enemy7,
               enemy8, enemy9, enemy10, enemy11, enemy12):
        fn()
    boss()
    powerups()
    audio()
    thumbnails(bg)
    print("DONE")
