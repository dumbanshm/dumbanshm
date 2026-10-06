"""Generate every SVG panel for the profile README.  python3 build.py"""
import math
from pathlib import Path

OUT = Path(__file__).parent / "assets"
OUT.mkdir(exist_ok=True)
W = 840

# ── palette (devansh-OS) ─────────────────────────────────────────────
BG, PANEL, LINE = "#0b0f14", "#10161e", "#1e2732"
TXT, MUTED, DIM = "#dfe5ec", "#9aa6b4", "#5f6c7c"
AMZ = "#ff9900"
OK, WARN, CRIT, CHEM, BLUE = "#2dd4bf", "#fbbf24", "#f87171", "#a78bfa", "#60a5fa"
MONO = "ui-monospace,SFMono-Regular,'JetBrains Mono',Menlo,Consolas,monospace"

BASE_CSS = f"""
text{{font-family:{MONO};fill:{TXT}}}
.m{{fill:{MUTED}}}.d{{fill:{DIM}}}.ok{{fill:{OK}}}.warn{{fill:{WARN}}}.crit{{fill:{CRIT}}}.chem{{fill:{CHEM}}}.blue{{fill:{BLUE}}}
.b{{font-weight:700}}
.fade{{opacity:0;animation:fade .6s ease-out forwards}}
.rise{{opacity:0;animation:rise .6s cubic-bezier(.2,.8,.2,1) forwards}}
.slide{{opacity:0;animation:slide .5s ease-out forwards}}
.draw{{animation:draw 1s ease-out forwards}}
.pop{{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .45s cubic-bezier(.3,1.6,.5,1) forwards}}
.pulse{{transform-box:fill-box;transform-origin:center;animation:pulse 2.4s ease-in-out infinite}}
.blink{{animation:blink 1.1s steps(1) infinite}}
@keyframes fade{{to{{opacity:1}}}}
@keyframes rise{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:none}}}}
@keyframes slide{{from{{opacity:0;transform:translateX(-10px)}}to{{opacity:1;transform:none}}}}
@keyframes draw{{to{{stroke-dashoffset:0}}}}
@keyframes pop{{from{{opacity:0;transform:scale(.2)}}to{{opacity:1;transform:scale(1)}}}}
@keyframes pulse{{0%,100%{{opacity:1;transform:scale(1)}}50%{{opacity:.35;transform:scale(.8)}}}}
@keyframes blink{{0%{{opacity:1}}50%{{opacity:0}}}}
"""


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def svg(name, h, body, css="", w=W):
    doc = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
           f'role="img"><style>{BASE_CSS}{css}</style>'
           f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="12" fill="{BG}" stroke="{LINE}"/>'
           f'{body}</svg>')
    (OUT / name).write_text(doc)


def d(s):  # animation-delay attribute
    return f'style="animation-delay:{s:.2f}s"'


def wrap(s, n):
    lines, cur = [], ""
    for w in s.split():
        if len(cur) + len(w) + (1 if cur else 0) > n:
            lines.append(cur); cur = w
        else:
            cur = f"{cur} {w}" if cur else w
    return lines + ([cur] if cur else [])


def titlebar(label, right="", y=26):
    return (f'<circle cx="22" cy="{y-4}" r="5" fill="#ff5f56"/><circle cx="38" cy="{y-4}" r="5" fill="#ffbd2e"/>'
            f'<circle cx="54" cy="{y-4}" r="5" fill="#27c93f"/>'
            f'<text x="74" y="{y}" font-size="12" class="m">{esc(label)}</text>'
            f'<text x="{W-20}" y="{y}" font-size="12" class="m" text-anchor="end">{esc(right)}</text>'
            f'<line x1="0" y1="{y+12}" x2="{W}" y2="{y+12}" stroke="{LINE}"/>')


