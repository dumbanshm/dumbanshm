"""Generate the profile README and its SVG panels.   python3 build.py

Every asset is written as <name>-<content hash>.svg and README.md is regenerated to point at
them, so GitHub's image cache can never serve a stale panel after an edit.
"""
import hashlib
import math
import random
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "assets"
OUT.mkdir(exist_ok=True)
W = 840

# ── palette ──────────────────────────────────────────────────────────
BG, PANEL, LINE = "#0b0f14", "#10161e", "#1e2732"
TXT, MUTED, DIM = "#dfe5ec", "#9aa6b4", "#5f6c7c"
AMZ = "#ff9900"
OK, WARN, CRIT, CHEM, BLUE = "#2dd4bf", "#fbbf24", "#f87171", "#a78bfa", "#60a5fa"
MONO = "ui-monospace,SFMono-Regular,'JetBrains Mono',Menlo,Consolas,monospace"

BASE_CSS = f"""
text{{font-family:{MONO};fill:{TXT}}}
.m{{fill:{MUTED}}}.d{{fill:{DIM}}}.chem{{fill:{CHEM}}}
.b{{font-weight:700}}
.fade{{opacity:0;animation:fade .6s ease-out forwards}}
.rise{{opacity:0;animation:rise .6s cubic-bezier(.2,.8,.2,1) forwards}}
.draw{{animation:draw 1s ease-out forwards}}
.pop{{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .45s cubic-bezier(.3,1.6,.5,1) forwards}}
@keyframes fade{{to{{opacity:1}}}}
@keyframes rise{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:none}}}}
@keyframes draw{{to{{stroke-dashoffset:0}}}}
@keyframes pop{{from{{opacity:0;transform:scale(.2)}}to{{opacity:1;transform:scale(1)}}}}
"""

BUILT = {}  # logical name -> hashed filename


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def svg(name, h, body, css="", w=W, box=True):
    frame = f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="14" fill="{BG}" stroke="{LINE}"/>' if box else ""
    doc = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
           f'role="img"><style>{BASE_CSS}{css}</style>{frame}{body}</svg>')
    fname = f"{name}-{hashlib.sha1(doc.encode()).hexdigest()[:8]}.svg"
    (OUT / fname).write_text(doc)
    BUILT[name] = fname


def d(s):  # animation-delay attribute
    return f'style="animation-delay:{s:.2f}s"'


def label(text, right=""):
    """Small muted label in the top corners of a panel (replaces the old window chrome)."""
    r = f'<text x="{W-32}" y="38" font-size="12" class="d" text-anchor="end">{esc(right)}</text>' if right else ""
    return f'<text x="32" y="38" font-size="12" class="d">{esc(text)}</text>{r}'


# ── header motifs: one element from each project, cycling ────────────
def motif_molecule(cx, cy):  # ChemVecto / InSilicomate
    R = 26
    pts = [(cx + R * math.cos(math.radians(90 + 60 * k)), cy - R * math.sin(math.radians(90 + 60 * k))) for k in range(6)]
    g = [f'<path d="M{" L".join(f"{x:.1f},{y:.1f}" for x, y in pts)} Z" fill="none" stroke="{MUTED}" stroke-width="2.4" stroke-linejoin="round"/>']
    for (x, y), (dx, dy), col in ((pts[0], (0, -22), CRIT), (pts[3], (0, 22), BLUE), (pts[2], (-19, 11), MUTED), (pts[5], (19, -11), MUTED)):
        g.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x+dx:.1f}" y2="{y+dy:.1f}" stroke="{MUTED}" stroke-width="2.4"/>'
                 f'<circle cx="{x+dx:.1f}" cy="{y+dy:.1f}" r="6" fill="{col}"/>')
    return "".join(g)


