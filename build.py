"""Generate the profile README and its SVG panels.   uv run --with fonttools --with brotli python build.py

Every panel is drawn twice, once per GitHub theme, and written as <name>-<theme>-<content hash>.svg.
README.md picks between them with <picture>, so each viewer gets the one matching their GitHub theme,
and the hash in the filename means GitHub's image cache can never serve a stale panel after an edit.
"""
import base64
import hashlib
import io
import itertools
import math
import random
import re
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).parent
OUT = ROOT / "assets"
W = 840            # GitHub's README column
ROW_H = 170        # one project row

# ── palettes: GitHub's own dark and light page colours, and the accents used across the page ──
DARK = dict(BG="#0d1117", PANEL="#0d1117", LINE="#30363d", TXT="#e6edf3", MUTED="#9198a1", DIM="#5d646d",
            OK="#3fb950", WARN="#d29922", CRIT="#f85149", CHEM="#bc8cff", BLUE="#58a6ff", INK="#e6edf3",
            AC="#f78166", AMZ="#ff9900", GO_PAPER="#e6edf3", GO_INK="#0d1117", WM=".13")
LIGHT = dict(BG="#ffffff", PANEL="#ffffff", LINE="#d1d9e0", TXT="#1f2328", MUTED="#59636e", DIM="#9198a1",
             OK="#1a7f37", WARN="#9a6700", CRIT="#cf222e", CHEM="#8250df", BLUE="#0969da", INK="#1f2328",
             AC="#cf222e", AMZ="#bc4c00", GO_PAPER="#ffffff", GO_INK="#1f2328", WM=".15")
THEMES = (("dark", DARK), ("light", LIGHT))
TAPE_INK = "#1b1036"

# ── content ──────────────────────────────────────────────────────────
HEXAGO_URL = "https://hexago-five.vercel.app"
RESUME_URL = "https://drive.google.com/drive/folders/1iT8INlIgLucSlDIcRWyVtYFwWAHjQjQm?usp=sharing"
CONTACT = [("email", "mailto:work.devanshmehta@gmail.com", "OK"),
           ("linkedin", "https://www.linkedin.com/in/devanshme", "BLUE"),
           ("resume", RESUME_URL, "WARN")]
PROJECTS = [  # key, title, status, one line, stack, link, colour
    ("devansh-os", "devansh-OS", "OSS", "Tells me what I've been neglecting.", "FastAPI · SQLite",
     "https://github.com/dumbanshm/devansh-OS", "OK"),
    ("confidently-wrong", "confidently-wrong", "LIVE", "Make an AI confidently wrong.", "FastAPI · Next.js",
     "https://confidently-wrong-silk.vercel.app", "CRIT"),
    ("codeweb", "codeweb", "LIVE", "Any repo → a dependency graph.", "Node · Neo4j",
     "https://codeweb-8z86.onrender.com", "CHEM"),
    ("codeclimb", "codeClimb", "LIVE", "Daily Codeforces drills.", "React Native · Firebase",
     "https://code-climb-nu.vercel.app", "WARN"),
    ("insilicomate", "InSilicomate", "OSS", "Where could a drug bind?", "Python · 3Dmol.js",
     "https://github.com/dumbanshm/InSilicomate", "BLUE"),
    ("hexago", "hexago", "LIVE", "Hides text and images in Go games.", "Python · Flask",
     HEXAGO_URL, "INK"),
]
TAPES = {"amz": ["CURRENTLY", "SDE INTERN @ AMAZON", "PRIME VIDEO"],
         "chem": ["EARLIER", "FOUNDING ENGINEER @ CHEMVECTO", "UNDER CONSTRUCTION"]}

# ── fonts: both SIL OFL 1.1 (see fonts/NOTICE.md), subset and embedded per panel ──
SANS, MONO = "Archivo", "Geist Mono"
FONT_FILES = {SANS: "fonts/Archivo.woff2", MONO: "fonts/GeistMono.woff2"}
ASC, DESC = .878, .21  # Archivo's vertical metrics, used to put baselines where a browser would

BUILT = {}  # (name, theme) -> hashed filename
UID = itertools.count()


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def font_faces(body):
    """GitHub serves README SVGs as images, which can't fetch web fonts, so each panel carries its own
    subset (only the glyphs it uses) of each font it uses, still variable so weight and width work."""
    text = " ".join(re.findall(r">([^<]+)<", body)).replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    out = []
    for family, path in FONT_FILES.items():
        if family == MONO and MONO not in body:
            continue
        f = TTFont(ROOT / path)
        opts = subset.Options()
        opts.flavor, opts.layout_features = "woff2", ["*"]
        sub = subset.Subsetter(opts)
        sub.populate(text=text + text.upper() + " ")
        sub.subset(f)
        buf = io.BytesIO()
        f.flavor = "woff2"
        f.save(buf)
        stretch = "font-stretch:62% 125%;" if family == SANS else ""
        out.append(f"@font-face{{font-family:'{family}';font-weight:100 900;{stretch}"
                   f"src:url(data:font/woff2;base64,{base64.b64encode(buf.getvalue()).decode()}) format('woff2')}}")
    return "".join(out)


BASE_CSS = f"""
text{{font-family:'{SANS}',sans-serif}}.mono{{font-family:'{MONO}',monospace}}
.cy{{opacity:0;animation:cyc 15.6s ease-in-out infinite both}}
@keyframes cyc{{0%{{opacity:0}}3%{{opacity:1}}16.7%{{opacity:1}}19.7%{{opacity:0}}100%{{opacity:0}}}}
.pulse{{transform-box:fill-box;transform-origin:center;animation:pulse 2s ease-out infinite}}
@keyframes pulse{{0%{{opacity:.55;transform:scale(1)}}100%{{opacity:0;transform:scale(2.4)}}}}
"""