# ── 1. header: name, thesis, caffeine molecule ───────────────────────
def caffeine(cx, cy, r, t0):
    """Ball-and-stick caffeine (C8H10N4O2): fused 6+5 purine core with substituents."""
    P = lambda a, rr=r: (cx + rr * math.cos(math.radians(a)), cy - rr * math.sin(math.radians(a)))
    hexa = {k: P(a) for k, a in zip(["C5", "C6", "N1", "C2", "N3", "C4"], [30, 90, 150, 210, 270, 330])}
    ax, ay = hexa["C5"]; bx, by = hexa["C4"]
    mx, my = (ax + bx) / 2, (ay + by) / 2
    apo = r / (2 * math.tan(math.radians(36)))  # pentagon apothem, side = hexagon side = r
    pc = (mx + apo, my)
    R5 = r / (2 * math.sin(math.radians(36)))
    ang = lambda p: math.degrees(math.atan2(-(p[1] - pc[1]), p[0] - pc[0]))
    a5 = ang(hexa["C5"])
    pent = {"N7": None, "C8": None, "N9": None}
    for i, k in enumerate(["N7", "C8", "N9"], 1):
        a = math.radians(a5 - 72 * i)
        pent[k] = (pc[0] + R5 * math.cos(a), pc[1] - R5 * math.sin(a))
    at = {**hexa, **pent}

    def out(k, centre, L=r * .9):
        x, y = at[k]; vx, vy = x - centre[0], y - centre[1]; n = math.hypot(vx, vy)
        return (x + vx / n * L, y + vy / n * L)
    ring_c = (cx, cy)
    sub = {"O6": out("C6", ring_c), "Me1": out("N1", ring_c), "O2": out("C2", ring_c),
           "Me3": out("N3", ring_c), "Me7": out("N7", pc)}
    at.update(sub)
    bonds = [("C5", "C6"), ("C6", "N1"), ("N1", "C2"), ("C2", "N3"), ("N3", "C4"), ("C4", "C5", 2),
             ("C5", "N7"), ("N7", "C8"), ("C8", "N9", 2), ("N9", "C4"),
             ("C6", "O6", 2), ("C2", "O2", 2), ("N1", "Me1"), ("N3", "Me3"), ("N7", "Me7")]
    g = []
    for i, b in enumerate(bonds):
        (x1, y1), (x2, y2) = at[b[0]], at[b[1]]
        L = math.hypot(x2 - x1, y2 - y1)
        lines = [(0, 0)]
        if len(b) == 3:
            nx, ny = -(y2 - y1) / L * 3, (x2 - x1) / L * 3
            lines = [(nx, ny), (-nx, -ny)]
        for ox, oy in lines:
            g.append(f'<line x1="{x1+ox:.1f}" y1="{y1+oy:.1f}" x2="{x2+ox:.1f}" y2="{y2+oy:.1f}" stroke="{DIM}" '
                     f'stroke-width="2.4" stroke-linecap="round" stroke-dasharray="{L:.1f}" stroke-dashoffset="{L:.1f}" '
                     f'class="draw" {d(t0 + .9 + i * .06)}/>')
    col = {"N": BLUE, "O": CRIT, "C": "#9aa6b2", "M": "#5d6977"}
    for i, (k, (x, y)) in enumerate(at.items()):
        e = k[0]
        rad = 9 if e in "NO" else 7 if e == "C" else 5.5
        g.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rad}" fill="{col[e]}" class="pop" {d(t0 + i * .05)}/>')
        if e in "NO":
            g.append(f'<text x="{x:.1f}" y="{y+3.5:.1f}" font-size="10" text-anchor="middle" class="b pop" '
                     f'style="fill:{BG};animation-delay:{t0 + i * .05:.2f}s">{e}</text>')
    return f'<g class="float">{"".join(g)}</g>'


