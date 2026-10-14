#!/usr/bin/env python3
"""Thumbnail Deck source (Portfolio, Oct 14 2026): this-or-that variations on the dollar sign with a green growth chart
(Max liked option 4, the growth-chart look). Labels only: no amounts, no account numbers, no tax figures.
Writes thumbnail.json ({"pairs":[...]}) for: ready_shelf.py build portfolio-thumbnail --source thumbnail.json"""
import json, os, sys, copy
sys.path.insert(0, "/workspace/style-swipe/tools")
from draft_svg import screen, t, lbl, rect, INK, MUTE, LINE
G, BRIGHT, MINT, SAFF, CREAM = "#0B6E4F", "#16A34A", "#E7F3EE", "#D4A017", "#FDFBF6"
BASE = dict(shape="rsq", bg=CREAM, fill=None, dcol=G, dstyle="bold", chart="line", place="behind", tip="arrow", sw=7,
            area=False, climb="steep", grid=False, ring=False, coin=False, accent=None, shadow=False, ccol=None)

def chart(c, x, y, w, h):
    col = c["ccol"] or (c["accent"] or c["dcol"] if c["fill"] is None else "#FFFFFF")
    sw = c["sw"]; s = ""
    if c["grid"]:
        for i in range(1, 4): s += f'<line x1="{x}" y1="{y+h*i/4}" x2="{x+w}" y2="{y+h*i/4}" stroke="{col}" stroke-opacity=".18" stroke-width="1.2"/>'
    if c["chart"] in ("bars", "steps"):
        n = 4; bw = w / (n * 1.6)
        for i in range(n):
            bh = h * (.3 + .7 * (i + 1) / n) if c["climb"] == "steep" else h * (.55 + .45 * (i + 1) / n)
            bx = x + i * (w / n) + (w / n - bw) / 2
            s += rect(bx, y + h - bh, bw, bh, col, "none", 3 if c["chart"] == "bars" else 0, extra='fill-opacity=".85"')
        return s
    pts = ([(0, .95), (.3, .7), (.5, .78), (.75, .38), (1, .05)] if c["climb"] == "steep" else [(0, .8), (.3, .65), (.55, .7), (.8, .5), (1, .4)])
    P = [(x + px * w, y + py * h) for px, py in pts]
    if c["chart"] == "curve":
        d = f"M{P[0][0]:.1f} {P[0][1]:.1f} C{x+w*.45:.1f} {y+h*.95:.1f} {x+w*.55:.1f} {y+h*.15:.1f} {P[-1][0]:.1f} {P[-1][1]:.1f}"
    else:
        d = "M" + " L".join(f"{a:.1f} {b:.1f}" for a, b in P)
    if c["area"]:
        s += f'<path d="{d} L{x+w:.1f} {y+h:.1f} L{x:.1f} {y+h:.1f} Z" fill="{col}" fill-opacity=".18"/>'
    s += f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>'
    ex, ey = P[-1]
    if c["tip"] == "arrow":
        s += f'<path d="M{ex-sw*2.6:.1f} {ey+sw*.4:.1f} L{ex+sw*.4:.1f} {ey-sw*.4:.1f} L{ex-sw*.6:.1f} {ey+sw*2.6:.1f} Z" fill="{col}"/>'
    elif c["tip"] == "dot":
        s += f'<circle cx="{ex}" cy="{ey}" r="{sw*1.1}" fill="{col}"/>'
    return s

def dollar(c, cx, cy, size):
    col = c["dcol"] if c["fill"] is None else "#FFFFFF"
    s = ""
    if c["coin"]:
        s += f'<circle cx="{cx}" cy="{cy-size*.32}" r="{size*.42}" fill="{"#FFFFFF" if c["fill"] is None else c["fill"]}" stroke="{col}" stroke-width="{max(1.2, 4 * c.get('k', 1)):.1f}"/>'
    if c["dstyle"] == "outline":
        return s + f'<text x="{cx}" y="{cy}" font-size="{size}" font-family="Khand" font-weight="700" text-anchor="middle" fill="none" stroke="{col}" stroke-width="{max(.8, 3 * c.get('k', 1)):.1f}">$</text>'
    return s + f'<text x="{cx}" y="{cy}" font-size="{size}" font-family="Khand" font-weight="700" text-anchor="middle" fill="{col}">$</text>'