def motif_graph(cx, cy):  # codeweb: a real codebase graph is a hairball, not a tree
    random.seed(23)
    nodes = []
    while len(nodes) < 34:
        x, y = random.gauss(0, 30), random.gauss(0, 26)
        if (x / 64) ** 2 + (y / 56) ** 2 < 1:
            kind = random.choices(("file", "fn", "mod"), (4, 7, 2))[0]
            nodes.append((cx + x, cy + y, kind))
    edges = set()
    for i, (x, y, _) in enumerate(nodes):  # each node calls a couple of near-ish neighbours…
        near = sorted(range(len(nodes)), key=lambda j: math.dist((x, y), nodes[j][:2]))[1:6]
        for j in random.sample(near, random.choice((1, 2, 2, 3))):
            edges.add(tuple(sorted((i, j))))
    for _ in range(7):  # …and a few long-range imports cut across everything
        edges.add(tuple(sorted(random.sample(range(len(nodes)), 2))))
    g = [f'<line x1="{nodes[a][0]:.1f}" y1="{nodes[a][1]:.1f}" x2="{nodes[b][0]:.1f}" y2="{nodes[b][1]:.1f}" '
         f'stroke="{DIM}" stroke-opacity=".8" stroke-width="1"/>' for a, b in edges]
    style = {"file": (BLUE, 4.6), "fn": (CHEM, 2.8), "mod": (OK, 5.6)}
    for x, y, kind in nodes:
        col, r = style[kind]
        g.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r * random.uniform(.8, 1.25):.1f}" fill="{col}"/>')
    return "".join(g)


def motif_heatmap(cx, cy):  # devansh-OS: one row per tracked metric, each its own hue
    random.seed(4)
    g = []
    for r, col in enumerate((OK, BLUE, WARN, CHEM, CRIT)):
        for c in range(7):
            op = random.choice((.12, .12, .35, .6, .9))
            g.append(f'<rect x="{cx-62+c*18}" y="{cy-44+r*18}" width="14" height="14" rx="3" fill="{col}" fill-opacity="{op}"/>')
    return "".join(g)


def motif_go(cx, cy):  # hexago
    g = [f'<rect x="{cx-50}" y="{cy-50}" width="100" height="100" rx="6" fill="#c69c5d"/>']
    for k in range(5):
        g.append(f'<line x1="{cx-38}" y1="{cy-38+k*19}" x2="{cx+38}" y2="{cy-38+k*19}" stroke="#4a3518"/>'
                 f'<line x1="{cx-38+k*19}" y1="{cy-38}" x2="{cx-38+k*19}" y2="{cy+38}" stroke="#4a3518"/>')
    for (c, r), black in (((1, 1), 1), ((2, 1), 0), ((1, 2), 0), ((3, 2), 1), ((2, 3), 1), ((3, 3), 0), ((0, 3), 1)):
        g.append(f'<circle cx="{cx-38+c*19}" cy="{cy-38+r*19}" r="8" fill="{"#111" if black else "#f2f2f2"}"/>')
    return "".join(g)


def motif_wrong(cx, cy):  # confidently-wrong: a very sure, very wrong answer
    return (f'<rect x="{cx-60}" y="{cy-46}" width="120" height="48" rx="12" fill="{PANEL}" stroke="{LINE}" stroke-width="1.5"/>'
            f'<path d="M{cx-30},{cy+2} l-8,14 l20,-14 z" fill="{PANEL}" stroke="{LINE}" stroke-width="1.5" stroke-linejoin="round"/>'
            f'<rect x="{cx-31}" y="{cy}" width="22" height="3" fill="{PANEL}"/>'
            f'<text x="{cx}" y="{cy-15}" font-size="19" text-anchor="middle" class="b">2 + 2 = 5</text>'
            f'<rect x="{cx-60}" y="{cy+30}" width="120" height="8" rx="4" fill="{LINE}"/>'
            f'<rect x="{cx-60}" y="{cy+30}" width="118" height="8" rx="4" fill="{CRIT}"/>'
            f'<text x="{cx+60}" y="{cy+56}" font-size="11" text-anchor="end" class="crit" style="fill:{CRIT}">99% sure</text>')


def motif_climb(cx, cy):  # codeClimb: a staircase in Codeforces rank colours, flag on top
    ranks = ["#9e9e9e", "#43a047", "#26a69a", "#3b82f6", "#a855f7", "#f59e0b", "#ef4444"]
    g, base = [], cy + 48
    for i, col in enumerate(ranks):
        h = 12 + i * 12
        g.append(f'<rect x="{cx-63+i*18}" y="{base-h}" width="16" height="{h}" rx="2.5" fill="{col}"/>')
    tx, ty = cx - 63 + 6 * 18 + 8, base - 84
    g.append(f'<line x1="{tx}" y1="{ty}" x2="{tx}" y2="{ty-26}" stroke="{TXT}" stroke-width="2"/>'
             f'<path d="M{tx},{ty-26} l16,6 l-16,6 z" fill="{TXT}"/>')
    return "".join(g)