def header():
    tags = [("backend systems", OK), ("data pipelines", BLUE), ("cheminformatics", CHEM), ("ML evaluation", WARN)]
    body = [titlebar("devansh@os ~ $ whoami", "Bengaluru · BITS Pilani '27")]
    body.append(f'<text x="32" y="98" font-size="40" class="b rise" {d(.2)}>Devansh Mehta</text>')
    body.append(f'<text x="34" y="128" font-size="15" class="rise" {d(.5)}>Backend &amp; data systems — '
                f'and dashboards that keep me honest.</text>')
    body.append(f'<text x="34" y="150" font-size="15" class="m rise" {d(.65)}>SDE intern @ <tspan style="fill:{AMZ}">Amazon</tspan>'
                f' · founding engineer @ <tspan class="chem">ChemVecto</tspan></text>')
    x = 34
    for i, (t, c) in enumerate(tags):
        wpx = len(t) * 7.3 + 22
        body.append(f'<g class="rise" {d(1.0 + i * .12)}><rect x="{x}" y="176" width="{wpx:.0f}" height="24" rx="12" '
                    f'fill="none" stroke="{c}" stroke-opacity=".55"/><text x="{x + wpx/2:.0f}" y="192" font-size="12" '
                    f'text-anchor="middle" style="fill:{c}">{t}</text></g>')
        x += wpx + 8
    body.append(f'<text x="34" y="232" font-size="12" class="d fade" {d(1.6)}>status: <tspan class="ok">● shipping</tspan>'
                f' · CS + Bio Sciences dual degree, class of \'27<tspan class="blink"> _</tspan></text>')
    body.append(caffeine(690, 140, 30, .4))
    css = ".float{animation:float 6s ease-in-out 2.5s infinite}@keyframes float{50%{transform:translateY(-5px)}}"
    svg("header.svg", 256, "".join(body), css)