def svg(name, theme, w, h, body):
    doc = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">'
           f'<style>{font_faces(body)}{BASE_CSS}</style>{body}</svg>')
    fname = f"{name}-{theme}-{hashlib.sha1(doc.encode()).hexdigest()[:8]}.svg"
    (OUT / fname).write_text(doc)
    BUILT[(name, theme)] = fname


# ── text measuring: so tapes loop seamlessly and things can sit right after a line of text ──
_METRICS = {}


def text_width(text, size, family=SANS, wdth=100, wght=400, spacing=0):
    key = (family, wdth, wght)
    if key not in _METRICS:
        f = TTFont(ROOT / FONT_FILES[family])
        if "fvar" in f:
            axes = {a.axisTag for a in f["fvar"].axes}
            f = instantiateVariableFont(f, {k: v for k, v in (("wdth", wdth), ("wght", wght)) if k in axes})
        _METRICS[key] = (f.getBestCmap(), f["hmtx"].metrics, f["head"].unitsPerEm)
    cmap, hmtx, upm = _METRICS[key]
    return sum(hmtx[cmap[ord(ch)]][0] if ord(ch) in cmap else upm * .5 for ch in text) * size / upm + spacing * len(text)


def baseline(top, size, line_height):
    """Where a browser puts the baseline of one line of Archivo in a line box starting at `top`."""
    return top + (line_height - (ASC + DESC) * size) / 2 + ASC * size


def sparkle(cx, cy, r, col):
    """A six-pointed star, the ✶ the fonts don't have."""
    pts = [(cx + (r if k % 2 == 0 else r * .42) * math.sin(k * math.pi / 6), cy - (r if k % 2 == 0 else r * .42) * math.cos(k * math.pi / 6))
           for k in range(12)]
    return f'<path d="M{" L".join(f"{a:.2f},{b:.2f}" for a, b in pts)} Z" fill="{col}"/>'


def star(cx, cy, r, col, op=1):
    """A five-pointed review star."""
    pts = [(cx + (r if k % 2 == 0 else r * .45) * math.sin(k * math.pi / 5), cy - (r if k % 2 == 0 else r * .45) * math.cos(k * math.pi / 5))
           for k in range(10)]
    return f'<path d="M{" L".join(f"{a:.1f},{b:.1f}" for a, b in pts)} Z" fill="{col}" fill-opacity="{op}"/>'


def arrow_ne(x, y, s, col):
    """A small ↗, drawn because the mono font doesn't have it."""
    return (f'<path d="M{x},{y} l{s},{-s} M{x+s*.35:.1f},{y-s} h{s*.65:.1f} v{s*.65:.1f}" fill="none" stroke="{col}" '
            f'stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>')


def bubble(x, y, w, h, c, text_svg, tail="left", fill=None, stroke=None):
    """A chat bubble drawn as one closed shape, with an iMessage-style flick at the bottom corner."""
    fill, stroke = fill or c["PANEL"], stroke or c["LINE"]
    r = min(16, h / 2)
    if tail == "right":
        d = (f"M{x+r},{y} H{x+w-r} A{r},{r} 0 0 1 {x+w},{y+r} V{y+h-6} "
             f"Q{x+w},{y+h+2} {x+w+9},{y+h+5} Q{x+w-6},{y+h+7} {x+w-14},{y+h} "
             f"H{x+r} A{r},{r} 0 0 1 {x},{y+h-r} V{y+r} A{r},{r} 0 0 1 {x+r},{y} Z")
    else:
        d = (f"M{x+r},{y} H{x+w-r} A{r},{r} 0 0 1 {x+w},{y+r} V{y+h-r} A{r},{r} 0 0 1 {x+w-r},{y+h} "
             f"H{x+14} Q{x+6},{y+h+7} {x-9},{y+h+5} Q{x},{y+h+2} {x},{y+h-6} V{y+r} A{r},{r} 0 0 1 {x+r},{y} Z")
    sw = 0 if stroke == "none" else 1.6
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"/>{text_svg}'


def hexagon_molecule(c, px, py, R, atoms, sw=2.4):
    """The little drug molecule: a ring with a few coloured atoms on sticks."""
    hp = [(px + R * math.cos(math.radians(90 + 60 * k)), py - R * math.sin(math.radians(90 + 60 * k))) for k in range(6)]
    g = [f'<path d="M{" L".join(f"{a:.1f},{b:.1f}" for a, b in hp)} Z" fill="none" stroke="{c["TXT"]}" stroke-width="{sw}" stroke-linejoin="round"/>']
    for k, (dx, dy), col, r in atoms:
        a, b = hp[k]
        g.append(f'<line x1="{a:.1f}" y1="{b:.1f}" x2="{a+dx:.1f}" y2="{b+dy:.1f}" stroke="{c["TXT"]}" stroke-width="{sw}"/>'
                 f'<circle cx="{a+dx:.1f}" cy="{b+dy:.1f}" r="{r}" fill="{col}"/>')
    return "".join(g)


