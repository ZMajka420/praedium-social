#!/usr/bin/env python3
"""Render a Praedium Insights news carousel from a JSON spec into 1080x1350 JPEGs.

Usage: python3 render.py spec.json out_dir

Spec:
{
  "source": "Auction.com Q3 2026 report via HousingWire",
  "slides": [
    {"type": "cover", "kicker": "...", "headline": ["LINE ONE", "LINE TWO"], "accent_line": 1, "sub": "..."},
    {"type": "stat", "kicker": "...", "big": "+25%", "label": "...", "body": "..."},
    {"type": "bars", "kicker": "...", "title": "...", "bars": [["California", 80], ...], "unit": "%", "note": "..."},
    {"type": "points", "kicker": "...", "title": "...", "points": ["...", "..."]},
    {"type": "cta", "kicker": "...", "title": "...", "body": "...", "cta": "..."}
  ]
}
Headline/title strings may wrap a phrase in *asterisks* to color it with the accent.
"""
import base64, html, json, re, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
W, H = 1080, 1350

def b64(path):
    return base64.b64encode(Path(path).read_bytes()).decode()

ICON = b64(HERE / "icon.png")
LOGO = b64(HERE / "logo.jpg")

def accent(text):
    t = html.escape(text)
    return re.sub(r"\*(.+?)\*", r'<span class="acc">\1</span>', t)

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1350px}
body{font-family:'Inter',sans-serif;color:#0B1B3F;background:#FFFFFF;overflow:hidden;position:relative;-webkit-font-smoothing:antialiased}
.top{position:absolute;top:72px;left:88px;right:88px;display:flex;align-items:center;justify-content:space-between;padding-bottom:28px;border-bottom:2px solid #0B1B3F}
.top img{height:72px}
.count{font-weight:600;font-size:22px;color:#6B7895;letter-spacing:2px}
.kicker{font-weight:700;font-size:23px;letter-spacing:3px;text-transform:uppercase;color:#1F5EEB}
.acc{color:#1F5EEB}
.content{position:absolute;left:88px;right:88px;top:200px;bottom:150px;display:flex;flex-direction:column;justify-content:center}
.foot{position:absolute;bottom:62px;left:88px;right:88px;display:flex;justify-content:space-between;align-items:center;font-size:20px;color:#6B7895;font-weight:500;padding-top:22px;border-top:1px solid #DDE2EC}
.foot b{color:#0B1B3F;font-weight:600}
.rule{width:72px;height:4px;background:#1F5EEB;margin:36px 0}

.cover .content{justify-content:center}
.cover h1{white-space:nowrap;font-family:'Inter Display';font-weight:800;font-size:91px;line-height:1.0;letter-spacing:-3.5px;margin-top:30px}
.cover .sub{font-size:34px;line-height:1.45;color:#3E4A66;font-weight:400;margin-top:40px;max-width:860px}
.cover .fig{display:flex;align-items:flex-end;gap:28px;padding:36px 0 40px;border-bottom:1px solid #DDE2EC;margin-bottom:56px}
.cover .fig .num{font-family:'Inter Display';font-weight:700;font-size:190px;line-height:.85;letter-spacing:-8px;color:#1F5EEB}
.cover .fig .cap{font-size:26px;line-height:1.4;color:#3E4A66;font-weight:500;max-width:420px;padding-bottom:10px}

.stat .big{font-family:'Inter Display';font-weight:700;font-size:300px;line-height:.85;letter-spacing:-12px;color:#0B1B3F;margin-top:40px}
.stat .label{font-family:'Inter Display';font-weight:700;font-size:54px;line-height:1.12;letter-spacing:-1.2px;margin-top:44px}
.stat .body{font-size:33px;line-height:1.5;color:#3E4A66;max-width:880px}

.bars h2,.points h2,.cta h2{font-family:'Inter Display';font-weight:800;font-size:72px;line-height:1.05;letter-spacing:-2.2px;margin-top:26px}
.bars .list{margin-top:64px;display:flex;flex-direction:column}
.bar{display:grid;grid-template-columns:240px 1fr 130px;align-items:center;gap:24px;padding:22px 0;border-bottom:1px solid #E6EAF1}
.bar:first-child{border-top:1px solid #E6EAF1}
.bar .n{font-size:30px;font-weight:500;color:#0B1B3F}
.bar .track{height:22px;background:transparent}
.bar .fill{height:100%;background:#C9D6F5}
.bar.hl .fill{background:#1F5EEB}
.bar.hl .n,.bar.hl .v{font-weight:700;color:#1F5EEB}
.bar .v{font-family:'Inter Display';font-weight:600;font-size:34px;text-align:right;color:#0B1B3F}
.note{margin-top:48px;font-size:29px;line-height:1.5;color:#3E4A66}

.points ol{list-style:none;margin-top:56px;display:flex;flex-direction:column}
.points li{display:grid;grid-template-columns:70px 1fr;gap:20px;font-size:33px;line-height:1.45;color:#0B1B3F;padding:26px 0;border-top:1px solid #E6EAF1}
.points li .i{font-family:'Inter Display';font-weight:700;font-size:30px;color:#1F5EEB;padding-top:3px}

.cta .body{font-size:36px;line-height:1.5;color:#3E4A66}
.cta .btn{align-self:flex-start;margin-top:60px;padding:26px 40px;background:#0B1B3F;color:#fff;font-weight:600;font-size:30px;letter-spacing:.3px}
.cta .url{margin-top:24px;font-size:26px;color:#6B7895;font-weight:500}
"""

def top(i, n):
    return f'<div class="top"><img src="data:image/jpeg;base64,{LOGO}"><div class="count">{i:02d} / {n:02d}</div></div>'

def foot(source, last=False):
    left = f"Source: {html.escape(source)}" if source else ""
    return f'<div class="foot"><span>{left}</span><span><b>@praedium_insights</b></span></div>'

def slide_html(s, i, n, source):
    t = s["type"]
    k = f'<div class="kicker">{html.escape(s.get("kicker",""))}</div>' if s.get("kicker") else ""
    if t == "cover":
        lines = s["headline"]
        al = s.get("accent_line")
        h = "<br>".join(f'<span class="acc">{html.escape(l)}</span>' if j == al else accent(l) for j, l in enumerate(lines))
        fig = f'<div class="fig"><div class="num">{html.escape(s["fig"])}</div><div class="cap">{accent(s.get("fig_caption",""))}</div></div>' if s.get("fig") else ""
        body = f'<div class="content">{fig}{k}<h1>{h}</h1><div class="sub">{accent(s.get("sub",""))}</div></div>'
    elif t == "stat":
        body = f'<div class="content">{k}<div class="big">{html.escape(s["big"])}</div><div class="label">{accent(s["label"])}</div><div class="rule"></div><div class="body">{accent(s.get("body",""))}</div></div>'
    elif t == "bars":
        mx = max(v for _, v in s["bars"]) or 1
        unit = s.get("unit", "")
        hl = set(s.get("highlight", []))
        rows = "".join(
            f'<div class="bar{" hl" if name in hl else ""}"><div class="n">{html.escape(name)}</div><div class="track"><div class="fill" style="width:{max(v/mx*100,3):.1f}%"></div></div><div class="v">{s.get("prefix","")}{v}{unit}</div></div>'
            for name, v in s["bars"])
        note = f'<div class="note">{accent(s["note"])}</div>' if s.get("note") else ""
        body = f'<div class="content">{k}<h2>{accent(s["title"])}</h2><div class="list">{rows}</div>{note}</div>'
    elif t == "points":
        items = "".join(f'<li><div class="i">{j+1}</div><div>{accent(p)}</div></li>' for j, p in enumerate(s["points"]))
        body = f'<div class="content">{k}<h2>{accent(s["title"])}</h2><ol>{items}</ol></div>'
    elif t == "cta":
        body = (f'<div class="content">{k}<h2>{accent(s["title"])}</h2><div class="rule"></div><div class="body">{accent(s.get("body",""))}</div>'
                f'<div class="btn">{html.escape(s.get("cta","Follow for daily market intel"))}</div><div class="url">praediumcrm.com</div></div>')
    else:
        raise ValueError(t)
    return f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body class="{t}">{top(i,n)}{body}{foot(source)}</body></html>'

def main(spec_path, out_dir):
    spec = json.loads(Path(spec_path).read_text())
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    slides = spec["slides"]; n = len(slides)
    paths = []
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": W, "height": H})
        for i, s in enumerate(slides, 1):
            pg.set_content(slide_html(s, i, n, spec.get("source", "")), wait_until="load")
            pg.wait_for_timeout(150)
            png = out / f"slide{i}.png"
            pg.screenshot(path=str(png), clip={"x": 0, "y": 0, "width": W, "height": H})
            from PIL import Image
            jpg = out / f"slide{i}.jpg"
            Image.open(png).convert("RGB").save(jpg, "JPEG", quality=92, optimize=True)
            png.unlink(); paths.append(str(jpg))
        b.close()
    print("\n".join(paths))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