MOTIFS = [motif_molecule, motif_graph, motif_heatmap, motif_go, motif_wrong, motif_climb]


def header():
    H, LX, LY = 236, 690, 118
    defs = (f'<pattern id="dots" width="16" height="16" patternUnits="userSpaceOnUse">'
            f'<circle cx="2" cy="2" r=".9" fill="#ffffff" fill-opacity=".07"/></pattern>'
            f'<radialGradient id="glow"><stop offset="0" stop-color="{CHEM}" stop-opacity=".16"/>'
            f'<stop offset="1" stop-color="{CHEM}" stop-opacity="0"/></radialGradient>'
            f'<linearGradient id="fadeR" x1="0" x2="1"><stop offset=".25" stop-color="#fff" stop-opacity="0"/>'
            f'<stop offset="1" stop-color="#fff" stop-opacity="1"/></linearGradient>'
            f'<mask id="m"><rect width="{W}" height="{H}" fill="url(#fadeR)"/></mask>'
            f'<clipPath id="clip"><rect width="{W}" height="{H}" rx="14"/></clipPath>')
    b = [f'<defs>{defs}</defs>',
         f'<g clip-path="url(#clip)"><rect width="{W}" height="{H}" fill="url(#dots)" mask="url(#m)"/>'
         f'<circle cx="{LX}" cy="{LY}" r="150" fill="url(#glow)"/></g>',
         f'<text x="42" y="56" font-size="13" class="d rise" {d(0)}><tspan style="fill:{OK}">~ $</tspan> whoami</text>',
         f'<text x="40" y="112" font-size="44" class="b rise" {d(.1)}>Devansh Mehta</text>',
         f'<text x="42" y="146" font-size="16" class="rise" {d(.3)}>Backend &amp; data systems.</text>',
         f'<text x="42" y="174" font-size="14" class="m rise" {d(.45)}>SDE intern @ <tspan style="fill:{AMZ}">Amazon</tspan>'
         f' · founding engineer @ <tspan class="chem">ChemVecto</tspan></text>',
         f'<text x="42" y="200" font-size="13" class="d rise" {d(.6)}>BITS Pilani · CS + Biological Sciences · \'27</text>',
         f'<circle cx="{LX}" cy="{LY}" r="82" fill="{BG}" fill-opacity=".6" stroke="{LINE}" stroke-width="1.5"/>',
         f'<circle cx="{LX}" cy="{LY}" r="96" fill="none" stroke="{LINE}" stroke-dasharray="2 6"/>']
    n, step = len(MOTIFS), 2.6
    cycle = n * step
    on, hold = 100 * .5 / cycle, 100 * step / cycle
    css = (f".mo{{opacity:0;animation:cyc {cycle}s ease-in-out infinite both}}"
           f"@keyframes cyc{{0%{{opacity:0;transform:translateY(6px)}}{on:.1f}%{{opacity:1;transform:none}}"
           f"{hold:.1f}%{{opacity:1;transform:none}}{hold+on:.1f}%{{opacity:0;transform:translateY(-6px)}}100%{{opacity:0}}}}")
    for i, fn in enumerate(MOTIFS):
        b.append(f'<g class="mo" style="animation-delay:{i*step:.1f}s">'
                 f'<g transform="translate({LX} {LY}) scale(.82) translate({-LX} {-LY})">{fn(LX, LY)}</g></g>')
    svg("header", H, "".join(b), css)


# ── contact buttons ──────────────────────────────────────────────────
RESUME_URL = "https://drive.google.com/file/d/1qVswRn4h9XEOOss8l3NJFACKPQXICMg2/view?usp=sharing"  # Google Drive link to the resume PDF