# ── wide watermarks: one per project row, drawn for an 840 x 170 strip ──
def wm_os(c):  # devansh-OS: a habit-tracker strip; each metric has its own streaks and gaps
    random.seed(4)
    step, cell = 32, 26
    g = []
    for r, col in enumerate((c["OK"], c["BLUE"], c["WARN"], c["CHEM"], c["CRIT"])):
        level = random.choice((0, 2, 3))
        for k in range(W // step + 1):
            if random.random() < .22:  # streaks start and die
                level = max(0, min(4, level + random.choice((-2, -1, 1, 2))))
            g.append(f'<rect x="{k*step+3}" y="{r*34+3}" width="{cell}" height="{cell}" rx="5" fill="{col}" '
                     f'fill-opacity="{(.08, .2, .4, .65, .95)[level]}"/>')
    return "".join(g)


def wm_wrong(c):  # confidently-wrong: one round of the game, on the half the name doesn't cover
    said, verdict, pct = "10/10, only got food poisoning twice", "glowing review", 98
    L, Z = 40, 1.32
    sw = len(said) * 7.9 + 34
    ax, aw = L + 8, 280
    g = [bubble(L, 34, sw, 34, c, f'<text x="{L+sw/2:.0f}" y="56" font-size="15" font-weight="600" text-anchor="middle" fill="#ffffff">{said}</text>',
                tail="right", fill=c["BLUE"], stroke="none"),
         bubble(ax, 82, aw, 52, c, f'<text x="{ax+14}" y="104" font-size="12" font-weight="700" fill="{c["MUTED"]}">AI</text>'
                f'<text x="{ax+36}" y="105" font-size="16" font-weight="800" fill="{c["TXT"]}">{verdict}</text>'
                f'<rect x="{ax+14}" y="115" width="170" height="7" rx="3.5" fill="{c["LINE"]}"/>'
                f'<rect x="{ax+14}" y="115" width="{170*pct/100:.0f}" height="7" rx="3.5" fill="{c["CRIT"]}"/>'
                f'<text x="{ax+192}" y="122" font-size="11.5" font-weight="700" fill="{c["CRIT"]}">{pct}% sure</text>'),
         "".join(star(ax + aw - 18 - i * 13, 99, 5.6, c["WARN"]) for i in range(5))]
    sx = ax + aw + 62
    g.append(f'<g transform="rotate(-10 {sx} 108)"><rect x="{sx-64}" y="86" width="128" height="44" rx="7" fill="none" stroke="{c["OK"]}" stroke-width="3"/>'
             f'<text x="{sx}" y="105" font-size="15" font-weight="900" text-anchor="middle" fill="{c["OK"]}" letter-spacing="1.5">FOOLED IT</text>'
             f'<text x="{sx}" y="122" font-size="12" font-weight="800" text-anchor="middle" fill="{c["OK"]}">+{pct*10} pts</text></g>')
    random.seed(2)  # confetti on the side the name covers
    confetti = []
    for _ in range(46):
        x, y, col = random.uniform(600, W), random.uniform(8, ROW_H - 8), random.choice([c[k] for k in ("OK", "WARN", "CHEM", "BLUE", "CRIT")])
        confetti.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="9" height="4" rx="1.5" fill="{col}" transform="rotate({random.uniform(0,180):.0f} {x:.0f} {y:.0f})"/>'
                        if random.random() < .5 else f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{random.uniform(2,3.5):.1f}" fill="{col}"/>')
    cy = 86  # the round spans ~34..138; scale it about its middle, then centre it in the row
    return ("".join(confetti) + f'<g transform="translate(0 {ROW_H/2 - cy}) translate({L} {cy}) scale({Z}) translate({-L} {-cy})">'
            + "".join(g) + "</g>")


def wm_web(c):  # codeweb: modules as clusters along the row, long-range imports cutting across
    random.seed(23)
    nodes, centres = [], [(70 + i * 140 + random.uniform(-20, 20), ROW_H / 2 + random.uniform(-25, 25)) for i in range(6)]
    for ci, (cx, cy) in enumerate(centres):
        for _ in range(random.randint(16, 24)):
            x, y = cx + random.gauss(0, 42), cy + random.gauss(0, 26)
            if 6 < y < ROW_H - 6:
                nodes.append((x, y, ci, random.choices(("file", "fn", "mod"), (4, 7, 2))[0]))
    edges = set()
    for i, (x, y, ci, _) in enumerate(nodes):
        near = sorted((j for j in range(len(nodes)) if nodes[j][2] == ci and j != i), key=lambda j: math.dist((x, y), nodes[j][:2]))[:5]
        for j in random.sample(near, min(len(near), random.choice((1, 2, 2, 3)))):
            edges.add(tuple(sorted((i, j))))
    for _ in range(26):  # imports between modules
        a, b = random.sample(range(len(nodes)), 2)
        if nodes[a][2] != nodes[b][2]:
            edges.add(tuple(sorted((a, b))))
    g = [f'<line x1="{nodes[a][0]:.1f}" y1="{nodes[a][1]:.1f}" x2="{nodes[b][0]:.1f}" y2="{nodes[b][1]:.1f}" stroke="{c["MUTED"]}" stroke-opacity=".7" stroke-width="1.2"/>'
         for a, b in edges]
    style = {"file": (c["BLUE"], 5.5), "fn": (c["CHEM"], 3.4), "mod": (c["OK"], 7)}
    for x, y, _, kind in nodes:
        col, r = style[kind]
        g.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r * random.uniform(.8, 1.25):.1f}" fill="{col}"/>')
    return "".join(g)


RANKS = ["#9e9e9e", "#43a047", "#26a69a", "#3b82f6", "#a855f7", "#f59e0b", "#ef4444"]  # Codeforces, newbie → red