def avatar(c, x, y, s):
    """Thumbnail tile at (x,y) size s."""
    out = ""; k = s / 150; c = dict(c, sw=max(1.2, c["sw"] * k), k=k)
    r = s / 2 if c["shape"] == "circle" else s * .22
    fill = c["fill"] or c["bg"]
    if c["shadow"]: out += rect(x + 3, y + 5, s, s, "#0A0A0A", "none", r, extra='fill-opacity=".12"')
    out += rect(x, y, s, s, fill, (G if c["ring"] else LINE), r, sw=(max(1.5, 4 * k) if c["ring"] else 1.2))
    p = s * .16; ix, iy, iw = x + p, y + p, s - 2 * p
    pl = c["place"]
    if c["chart"] == "none":
        out += dollar(c, x + s / 2, y + s * .8, s * .78)
    elif pl == "behind":
        out += chart(c, ix, iy + iw * .1, iw, iw * .8)
        out += dollar(c, x + s / 2, y + s * .78, s * .7)
    elif pl == "below":
        out += dollar(c, x + s / 2, y + s * .58, s * .52)
        out += chart(c, ix, y + s * .62, iw, s * .22)
    elif pl == "beside":
        out += dollar(c, x + s * .32, y + s * .74, s * .6)
        out += chart(c, x + s * .52, iy + iw * .2, s * .34, iw * .6)
    elif pl == "badge":
        out += dollar(c, x + s * .44, y + s * .8, s * .74)
        bx, by, bs = x + s * .6, y + s * .6, s * .34
        out += rect(bx, by, bs, bs, "#FFFFFF", G, bs * .25, sw=max(1, 2 * k))
        cc = dict(c, fill=None, sw=max(1, c["sw"] * .5), grid=False, area=False, ccol=G)
        out += chart(cc, bx + bs * .18, by + bs * .2, bs * .64, bs * .6)
    if c["accent"] and c["chart"] != "none":
        out += f'<circle cx="{x+s*.82}" cy="{y+s*.2}" r="{s*.05}" fill="{SAFF}"/>'
    return out

def screen_for(c, label):
    body = lbl(14, 24, "Portfolio Thumbnail")
    body += avatar(c, 45, 40, 150)
    body += t(120, 220, label, 13, INK, "khand", 700, "middle")
    body += lbl(14, 248, "At small sizes")
    body += avatar(c, 14, 256, 36) + avatar(c, 58, 262, 28) + avatar(c, 94, 268, 20)
    body += rect(126, 258, 100, 32, "#FFFFFF", LINE, 8) + avatar(c, 131, 262, 24) + t(160, 279, "Portfolio", 10, INK, "khand", 700)
    return screen(body, CREAM)

def O(pid, side, label, cfg):
    c = dict(BASE, **cfg)
    return {"id": f"pfthumb_{pid}_{side}", "label": label, "desc": f"Thumbnail: {label.lower()}.", "tags": ["visual", "brand"],
            "feeling": "visual", "notes": True, "share": True, "visual": {"type": "hm", "m": "svg", "svg": screen_for(c, label), "bg": CREAM}}