def icon(kind, x, y, col):
    """18px line icons, drawn by hand so nothing is fetched."""
    if kind == "email":
        return (f'<rect x="{x}" y="{y+2}" width="18" height="14" rx="2.5" fill="none" stroke="{col}" stroke-width="1.7"/>'
                f'<path d="M{x+1},{y+4} l8,6 l8,-6" fill="none" stroke="{col}" stroke-width="1.7" stroke-linejoin="round"/>')
    if kind == "linkedin":
        return (f'<rect x="{x}" y="{y}" width="18" height="18" rx="3.5" fill="{col}"/>'
                f'<text x="{x+9}" y="{y+13.5}" font-size="11.5" text-anchor="middle" class="b" '
                f'style="fill:{BG};font-family:Helvetica,Arial,sans-serif">in</text>')
    return (f'<path d="M{x+2},{y} h9 l5,5 v13 h-14 z" fill="none" stroke="{col}" stroke-width="1.7" stroke-linejoin="round"/>'
            f'<path d="M{x+11},{y} v5 h5 M{x+5},{y+10} h8 M{x+5},{y+14} h6" fill="none" stroke="{col}" stroke-width="1.5"/>')


def frosted(w, h, tint, rx=14, blob=(.82, .1, .55), strength=.42):
    """Matte frosted glass: a blurred colour blob behind a translucent frost layer, fine grain,
    a hairline white border and a light rim along the top edge."""
    bx, by, br = w * blob[0], h * blob[1], min(w, h) * blob[2] + 30
    return (f'<defs><clipPath id="gc"><rect width="{w}" height="{h}" rx="{rx}"/></clipPath>'
            f'<filter id="gb" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="{br*.45:.0f}"/></filter>'
            f'<filter id="gn" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".85" '
            f'numOctaves="2" stitchTiles="stitch"/><feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 .07 0"/></filter>'
            f'<linearGradient id="gf" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".07"/>'
            f'<stop offset="1" stop-color="#fff" stop-opacity=".015"/></linearGradient></defs>'
            f'<g clip-path="url(#gc)"><rect width="{w}" height="{h}" fill="{BG}"/>'
            f'<circle cx="{bx:.0f}" cy="{by:.0f}" r="{br:.0f}" fill="{tint}" fill-opacity="{strength}" filter="url(#gb)"/>'
            f'<circle cx="{w*.08:.0f}" cy="{h*1.05:.0f}" r="{br*.7:.0f}" fill="{tint}" fill-opacity="{strength*.35:.2f}" filter="url(#gb)"/>'
            f'<rect width="{w}" height="{h}" fill="url(#gf)"/><rect width="{w}" height="{h}" filter="url(#gn)"/></g>'
            f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="{rx}" fill="none" stroke="#fff" stroke-opacity=".09"/>'
            f'<path d="M{rx},1 H{w-rx}" stroke="#fff" stroke-opacity=".22" stroke-linecap="round"/>')


def button(name, title, accent):
    """One contact row for the footer's right column."""
    w, h = 300, 48
    body = (f'{frosted(w, h, accent, rx=12, blob=(.12, .5, .9), strength=.32)}'
            f'{icon(title, 22, 15, accent)}'
            f'<text x="54" y="29" font-size="14" class="b">{esc(title)}</text>'
            f'<text x="{w-22}" y="29" font-size="14" text-anchor="end" class="m">↗</text>')
    svg(name, h, body, w=w, box=False)


def pill(name, text):
    w, h = 200, 40
    body = (f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="20" fill="{BG}" stroke="{LINE}"/>'
            f'<text x="{w/2}" y="25" font-size="12.5" text-anchor="middle" class="m">{esc(text)} ↗</text>')
    svg(name, h, body, w=w, box=False)


MORE = [("sparkathon", "https://github.com/dumbanshm/sparkathon"),
        ("contest-reminders", "https://github.com/dumbanshm/contest-reminders"),
        ("placement-enforcer", "https://github.com/dumbanshm/placement-enforcer-android-app"),
        ("gocrypt", "https://github.com/dumbanshm/gocrypt")]