def wm_climb(c):  # codeClimb: a Codeforces rating graph climbing through the rank bands
    bands = list(zip((0, 1200, 1400, 1600, 1900, 2100, 2400), (1200, 1400, 1600, 1900, 2100, 2400, 2700), RANKS))
    lo, hi = 900, 2600
    y = lambda v: ROW_H - (v - lo) / (hi - lo) * ROW_H
    g = [f'<rect x="0" y="{y(min(b, hi)):.1f}" width="{W}" height="{y(max(a, lo)) - y(min(b, hi)):.1f}" fill="{col}" fill-opacity=".35"/>'
         for a, b, col in bands]
    random.seed(7)
    v, pts = 1000, []
    for i in range(44):
        v = max(lo + 40, min(2420, v + random.gauss(30, 70)))
        pts.append((12 + i * (W - 40) / 43, y(v)))
    g.append(f'<polyline points="{" ".join(f"{a:.1f},{b:.1f}" for a, b in pts)}" fill="none" stroke="{c["TXT"]}" stroke-width="2.2" stroke-linejoin="round"/>')
    g += [f'<circle cx="{a:.1f}" cy="{b:.1f}" r="3.6" fill="{c["BG"]}" stroke="{c["TXT"]}" stroke-width="1.8"/>' for a, b in pts]
    fx, fy = pts[-1]
    g.append(f'<line x1="{fx}" y1="{fy}" x2="{fx}" y2="{fy-30}" stroke="{c["TXT"]}" stroke-width="2"/>'
             f'<path d="M{fx},{fy-30} l18,7 l-18,7 z" fill="{c["TXT"]}"/>')
    return "".join(g)


def wm_bind(c):  # InSilicomate: a soft landscape (the protein); a molecule tries a couple of spots, then fits
    def ground(x):
        y = 132 - 10 * math.sin(x / 60) - 6 * math.sin(x / 23)
        for px, depth, wdt in ((190, 34, 34), (480, 30, 32), (690, 42, 36)):
            y += depth * math.exp(-((x - px) / wdt) ** 2)
        return y
    pts = [(x, ground(x)) for x in range(-10, W + 12, 6)]
    g = [f'<path d="M-10,{ROW_H+10} L{" L".join(f"{a:.1f},{b:.1f}" for a, b in pts)} L{W+12},{ROW_H+10} Z" fill="{c["MUTED"]}" fill-opacity=".35" '
         f'stroke="{c["MUTED"]}" stroke-width="2.4" stroke-linejoin="round"/>']

    def mol(x, y, op=1):
        return (f'<g opacity="{op}"><circle cx="{x}" cy="{y:.1f}" r="12" fill="{c["BG"]}"/>'
                + hexagon_molecule(c, x, y, 12, [(0, (0, -10), c["CRIT"], 4.5), (3, (0, 10), c["BLUE"], 4.5)]) + "</g>")
    hops = [(190, ground(190) - 20), (480, ground(480) - 20), (690, ground(690) - 18)]
    for (x0, y0), (x1, y1) in zip(hops, hops[1:]):
        g.append(f'<path d="M{x0},{y0-14:.1f} Q{(x0+x1)/2},-30 {x1},{y1-16:.1f}" fill="none" stroke="{c["TXT"]}" stroke-opacity=".6" '
                 f'stroke-width="1.8" stroke-dasharray="2 7" stroke-linecap="round"/>')
    for (x, y), word in zip(hops[:2], ("nope", "hmm, nope")):
        g.append(mol(x, y, .45) + f'<text x="{x}" y="{y-30:.0f}" font-size="14" text-anchor="middle" fill="{c["MUTED"]}" font-style="italic">{word}</text>')
    x, y = hops[2]
    g.append(f'<circle cx="{x}" cy="{y:.1f}" r="34" fill="{c["OK"]}" fill-opacity=".18"/>' + mol(x, y))
    g += [star(sx, sy, r, c["WARN"]) for sx, sy, r in ((x - 40, y - 34, 7), (x + 40, y - 26, 5.5), (x + 28, y - 50, 4))]
    g.append(f'<text x="{x}" y="{y-52:.0f}" font-size="17" font-weight="800" text-anchor="middle" fill="{c["OK"]}">fits!</text>')
    return "".join(g)


def wm_go(c, msg="let's chat"):  # hexago: an open board whose middle stones really encode a message (black = 1)
    cell = 24
    cols, rows = W // cell, ROW_H // cell
    x0, y0 = (W - (cols - 1) * cell) / 2, (ROW_H - (rows - 1) * cell) / 2
    g = [f'<line x1="{x0}" y1="{y0+r*cell}" x2="{x0+(cols-1)*cell}" y2="{y0+r*cell}" stroke="{c["MUTED"]}" stroke-width="1.2"/>' for r in range(rows)]
    g += [f'<line x1="{x0+k*cell}" y1="{y0}" x2="{x0+k*cell}" y2="{y0+(rows-1)*cell}" stroke="{c["MUTED"]}" stroke-width="1.2"/>' for k in range(cols)]
    bits = "".join(f"{ord(ch):08b}" for ch in msg)
    span = 16
    c0, r0 = (cols - span) // 2, (rows - math.ceil(len(bits) / span)) // 2
    for i, b in enumerate(bits):
        r, k = divmod(i, span)
        x, y = x0 + (c0 + k) * cell, y0 + (r0 + r) * cell
        g.append(f'<circle cx="{x}" cy="{y}" r="9.5" fill="{c["TXT"]}"/>' if b == "1" else
                 f'<circle cx="{x}" cy="{y}" r="9" fill="{c["BG"]}" stroke="{c["TXT"]}" stroke-width="1.6"/>')
    return "".join(g)