P = [  # (category, ask, (labelA, cfgA), (labelB, cfgB))
 ("Chart Or Plain", "Growth Chart Dollar Or Flat Green Dollar?", ("Green Growth Chart Dollar", {}), ("Flat Green Dollar", {"chart": "none"})),
 ("Chart Type", "Line Chart Or Bar Chart Behind The Dollar?", ("Rising Line Behind Dollar", {}), ("Rising Bars Behind Dollar", {"chart": "bars"})),
 ("Chart Placement", "Chart Behind The Dollar Or Under It?", ("Chart Behind Dollar", {}), ("Chart Under Dollar", {"place": "below"})),
 ("Line Tip", "Arrow Tip Or Dot Tip On The Line?", ("Arrow Tip", {"place": "below"}), ("Dot Tip", {"place": "below", "tip": "dot"})),
 ("Tile Shape", "Rounded Square Or Circle?", ("Rounded Square Tile", {"chart": "bars", "climb": "gentle"}), ("Circle Tile", {"chart": "bars", "climb": "gentle", "shape": "circle"})),
 ("Background", "Cream Background Or Soft Green Background?", ("Cream Background", {"place": "beside"}), ("Soft Green Background", {"place": "beside", "bg": MINT})),
 ("Fill", "Green Dollar On Light Or White Dollar On Solid Green?", ("Green On Light", {"tip": "dot", "climb": "gentle"}), ("White On Solid Green", {"tip": "dot", "climb": "gentle", "fill": G})),
 ("Line Weight", "Thick Line Or Thin Line?", ("Thick Chart Line", {"place": "below", "tip": "none", "sw": 9}), ("Thin Chart Line", {"place": "below", "tip": "none", "sw": 4})),
 ("Accent Colour", "All Green Or Green With A Gold Accent?", ("All Green", {"chart": "curve", "tip": "dot"}), ("Green With Gold Accent", {"chart": "curve", "tip": "dot", "accent": SAFF})),
 ("Dollar Style", "Bold Dollar Or Outline Dollar?", ("Bold Dollar", {"place": "badge"}), ("Outline Dollar", {"place": "badge", "dstyle": "outline"})),
 ("Area Fill", "Line Only Or Shaded Area Under The Line?", ("Line Only", {"place": "below", "climb": "gentle", "tip": "none"}), ("Shaded Area Under Line", {"place": "below", "climb": "gentle", "tip": "none", "area": True})),
 ("Climb", "Steep Climb Or Gentle Climb?", ("Steep Climb", {"chart": "curve", "tip": "arrow"}), ("Gentle Climb", {"chart": "curve", "tip": "arrow", "climb": "gentle"})),
 ("Badge Or Full", "Small Chart Badge Or Full Chart?", ("Chart Badge In Corner", {"place": "badge", "shape": "circle"}), ("Full Chart Behind", {"shape": "circle"})),
 ("Grid", "Grid Lines Or No Grid?", ("Faint Grid Lines", {"chart": "bars", "grid": True, "place": "beside"}), ("No Grid", {"chart": "bars", "place": "beside"})),
 ("Border", "Green Ring Border Or Plain Edge?", ("Green Ring Border", {"chart": "steps", "ring": True}), ("Plain Edge", {"chart": "steps"})),
 ("Layout", "Dollar Beside The Chart Or Stacked Above It?", ("Dollar Beside Chart", {"place": "beside", "tip": "dot"}), ("Dollar Above Chart", {"place": "below", "tip": "dot"})),
 ("Coin", "Dollar In A Coin Or Plain Dollar?", ("Dollar In A Coin", {"coin": True, "place": "below", "climb": "gentle", "sw": 5}), ("Plain Dollar", {"place": "below", "climb": "gentle", "sw": 5})),
 ("Green Shade", "Deep Green Or Bright Green?", ("Deep Jungle Green", {"area": True, "tip": "none"}), ("Bright Leaf Green", {"area": True, "tip": "none", "dcol": BRIGHT})),
 ("Bars Shape", "Rounded Bars Or Stepped Blocks?", ("Rounded Bars", {"chart": "bars", "place": "below"}), ("Stepped Blocks", {"chart": "steps", "place": "below"})),
 ("Depth", "Soft Shadow Or Flat?", ("Soft Shadow Tile", {"shadow": True, "chart": "curve", "tip": "dot"}), ("Flat Tile", {"chart": "curve", "tip": "dot"})),
 ("Solid Circle", "Solid Green Circle Or Cream Circle?", ("Solid Green Circle", {"shape": "circle", "fill": G, "place": "badge"}), ("Cream Circle", {"shape": "circle", "place": "badge"})),
 ("Curve Or Angles", "Smooth Curve Or Sharp Zig-Zag?", ("Smooth Curve", {"chart": "curve", "area": True, "tip": "arrow", "place": "below"}), ("Sharp Zig-Zag", {"area": True, "tip": "arrow", "place": "below"})),
]
pairs = []
for i, (cat, ask, (la, ca), (lb, cb)) in enumerate(P, 1):
    pid = f"{i:02d}"
    pairs.append({"group": "Thumbnail", "category": cat, "app": "Portfolio", "ask": f"{cat}: {ask}",
                  "optionA": O(pid, "a", la, ca), "optionB": O(pid, "b", lb, cb),
                  "purpose": "new", "retest": False, "notes": True, "share": True, "id": f"portfolio-thumb-{pid}", "repeat": False, "generated": "2026-10-14"})
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "thumbnail.json")
json.dump({"pairs": pairs}, open(out, "w"), indent=1, ensure_ascii=False)
print("wrote", out, len(pairs), "pairs")
