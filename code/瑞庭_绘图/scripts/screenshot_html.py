# -*- coding: utf-8 -*-
"""
Screenshot an ECharts/echarts-gl HTML file via headless Edge.

Usage:
    python screenshot_html.py <html_path> <out_png> [--width 1480] [--height 900] [--element .stage] [--wait 4000]
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("html", type=Path)
    p.add_argument("out", type=Path)
    p.add_argument("--width", type=int, default=1480)
    p.add_argument("--height", type=int, default=900)
    p.add_argument("--element", default=".stage")
    p.add_argument("--wait", type=int, default=4500, help="ms to wait for ECharts to render")
    p.add_argument("--bg", default=None, help="page background color override")
    args = p.parse_args()

    if not args.html.exists():
        print(f"HTML not found: {args.html}")
        return 1

    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--hide-scrollbars")
    opts.add_argument("--enable-webgl")
    opts.add_argument("--ignore-gpu-blocklist")
    opts.add_argument("--enable-unsafe-swiftshader")
    opts.add_argument("--enable-features=Vulkan,UseSkiaRenderer")
    opts.add_argument("--use-gl=angle")
    opts.add_argument("--use-angle=swiftshader")
    opts.add_argument(f"--window-size={args.width},{args.height}")
    opts.add_argument("--force-device-scale-factor=1")

    # Use local Edge. If edge isn't installed, fall back to Chrome.
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    edge_path = next((c for c in candidates if os.path.exists(c)), None)
    if edge_path:
        opts.binary_location = edge_path
    else:
        print("Edge not found, will try default browser", flush=True)

    service = Service()
    driver = webdriver.Edge(options=opts, service=service)
    try:
        file_url = f"file:///{args.html.as_posix()}"
        driver.get(file_url)
        # Wait for body + the target element
        WebDriverWait(driver, 25).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        # Let ECharts render
        time.sleep(args.wait / 1000.0)

        if args.element == "body":
            el = driver.find_element(By.TAG_NAME, "body")
        else:
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, args.element))
                )
            except Exception as e:
                print(f"Element {args.element!r} not found, falling back to body. ({e})", flush=True)
            el = driver.find_element(By.CSS_SELECTOR, args.element) if driver.find_elements(
                By.CSS_SELECTOR, args.element) else driver.find_element(By.TAG_NAME, "body")

        el.screenshot(str(args.out))
        print(f"  saved {args.out}  ({args.out.stat().st_size:,} B)")
    finally:
        driver.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