# ── flagship: what ChemVecto does (not how) ──────────────────────────
def flagship():
    H = 300
    b = [label("featured", "founding engineer · 2026")]
    b.append(f'<text x="32" y="86" font-size="26" class="b rise" {d(.1)}>Chem<tspan class="chem">Vecto</tspan></text>')
    b.append(f'<text x="32" y="114" font-size="14" class="m rise" {d(.25)}>From one molecule to a shortlist worth making.</text>')

    cy, n = 190, 5
    cxs = [32 + (W - 64) * (i + .5) / n for i in range(n)]
    steps = ["a molecule", "its look-alikes", "risk screen", "best trade-offs", "quantum check"]
    t0 = lambda i: .8 + i * .55

    # 1 — a molecule
    x0, R = cxs[0], 20
    pts = [(x0 + R * math.cos(math.radians(90 + 60 * k)), cy - R * math.sin(math.radians(90 + 60 * k))) for k in range(6)]
    ring = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z"
    b.append(f'<path d="{ring}" fill="none" stroke="{MUTED}" stroke-width="2.2" stroke-linejoin="round" '
             f'stroke-dasharray="{6*R}" stroke-dashoffset="{6*R}" class="draw" {d(t0(0))}/>')
    for (x, y), (dx, dy), col in ((pts[0], (0, -18), CRIT), (pts[3], (0, 18), BLUE), (pts[2], (-16, 9), MUTED)):
        b.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x+dx:.1f}" y2="{y+dy:.1f}" stroke="{MUTED}" stroke-width="2.2" class="fade" {d(t0(0)+.4)}/>'
                 f'<circle cx="{x+dx:.1f}" cy="{y+dy:.1f}" r="5" fill="{col}" class="pop" {d(t0(0)+.5)}/>')

    # 2 — look-alikes in chemical space
    random.seed(11)
    x1, cloud = cxs[1], []
    while len(cloud) < 46:
        x, y = random.gauss(0, 1), random.gauss(0, 1)
        if (x / 1.6) ** 2 + (y / 1.0) ** 2 < 2.2:
            cloud.append((x1 + x * 30, cy + y * 19))
    q = (x1 + 4, cy - 2)
    near = sorted(cloud, key=lambda p: math.dist(p, q))[:7]
    for i, (x, y) in enumerate(cloud):
        if (x, y) not in near:
            b.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2" fill="{DIM}" class="fade" {d(t0(1) + (i % 9) * .04)}/>')
    for i, (x, y) in enumerate(near):
        L = math.dist(q, (x, y))
        b.append(f'<line x1="{q[0]:.1f}" y1="{q[1]:.1f}" x2="{x:.1f}" y2="{y:.1f}" stroke="{CHEM}" stroke-opacity=".6" stroke-width="1.2" '
                 f'stroke-dasharray="{L:.1f}" stroke-dashoffset="{L:.1f}" class="draw" {d(t0(1)+.4+i*.04)}/>'
                 f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{CHEM}" class="pop" {d(t0(1)+.5+i*.04)}/>')
    b.append(f'<circle cx="{q[0]:.1f}" cy="{q[1]:.1f}" r="5" fill="{TXT}" class="pop" {d(t0(1)+.3)}/>')

    # 3 — risk screen
    x2 = cxs[2]
    for i, ok in enumerate([1, 0, 1, 1, 0, 1, 0, 1]):
        x, y = x2 - 45 + (i % 4) * 30, cy - 14 + (i // 4) * 28
        col = OK if ok else CRIT
        b.append(f'<circle cx="{x}" cy="{y}" r="8" fill="{col}" fill-opacity="{.9 if ok else .25}" class="pop" {d(t0(2)+i*.06)}/>')
        if not ok:
            b.append(f'<path d="M{x-4},{y-4} L{x+4},{y+4} M{x+4},{y-4} L{x-4},{y+4}" stroke="{CRIT}" stroke-width="1.8" '
                     f'stroke-linecap="round" class="fade" {d(t0(2)+.5)}/>')

    # 4 — best trade-offs
    x3 = cxs[3]
    ax, ay = x3 - 46, cy + 30
    b.append(f'<path d="M{ax},{ay-62} V{ay} H{ax+96}" fill="none" stroke="{LINE}" stroke-width="1.5" class="fade" {d(t0(3))}/>')
    random.seed(3)
    for i in range(14):
        px, py = ax + 8 + random.random() * 70, ay - 6 - random.random() * 44
        b.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="2.4" fill="{DIM}" class="fade" {d(t0(3)+.1+i*.02)}/>')
    front = [(ax + 8, ay - 56), (ax + 34, ay - 50), (ax + 58, ay - 38), (ax + 80, ay - 18)]
    L = sum(math.dist(front[i], front[i + 1]) for i in range(3))
    b.append(f'<path d="M{" L".join(f"{x},{y}" for x, y in front)}" fill="none" stroke="{BLUE}" stroke-width="1.6" '
             f'stroke-dasharray="{L:.0f}" stroke-dashoffset="{L:.0f}" class="draw" {d(t0(3)+.4)}/>')
    for i, (x, y) in enumerate(front):
        b.append(f'<circle cx="{x}" cy="{y}" r="3.6" fill="{BLUE}" class="pop" {d(t0(3)+.5+i*.07)}/>')

    # 5 — quantum check
    x4 = cxs[4]
    for k, (ry, rx, op) in enumerate(((26, 16, .9), (19, 11, .65), (11, 6, .4))):
        for sgn, col in ((-1, BLUE), (1, CHEM)):
            yc = cy + sgn * (ry + 2)
            per = math.pi * (3 * (rx + ry) - math.sqrt((3 * rx + ry) * (rx + 3 * ry)))
            b.append(f'<ellipse cx="{x4:.1f}" cy="{yc:.1f}" rx="{rx}" ry="{ry}" fill="none" stroke="{col}" stroke-opacity="{op}" '
                     f'stroke-width="1.5" stroke-dasharray="{per:.1f}" stroke-dashoffset="{per:.1f}" class="draw" {d(t0(4)+k*.15)}/>')
    b.append(f'<circle cx="{x4:.1f}" cy="{cy}" r="3" fill="{TXT}" class="pop" {d(t0(4))}/>')

    for i in range(n - 1):
        mx = (cxs[i] + cxs[i + 1]) / 2
        b.append(f'<text x="{mx:.0f}" y="{cy+5}" font-size="16" text-anchor="middle" class="d fade" {d(t0(i)+.4)}>›</text>')
    for i, a in enumerate(steps):
        b.append(f'<text x="{cxs[i]:.0f}" y="{cy+72}" font-size="13" text-anchor="middle" class="m rise" {d(t0(i)+.2)}>{esc(a)}</text>')
    svg("chemvecto", H, "".join(b))


# ── project cards ────────────────────────────────────────────────────
CW, CH = 412, 118
PROJECTS = [  # key, title, status, one line, stack, link
    ("devansh-os", "devansh-OS", "OSS", "Tells me what I've been neglecting.", "FastAPI · SQLite",
     "https://github.com/dumbanshm/devansh-OS"),
    ("confidently-wrong", "confidently-wrong", "LIVE", "Make an AI confidently wrong.", "FastAPI · Next.js",
     "https://confidently-wrong-silk.vercel.app"),
    ("codeweb", "codeweb", "LIVE", "Any repo → a dependency graph.", "Node · Neo4j",
     "https://codeweb-8z86.onrender.com"),
    ("codeclimb", "codeClimb", "LIVE", "Daily Codeforces drills.", "React Native · Firebase",
     "https://code-climb-nu.vercel.app"),
    ("insilicomate", "InSilicomate", "OSS", "Where could a drug bind?", "Python · 3Dmol.js",
     "https://github.com/dumbanshm/InSilicomate"),
    ("hexago", "hexago", "OSS", "Hides messages in Go games.", "Python · Flask",
     "https://github.com/dumbanshm/hexago"),
]


def go_board(x, y, msg="hire me", n=9, cell=8.5):
    """hexago's scheme: black = 1, white = 0, 8 stones per character, row by row."""
    bits = "".join(f"{ord(c):08b}" for c in msg)
    g = [f'<rect x="{x-7}" y="{y-7}" width="{(n-1)*cell+14}" height="{(n-1)*cell+14}" rx="4" fill="#c69c5d"/>']
    for k in range(n):
        g.append(f'<line x1="{x}" y1="{y+k*cell}" x2="{x+(n-1)*cell}" y2="{y+k*cell}" stroke="#4a3518" stroke-width=".8"/>'
                 f'<line x1="{x+k*cell}" y1="{y}" x2="{x+k*cell}" y2="{y+(n-1)*cell}" stroke="#4a3518" stroke-width=".8"/>')
    for i, bit in enumerate(bits):
        r, c = divmod(i, n)
        g.append(f'<circle cx="{x+c*cell}" cy="{y+r*cell}" r="{cell*.43:.1f}" fill="{"#111" if bit == "1" else "#f2f2f2"}" '
                 f'class="pop" {d(.4 + i*.03)}/>')
    return "".join(g)


TINT = {"devansh-os": OK, "confidently-wrong": CRIT, "codeweb": CHEM, "codeclimb": WARN,
        "insilicomate": BLUE, "hexago": "#c69c5d"}


def card(i, key, title, status, line, stack, link):
    t = TINT[key]
    b = [frosted(CW, CH, t),
         f'<g class="rise" {d(.05 + i*.06)}>',
         f'<text x="24" y="42" font-size="17" class="b">{esc(title)}</text>',
         f'<text x="24" y="70" font-size="13" class="m">{esc(line)}</text>',
         f'<text x="24" y="{CH-22}" font-size="11.5" class="d">{esc(stack)}</text></g>']
    c = OK if status == "LIVE" else DIM
    b.append(f'<circle cx="{CW-24-len(status)*7-10}" cy="37" r="3.5" fill="{c}"/>'
             f'<text x="{CW-24}" y="41" font-size="11" text-anchor="end" style="fill:{c}">{status}</text>')
    svg(f"card-{key}", CH, "".join(b), w=CW, box=False)


EGG_W = 520


def easter_egg():
    H = 164
    b = [go_board(30, 32, cell=12.5)]
    lines = [("this board isn't a game.", ""), ("", ""), ("read it row by row:", "m"), ("black = 1, white = 0,", "m"),
             ("8 stones per letter.", "m")]
    for i, (ln, cl) in enumerate(lines):
        if ln:
            b.append(f'<text x="180" y="{46 + i*20}" font-size="15" class="{cl} fade" {d(2.2 + i*.12)}>{esc(ln)}</text>')
    b.append(f'<text x="180" y="{H-16}" font-size="12" class="d fade" {d(3)}>encoded with hexago</text>')
    svg("easter-egg", H, "".join(b), w=EGG_W)


def section_title(name, text):
    svg(name, 40, f'<text x="2" y="26" font-size="13" class="d">{esc(text)}</text>'
                  f'<line x1="{len(text)*8+14}" y1="21" x2="{W-2}" y2="21" stroke="{LINE}"/>', box=False)


# ── README ───────────────────────────────────────────────────────────
def readme():
    a = lambda k: f"./assets/{BUILT[k]}"
    cards = "\n".join(
        f'  <a href="{link}"><img src="{a("card-" + key)}" width="49%" alt="{title}: {line}" /></a>'
        for key, title, status, line, stack, link in PROJECTS)
    rows = [("btn-email", "mailto:work.devanshmehta@gmail.com", "Email"),
            ("btn-linkedin", "https://www.linkedin.com/in/devanshme", "LinkedIn")]
    if RESUME_URL:
        rows.append(("btn-resume", RESUME_URL, "Resume"))
    contacts = "<br>\n".join(f'  <a href="{href}"><img src="{a(k)}" width="37%" alt="{alt}" /></a>' for k, href, alt in rows)
    return f"""<!-- Generated by build.py. Edit that, then run `python3 build.py`. -->
<p align="center">
  <img src="{a("header")}" width="100%" alt="Devansh Mehta. Backend and data systems. SDE intern at Amazon, founding engineer at ChemVecto. BITS Pilani, CS + Biological Sciences, 2027." />
</p>

<p align="center">
  <img src="{a("chemvecto")}" width="100%" alt="ChemVecto, where I was founding engineer: from one molecule to a shortlist worth making. A molecule, its look-alikes, a risk screen, the best trade-offs, then a quantum check." />
</p>

<p align="center">
  <img src="{a("section-projects")}" width="100%" alt="Projects" />
</p>

<p align="center">
{cards}
</p>

<p align="center">
  <img src="{a("section-contact")}" width="100%" alt="Contact" />
</p>

<p>
  <img align="left" src="{a("easter-egg")}" width="61%" alt="A Go board whose stones encode a message: black = 1, white = 0, 8 stones per letter, read row by row." />
{contacts}
</p>
"""


if __name__ == "__main__":
    for old in OUT.glob("*.svg"):
        old.unlink()
    header()
    flagship()
    section_title("section-projects", "projects")
    for i, p in enumerate(PROJECTS):
        card(i, *p)
    section_title("section-contact", "say hi")
    easter_egg()
    button("btn-email", "email", OK)
    button("btn-linkedin", "linkedin", BLUE)
    button("btn-resume", "resume", WARN)
    (ROOT / "README.md").write_text(readme())
    print("built", len(BUILT), "assets")