WIDE = {"devansh-os": wm_os, "confidently-wrong": wm_wrong, "codeweb": wm_web, "codeclimb": wm_climb,
        "insilicomate": wm_bind, "hexago": wm_go}


# ── round icons for the header sticker: centred on 0,0, radius ≤ 60 ──
def r_os(c):  # devansh-OS: activity rings, one per metric, each as far round as you've kept it up
    g = []
    for i, (col, done) in enumerate(((c["CRIT"], .82), (c["OK"], .64), (c["BLUE"], .9), (c["WARN"], .38), (c["CHEM"], .55))):
        r = 54 - i * 10.5
        circ = 2 * math.pi * r
        g.append(f'<circle r="{r}" fill="none" stroke="{col}" stroke-opacity=".2" stroke-width="8.5"/>'
                 f'<circle r="{r}" fill="none" stroke="{col}" stroke-width="8.5" stroke-linecap="round" '
                 f'stroke-dasharray="{circ*done:.1f} {circ:.1f}" transform="rotate(-90)"/>')
    return "".join(g)


def r_wrong(c):  # confidently-wrong: one speech bubble, very sure and very wrong
    return (bubble(-50, -32, 100, 50, c, f'<text x="0" y="5" font-size="27" font-weight="900" text-anchor="middle" '
                   f'font-stretch="70%" style="font-stretch:70%" fill="{c["TXT"]}">2+2=5</text>', stroke=c["MUTED"])
            + f'<text x="38" y="38" font-size="11" font-weight="800" text-anchor="end" fill="{c["OK"]}">99% sure</text>')


def r_web(c):  # codeweb: the hairball, spread over a disc
    random.seed(23)
    nodes = []
    while len(nodes) < 40:
        r, a = 50 * math.sqrt(random.random()), random.uniform(0, math.tau)
        nodes.append((r * math.cos(a), r * math.sin(a), random.choices(("file", "fn", "mod"), (4, 7, 2))[0]))
    edges = set()
    for i, (x, y, _) in enumerate(nodes):
        near = sorted(range(len(nodes)), key=lambda j: math.dist((x, y), nodes[j][:2]))[1:6]
        for j in random.sample(near, random.choice((1, 2, 2, 3))):
            edges.add(tuple(sorted((i, j))))
    for _ in range(6):
        edges.add(tuple(sorted(random.sample(range(len(nodes)), 2))))
    g = [f'<line x1="{nodes[a][0]:.1f}" y1="{nodes[a][1]:.1f}" x2="{nodes[b][0]:.1f}" y2="{nodes[b][1]:.1f}" stroke="{c["MUTED"]}" stroke-opacity=".8"/>'
         for a, b in edges]
    style = {"file": (c["BLUE"], 4.4), "fn": (c["CHEM"], 2.8), "mod": (c["OK"], 5.4)}
    for x, y, kind in nodes:
        col, r = style[kind]
        g.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r * random.uniform(.85, 1.2):.1f}" fill="{col}"/>')
    return "".join(g)


def r_climb(c):  # codeClimb: the rank bands on a disc, the rating climbing to a flag
    cid, R, h = f"cl{next(UID)}", 56, 112 / 7
    g = [f'<defs><clipPath id="{cid}"><circle r="{R}"/></clipPath></defs><g clip-path="url(#{cid})">']
    g += [f'<rect x="-60" y="{R - (i + 1) * h:.1f}" width="120" height="{h + .5:.1f}" fill="{col}" fill-opacity=".4"/>' for i, col in enumerate(RANKS)]
    random.seed(7)
    pts, y = [], 42
    for i in range(13):
        y = max(-36, y - random.uniform(1, 12))  # mostly up, the odd small dip
        pts.append((-50 + i * 100 / 12, y))
    g.append(f'<polyline points="{" ".join(f"{a:.1f},{b:.1f}" for a, b in pts)}" fill="none" stroke="{c["TXT"]}" stroke-width="2.4" stroke-linejoin="round"/>')
    g += [f'<circle cx="{a:.1f}" cy="{b:.1f}" r="3" fill="{c["BG"]}" stroke="{c["TXT"]}" stroke-width="1.6"/>' for a, b in pts]
    fx, fy = pts[-1]
    g.append(f'</g><line x1="{fx}" y1="{fy:.1f}" x2="{fx}" y2="{fy-22:.1f}" stroke="{c["TXT"]}" stroke-width="2"/>'
             f'<path d="M{fx},{fy-22:.1f} l14,5 l-14,5 z" fill="{c["TXT"]}"/>')
    return "".join(g)


def r_bind(c):  # InSilicomate: an energy landscape from above, contours closing in on where the molecule binds
    g = []
    for i, r in enumerate((52, 42, 32, 23)):
        pts = []
        for t in range(0, 361, 6):
            th = math.radians(t)
            w = r + 3.2 * math.sin(3 * th + i) + 2 * math.sin(5 * th + 2 * i)
            pts.append((w * math.cos(th), 6 + w * .92 * math.sin(th) - (3 - i) * 1.5))
        g.append(f'<path d="M{" L".join(f"{x:.1f},{y:.1f}" for x, y in pts)} Z" fill="none" stroke="{c["MUTED"]}" '
                 f'stroke-opacity="{.35 + i * .15:.2f}" stroke-width="1.8" stroke-linejoin="round"/>')
    fid = f"fd{next(UID)}"  # the molecule's field of interaction: a soft glow fading out
    g.append(f'<defs><radialGradient id="{fid}"><stop offset="0" stop-color="{c["OK"]}" stop-opacity=".55"/>'
             f'<stop offset=".6" stop-color="{c["OK"]}" stop-opacity=".22"/><stop offset="1" stop-color="{c["OK"]}" stop-opacity="0"/></radialGradient></defs>'
             f'<circle cx="0" cy="4" r="20" fill="url(#{fid})"/>')
    g.append(hexagon_molecule(c, 0, 4, 10, [(0, (0, -9), c["CRIT"], 4.2), (2, (-8, 4.5), c["TXT"], 4.2), (3, (0, 9), c["BLUE"], 4.2)]))
    return "".join(g)