# ── 2. flagship: what ChemVecto does (not how) ───────────────────────
def flagship():
    import random
    H = 336
    b = [titlebar("flagship · ChemVecto", "founding engineer · Mar–Jun 2026")]
    b.append(f'<text x="32" y="80" font-size="24" class="b rise" {d(.1)}>Chem<tspan class="chem">Vecto</tspan></text>')
    b.append(f'<text x="32" y="104" font-size="14" class="m rise" {d(.25)}>Screen chemical space. Then go quantum.</text>')
    b.append(f'<text x="32" y="134" font-size="13" class="rise" {d(.4)}>Takes a chemist from one molecule to a shortlist of better ones worth making.</text>')

    cy, n = 208, 5
    cxs = [32 + (W - 64) * (i + .5) / n for i in range(n)]
    steps = [("a molecule", "drawn or pasted"), ("its look-alikes", "in chemical space"),
             ("risk screen", "tox & drug-likeness"), ("best trade-offs", "ranked across goals"),
             ("quantum check", "on the shortlist")]
    t0 = lambda i: .8 + i * .55

    # 1 — a molecule
    x0 = cxs[0]; R = 20
    pts = [(x0 + R * math.cos(math.radians(90 + 60 * k)), cy - R * math.sin(math.radians(90 + 60 * k))) for k in range(6)]
    ring = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z"
    b.append(f'<path d="{ring}" fill="none" stroke="{MUTED}" stroke-width="2.2" stroke-linejoin="round" '
             f'stroke-dasharray="{6*R}" stroke-dashoffset="{6*R}" class="draw" {d(t0(0))}/>')
    for (x, y), (dx, dy), col in ((pts[0], (0, -18), CRIT), (pts[3], (0, 18), BLUE), (pts[2], (-16, 9), MUTED)):
        b.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x+dx:.1f}" y2="{y+dy:.1f}" stroke="{MUTED}" stroke-width="2.2" class="fade" {d(t0(0)+.4)}/>'
                 f'<circle cx="{x+dx:.1f}" cy="{y+dy:.1f}" r="5" fill="{col}" class="pop" {d(t0(0)+.5)}/>')

    # 2 — look-alikes in chemical space
    random.seed(11); x1 = cxs[1]; cloud = []
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

    # 3 — risk screen: some candidates pass, some get flagged
    x2 = cxs[2]
    for i, ok in enumerate([1, 0, 1, 1, 0, 1, 0, 1]):
        x, y = x2 - 45 + (i % 4) * 30, cy - 14 + (i // 4) * 28
        col = OK if ok else CRIT
        b.append(f'<circle cx="{x}" cy="{y}" r="8" fill="{col}" fill-opacity="{.9 if ok else .25}" class="pop" {d(t0(2)+i*.06)}/>')
        if not ok:
            b.append(f'<path d="M{x-4},{y-4} L{x+4},{y+4} M{x+4},{y-4} L{x-4},{y+4}" stroke="{CRIT}" stroke-width="1.8" '
                     f'stroke-linecap="round" class="fade" {d(t0(2)+.5)}/>')

    # 4 — best trade-offs: a frontier across two goals
    x3 = cxs[3]; ax, ay = x3 - 46, cy + 30
    b.append(f'<path d="M{ax},{ay-62} V{ay} H{ax+96}" fill="none" stroke="{LINE}" stroke-width="1.5" class="fade" {d(t0(3))}/>')
    random.seed(3)
    for i in range(14):
        px, py = ax + 8 + random.random() * 70, ay - 6 - random.random() * 44
        b.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="2.4" fill="{DIM}" class="fade" {d(t0(3)+.1+i*.02)}/>')
    front = [(ax + 8, ay - 56), (ax + 34, ay - 50), (ax + 58, ay - 38), (ax + 80, ay - 18)]
    path = "M" + " L".join(f"{x},{y}" for x, y in front)
    L = sum(math.dist(front[i], front[i + 1]) for i in range(3))
    b.append(f'<path d="{path}" fill="none" stroke="{BLUE}" stroke-width="1.6" stroke-dasharray="{L:.0f}" '
             f'stroke-dashoffset="{L:.0f}" class="draw" {d(t0(3)+.4)}/>')
    for i, (x, y) in enumerate(front):
        b.append(f'<circle cx="{x}" cy="{y}" r="3.6" fill="{BLUE}" class="pop" {d(t0(3)+.5+i*.07)}/>')

    # 5 — quantum check: an orbital drawn as contour lobes
    x4 = cxs[4]
    for k, (ry, rx, op) in enumerate(((26, 16, .9), (19, 11, .65), (11, 6, .4))):
        for sgn, col in ((-1, BLUE), (1, CHEM)):
            yc = cy + sgn * (ry + 2)
            per = math.pi * (3 * (rx + ry) - math.sqrt((3 * rx + ry) * (rx + 3 * ry)))
            b.append(f'<ellipse cx="{x4:.1f}" cy="{yc:.1f}" rx="{rx}" ry="{ry}" fill="none" stroke="{col}" stroke-opacity="{op}" '
                     f'stroke-width="1.5" stroke-dasharray="{per:.1f}" stroke-dashoffset="{per:.1f}" class="draw" {d(t0(4)+k*.15)}/>')
    b.append(f'<circle cx="{x4:.1f}" cy="{cy}" r="3" fill="{TXT}" class="pop" {d(t0(4))}/>')

    # connectors + labels
    for i in range(n - 1):
        mx = (cxs[i] + cxs[i + 1]) / 2
        b.append(f'<text x="{mx:.0f}" y="{cy+5}" font-size="16" text-anchor="middle" class="d fade" {d(t0(i)+.4)}>›</text>')
    for i, (a, sub) in enumerate(steps):
        b.append(f'<g class="rise" {d(t0(i)+.2)}><text x="{cxs[i]:.0f}" y="{cy+66}" font-size="13" text-anchor="middle" class="b">{esc(a)}</text>'
                 f'<text x="{cxs[i]:.0f}" y="{cy+85}" font-size="11.5" text-anchor="middle" class="m">{esc(sub)}</text></g>')
    svg("flagship.svg", H, "".join(b))


# ── 3. project cards ─────────────────────────────────────────────────
CW, CH = 412, 176
PROJECTS = [
    ("devansh-OS", "OSS", OK, "Self-hosted personal analytics that flags what I've been neglecting. Plug-in providers unify "
     "8 data sources; sub-50ms reads.", "FastAPI · SQLite · APScheduler · PyInstaller", "25MB native macOS app · 7-day sprint"),
    ("confidently-wrong", "LIVE", OK, "Trick an open-source 421M-param model into confident wrong answers. ~2.4k examples scored on "
     "ECE/Brier; shipped 6/12 missions on evidence.", "FastAPI on Cloud Run · Next.js · Firebase", "solo · live leaderboard · LLM judge"),
    ("codeweb", "LIVE", OK, "Turns any local or GitHub repo into an interactive dependency graph of files, functions and "
     "imports, with AI node explanations.", "Node · Neo4j · Groq · Render", "multi-tenant · batched UNWIND ingest"),
    ("codeClimb", "LIVE", OK, "Codeforces training PWA: personalized daily drills from your rating history, AI hints and a "
     "live friends leaderboard.", "React Native · Expo · Firebase · Vercel", "~92% fewer API calls via caching"),
    ("InSilicomate", "OSS", CHEM, "Consensus binding-site finder (CASTp × COACH-D) that auto-preps AutoDock Vina "
     "docking runs, with 3D pocket viewer.", "Python · 3Dmol.js · AutoDock Vina", "structural bio"),
    ("hexago", "OSS", CHEM, "Steganography in Go: hides text and images inside perfectly valid SGF game records.",
     "Python · Flask · Pillow", "1 bit / stone"),
]


def card(name, status, accent, desc, stack, badge, i):
    b = [f'<rect x=".5" y=".5" width="{CW-1}" height="{CH-1}" rx="12" fill="{BG}" stroke="{LINE}"/>',
         f'<rect x="0" y="16" width="3" height="28" rx="1.5" fill="{accent}"/>',
         f'<text x="20" y="36" font-size="17" class="b slide" {d(.1)}>{esc(name)}</text>']
    sc = OK if status == "LIVE" else MUTED
    b.append(f'<circle cx="{CW-70}" cy="31" r="4" fill="{sc}" class="{"pulse" if status == "LIVE" else ""}"/>'
             f'<text x="{CW-60}" y="35" font-size="11" style="fill:{sc}" class="b">{status}</text>')
    for j, ln in enumerate(wrap(desc, 50)[:3]):
        b.append(f'<text x="20" y="{64 + j*18}" font-size="12.5" class="fade" {d(.25 + j*.08)}>{esc(ln)}</text>')
    b.append(f'<line x1="20" y1="{CH-40}" x2="{CW-20}" y2="{CH-40}" stroke="{LINE}"/>')
    b.append(f'<text x="20" y="{CH-17}" font-size="11" class="m fade" {d(.6)}>{esc(stack)}</text>')
    b.append(f'<text x="20" y="{CH-52}" font-size="11.5" class="fade" style="fill:{accent};animation-delay:.7s">▸ {esc(badge)}</text>')
    doc = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{CW}" height="{CH}" viewBox="0 0 {CW} {CH}" role="img">'
           f'<style>{BASE_CSS}</style>{"".join(b)}</svg>')
    (OUT / f"card-{name.lower()}.svg").write_text(doc)


