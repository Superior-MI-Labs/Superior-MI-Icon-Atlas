#!/usr/bin/env python3
"""Smoke-test the actual public browsing page, facets and asset inspector."""
from __future__ import annotations

import contextlib
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from playwright.sync_api import expect, sync_playwright

SITE = Path(__file__).resolve().parents[1] / "site"


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def published_matches():
    return f"{json.loads((SITE/'public-catalog.json').read_text())['approved_count']:,} matches"


def check(page):
    errors = []
    page.on("pageerror", lambda err: errors.append(str(err)))
    page.reload(wait_until="networkidle")
    expect(page.locator("#count")).to_have_text(published_matches(), timeout=20000)

    page.locator("#pack").select_option("legacy-icons")
    expect(page.locator("#count")).to_have_text("2,073 matches")
    page.locator("#domain").select_option("programming")
    expect(page.locator("#count")).to_have_text("195 matches")
    page.locator("#clear-filters").click()
    expect(page.locator("#count")).to_have_text(published_matches())

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

    # Clear the previous "healthbar" query before selecting a pack: facets show only matching options.
    page.locator("#clear-filters").click()
    # Recolor is a legacy-only control; newer published assets can rank first for "flame".
    page.locator("#pack").select_option("legacy-icons")
    page.locator("#search").fill("flame")
    page.locator("#gallery .asset-tile").first.wait_for(timeout=10000)
    page.locator("#gallery .asset-tile").first.click()
    page.locator("#detail[open]").wait_for(timeout=20000)
    assert not page.locator("#tint-options").is_hidden(), "Legacy recolor control missing"
    page.locator("#tint-enabled").check()
    page.locator("#detail-canvas").wait_for()
    page.locator("#close").click()
    # Import both published ZIPs via their real public entrypoints and inspect controls.
    url=page.url.split('?',1)[0]
    page.goto(url+"?asset=smi.hud.royalforge02.widget.hearts.ruby.adaptive",wait_until="networkidle")
    page.locator("#detail[open]").wait_for(timeout=20000)
    sliders=page.locator("#controls input[type=range]")
    assert sliders.count()==3, "Adaptive hearts must expose max, columns, and current value sliders"
    max_control=page.locator("#controls label").filter(has_text="max").locator('input[type=range]')
    columns=page.locator("#controls label").filter(has_text="columns").locator('input[type=range]')
    value=page.locator("#controls label").filter(has_text="value").locator('input[type=range]')
    def set_slider(control,value):
        control.evaluate("""(e,v)=>{e.value=String(v);e.dispatchEvent(new Event('input',{bubbles:true}))}""",value)
    # Keep the exact slider element alive across capacity updates.
    max_control.evaluate("(e)=>{window.__maxSliderBefore=e}")
    set_slider(max_control,1)
    assert page.evaluate("window.__maxSliderBefore?.isConnected"), "Capacity input was replaced mid-drag"
    set_slider(value,3)
    expect(value).to_have_value("3")
    one_width=int(page.locator("#detail-canvas").get_attribute("width"))
    set_slider(max_control,20)
    assert page.evaluate("window.__maxSliderBefore===document.querySelector('#controls input[data-input-key=max]')"), "Slider identity changed across capacity updates"
    set_slider(columns,10)
    set_slider(value,63)
    expect(value).to_have_value("63")
    page.wait_for_timeout(200)
    many_width=int(page.locator("#detail-canvas").get_attribute("width"))
    assert many_width>one_width, f"Adaptive preview dimensions did not expand: {one_width} to {many_width}"
    page.locator("#close").click()
    page.goto(url+"?asset=smi.ui.fantasy01.wave2.widget.toggle",wait_until="networkidle")
    page.locator("#detail[open]").wait_for(timeout=20000)
    toggle=page.locator("#controls input[type=checkbox]").first
    assert toggle.count()==1, "Core controls must expose an interactive on/off checkbox"
    page.wait_for_timeout(120)
    off=page.locator("#detail-canvas").evaluate("(e)=>e.toDataURL()")
    toggle.check()
    assert page.locator("#controls button").count()>=1, "Toggle must offer declared event preview"
    page.locator("#controls button").filter(has_text="Send activate").click()
    expect(toggle).not_to_be_checked()
    toggle.check()
    page.wait_for_timeout(120)
    on=page.locator("#detail-canvas").evaluate("(e)=>e.toDataURL()")
    assert on!=off, "On/off toggle must visibly change when checked"
    page.locator("#close").click()
    # Direct pointer interaction must dispatch through the same value contract
    # as the ordinary control, on both public and local Builder previews.
    page.goto(url+"?asset=smi.ui.fantasy01.widget.slider.gem",wait_until="networkidle")
    page.locator("#detail[open]").wait_for(timeout=20000)
    canvas=page.locator("#detail-canvas")
    assert canvas.get_attribute("data-interactive")=="true", "Published slider should support direct preview drag"
    box=canvas.bounding_box()
    assert box and box["width"]>0 and box["height"]>0
    y=box["y"]+box["height"]/2
    page.mouse.move(box["x"]+box["width"]*0.22,y)
    page.mouse.down()
    page.mouse.move(box["x"]+box["width"]*0.78,y,steps=5)
    page.mouse.up()
    value=int(page.locator('#controls input[data-input-key="value"]').input_value())
    assert 65<=value<=95, f"Drag did not update authored slider value: {value}"
    page.locator("#close").click()

    page.goto(url+"builder.html?example=royal-forge-controls.zip&asset=smi.ui.fantasy01.wave2.widget.scroll-horizontal",wait_until="networkidle")
    stage=page.locator("#stage")
    expect(stage).to_have_attribute("data-interactive","true",timeout=20000)
    stage.scroll_into_view_if_needed()
    box=stage.bounding_box()
    assert box and box["width"]>0 and box["height"]>0
    # The builder centers the selected 268 x 44 asset in a 320 x 240 stage.
    start_x=box["x"]+box["width"]*.25
    finish_x=box["x"]+box["width"]*.75
    stage_y=box["y"]+box["height"]*.5
    assert page.evaluate("([x,y])=>document.elementFromPoint(x,y)?.id",[start_x,stage_y])=="stage", "Canvas must be visible before a pointer test"
    page.mouse.move(start_x,stage_y)
    page.mouse.down()
    page.mouse.move(finish_x,stage_y,steps=5)
    page.mouse.up()
    imported_value=int(page.locator('#input-controls input[data-input-key="value"]').input_value())
    assert imported_value>60, f"Builder drag did not update canonical input: {imported_value}; status: {page.locator('#builder-status').inner_text()}"
    page.goto(url+"builder.html",wait_until="networkidle")
    page.locator("#upload").set_input_files(str(SITE/"demo"/"character-animations.zip"))
    page.locator('#asset-list button[data-asset-id="smi.example.robot.states"]').click()
    option=page.locator("#test-drive-profile")
    expect(option).to_have_value("smi.example.robot.platformer",timeout=20000)
    stage=page.locator("#stage")
    stage.scroll_into_view_if_needed()
    page.locator("#test-drive").click()
    stage.focus()
    page.keyboard.down("ArrowRight")
    expect(page.locator("#input-controls select").first).to_have_value("walk")
    page.keyboard.up("ArrowRight")
    expect(page.locator("#input-controls select").first).to_have_value("idle")
    page.locator("#test-drive").click()
    expect(page.locator("#test-drive")).to_have_attribute("aria-pressed","false")
    option.select_option("smi.example.robot.alternative")
    page.locator("#test-drive").click()
    stage.focus()
    page.keyboard.down("w")
    expect(page.locator("#input-controls select").first).to_have_value("walk")
    page.keyboard.up("w")
    expect(page.locator("#input-controls select").first).to_have_value("idle")
    page.locator("#test-drive").click()

    # Robot: one stat action changes both the resource and an existing
    # animated enum through the authored behavior.on event.
    page.locator('#asset-list button[data-asset-id="smi.example.robot.actor"]').click()
    expect(page.locator("#stat-panel")).to_be_visible()
    assert page.locator('#stat-profile').input_value()=="smi.example.robot.stamina-lab"
    page.locator('#stat-actions button[data-stat-action="dash"]').click()
    expect(page.locator('#input-controls input[data-input-key="stamina"]')).to_have_value("40")
    expect(page.locator('#input-controls select[data-input-key="animation"]')).to_have_value("walk")
    page.locator('#stat-actions button[data-stat-action="recover"]').click()
    expect(page.locator('#input-controls input[data-input-key="stamina"]')).to_have_value("65")
    expect(page.locator('#input-controls select[data-input-key="animation"]')).to_have_value("idle")

    # HUD: stat costs must reject atomically and bound visual sliders remain
    # synchronized in both directions. The same Builder opens both pack types.
    page.locator("#upload").set_input_files(str(SITE/"demo"/"interactive-hud.zip"))
    expect(page.locator("#stat-panel")).to_be_visible()
    assert page.locator("#stat-profile").input_value()=="smi.example.hud.energy-lab"
    energy=page.locator('#input-controls input[data-input-key="value"]')
    expect(energy).to_have_value("72")
    for _ in range(3):
        page.locator('#stat-actions button[data-stat-action="dash"]').click()
    expect(energy).to_have_value("12")
    page.locator('#stat-actions button[data-stat-action="dash"]').click()
    expect(energy).to_have_value("12")
    assert "Insufficient energy" in page.locator("#builder-status").inner_text()
    page.locator('#stat-actions button[data-stat-action="restore"]').click()
    expect(energy).to_have_value("27")
    energy.evaluate("(el)=>{el.value='88';el.dispatchEvent(new Event('input',{bubbles:true}))}")
    expect(page.locator('output[data-stat-value="energy"]')).to_have_text("88")
    page.locator('#stat-actions button[data-stat-action="dash"]').click()
    expect(energy).to_have_value("68")

    # Export definitions, never current simulation values. Reimport the ZIP
    # into a clean Builder and confirm the initial stat is restored.
    with page.expect_download() as saved:
        page.locator("#export").click()
    with TemporaryDirectory() as temp:
        exported=Path(temp)/"stat-roundtrip.zip"
        saved.value.save_as(str(exported))
        with ZipFile(exported) as z:
            copied=json.loads(z.read("manifest.json"))
        assert len(copied.get("stat_profiles",[]))==1
        assert copied["stat_profiles"][0]["stats"]["energy"]["initial"]==72
        assert copied["stat_profiles"][0]["bindings"]==[{"stat":"energy","input":"value"}]
        page.goto(url+"builder.html",wait_until="networkidle")
        page.locator("#upload").set_input_files(str(exported))
        expect(page.locator("#stat-panel")).to_be_visible()
        expect(page.locator('#input-controls input[data-input-key="value"]')).to_have_value("72")
    page.goto(url,wait_until="networkidle")
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
                expect(mobile.locator("#count")).to_have_text(published_matches(), timeout=20000)
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
