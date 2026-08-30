# -*- coding: utf-8 -*-
"""Draw the carbon-theme cover illustration as separate transparent layers.

The layers are kept apart so PowerPoint can animate them in sequence:
    art_sky      sun + clouds (top right)
    art_hills    soft green hills + trees (bottom band)
    art_plant    factory + chimneys + wind turbine (bottom left)
    art_smoke1-3 three chimney plumes, drawn light to heavy
    art_leaf     a single leaf / growth mark used as a small accent

Flat, low-saturation shapes only: no clip-art, no gradients that fight the deck.
"""
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse, Polygon, Rectangle, FancyBboxPatch

OUT = Path(r"C:\Users\user\Desktop\Overall_Data Visual Assignment"
           r"\4_Final_whole_result\build\figures")
OUT.mkdir(parents=True, exist_ok=True)

SKY = "#D8E4EC"
CLOUD = "#FFFFFF"
SUN = "#E9DCC0"
SLATE = "#8D9AA4"
SLATE_D = "#6F7C87"
SLATE_L = "#AAB5BD"
SMOKE = "#C6CDD2"
GREEN_D = "#6E8C74"
GREEN = "#8FAA92"
GREEN_L = "#C3D6C4"
GREEN_XL = "#DCE8DA"


def canvas(w, h):
    fig = plt.figure(figsize=(w, h), dpi=220)
    fig.patch.set_alpha(0)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100 * h / w)
    ax.set_axis_off()
    ax.patch.set_alpha(0)
    return fig, ax


def save(fig, name):
    fig.savefig(OUT / f"{name}.png", transparent=True, bbox_inches=None, pad_inches=0)
    plt.close(fig)
    print("  saved", name)


def cloud(ax, x, y, s, color=CLOUD, alpha=1.0):
    for dx, dy, r in [(-1.05, -0.08, 0.62), (-0.35, 0.22, 0.85), (0.5, 0.05, 0.7),
                      (1.15, -0.14, 0.5)]:
        ax.add_patch(Circle((x + dx * s, y + dy * s), r * s, facecolor=color,
                            edgecolor="none", alpha=alpha, zorder=3))
    ax.add_patch(Rectangle((x - 1.6 * s, y - 0.72 * s), 3.2 * s, 0.75 * s,
                           facecolor=color, edgecolor="none", alpha=alpha, zorder=3))


# ---------------------------------------------------------------- sky layer
fig, ax = canvas(5.2, 2.6)
ax.add_patch(Circle((80, 36), 9.0, facecolor=SUN, edgecolor="none", alpha=0.9))
ax.add_patch(Circle((80, 36), 13.5, facecolor=SUN, edgecolor="none", alpha=0.3))
cloud(ax, 26, 30, 5.6, "#D6E2EA", 0.95)
cloud(ax, 52, 15, 4.2, "#E2EBF1", 0.95)
cloud(ax, 88, 13, 3.2, "#D6E2EA", 0.8)
for x, y, w in [(10, 42, 15), (16, 38.5, 10), (60, 41, 12)]:
    ax.add_patch(FancyBboxPatch((x, y), w, 0.5,
                                boxstyle="round,pad=0.2,rounding_size=0.3",
                                facecolor="#DDE7EE", edgecolor="none", alpha=0.85))
save(fig, "art_sky")

# ---------------------------------------------------------------- hills layer
fig, ax = canvas(7.6, 1.9)
xs = np.linspace(0, 100, 400)
ax.fill_between(xs, 6 + 3.2 * np.sin(xs / 17) + 1.1 * np.cos(xs / 6), 0,
                color=GREEN_XL, zorder=1)
ax.fill_between(xs, 4.2 + 2.1 * np.sin(xs / 12 + 1.4), 0, color=GREEN_L, zorder=2)
for x, s in [(12, 1.0), (23, 0.75), (58, 0.85), (70, 1.05), (84, 0.7), (93, 0.9)]:
    ax.add_patch(Rectangle((x - 0.16 * s, 2.2), 0.32 * s, 1.5 * s,
                           facecolor=GREEN_D, edgecolor="none", zorder=4))
    ax.add_patch(Circle((x, 4.4 * s / 1.0 + 0.4), 1.5 * s, facecolor=GREEN,
                        edgecolor="none", zorder=4))
    ax.add_patch(Circle((x - 0.9 * s, 3.5 * s + 0.3), 1.05 * s, facecolor=GREEN_D,
                        edgecolor="none", alpha=0.75, zorder=3))
