"""
Build a GitHub-activity stats card SVG: Total Contributions | Current Streak
(with a ring + flame icon) | Longest Streak -- styled after the user's
reference screenshot (pink numbers, green streak ring, gold streak count),
but kept in the same dark terminal-window chrome as the other profile cards.

Reads real numbers from data/contributions.json (produced by
fetch_contributions.py) -- no placeholder data.

    STATIC=1 python3 scripts/make_activity_card.py   # frozen preview
    python3 scripts/make_activity_card.py            # real animated file
"""
import datetime
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
IN_PATH = os.path.join(HERE, "..", "data", "contributions.json")
OUT_PATH = os.path.join(HERE, "..", "activity-card.svg")
STATIC = bool(os.environ.get("STATIC"))

W, H = 560, 224
PAD = 20
TITLEBAR_H = 30

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
MUTED = "#7d8590"
TITLE_TEXT = "#7d8590"
INK = "#c9d1d9"

PINK = "#f0567a"
GREEN = "#2ee89e"
GOLD = "#ffce54"

# a simple, generic flame silhouette (not traced from any icon library)
FLAME_PATH = (
    "M12 1.5c-1.1 2.6-3.6 4.4-3.6 8 0 2.9 2.3 5.2 5.2 5.2s5.2-2.3 5.2-5.2"
    "c0-1.4-.5-2.4-1.2-3.4.1 1.4-.6 2.4-1.4 2.4.6-1.8-.1-3.5-1.5-5.2"
    "-.9-1.1-1.9-1.4-2.7-1.8z"
)


def esc(s):
    return html.escape(s)


def fmt_short(date_s):
    d = datetime.date.fromisoformat(date_s)
    return f"{d.strftime('%b')} {d.day}"


def fmt_long(date_s):
    d = datetime.date.fromisoformat(date_s)
    return f"{d.strftime('%b')} {d.day}, {d.year}"


def range_label(start_s, end_s, today_is_end):
    start = fmt_long(start_s)
    end = "Present" if today_is_end else fmt_long(end_s)
    return f"{start} - {end}"


def streak_range_label(start_s, end_s):
    if start_s is None:
        return "No active streak"
    sd = datetime.date.fromisoformat(start_s)
    ed = datetime.date.fromisoformat(end_s)
    if sd.year == ed.year:
        return f"{fmt_short(start_s)} - {fmt_short(end_s)}"
    return f"{fmt_short(start_s)}, {sd.year} - {fmt_short(end_s)}, {ed.year}"


def reveal(inner, i, static):
    if static:
        return f"<g>{inner}</g>"
    delay = 0.15 + i * 0.12
    return (f'<g opacity="0" transform="translate(0,6)">{inner}'
            f'<animate attributeName="opacity" from="0" to="1" begin="{delay:.2f}s" dur="0.45s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" from="0 6" to="0 0" '
            f'begin="{delay:.2f}s" dur="0.45s" fill="freeze" calcMode="spline" keySplines="0.2 0.8 0.2 1"/></g>')


def render(data, static=False):
    total = data["total_contributions"]
    rng = data["range"]
    cur = data["current_streak"]
    longest = data["longest_streak"]

    col_w = (W - 2 * PAD) / 3
    col1_x = PAD + col_w * 0.5
    col2_x = PAD + col_w * 1.5
    col3_x = PAD + col_w * 2.5
    div1_x = PAD + col_w
    div2_x = PAD + col_w * 2

    top = TITLEBAR_H
    circle_cy = top + 62
    circle_r = 34

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        '<defs>'
        f'<linearGradient id="abg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
        f'<rect width="{W}" height="{H}" rx="12" fill="url(#abg)"/>',
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
    ]
    for i, dotcol in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dotcol}"/>')
    parts.append(f'<text x="{W/2}" y="{TITLEBAR_H/2 + 4}" fill="{TITLE_TEXT}" font-size="12" '
                 f'text-anchor="middle">Bhavesh-Malpure: ~$ github --activity</text>')

    # column dividers
    parts.append(f'<line x1="{div1_x:.1f}" y1="{top+22}" x2="{div1_x:.1f}" y2="{H-22}" stroke="{FRAME}"/>')
    parts.append(f'<line x1="{div2_x:.1f}" y1="{top+22}" x2="{div2_x:.1f}" y2="{H-22}" stroke="{FRAME}"/>')

    # --- column 1: Total Contributions ---
    inner1 = (
        f'<text x="{col1_x:.1f}" y="{top+58}" fill="{PINK}" font-size="30" font-weight="700" text-anchor="middle">{total:,}</text>'
        f'<text x="{col1_x:.1f}" y="{top+82}" fill="{PINK}" font-size="12.5" font-weight="700" text-anchor="middle">Total Contributions</text>'
        f'<text x="{col1_x:.1f}" y="{top+104}" fill="{MUTED}" font-size="10.5" text-anchor="middle">{esc(range_label(rng["start"], rng["end"], True))}</text>'
    )
    parts.append(reveal(inner1, 0, static))

    # --- column 2: Current Streak (ring + flame + gold number) ---
    flame_scale = 1.15
    flame_y_offset = circle_cy - circle_r - 15
    inner2 = (
        f'<circle cx="{col2_x:.1f}" cy="{circle_cy}" r="{circle_r}" fill="none" stroke="{GREEN}" stroke-width="4"/>'
        f'<g transform="translate({col2_x-12*flame_scale:.1f},{flame_y_offset:.1f}) scale({flame_scale})">'
        f'<path d="{FLAME_PATH}" fill="{GREEN}"/></g>'
        f'<text x="{col2_x:.1f}" y="{circle_cy+9}" fill="{GOLD}" font-size="26" font-weight="700" text-anchor="middle">{cur["length"]}</text>'
        f'<text x="{col2_x:.1f}" y="{circle_cy+circle_r+24}" fill="{GREEN}" font-size="12.5" font-weight="700" text-anchor="middle">Current Streak</text>'
        f'<text x="{col2_x:.1f}" y="{circle_cy+circle_r+46}" fill="{MUTED}" font-size="10.5" text-anchor="middle">{esc(streak_range_label(cur["start"], cur["end"]))}</text>'
    )
    parts.append(reveal(inner2, 1, static))

    # --- column 3: Longest Streak ---
    inner3 = (
        f'<text x="{col3_x:.1f}" y="{top+58}" fill="{PINK}" font-size="30" font-weight="700" text-anchor="middle">{longest["length"]}</text>'
        f'<text x="{col3_x:.1f}" y="{top+82}" fill="{PINK}" font-size="12.5" font-weight="700" text-anchor="middle">Longest Streak</text>'
        f'<text x="{col3_x:.1f}" y="{top+104}" fill="{MUTED}" font-size="10.5" text-anchor="middle">{esc(streak_range_label(longest["start"], longest["end"]))}</text>'
    )
    parts.append(reveal(inner3, 2, static))

    parts.append("</svg>")
    return "".join(parts)


if __name__ == "__main__":
    data = json.load(open(IN_PATH))
    svg = render(data, static=STATIC)
    with open(OUT_PATH, "w") as f:
        f.write(svg)
    print(f"wrote {OUT_PATH} ({len(svg)} bytes)")