# ── 4. neglect detection (the grass joke) ────────────────────────────
def neglect():
    rows = [
        ("✕", CRIT, "GitHub graph:", "mostly grass. The real work lives in private repos and at my day job."),
        ("✓", OK, "Shipping:", "3 projects live · SDE intern @ Amazon since July 2026."),
    ]
    b = [titlebar("NEGLECT DETECTION", "✕ 1 critical   ✓ 1 ok")]
    b.append(f'<text x="32" y="68" font-size="12" class="m fade">// devansh-OS rule: the data never lies, so neither does this panel.</text>')
    for i, (ic, c, k, v) in enumerate(rows):
        y = 100 + i * 28; t = .4 + i * .35
        b.append(f'<g class="slide" {d(t)}><text x="32" y="{y}" font-size="14" class="b" style="fill:{c}">{ic}</text>'
                 f'<text x="56" y="{y}" font-size="13" class="b" style="fill:{c}">{esc(k)}</text>'
                 f'<text x="{56 + len(k)*8 + 10}" y="{y}" font-size="13">{esc(v)}</text></g>')
    # tiny grass strip — 53 weeks, mostly empty, a few bursts
    import random
    random.seed(7)
    gx, gy = 32, 166
    for wk in range(53):
        for dy in range(2):
            lit = random.random() < (0.35 if 26 <= wk <= 38 else 0.05)
            col = random.choice(["#0e4429", "#006d32", "#26a641"]) if lit else "#161b22"
            b.append(f'<rect x="{gx + wk*14.6:.1f}" y="{gy + dy*12}" width="11" height="9" rx="2" fill="{col}"/>')
    b.append(f'<text x="{W-32}" y="{gy+44}" font-size="10" class="d" text-anchor="end">↑ public contributions, artistically compressed</text>')
    svg("neglect.svg", 226, "".join(b))


