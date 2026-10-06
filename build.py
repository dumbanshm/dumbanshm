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


def motif_graph(cx, cy):  # codeweb
    nodes = [(0, 0), (-46, -26), (40, -34), (-50, 24), (44, 22), (6, 44), (-8, -50)]
    edges = [(0, 1), (0, 2), (0, 3), (0, 4), (4, 5), (3, 5), (1, 6), (2, 6), (2, 4)]
    g = [f'<line x1="{cx+nodes[a][0]}" y1="{cy+nodes[a][1]}" x2="{cx+nodes[b][0]}" y2="{cy+nodes[b][1]}" stroke="{DIM}" stroke-width="1.8"/>' for a, b in edges]
    for i, (x, y) in enumerate(nodes):
        g.append(f'<circle cx="{cx+x}" cy="{cy+y}" r="{9 if i == 0 else 6}" fill="{OK if i == 0 else BLUE}"/>')
    return "".join(g)


def motif_heatmap(cx, cy):  # devansh-OS
    random.seed(4)
    shades = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
    return "".join(f'<rect x="{cx-62+c*18}" y="{cy-44+r*18}" width="14" height="14" rx="3" fill="{random.choice(shades)}"/>'
                   for r in range(5) for c in range(7))


def motif_go(cx, cy):  # hexago
    g = [f'<rect x="{cx-50}" y="{cy-50}" width="100" height="100" rx="6" fill="#c69c5d"/>']
    for k in range(5):
        g.append(f'<line x1="{cx-38}" y1="{cy-38+k*19}" x2="{cx+38}" y2="{cy-38+k*19}" stroke="#4a3518"/>'
                 f'<line x1="{cx-38+k*19}" y1="{cy-38}" x2="{cx-38+k*19}" y2="{cy+38}" stroke="#4a3518"/>')
    for (c, r), black in (((1, 1), 1), ((2, 1), 0), ((1, 2), 0), ((3, 2), 1), ((2, 3), 1), ((3, 3), 0), ((0, 3), 1)):
        g.append(f'<circle cx="{cx-38+c*19}" cy="{cy-38+r*19}" r="8" fill="{"#111" if black else "#f2f2f2"}"/>')
    return "".join(g)


def motif_calibration(cx, cy):  # confidently-wrong
    x0, y0, s = cx - 50, cy + 50, 100
    g = [f'<path d="M{x0},{y0-s} V{y0} H{x0+s}" fill="none" stroke="{DIM}" stroke-width="1.8"/>',
         f'<line x1="{x0}" y1="{y0}" x2="{x0+s}" y2="{y0-s}" stroke="{DIM}" stroke-dasharray="4 4"/>']
    for i, h in enumerate((.18, .3, .36, .42, .5)):  # overconfident: bars sit under the diagonal
        g.append(f'<rect x="{x0+4+i*19}" y="{y0-h*s}" width="14" height="{h*s}" rx="2" fill="{CRIT}" fill-opacity=".75"/>')
    return "".join(g)


def motif_climb(cx, cy):  # codeClimb
    pts = [(-55, 40), (-35, 28), (-18, 34), (0, 10), (18, 16), (36, -14), (55, -40)]
    path = "M" + " L".join(f"{cx+x},{cy+y}" for x, y in pts)
    return (f'<path d="{path}" fill="none" stroke="{WARN}" stroke-width="2.6" stroke-linejoin="round"/>'
            + "".join(f'<circle cx="{cx+x}" cy="{cy+y}" r="4" fill="{WARN}"/>' for x, y in pts))


MOTIFS = [("chemvecto", motif_molecule), ("codeweb", motif_graph), ("devansh-os", motif_heatmap),
          ("hexago", motif_go), ("confidently-wrong", motif_calibration), ("codeclimb", motif_climb)]