def r_go(c):  # hexago: a crowded, chaotic game on an open board that fades out at the edges
    cid, s = f"gf{next(UID)}", 11
    g = [f'<defs><radialGradient id="{cid}g"><stop offset=".82" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
         f'<mask id="{cid}"><circle r="62" fill="url(#{cid}g)"/></mask></defs><g mask="url(#{cid})">']
    for k in range(-6, 7):
        g.append(f'<line x1="-66" y1="{k*s}" x2="66" y2="{k*s}" stroke="{c["MUTED"]}" stroke-width="1"/>'
                 f'<line x1="{k*s}" y1="-66" x2="{k*s}" y2="66" stroke="{c["MUTED"]}" stroke-width="1"/>')
    random.seed(19)
    spots = [(i, j) for i in range(-5, 6) for j in range(-5, 6) if i * i + j * j <= 26]
    for i, j in random.sample(spots, 52):
        g.append(f'<circle cx="{i*s}" cy="{j*s}" r="4.9" fill="{c["TXT"]}"/>' if random.random() < .5 else
                 f'<circle cx="{i*s}" cy="{j*s}" r="4.6" fill="{c["BG"]}" stroke="{c["TXT"]}" stroke-width="1.3"/>')
    return "".join(g) + "</g>"


ROUND = {"devansh-os": r_os, "confidently-wrong": r_wrong, "codeweb": r_web, "codeclimb": r_climb,
         "insilicomate": r_bind, "hexago": r_go}


# ── header: name, the two tapes, the sticker, and the line into the projects ──
BIG, BIG_LH = 176, 140.8


def tape(kind, c, top, angle, size):
    """A printed band across the page, scrolling forever; its text repeats in units of known width."""
    ink, words = TAPE_INK, TAPES[kind]
    wd, wt, ls = 70, 900, size * .01
    space, star_r = text_width(" ", size, wdth=wd, wght=wt) + ls, size * .34
    y = top + 29 + .686 * size / 2  # cap height centred in the 58px band
    unit, x = [], 0
    for w in words:
        unit.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{wt}" font-stretch="{wd}%" '
                    f'style="font-stretch:{wd}%" letter-spacing="{ls:.2f}" fill="{ink}">{esc(w)}</text>')
        x += text_width(w, size, wdth=wd, wght=wt, spacing=ls) + space
        unit.append(sparkle(x + star_r, y - .686 * size / 2, star_r, ink))
        x += 2 * star_r + space
    L = x
    copies = math.ceil((W + 2 * 64 + L) / L) + 1
    run = "".join(f'<g transform="translate({k*L:.1f} 0)">{"".join(unit)}</g>' for k in range(copies))
    frm, to = ("0 0", f"{-L:.1f} 0") if kind == "amz" else (f"{-L:.1f} 0", "0 0")
    band = (f'<rect x="-64" y="{top}" width="{W+128}" height="58" fill="{c["AMZ"] if kind == "amz" else c["CHEM"]}"/>')
    if kind == "chem":  # under-construction stripes along both edges
        pid = f"hz{next(UID)}"
        band += (f'<defs><pattern id="{pid}" width="18" height="18" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
                 f'<rect width="9" height="18" fill="{ink}"/></pattern></defs>'
                 f'<rect x="-64" y="{top}" width="{W+128}" height="10" fill="url(#{pid})"/>'
                 f'<rect x="-64" y="{top+48}" width="{W+128}" height="10" fill="url(#{pid})"/>')
    cx, cy = W / 2, top + 29
    return (f'<g transform="rotate({angle} {cx} {cy})" opacity="{.55 if kind == "chem" else 1}">{band}'
            f'<g transform="translate(-64 0)"><g>{run}<animateTransform attributeName="transform" type="translate" '
            f'from="{frm}" to="{to}" dur="13.33s" repeatCount="indefinite"/></g></g></g>')


def sticker(c, cx, cy):
    """The round sticker: a slowly spinning rim, and the projects' round icons taking turns in the middle."""
    R = 82
    segs = ["SIDE PROJECTS", "BUILT FOR FUN"] * 2
    size, wt, wd, ls = 12.5, 800, 80, 1.2  # a slightly narrow cut, so all four phrases fit round the rim with air between
    widths = [text_width(s, size, wdth=wd, wght=wt, spacing=ls) for s in segs]
    circ = 2 * math.pi * R
    sr = 4.2
    gap = (circ - sum(widths) - len(segs) * 2 * sr) / (2 * len(segs))
    pid, fid = f"rim{next(UID)}", f"sh{next(UID)}"
    rim, s = [], 0
    for seg, w in zip(segs, widths):
        rim.append(f'<text font-size="{size}" font-weight="{wt}" font-stretch="{wd}%" style="font-stretch:{wd}%" letter-spacing="{ls}" fill="{c["TXT"]}">'
                   f'<textPath href="#{pid}" startOffset="{s:.1f}">{seg}</textPath></text>')
        s += w + gap
        th = math.pi + (s + sr) / R  # path starts at the left and runs clockwise over the top
        rim.append(sparkle((R + 4.3) * math.cos(th), (R + 4.3) * math.sin(th), sr, c["TXT"]))
        s += 2 * sr + gap
    icons = "".join(f'<g class="cy" style="animation-delay:{i*2.6:.1f}s"><g transform="scale({140/128:.4f})">{ROUND[k](c)}</g></g>'
                    for i, (k, *_r) in enumerate(PROJECTS))
    return (f'<defs><path id="{pid}" d="M{-R},0 A{R},{R} 0 1 1 {R},0 A{R},{R} 0 1 1 {-R},0"/>'
            f'<filter id="{fid}" x="-30%" y="-30%" width="160%" height="170%"><feDropShadow dx="0" dy="10" stdDeviation="12" flood-color="#000" flood-opacity=".35"/></filter></defs>'
            f'<g transform="translate({cx} {cy}) rotate(-8)">'
            f'<circle r="101" fill="{c["BG"]}" stroke="{c["TXT"]}" stroke-width="2" filter="url(#{fid})"/>'
            f'<g>{"".join(rim)}<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="30s" repeatCount="indefinite"/></g>'
            f'{icons}</g>')