# ── 5. stack ─────────────────────────────────────────────────────────
def stack():
    groups = [
        ("lang", OK, ["Python", "TypeScript", "JavaScript", "SQL", "Dart"]),
        ("backend", BLUE, ["FastAPI", "Redis/RQ", "Postgres/Supabase", "Neo4j", "SQLite", "Docker"]),
        ("science", CHEM, ["RDKit", "PySCF", "scikit-learn", "AutoDock Vina", "3Dmol.js"]),
        ("ship", WARN, ["Vercel", "Railway", "Render", "Modal", "Expo", "PyInstaller"]),
    ]
    b = [titlebar("devansh@os ~ $ cat stack.toml")]
    for i, (k, c, items) in enumerate(groups):
        y = 74 + i * 34
        b.append(f'<text x="32" y="{y}" font-size="13" class="b slide" style="fill:{c};animation-delay:{.2+i*.15:.2f}s">[{k}]</text>')
        x = 132
        for j, it in enumerate(items):
            wpx = len(it) * 7.4 + 18
            b.append(f'<g class="fade" {d(.35 + i*.15 + j*.05)}><rect x="{x:.0f}" y="{y-15}" width="{wpx:.0f}" height="22" rx="5" '
                     f'fill="{PANEL}" stroke="{LINE}"/><text x="{x + wpx/2:.0f}" y="{y}" font-size="12" text-anchor="middle">{esc(it)}</text></g>')
            x += wpx + 7
    svg("stack.svg", 206, "".join(b))


# ── 6. footer: a Go board that actually hides a message (hexago) ────
def footer():
    msg = "hire me"
    bits = "".join(f"{ord(ch):08b}" for ch in msg)  # 56 bits, black=1 white=0 (hexago's scheme)
    N, cell, bx, by = 9, 11, 46, 60
    b = [titlebar("easter-egg.sgf", "encoded with hexago")]
    b.append(f'<rect x="{bx-9}" y="{by-9}" width="{(N-1)*cell+18}" height="{(N-1)*cell+18}" rx="4" fill="#c69c5d"/>')
    for k in range(N):
        b.append(f'<line x1="{bx}" y1="{by+k*cell}" x2="{bx+(N-1)*cell}" y2="{by+k*cell}" stroke="#4a3518" stroke-width="1"/>'
                 f'<line x1="{bx+k*cell}" y1="{by}" x2="{bx+k*cell}" y2="{by+(N-1)*cell}" stroke="#4a3518" stroke-width="1"/>')
    for i, bit in enumerate(bits):
        r_, c_ = divmod(i, N)
        fill, st = ("#111", "#000") if bit == "1" else ("#f2f2f2", "#999")
        b.append(f'<circle cx="{bx+c_*cell}" cy="{by+r_*cell}" r="4.6" fill="{fill}" stroke="{st}" class="pop" {d(.3 + i*.045)}/>')
    b.append(f'<text x="170" y="94" font-size="13" class="m fade" {d(3.0)}>this position is not a game.</text>'
             f'<text x="170" y="116" font-size="12" class="d fade" {d(3.3)}>(black = 1)</text>')
    svg("footer.svg", 166, "".join(b))


if __name__ == "__main__":
    header(); flagship(); neglect(); footer()
    for i, p in enumerate(PROJECTS):
        card(*p, i)
    print("built", sorted(p.name for p in OUT.iterdir()))