def header():
    H = 220
    b = [f'<text x="40" y="92" font-size="44" class="b rise" {d(.1)}>Devansh Mehta</text>',
         f'<text x="42" y="128" font-size="16" class="rise" {d(.3)}>Backend &amp; data systems.</text>',
         f'<text x="42" y="156" font-size="14" class="m rise" {d(.45)}>SDE intern @ <tspan style="fill:{AMZ}">Amazon</tspan>'
         f' · ex-founding engineer @ <tspan class="chem">ChemVecto</tspan></text>',
         f'<text x="42" y="182" font-size="13" class="d rise" {d(.6)}>BITS Pilani · CS + Biological Sciences · \'27</text>']
    n, step = len(MOTIFS), 2.6
    cycle = n * step
    on, hold = 100 * .5 / cycle, 100 * step / cycle
    css = (f".mo{{opacity:0;animation:cyc {cycle}s ease-in-out infinite both}}"
           f"@keyframes cyc{{0%{{opacity:0;transform:translateY(6px)}}{on:.1f}%{{opacity:1;transform:none}}"
           f"{hold:.1f}%{{opacity:1;transform:none}}{hold+on:.1f}%{{opacity:0;transform:translateY(-6px)}}100%{{opacity:0}}}}")
    for i, (name, fn) in enumerate(MOTIFS):
        b.append(f'<g class="mo" style="animation-delay:{i*step:.1f}s">{fn(700, 100)}'
                 f'<text x="700" y="190" font-size="11" text-anchor="middle" class="d">{name}</text></g>')
    svg("header", H, "".join(b), css)


# ── contact buttons ──────────────────────────────────────────────────
def button(name, text):
    w, h = 132, 38
    body = (f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="19" fill="{BG}" stroke="{LINE}"/>'
            f'<text x="{w/2}" y="24" font-size="13" text-anchor="middle">{esc(text)}</text>')
    svg(name, h, body, w=w, box=False)


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
        g.append(f'<circle cx="{x+c*cell}" cy="{y+r*cell}" r="3.7" fill="{"#111" if bit == "1" else "#f2f2f2"}" '
                 f'class="pop" {d(.4 + i*.03)}/>')
    return "".join(g)


def card(i, key, title, status, line, stack, link):
    b = [f'<g class="rise" {d(.05 + i*.06)}>',
         f'<text x="24" y="42" font-size="17" class="b">{esc(title)}</text>',
         f'<text x="24" y="70" font-size="13" class="m">{esc(line)}</text>',
         f'<text x="24" y="{CH-22}" font-size="11.5" class="d">{esc(stack)}</text></g>']
    if key == "hexago":
        b.append(go_board(CW - 92, 26))
    else:
        live = status == "LIVE"
        c = OK if live else DIM
        b.append(f'<circle cx="{CW-24-len(status)*7-10}" cy="37" r="3.5" fill="{c}"/>'
                 f'<text x="{CW-24}" y="41" font-size="11" text-anchor="end" style="fill:{c}">{status}</text>')
    svg(f"card-{key}", CH, "".join(b), w=CW)


def section_title(name, text):
    svg(name, 40, f'<text x="2" y="26" font-size="13" class="d">{esc(text)}</text>'
                  f'<line x1="{len(text)*8+14}" y1="21" x2="{W-2}" y2="21" stroke="{LINE}"/>', box=False)


# ── README ───────────────────────────────────────────────────────────
def readme():
    a = lambda k: f"./assets/{BUILT[k]}"
    cards = "\n".join(
        f'  <a href="{link}"><img src="{a("card-" + key)}" width="49%" alt="{title}: {line}" /></a>'
        for key, title, status, line, stack, link in PROJECTS)
    return f"""<!-- Generated by build.py. Edit that, then run `python3 build.py`. -->
<p align="center">
  <img src="{a("header")}" width="100%" alt="Devansh Mehta. Backend and data systems. SDE intern at Amazon, ex-founding engineer at ChemVecto. BITS Pilani, CS + Biological Sciences, 2027." />
</p>

<p align="center">
  <a href="mailto:work.devanshmehta@gmail.com"><img src="{a("btn-email")}" height="38" alt="Email" /></a>
  <a href="https://www.linkedin.com/in/devanshme"><img src="{a("btn-linkedin")}" height="38" alt="LinkedIn" /></a>
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
"""


if __name__ == "__main__":
    for old in OUT.glob("*.svg"):
        old.unlink()
    header()
    button("btn-email", "✉  email")
    button("btn-linkedin", "in  linkedin")
    flagship()
    section_title("section-projects", "projects")
    for i, p in enumerate(PROJECTS):
        card(i, *p)
    (ROOT / "README.md").write_text(readme())
    print("built", len(BUILT), "assets")
