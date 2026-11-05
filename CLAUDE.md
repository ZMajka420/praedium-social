# praedium-social

Automation repo for Praedium Insights news carousels (Instagram @praedium_insights + Facebook Page "Praedium Insights").

- `tools/render.py spec.json out_dir` renders 1080x1350 JPEG slides (white editorial style, navy #0B1B3F, accent #1F5EEB, Inter Display). Needs `tools/icon.png` and `tools/logo.jpg` beside it.
- Slide types: cover (headline lines, optional fig + fig_caption, sub), stat (big, label, body), bars (title, bars, prefix/unit, highlight, note), points (title, points), cta (title, body, cta). `*phrase*` = accent color.
- Each carousel lives in `carousels/YYYY-MM-DD-<slot>-<slug>/` with `spec.json` + `slide1..N.jpg`. Repo is public; Instagram pulls images from `https://raw.githubusercontent.com/ZMajka420/praedium-social/main/<path>`.
- `stories.json` logs posted stories (never repeat) and a backlog for slow news days.
- Style rules: white background, clean and professional, no gradients/glows/emoji in slides, no copied article images or text — original layouts and paraphrased facts only, always credit the source on every slide.