def header(theme, c):
    H = 495
    tb = baseline(0, 12, 18)
    top = "".join(f'<text x="{x}" y="{tb:.1f}" font-size="12" font-weight="600" letter-spacing=".96" text-anchor="{a}" fill="{c["MUTED"]}">{t}</text>'
                  for x, a, t in ((0, "start", "DEVANSH MEHTA"), (318, "start", "BACKEND &amp; DATA SYSTEMS"), (W, "end", "BITS PILANI GOA ’27")))
    big = "".join(f'<text x="-2" y="{baseline(36 + i * BIG_LH, BIG, BIG_LH):.1f}" font-size="{BIG}" font-weight="900" font-stretch="62%" '
                  f'style="font-stretch:62%" letter-spacing="-3.52" fill="{c["TXT"]}">{t}</text>' for i, t in enumerate(("DEVANSH", "MEHTA")))
    tapes = tape("chem", c, 374, 2.2, 26) + tape("amz", c, 308, -6, 30)
    label = "THINGS I BUILD ON THE SIDE"
    lw = text_width(label, 12, MONO, wght=600, spacing=2.16)
    seg = (f'<line x1="0" y1="482" x2="{W/2 - lw/2 - 14:.1f}" y2="482" stroke="{c["LINE"]}"/>'
           f'<line x1="{W/2 + lw/2 + 14:.1f}" y1="482" x2="{W}" y2="482" stroke="{c["LINE"]}"/>'
           f'<text class="mono" x="{W/2 + 1.08:.1f}" y="486.5" font-size="12" font-weight="600" letter-spacing="2.16" text-anchor="middle" fill="{c["MUTED"]}">{label}</text>')
    svg("header", theme, W, H, top + big + tapes + sticker(c, 716, 250) + seg)


