# -*- coding: utf-8 -*-
"""Package PowerPoint-rendered slide PNGs into one offline HTML presentation."""

from __future__ import annotations

import base64
import hashlib
import html
import json
from pathlib import Path


SLIDE_DIR = Path(
    "code/_cleanup_archive_20260827/reviews/"
    "review_spatial_ppt_final_v11_html_source"
)
OUTPUT = Path(
    "code/_cleanup_archive_20260827/ppt_intermediates/"
    "空间域可视化_final_v11_self_contained.html"
)
TITLE = "Spatial-domain CO₂ visualisation"


def data_url(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def main() -> None:
    paths = [SLIDE_DIR / f"slide-{index}.png" for index in range(1, 7)]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing rendered slides: {missing}")

    sources = [data_url(path) for path in paths]
    source_json = json.dumps(sources, ensure_ascii=False)
    digest = hashlib.sha256("".join(sources).encode("ascii")).hexdigest()

    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="generator" content="PowerPoint slide render packaged as self-contained HTML">
  <meta name="slide-image-sha256" content="{digest}">
  <title>{html.escape(TITLE)}</title>
  <style>
    :root {{ color-scheme: dark; }}
    * {{ box-sizing: border-box; }}
    html, body {{ width: 100%; height: 100%; margin: 0; overflow: hidden; }}
    body {{
      display: grid;
      place-items: center;
      background: #111;
      font-family: "Segoe UI", Arial, sans-serif;
      user-select: none;
    }}
    .stage {{
      position: relative;
      width: min(100vw, calc(100vh * 16 / 9));
      height: min(100vh, calc(100vw * 9 / 16));
      background: #000;
      overflow: hidden;
      box-shadow: 0 0 38px rgba(0, 0, 0, .55);
    }}
    .slide {{
      position: absolute;
      inset: 0;
      display: none;
      width: 100%;
      height: 100%;
      object-fit: contain;
      background: #fff;
      pointer-events: none;
      -webkit-user-drag: none;
    }}
    .slide.active {{ display: block; }}
    .hit {{ position: absolute; inset-block: 0; width: 22%; cursor: pointer; }}
    .hit.prev {{ left: 0; }}
    .hit.next {{ right: 0; }}
    .controls {{
      position: absolute;
      left: 50%;
      bottom: 18px;
      display: flex;
      align-items: center;
      gap: 10px;
      transform: translateX(-50%);
      padding: 8px 12px;
      border: 1px solid rgba(255,255,255,.25);
      border-radius: 999px;
      background: rgba(0,0,0,.68);
      color: #fff;
      opacity: 0;
      transition: opacity .18s ease;
      backdrop-filter: blur(8px);
    }}
    body.show-controls .controls, .controls:focus-within {{ opacity: 1; }}
    button {{
      min-width: 34px;
      height: 30px;
      border: 0;
      border-radius: 999px;
      background: rgba(255,255,255,.14);
      color: #fff;
      font: inherit;
      cursor: pointer;
    }}
    button:hover {{ background: rgba(255,255,255,.25); }}
    .counter {{ min-width: 58px; text-align: center; font-size: 13px; }}
    .help {{
      position: absolute;
      right: 14px;
      bottom: 12px;
      color: rgba(255,255,255,.75);
      font-size: 12px;
      opacity: 0;
      transition: opacity .18s ease;
    }}
    body.show-controls .help {{ opacity: 1; }}
    @media print {{
      @page {{ size: 13.333in 7.5in; margin: 0; }}
      html, body {{ display: block; width: auto; height: auto; overflow: visible; background: #fff; }}
      .stage {{ width: 13.333in; height: auto; overflow: visible; box-shadow: none; }}
      .slide {{ position: relative; display: block; width: 13.333in; height: 7.5in; page-break-after: always; }}
      .hit, .controls, .help {{ display: none !important; }}
    }}
  </style>
</head>
<body>
  <main class="stage" id="stage" aria-label="{html.escape(TITLE)}"></main>
  <script>
    const sources = {source_json};
    const stage = document.getElementById('stage');
    let current = Math.max(0, Math.min(sources.length - 1,
      Number(new URLSearchParams(location.hash.slice(1)).get('slide') || 1) - 1));

    const images = sources.map((src, index) => {{
      const image = document.createElement('img');
      image.className = 'slide';
      image.src = src;
      image.alt = `Slide ${{index + 1}} of ${{sources.length}}`;
      image.decoding = 'sync';
      stage.appendChild(image);
      return image;
    }});

    const previousHit = Object.assign(document.createElement('div'), {{ className: 'hit prev' }});
    const nextHit = Object.assign(document.createElement('div'), {{ className: 'hit next' }});
    stage.append(previousHit, nextHit);

    const controls = document.createElement('nav');
    controls.className = 'controls';
    controls.setAttribute('aria-label', 'Slide controls');
    controls.innerHTML = `
      <button type="button" data-action="previous" aria-label="Previous slide">←</button>
      <span class="counter" aria-live="polite"></span>
      <button type="button" data-action="next" aria-label="Next slide">→</button>
      <button type="button" data-action="fullscreen" aria-label="Toggle fullscreen">⛶</button>`;
    stage.appendChild(controls);
    const counter = controls.querySelector('.counter');

    const help = document.createElement('div');
    help.className = 'help';
    help.textContent = '← → / Space · F fullscreen';
    stage.appendChild(help);

    function show(index) {{
      current = (index + images.length) % images.length;
      images.forEach((image, i) => image.classList.toggle('active', i === current));
      counter.textContent = `${{current + 1}} / ${{images.length}}`;
      history.replaceState(null, '', `#slide=${{current + 1}}`);
      document.title = `${{current + 1}}/${{images.length}} · {html.escape(TITLE)}`;
    }}
    function next() {{ show(current + 1); }}
    function previous() {{ show(current - 1); }}
    async function fullscreen() {{
      if (!document.fullscreenElement) await stage.requestFullscreen();
      else await document.exitFullscreen();
    }}

    previousHit.addEventListener('click', previous);
    nextHit.addEventListener('click', next);
    controls.addEventListener('click', event => {{
      const action = event.target.closest('button')?.dataset.action;
      if (action === 'previous') previous();
      if (action === 'next') next();
      if (action === 'fullscreen') fullscreen();
    }});
    document.addEventListener('keydown', event => {{
      if (['ArrowRight', 'PageDown', 'Enter', ' '].includes(event.key)) {{ event.preventDefault(); next(); }}
      if (['ArrowLeft', 'PageUp', 'Backspace'].includes(event.key)) {{ event.preventDefault(); previous(); }}
      if (event.key.toLowerCase() === 'f') fullscreen();
      if (event.key === 'Home') show(0);
      if (event.key === 'End') show(images.length - 1);
    }});

    let controlsTimer;
    function revealControls() {{
      document.body.classList.add('show-controls');
      clearTimeout(controlsTimer);
      controlsTimer = setTimeout(() => document.body.classList.remove('show-controls'), 1400);
    }}
    document.addEventListener('mousemove', revealControls);
    document.addEventListener('touchstart', revealControls, {{ passive: true }});
    show(current);
  </script>
</body>
</html>
"""
    OUTPUT.write_text(document, encoding="utf-8")
    print(f"{OUTPUT} ({OUTPUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