save(fig, "art_hills")

# ---------------------------------------------------------------- plant layer
fig, ax = canvas(3.9, 2.4)
# main hall
ax.add_patch(Rectangle((10, 6), 36, 20, facecolor=SLATE, edgecolor="none"))
ax.add_patch(Polygon([(10, 26), (28, 33), (46, 26)], facecolor=SLATE_D,
                     edgecolor="none"))
for i in range(5):
    ax.add_patch(Rectangle((14 + i * 6.4, 11.5), 4.2, 6.5, facecolor="#EDF1F3",
                           edgecolor="none", alpha=0.9))
# chimneys
for x, h, w in [(50, 44, 8.5), (61, 34, 7.0), (70.5, 26, 6.0)]:
    ax.add_patch(Rectangle((x, 6), w, h, facecolor=SLATE_L, edgecolor="none"))
    ax.add_patch(Rectangle((x - 0.7, 6 + h - 2.4), w + 1.4, 2.4,
                           facecolor=SLATE_D, edgecolor="none"))
    ax.add_patch(Rectangle((x, 6 + h * 0.45), w, 2.0, facecolor=SLATE_D,
                           edgecolor="none", alpha=0.55))
# wind turbine on the right: the clean-transition counterpart
ax.add_patch(Rectangle((86, 6), 1.5, 30, facecolor="#C2CBD1", edgecolor="none"))
for ang in (90, 210, 330):
    a = np.deg2rad(ang)
    ax.add_patch(Polygon([(86.75, 36), (86.75 + 11 * np.cos(a), 36 + 11 * np.sin(a)),
                          (86.75 + 9.5 * np.cos(a + 0.16),
                           36 + 9.5 * np.sin(a + 0.16))],
                         facecolor="#C2CBD1", edgecolor="none"))
ax.add_patch(Circle((86.75, 36), 1.3, facecolor=SLATE_D, edgecolor="none"))
ax.add_patch(Rectangle((0, 4.6), 100, 1.6, facecolor="#B9C6BA", edgecolor="none"))
save(fig, "art_plant")

# ---------------------------------------------------------------- smoke plumes
for idx, (cx, base, puffs, alpha0) in enumerate(
        [(0.5, 0.0, 6, 0.55), (0.5, 0.0, 5, 0.42), (0.5, 0.0, 4, 0.32)], start=1):
    fig, ax = canvas(1.5, 2.3)
    h = 100 * 2.3 / 1.5
    for i in range(puffs):
        t = i / max(puffs - 1, 1)
        y = base + 8 + t * (h - 22)
        r = 11 + 13 * t
        x = 50 + 16 * np.sin(t * 2.4 + idx)
        ax.add_patch(Ellipse((x, y), r * 1.5, r * 1.15, facecolor=SMOKE,
                             edgecolor="none", alpha=alpha0 * (1 - 0.55 * t)))
    save(fig, f"art_smoke{idx}")

# ---------------------------------------------------------------- leaf accent
fig, ax = canvas(1.3, 1.3)
ax.add_patch(Polygon([(50, 8), (86, 52), (50, 96), (14, 52)], facecolor=GREEN,
                     edgecolor="none", alpha=0.0))
ax.add_patch(Ellipse((50, 52), 52, 84, angle=25, facecolor=GREEN,
                     edgecolor="none", alpha=0.9))
ax.plot([32, 68], [18, 88], color="#EDF3EC", lw=3.2, solid_capstyle="round")
save(fig, "art_leaf")

# ------------------------------------------------- NTU logo cut from the template
# The teacher's template ships the footer (red rule + logo) as one opaque white
# picture. The deck now uses a tinted background, so the logo is cut out with a
# transparent surround and the red rule is redrawn natively.
from PIL import Image

ASSETS = OUT.parent / "assets"
src = Image.open(ASSETS / "image1.png").convert("RGBA")
W, H = src.size
crop = src.crop((int(0.006 * W), int(0.900 * H), int(0.140 * W), int(0.998 * H)))
px = crop.load()
for yy in range(crop.height):
    for xx in range(crop.width):
        r, g, b, a = px[xx, yy]
        if r > 240 and g > 240 and b > 240:
            px[xx, yy] = (r, g, b, 0)
crop.save(ASSETS / "ntu_logo.png")
print("  saved ntu_logo.png", crop.size)

print("done ->", OUT)