# ── one row per project ──────────────────────────────────────────────
def row(theme, c, i, key, title, status, line, stack, col):
    hid, vid, mh, mv = (f"{p}{next(UID)}" for p in ("h", "v", "mh", "mv"))
    art = (f'<defs><linearGradient id="{hid}"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".03" stop-color="#fff"/>'
           f'<stop offset=".97" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
           f'<linearGradient id="{vid}" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".12" stop-color="#fff"/>'
           f'<stop offset=".88" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
           f'<mask id="{mh}"><rect width="{W}" height="{ROW_H}" fill="url(#{hid})"/></mask>'
           f'<mask id="{mv}"><rect width="{W}" height="{ROW_H}" fill="url(#{vid})"/></mask></defs>'
           f'<g mask="url(#{mv})"><g mask="url(#{mh})"><g opacity="{c["WM"]}">{WIDE[key](c)}</g></g></g>')
    right = i % 2 == 1
    x, anchor = (W - 24, "end") if right else (24, "start")
    size = min(76, 900 // len(title))
    total = 23 + 8 + .85 * size + 8 + 41
    y0 = (ROW_H - total) / 2
    # status pill: live is always green with a pulsing dot, open source always grey with a hollow one
    live = status == "LIVE"
    pc = c["OK"] if live else c["MUTED"]
    pw = 68 if live else 60
    px = x - pw if right else x
    dot = (f'<circle class="pulse" cx="{px+13.5}" cy="{y0+11.5}" r="4" fill="{pc}"/><circle cx="{px+13.5}" cy="{y0+11.5}" r="4" fill="{pc}"/>' if live
           else f'<circle cx="{px+13.5}" cy="{y0+11.5}" r="3.25" fill="none" stroke="{pc}" stroke-width="1.5"/>')
    pill = (f'<rect x="{px+.75}" y="{y0+.75}" width="{pw-1.5}" height="21.5" rx="10.75" fill="none" stroke="{pc}" stroke-width="1.5"/>{dot}'
            f'<text class="mono" x="{px+24.5}" y="{y0+15.4:.1f}" font-size="11" font-weight="600" letter-spacing="1.32" fill="{pc}">{"LIVE" if live else "OSS"}</text>')
    ny = y0 + 31
    name = (f'<text x="{x}" y="{ny + .759 * size:.1f}" font-size="{size}" font-weight="900" font-stretch="66%" style="font-stretch:66%" '
            f'letter-spacing="{-.01*size:.2f}" text-anchor="{anchor}" fill="{c[col]}">{esc(title.upper())}</text>')
    dy = ny + .85 * size + 8
    desc = (f'<text x="{x}" y="{dy+16.3:.1f}" font-size="15" text-anchor="{anchor}" fill="{c["MUTED"]}">{esc(line)}</text>'
            f'<text class="mono" x="{x}" y="{dy+37:.1f}" font-size="10.5" text-anchor="{anchor}" fill="{c[col]}">{esc(stack.upper())}</text>')
    svg(f"row-{key}", theme, W, ROW_H, art + pill + name + desc)


# ── contact: the board and LET'S CHAT., then one small panel per link ──
LUCIDE = {  # Lucide icons (ISC licence), 24 x 24, stroked
    "email": '<rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
    "resume": '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/>'
              '<path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>',
}
LINKEDIN = ("M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046"
            "c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 "
            "2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 "
            ".774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z")  # Simple Icons, CC0


def go_board(c, x, y, msg="Let's chat!", n=11, cell=9):
    """hexago's scheme: black = 1, white = 0, 8 stones per character, row by row."""
    bits = "".join(f"{ord(ch):08b}" for ch in msg)
    side = (n - 1) * cell
    g = [f'<rect x="{x-7}" y="{y-7}" width="{side+14}" height="{side+14}" fill="{c["GO_PAPER"]}" stroke="{c["GO_INK"]}" stroke-width="1.5"/>']
    for k in range(n):
        g.append(f'<line x1="{x}" y1="{y+k*cell}" x2="{x+side}" y2="{y+k*cell}" stroke="{c["GO_INK"]}" stroke-width=".8"/>'
                 f'<line x1="{x+k*cell}" y1="{y}" x2="{x+k*cell}" y2="{y+side}" stroke="{c["GO_INK"]}" stroke-width=".8"/>')
    for i, bit in enumerate(bits):
        r, k = divmod(i, n)
        g.append(f'<circle cx="{x+k*cell}" cy="{y+r*cell}" r="{cell*.43:.1f}" ' +
                 (f'fill="{c["GO_INK"]}"/>' if bit == "1" else f'fill="{c["GO_PAPER"]}" stroke="{c["GO_INK"]}" stroke-width="1"/>'))
    return "".join(g)


CONTACT_W, ICON_W, CONTACT_H = 590, 72, 104


def contact(theme, c):
    sub = "THE BOARD SAYS IT TOO · DECODE IT ON HEXAGO"
    sw = text_width(sub, 11, MONO, wght=600, spacing=1.1)
    body = (go_board(c, 7, 7) +
            f'<text x="146" y="{baseline(13, 64, 57.6):.1f}" font-size="64" font-weight="900" font-stretch="66%" style="font-stretch:66%" fill="{c["TXT"]}">LET’S CHAT.</text>'
            f'<text class="mono" x="146" y="88" font-size="11" font-weight="600" letter-spacing="1.1" fill="{c["AC"]}">{sub}</text>'
            + arrow_ne(146 + sw + 4, 87, 7, c["AC"]))
    svg("contact", theme, CONTACT_W, CONTACT_H, body)
    for k, _href, col in CONTACT:
        x0 = (ICON_W - 40) / 2
        if k == "linkedin":
            icon = f'<g transform="translate({x0} 22) scale({40/24:.4f})"><path d="{LINKEDIN}" fill="{c[col]}"/></g>'
        else:
            icon = (f'<g transform="translate({x0} 22) scale({40/24:.4f})" fill="none" stroke="{c[col]}" stroke-width="2" '
                    f'stroke-linecap="round" stroke-linejoin="round">{LUCIDE[k]}</g>')
        label = f'<text class="mono" x="{ICON_W/2 + .66}" y="80" font-size="11" font-weight="600" letter-spacing="1.32" text-anchor="middle" fill="{c["MUTED"]}">{k.upper()}</text>'
        svg(f"btn-{k}", theme, ICON_W, CONTACT_H, icon + label)


# ── README ───────────────────────────────────────────────────────────
def pic(name, width, alt):
    dark, light = BUILT[(name, "dark")], BUILT[(name, "light")]
    return (f'<picture><source media="(prefers-color-scheme: dark)" srcset="./assets/{dark}" />'
            f'<img src="./assets/{light}" width="{width}" alt="{esc(alt)}" /></picture>')


def readme():
    rows = "\n".join(f'  <a href="{link}">{pic("row-" + key, "100%", f"{title} ({status.lower()}): {line} {stack}.")}</a>'
                     for key, title, status, line, stack, link, _c in PROJECTS)
    pct = lambda w: f"{100 * w / W:.1f}%"
    icons = "\n".join(f'  <a href="{href}">{pic("btn-" + k, pct(ICON_W), k.title())}</a>' for k, href, _c in CONTACT)
    return f"""<!-- Generated by build.py. Edit that, then run `uv run --with fonttools --with brotli python build.py`. -->
<p align="center">
  {pic("header", "100%", "Devansh Mehta. Backend and data systems. Currently an SDE intern at Amazon (Prime Video); earlier, founding engineer at ChemVecto. BITS Pilani Goa, class of 2027. Things I build on the side:")}
</p>

<p align="center">
{rows}
</p>

<p align="center">
  <a href="{HEXAGO_URL}/#lets-chat">{pic("contact", pct(CONTACT_W), "Let's chat. A Go board whose stones spell it out: black = 1, white = 0, 8 stones per letter. Opens hexago, which decodes it.")}</a>
{icons}
</p>
"""


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.svg"):
        old.unlink()
    for theme, c in THEMES:
        header(theme, c)
        for i, (key, title, status, line, stack, _link, col) in enumerate(PROJECTS):
            row(theme, c, i, key, title, status, line, stack, col)
        contact(theme, c)
    (ROOT / "README.md").write_text(readme())
    print("built", len(BUILT), "assets")
