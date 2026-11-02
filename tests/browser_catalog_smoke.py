#!/usr/bin/env python3
"""Smoke-test the actual public browsing page, facets and asset inspector."""
from __future__ import annotations

import contextlib
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import expect, sync_playwright

SITE = Path(__file__).resolve().parents[1] / "site"


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def check(page):
    errors = []
    page.on("pageerror", lambda err: errors.append(str(err)))
    page.reload(wait_until="networkidle")
    expect(page.locator("#count")).to_have_text("70 matches", timeout=20000)

    page.locator("#pack").select_option("legacy-icons")
    expect(page.locator("#count")).to_have_text("2,073 matches")
    page.locator("#domain").select_option("programming")
    expect(page.locator("#count")).to_have_text("195 matches")
    page.locator("#clear-filters").click()
    expect(page.locator("#count")).to_have_text("70 matches")

    page.locator("#status").select_option("archive")
    expect(page.locator("#count")).to_have_text("2,073 matches")
    page.locator("#review").select_option("reviewed")
    expect(page.locator("#count")).to_have_text("734 matches")
    page.locator("#clear-filters").click()

    page.locator("#search").fill("healthbar")
    page.locator("#gallery .asset-tile").first.wait_for(timeout=10000)
    assert "Health Meter" in page.locator("#gallery").inner_text(), "Synonym search failed"
    page.locator("#gallery .asset-tile").first.click()
    page.locator("#detail[open]").wait_for(timeout=20000)
    assert page.locator("#detail-tags span").count() >= 1, "No manifest keywords in inspector"
    page.locator("#close").click()

    page.locator("#search").fill("flame")
    page.locator("#gallery .asset-tile").first.wait_for(timeout=10000)
    page.locator("#gallery .asset-tile").first.click()
    page.locator("#detail[open]").wait_for(timeout=20000)
    assert not page.locator("#tint-options").is_hidden(), "Legacy recolor control missing"
    page.locator("#tint-enabled").check()
    page.locator("#detail-canvas").wait_for()
    page.locator("#close").click()
    assert not errors, "Browser JavaScript errors: " + repr(errors)
    return page.locator("#count").inner_text()


def main():
    assert (SITE / "public-catalog.json").exists(), "Build site before browser smoke"
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(SITE)))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/"
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 1000}, base_url=url)
                page.goto(url, wait_until="networkidle")
                print("Desktop:", check(page))
                mobile = browser.new_page(viewport={"width": 390, "height": 844}, base_url=url)
                mobile.goto(url, wait_until="networkidle")
                expect(mobile.locator("#count")).to_have_text("70 matches", timeout=20000)
                assert mobile.evaluate("document.documentElement.scrollWidth <= innerWidth + 2"), "Horizontal overflow on mobile"
                print("Responsive viewport: PASS")
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
    print("Public browser end-to-end smoke: PASS")


if __name__ == "__main__":
    main()
