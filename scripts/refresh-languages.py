#!/usr/bin/env python3
"""Regenerate assets/work-languages.svg with fresh "languages by commit" data.

Data source: the most-commit-language card produced by
vn7n24fzkq/github-profile-summary-cards, run earlier in the workflow with
AUTO_PUSH disabled (so its ~50 theme folders are never committed). We parse that
card's donut geometry + legend, keep the top 3 languages plus an "Other" bucket,
and re-render our own styled editorial card.

Usage: python3 scripts/refresh-languages.py [path-to-most-commit-language.svg]
"""
import math, re, sys

CARD_DEFAULT = "profile-summary-card-output/tokyonight/2-most-commit-language.svg"
OUT = "assets/work-languages.svg"

# brand: matches yipjunkai.com — Geist type, near-black ground, rose-to-purple accent
MONO = "'Geist Mono', ui-monospace, 'SF Mono', Menlo, Consolas, monospace"
SANS = "'Geist', ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"
PALETTE = ["#EE696B", "#C56A9A", "#8A5FA8"]  # top 3: coral -> mauve -> purple
OTHER = "#4E4A55"

WORK = [
    ("pyvolr", "Black-Scholes pricing, Greeks &amp; implied vol &#183; Rust core"),
    ("secrets-spotter", "Real-time secret detection &#183; Rust / WASM"),
    ("PINN-DER", "Physics-informed nets with calibrated uncertainty"),
]


def parse_card(text):
    """Return [(language, fraction), ...] from the summary-card SVG."""
    names = re.findall(r'style="fill: #38bdae;[^"]*">([^<]+)</text>', text)
    arcs = re.findall(
        r'M(-?[0-9.eE+-]+),(-?[0-9.eE+-]+)A[0-9.]+,[0-9.]+,[0-9.]+,[01],[01],(-?[0-9.eE+-]+),(-?[0-9.eE+-]+)',
        text,
    )

    def ang(x, y):
        return math.degrees(math.atan2(x, -y)) % 360

    fracs = []
    for x0, y0, x1, y1 in arcs:
        span = (ang(float(x1), float(y1)) - ang(float(x0), float(y0))) % 360
        fracs.append(span / 360.0)
    return list(zip(names, fracs))


def bucket_top3(langs):
    langs = sorted(langs, key=lambda t: -t[1])
    segs = [[n, round(f * 100)] for n, f in langs[:3]]
    segs.append(["Other", round(sum(f for _, f in langs[3:]) * 100)])
    segs[0][1] += 100 - sum(p for _, p in segs)  # keep total at 100
    return [(n, p) for n, p in segs]


def donut(cx, cy, R, r, segs):
    out, acc = [], 0.0
    colors = PALETTE + [OTHER]

    def pt(rad, deg):
        t = math.radians(deg)
        return round(cx + rad * math.sin(t), 3), round(cy - rad * math.cos(t), 3)

    for (name, pct), color in zip(segs, colors):
        a0, a1 = acc / 100 * 360, (acc + pct) / 100 * 360
        acc += pct
        large = 1 if (a1 - a0) > 180 else 0
        ox0, oy0 = pt(R, a0); ox1, oy1 = pt(R, a1)
        ix1, iy1 = pt(r, a1); ix0, iy0 = pt(r, a0)
        out.append((f"M{ox0},{oy0}A{R},{R},0,{large},1,{ox1},{oy1}"
                    f"L{ix1},{iy1}A{r},{r},0,{large},0,{ix0},{iy0}Z", color))
    return out


def render(segs):
    cx, cy, R, r = 566, 190, 58, 37
    paths = "\n    ".join(f'<path d="{d}" fill="{c}"/>' for d, c in donut(cx, cy, R, r, segs))
    top_name, top_pct = segs[0]
    langdesc = ", ".join(f"{n} {p} percent" for n, p in segs)
    worknames = ", ".join(n for n, _ in WORK)

    # centre the work list vertically on the donut (cy=190) whatever the count
    items = ""
    n_items = len(WORK)
    step = 74 if n_items <= 3 else 64
    ys = [round(190 - step * (n_items - 1) / 2 + step * i) for i in range(n_items)]
    for i, (n, d) in enumerate(WORK):
        y = ys[i]
        items += f'  <text x="48" y="{y}" font-family="{SANS}" font-weight="600" font-size="18" fill="#EDEDED">{n}</text>\n'
        items += f'  <text x="48" y="{y + 19}" font-family="{SANS}" font-size="12.5" fill="#8A8A90">{d}</text>\n'
        if i < n_items - 1:
            items += f'  <line x1="48" y1="{y + 34}" x2="440" y2="{y + 34}" stroke="#221E26" stroke-width="1"/>\n'

    legend = ""
    colors = PALETTE + [OTHER]
    for i, (name, pct) in enumerate(segs):
        y = [154, 180, 206, 232][i]
        legend += (f'    <rect x="648" y="{y - 10}" width="11" height="11" rx="2.5" fill="{colors[i]}"/>'
                   f'<text x="668" y="{y}" fill="#C9C9CE">{name}</text>'
                   f'<text x="772" y="{y}" text-anchor="end" fill="#7C7C82">{pct}%</text>\n')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="330" viewBox="0 0 800 330" role="img" aria-label="Selected work: {worknames}. Languages by commit over the last year: {langdesc}.">
  <rect x="0.75" y="0.75" width="798.5" height="328.5" rx="14" fill="#0A0A0A" stroke="#262229" stroke-width="1.5"/>
  <text x="48" y="54" font-family="{MONO}" font-size="12" letter-spacing="3.2" fill="#8A8A90">SELECTED WORK</text>
{items}  <line x1="470" y1="40" x2="470" y2="290" stroke="#221E26" stroke-width="1"/>
  <text x="502" y="54" font-family="{MONO}" font-size="12" letter-spacing="3.2" fill="#8A8A90">LANGUAGES &#183; BY COMMIT</text>
  <g>
    {paths}
    <text x="{cx}" y="{cy - 1}" text-anchor="middle" font-family="{SANS}" font-weight="700" font-size="23" fill="#EE696B">{top_pct}%</text>
    <text x="{cx}" y="{cy + 17}" text-anchor="middle" font-family="{MONO}" font-size="9.5" letter-spacing="2.5" fill="#8A8A90">{top_name.upper()}</text>
  </g>
  <g font-family="{MONO}" font-size="12.5">
{legend}  </g>
</svg>
'''


def main():
    card = sys.argv[1] if len(sys.argv) > 1 else CARD_DEFAULT
    segs = bucket_top3(parse_card(open(card).read()))
    open(OUT, "w").write(render(segs))
    print("languages by commit:", ", ".join(f"{n} {p}%" for n, p in segs))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
