#!/usr/bin/env python3
"""Smoke-test the actual public browsing page, facets and asset inspector."""
from __future__ import annotations

import argparse
import contextlib
import json
import re
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
    return f"{json.loads((SITE/'public-catalog.json').read_text())['discoverable_count']:,} matches"


def world_matches():
    assets=json.loads((SITE/'public-catalog.json').read_text())['assets']
    return f"{sum(not a.get('legacy') and a.get('discovery','standalone')=='standalone' and 'world' in a.get('category_path',[]) for a in assets):,} matches"


def check(page,published_only=False):
    errors = []
    page.on("pageerror", lambda err: errors.append(str(err)))
    page.reload(wait_until="networkidle")
    expect(page.locator("#count")).to_have_text(published_matches(), timeout=20000)
    expect(page.locator("#app-sidebar")).to_be_visible()
    expect(page.locator(".app-topbar #search")).to_be_visible()
    page.keyboard.press("Control+k")
    expect(page.locator("#search")).to_be_focused()
    assert page.locator("#hero-art img").count() >= 1
    assert page.locator("#sidebar-categories a").count() >= 4
    assert page.locator("#theme-directory a").count() >= 1
    family = page.locator('#collection-family-directory a').filter(has_text='Painterly Fantasy World')
    expect(family).to_have_count(1)
    previews = family.locator('.collection-covers img').evaluate_all("images => images.map(img => img.getAttribute('src'))")
    assert 1 <= len(previews) <= 3 and len(set(previews)) == len(previews), previews
    assert all(src.startswith('previews/') for src in previews), previews
    expect(page.locator('#hero-totals')).to_have_text(page.locator('#library-totals').inner_text())
    family.click()
    expect(page.locator('#family')).to_have_value('painterly-fantasy')
    catalog = json.loads((SITE/'public-catalog.json').read_text())
    family_count = sum(a.get('family') == 'painterly-fantasy' and not a.get('legacy') and a.get('discovery', 'standalone') == 'standalone' for a in catalog['assets'])
    assert family_count >= 53
    expect(page.locator('#count')).to_have_text(f'{family_count:,} matches')
    page.locator('#clear-filters').click()
    expect(page.locator('#shown-count')).to_have_text('24 of '+published_matches().split()[0]+' shown')

    # Discovery is navigable without typing a query; counts come from the same catalog.
    page.locator('#category-directory a').filter(has_text='World & Environment').click()
    expect(page.locator('#count')).to_have_text(world_matches())
    page.locator('#sort').select_option('name')
    page.locator('#category-children a').filter(has_text='Props').click()
    expect(page.locator('#sort')).to_have_value('name')
    expect(page.locator('#count')).to_have_text('4 matches')
    page.locator('#category-children a').filter(has_text='Containers').click()
    page.locator('#category-children a').filter(has_text='Chests').click()
    expect(page.locator('#count')).to_have_text('4 matches')
    page.locator('#perspective').select_option('isometric')
    expect(page.locator('#count')).to_have_text('4 matches')
    # Verify gallery-only browsing on a fresh page, including actual network requests.
    preview_context=page.context.browser.new_context(viewport=page.viewport_size)
    preview_page=preview_context.new_page()
    requests=[]
    preview_page.on('request',lambda req:requests.append(req.url))
    try:
        preview_page.goto(page.url,wait_until='networkidle')
        card=preview_page.locator('#gallery .asset-tile').first
        card.scroll_into_view_if_needed()
        expect(card.locator('canvas')).to_have_attribute('data-preview','thumbnail')
        assert any('/previews/' in url for url in requests),requests
        chest_pack=next(p for p in catalog['packs'] if p['zip']=='demo/fantasy-recovered-chests-20261125.zip')
        chest_zip='/'+chest_pack.get('immutable_zip',chest_pack['zip'])
        assert not any(url.endswith(chest_zip) for url in requests),requests
        card.click()
        expect(preview_page.locator('#detail[open]')).to_be_visible()
        expect(preview_page.locator('#detail-classification')).to_contain_text('Isometric')
        expect(preview_page.locator('#detail-classification')).to_contain_text('Chests')
        expect(preview_page.locator('#download-png')).to_be_enabled(timeout=20000)
        assert any(url.endswith(chest_zip) for url in requests),requests
    finally:
        preview_context.close()
    assert 'perspective=isometric' in page.url
    page.reload(wait_until='networkidle')
    expect(page.locator('#count')).to_have_text('4 matches')
    expect(page.locator('#category_path')).to_have_value('world.props.containers.chests')
    page.locator('.browse-nav [data-view="collections"]').click()
    expect(page.locator('#collection-directory')).to_be_visible()
    grass = page.locator('#family-directory .collection-card').filter(has_text='Fantasy Recovered Grass')
    assert 1 <= grass.locator('.collection-covers img').count() <= 3
    expect(grass.get_by_role('link',name='Open in Builder')).to_have_attribute('href',re.compile(r'^builder[.]html[?]example=.*&asset='))
    grass.locator('a.directory-link').first.click()
    expect(page.locator('#count')).to_have_text('12 matches')
    page.locator('#clear-filters').click()
    expect(page.locator('#discovery')).to_be_visible()
    assert 'category_path=' not in page.url
    page.locator('#archive-directory a').click()
    expect(page.locator('#count')).to_have_text('2,073 matches')
    page.locator('#clear-filters').click()
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

    page.locator("#scope").select_option("components")
    expect(page.locator("#count")).to_have_text("639 matches")
    page.locator("#clear-filters").click()
    expect(page.locator("#count")).to_have_text(published_matches())
    page.locator("#search").fill("healthbar")
    page.locator("#gallery .asset-tile").first.wait_for(timeout=10000)
    assert "Health Meter" in page.locator("#gallery").inner_text(), "Synonym search failed"
    page.locator("#gallery .asset-tile").first.click()
    page.locator("#detail[open]").wait_for(timeout=20000)
    assert page.locator("#detail-tags span").count() >= 1, "No manifest keywords in inspector"
    expect(page.locator('#download-png')).to_be_enabled(timeout=20000)
    page.locator('#step').click()
    expect(page.locator('#play')).to_have_text('Play')
    page.locator("#close").click()
    page.locator('#gallery .asset-tile').first.click()
    expect(page.locator('#play')).to_have_text('Pause')
    expect(page.locator('#download-png')).to_be_enabled(timeout=20000)
    page.locator('#close').click()

    # A playable demo remains the canonical published Sky asset, but gets
    # a separate direct-play link in its normal search card and detail view.
    page.locator("#clear-filters").click()
    page.locator("#experience").select_option("playable")
    expect(page.locator("#count")).to_have_text("1 matches")
    sky=page.locator("#gallery .showcase-card")
    expect(sky).to_have_count(1)
    expect(sky.locator("a.showcase-link")).to_have_attribute("href","sky-prototype.html")
    sky.locator("button.asset-tile").click()
    expect(page.locator("#detail[open]")).to_be_visible()
    expect(page.locator("#detail-showcases a.showcase-link")).to_have_attribute("href","sky-prototype.html")
    page.locator("#close").click()
    page.locator("#clear-filters").click()
    page.locator("#search").fill("playable interactive demo")
    expect(page.locator("#gallery .showcase-card")).to_have_count(1)
    page.locator("#clear-filters").click()

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
    # Overlapping bundles can coexist in one browser session. Navigate via
    # the dependency inspector, rather than resetting the loaded ZIP cache.
    page.locator("#clear-filters").click()
    page.locator("#search").fill("smi.hud.royalforge.complete")
    page.locator("#gallery .asset-tile").first.click()
    expect(page.locator("#detail-title")).to_have_text("Royal Forge Complete Gameplay HUD")
    page.locator("#detail[open]").wait_for(timeout=20000)
    expect(page.locator("#controls [data-input-key]")).to_have_count(28)
    page.locator("#detail-components summary").click()
    page.locator('#detail-related button[title="smi.hud.royalforge02.hud.adventurer"]').click()
    expect(page.locator("#controls [data-input-key]")).to_have_count(7)
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
    expect(page.locator(".atlas-tool-nav a[aria-current=page]")).to_have_text("Builder / My Bag")
    expect(page.locator("body")).to_have_class(re.compile(r"atlas-theme"))
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
    if not published_only:
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
        expect(page.locator('#stat-derived-values')).to_contain_text('"mobility":11.25')
        page.locator('#stat-actions button[data-stat-action="haste"]').click()
        expect(page.locator('#stat-derived-values')).to_contain_text('"mobility":14.75')
        expect(page.locator('#stat-effective-values')).to_contain_text('"speed":6')
        expect(page.locator('#input-controls input[data-input-key="mobility"]')).to_have_value("14.75")
        assert page.locator('#input-controls input[data-input-key="mobility"]').is_disabled()
        page.locator('#stat-advance').click()
        expect(page.locator('#stat-effects-status')).to_contain_text("2000 ms")
        page.locator('#stat-step-ms').fill("2000")
        page.locator('#stat-advance').click()
        expect(page.locator('#stat-effects-status')).to_have_text("No active effects")
        expect(page.locator('#stat-derived-values')).to_contain_text('"mobility":10.75')
        expect(page.locator('#input-controls select[data-input-key="animation"]')).to_have_value("idle")

        # HUD: stat costs must reject atomically and bound visual sliders remain
        # synchronized in both directions. The same Builder opens both pack types.
        page.locator("#upload").set_input_files(str(SITE/"demo"/"interactive-hud.zip"))
        expect(page.locator("#stat-panel")).to_be_visible()
        expect(page.locator("#stat-profile")).to_have_value("smi.example.hud.energy-lab",timeout=20000)
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
        page.locator('#stat-actions button[data-stat-action="focus"]').click()
        expect(energy).to_have_value("68") # 10 spent and +10 temporary modifier
        expect(page.locator('output[data-stat-value="energy"]')).to_have_text("58")
        expect(page.locator('#stat-effects-status')).to_contain_text("3000 ms")
        page.locator('#stat-step-ms').fill("3000")
        page.locator('#stat-advance').click()
        expect(energy).to_have_value("58")
        expect(page.locator('#stat-derived-values')).to_contain_text('"readiness":49')

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
            exported_ids={a["id"] for a in copied["assets"]}
            assert {"smi.example.hud.meter","smi.example.hud.frame",
                    "smi.example.hud.fill","smi.example.hud.thumb"} <= exported_ids, exported_ids
            assert len(copied["textures"])==1, "Export must contain the referenced source texture"
            assert copied["stat_profiles"][0]["stats"]["energy"]["initial"]==72
            assert copied["stat_profiles"][0]["bindings"]==[{"stat":"energy","input":"value"}]
            assert copied["stat_profiles"][0]["effects"]["focus"]["duration_ms"]==3000
            assert "readiness" in copied["stat_profiles"][0]["derived"]
            page.goto(url+"builder.html",wait_until="networkidle")
            page.locator("#upload").set_input_files(str(exported))
            expect(page.locator("#stat-panel")).to_be_visible()
            expect(page.locator('#input-controls input[data-input-key="value"]')).to_have_value("72")
    # Public Builder quick-open must never point to unpublished test fixtures.
    page.goto(url+"builder.html",wait_until="networkidle")
    picker=page.locator("#public-example")
    expect(picker.locator('option[value="royal-forge-complete.zip"]')).to_have_count(1)
    assert picker.locator('option[value="starter-pack.zip"]').count()==0
    button=page.locator("#open-collection")
    expect(button).to_be_visible()
    expect(button).to_be_disabled()
    picker.select_option("royal-forge-complete.zip")
    expect(button).to_be_enabled()
    button.click()
    expect(page.locator("#preview-name")).to_have_text("Royal Forge Complete Gameplay HUD",timeout=20000)
    # Overlapping ZIPs share identical IDs, and removing one bag must not
    # remove assets still owned by the other.
    page.goto(url+"builder.html",wait_until="networkidle")
    page.locator("#upload").set_input_files(str(SITE/"demo"/"royal-forge-controls.zip"))
    expect(page.locator("#bag-count")).to_have_text("1 ZIP")
    page.locator("#upload").set_input_files(str(SITE/"demo"/"royal-forge-complete.zip"))
    expect(page.locator("#bag-count")).to_have_text("2 ZIPs")
    expect(page.locator("#preview-name")).to_have_text("Royal Forge Complete Gameplay HUD")
    page.locator("#bag-list .bag-card").filter(has_text="Royal Forge Core Controls").get_by_role("button",name="Remove").click()
    expect(page.locator("#bag-count")).to_have_text("1 ZIP")
    expect(page.locator("#preview-name")).to_have_text("Royal Forge Complete Gameplay HUD")
    page.locator("#asset-search").fill("smi.ui.fantasy01.wave2.widget.action-inventory-hud")
    page.locator('#asset-list [data-asset-id="smi.ui.fantasy01.wave2.widget.action-inventory-hud"]').click()
    expect(page.locator("#preview-name")).to_have_text("Royal Forge Action and Inventory HUD")
    # Reverse ownership order: the complete pack's regions must survive its
    # removal when a standalone source bag is still present.
    if not published_only:
        page.goto(url+"builder.html",wait_until="networkidle")
        for filename,count in (("royal-forge-complete.zip",1),("royal-forge-controls.zip",2)):
            page.locator("#upload").set_input_files(str(SITE/"demo"/filename))
            expect(page.locator("#bag-count")).to_have_text(f"{count} ZIP"+("s" if count!=1 else ""),timeout=20000)
        # A failed conflicting import must not replace assets or add a bag.
        with TemporaryDirectory() as temp:
            conflict=Path(temp)/"conflict.zip"
            with ZipFile(SITE/"demo"/"royal-forge-controls.zip") as original, ZipFile(conflict,"w") as mutated:
                for entry in original.infolist():
                    data=original.read(entry.filename)
                    if entry.filename=="manifest.json":
                        doc=json.loads(data)
                        doc["assets"][0]["name"]+=" conflicting copy"
                        data=json.dumps(doc).encode()
                    mutated.writestr(entry,data)
            page.locator("#upload").set_input_files(str(conflict))
            expect(page.locator("#builder-status")).to_contain_text("Conflicting asset ID",timeout=20000)
            expect(page.locator("#bag-count")).to_have_text("2 ZIPs")
        page.locator("#bag-list .bag-card").filter(has_text="Royal Forge Complete Gameplay HUD").get_by_role("button",name="Remove").click()
        expect(page.locator("#bag-count")).to_have_text("1 ZIP")
        expect(page.locator("#preview-name")).to_have_text("Royal Forge Action and Inventory HUD")
        # Export the retained asset and re-open its portable dependency closure.
        with page.expect_download() as saved:
            page.locator("#export").click()
        with TemporaryDirectory() as temp:
            exported=Path(temp)/"retained-hud.zip"
            saved.value.save_as(str(exported))
            with ZipFile(exported) as archive:
                index=json.loads(archive.read("collection.json"))
                assert index["entry_asset"]=="smi.ui.fantasy01.wave2.widget.action-inventory-hud"
                assert len(json.loads(archive.read("manifest.json"))["assets"])<219
            page.goto(url+"builder.html",wait_until="networkidle")
            page.locator("#upload").set_input_files(str(exported))
            expect(page.locator("#preview-name")).to_have_text("Royal Forge Action and Inventory HUD",timeout=20000)
    # Experimental Sky scene: one canonical authored ZIP drives both the
    # interactive preview and catalog Builder import; no duplicated art data.
    page.goto(url+"sky-prototype.html",wait_until="domcontentloaded")
    expect(page.locator("#events")).to_contain_text("prototype loaded",timeout=45000)
    page.keyboard.press("Space")
    expect(page.locator("#state")).to_contain_text("jump",timeout=5000)
    page.keyboard.press("KeyP")
    expect(page.locator("#pause-screen")).to_be_visible()
    page.locator("#resume").click()
    expect(page.locator("#pause-screen")).to_be_hidden()
    page.keyboard.press("KeyI")
    expect(page.locator("#inventory-screen")).to_be_visible()
    page.locator("#close-inventory").click()
    expect(page.locator("#inventory-screen")).to_be_hidden()
    # A real material uses the existing detail renderer, a separate repeat canvas,
    # metadata-based recommendations and the shared selected-asset ZIP export.
    catalog=json.loads((SITE/'public-catalog.json').read_text())
    materials=[a for a in catalog['assets'] if a['id'].startswith('smi.material.gflow.')]
    assert len(materials)==302
    material=next(a for a in materials if a['name']=='Fantasy meadow grass')
    page.goto(url+'?asset='+material['id'],wait_until='domcontentloaded')
    expect(page.locator('#detail[open]')).to_be_visible(timeout=30000)
    expect(page.locator('#download-png')).to_be_enabled(timeout=30000)
    repeat=page.locator('canvas[data-material-repeat]')
    expect(repeat).to_be_visible()
    assert repeat.evaluate('(e)=>{const p=e.getContext("2d").getImageData(0,0,512,512).data;return p[3]===255&&p[3+4*256]===255&&p[0]===p[4*256]&&p[1]===p[4*256+1]&&p[2]===p[4*256+2]}')
    expect(page.locator('#detail-related')).to_contain_text('Suggested matches')
    with page.expect_download() as saved:
        page.locator('#download-asset').click()
    with TemporaryDirectory() as temp:
        exported=Path(temp)/'material.zip';saved.value.save_as(str(exported))
        with ZipFile(exported) as archive:
            pack=json.loads(archive.read('manifest.json'));assert len(pack['assets'])==1
            assert pack['assets'][0]['id']==material['id'];assert pack['assets'][0]['material']==material['material'];assert pack['assets'][0]['visual_profile']==material['visual_profile']

    page.goto(url,wait_until="networkidle")
    assert not errors, "Browser JavaScript errors: " + repr(errors)
    return page.locator("#count").inner_text()


def check_capability_discovery(browser, url):
    """Actual app and archive previews; only the catalog facts are synthetic.

    Keep the production catalog and authored archives untouched. Intercept a
    single page's catalog response to test newly introduced offers, missing
    representation evidence and navigation against real published ZIPs.
    """
    catalog = json.loads((SITE / "public-catalog.json").read_text())
    materials = [a for a in catalog["assets"] if a["id"].startswith("smi.material.gflow.")]
    target = next(a for a in materials if a["name"] == "Fantasy meadow grass")
    unknown = next(a for a in materials if a["pack"] == target["pack"] and a["id"] != target["id"])
    offer = next(a for a in materials if a["pack"] != target["pack"])
    # Isolate the fixture from any future real offers; do not modify the source file.
    for concept in catalog.get("concepts", []):
        concept.pop("discovery_offers", None)
    target_concept = "test.browser.capability.surface"
    offer_concept = "test.browser.capability.overlay"
    assert not {target_concept, offer_concept} & {c["id"] for c in catalog.get("concepts", [])}
    target["concept_id"] = unknown["concept_id"] = target_concept
    offer["concept_id"] = offer_concept
    # These are test-only declarations, not claims about the source artwork.
    target["interfaces"] = ["test.browser.surface/1"]
    unknown["interfaces"] = []
    catalog.setdefault("concepts", []).extend([
        {"id": target_concept, "name": "Fixture surface", "pack": target["pack"],
         "capabilities": ["test.browser.surface"]},
        {"id": offer_concept, "name": "Fixture overlay", "pack": offer["pack"],
         "discovery_offers": {"apply": {"role": "overlay", "requirements": [
             {"scope": "concept", "op": "capability.has", "key": "test.browser.surface"},
             {"scope": "representation", "op": "interface.has", "key": "test.browser.surface/1"}
         ]}}}
    ])
    owner = next(p for p in catalog["packs"] if p["id"] == offer["pack"])
    offer_archive = "/" + owner["immutable_zip"]
    context = browser.new_context(viewport={"width": 1440, "height": 1000})
    page = context.new_page()
    errors, requests = [], []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("request", lambda request: requests.append(request.url))
    page.route("**/public-catalog.json", lambda route: route.fulfill(json=catalog))
    try:
        page.goto(url + "?asset=" + target["id"], wait_until="domcontentloaded")
        expect(page.locator("#download-png")).to_be_enabled(timeout=30000)
        page.locator("#detail-components > summary").click()
        panel = page.locator("[data-discovery-section]")
        matched = panel.locator('[data-discovery-group="compatible"]')
        expect(matched).to_be_visible(timeout=20000)
        expect(matched.locator("summary").first).to_have_text("Declared requirements matched (1)")
        expect(matched.get_by_role("button", name=re.compile("Fixture overlay", re.I))).to_be_visible()
        matched.get_by_text("Requirements and evidence", exact=True).click()
        expect(matched).to_contain_text("representation · interface.has · test.browser.surface/1: compatible")
        assert not any(u.endswith(offer_archive) for u in requests), requests
        matched.get_by_role("button", name=re.compile("Fixture overlay", re.I)).click()
        expect(page.locator("#detail-id")).to_have_text(offer["id"], timeout=20000)
        expect(page.locator("#download-png")).to_be_enabled(timeout=30000)
        assert any(u.endswith(offer_archive) for u in requests), requests
        page.locator("#detail-components > summary").click()
        reverse = page.locator('[data-discovery-offer="apply"]')
        expect(reverse).to_be_visible()
        expect(reverse.locator("[data-discovery-group]")).to_have_count(0)
        reverse.locator("summary").first.click()
        reverse_match = reverse.locator('[data-discovery-group="compatible"]')
        expect(reverse_match.get_by_role("button", name=target["name"], exact=True)).to_be_visible(timeout=20000)
        expect(reverse.locator('[data-discovery-group="unknown"]')).to_have_count(1)
        reverse_match.get_by_role("button", name=target["name"], exact=True).click()
        expect(page.locator("#detail-id")).to_have_text(target["id"], timeout=20000)
        page.goto(url + "?asset=" + unknown["id"], wait_until="domcontentloaded")
        expect(page.locator("#download-png")).to_be_enabled(timeout=30000)
        page.locator("#detail-components > summary").click()
        expect(page.locator('[data-discovery-group="compatible"]')).to_have_count(0)
        expect(page.locator('[data-discovery-group="unknown"] > summary')).to_have_text("Incomplete evidence (1)")
        assert not errors, errors
    finally:
        context.close()
    print("Capability discovery Inspector with test-only catalog offers: PASS")


def check_authored_discovery(browser, url):
    """Actual authored HUD offers and Builder archive identity isolation."""
    asset_id = "smi.hud.royalforge02.bar.fill.mana"
    context = browser.new_context(viewport={"width": 1440, "height": 1000})
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    try:
        page.goto(url + "?asset=" + asset_id, wait_until="domcontentloaded")
        expect(page.locator("#download-png")).to_be_enabled(timeout=30000)
        page.locator("#detail-components > summary").click()
        matched = page.locator('[data-discovery-section] [data-discovery-group="compatible"]')
        expect(matched).to_be_visible(timeout=20000)
        expect(matched.get_by_role("button", name=re.compile("Royal Forge Configurable Resource Meter", re.I))).to_be_visible()
        page.goto(url + "builder.html?example=royal-forge-hud-resources.zip&asset=" + asset_id,
                  wait_until="domcontentloaded")
        expect(page.locator("#preview-name")).to_have_text("Bar Fill Mana", timeout=30000)
        panel = page.locator("#builder-discovery")
        expect(panel).to_be_visible(timeout=30000)
        panel.locator("summary").first.click()
        expect(panel).to_contain_text("Current public catalog")
        expect(panel).to_contain_text("Declared requirements matched")
        # A repacked private ZIP with unchanged IDs must not inherit the public
        # identity. Its bytes differ even though all art and definitions agree.
        with TemporaryDirectory() as temp:
            private = Path(temp) / "private-resource.zip"
            with ZipFile(SITE / "demo" / "royal-forge-hud-resources.zip") as original, ZipFile(private, "w") as archive:
                for entry in original.infolist():
                    archive.writestr(entry, original.read(entry.filename))
                archive.comment = b"private test archive"
            page.goto(url + "builder.html", wait_until="domcontentloaded")
            page.locator("#upload").set_input_files(str(private))
            expect(page.locator("#bag-count")).to_have_text("1 ZIP", timeout=30000)
            page.locator("#asset-search").fill(asset_id)
            page.locator('#asset-list [data-asset-id="' + asset_id + '"]').click()
            expect(page.locator("#preview-name")).to_have_text("Bar Fill Mana")
            panel = page.locator("#builder-discovery")
            expect(panel).to_be_visible()
            panel.locator("summary").first.click()
            expect(panel).to_contain_text("This exact imported ZIP only")
            expect(panel).to_contain_text("Declared requirements matched")
            expect(panel).not_to_contain_text("Current public catalog")
        assert not errors, errors
    finally:
        context.close()
    print("Authored HUD discovery and private Builder provenance: PASS")


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--published-only',action='store_true');args=parser.parse_args()
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
                print("Desktop:", check(page,args.published_only))
                check_capability_discovery(browser, url)
                check_authored_discovery(browser, url)
                mobile = browser.new_page(viewport={"width": 390, "height": 844}, base_url=url)
                mobile.goto(url, wait_until="networkidle")
                expect(mobile.locator("#count")).to_have_text(published_matches(), timeout=20000)
                assert mobile.evaluate("document.documentElement.scrollWidth <= innerWidth + 2"), "Horizontal overflow on mobile"
                assert mobile.locator("#app-sidebar").evaluate("(e)=>e.inert")
                expect(mobile.locator("#facet-panel")).to_be_hidden()
                mobile.locator("#nav-toggle").click()
                expect(mobile.locator("#nav-toggle")).to_have_attribute("aria-expanded","true")
                assert not mobile.locator("#app-sidebar").evaluate("(e)=>e.inert")
                expect(mobile.locator(".app-brand")).to_be_focused()
                mobile.keyboard.press("Escape")
                expect(mobile.locator("#nav-toggle")).to_be_focused()
                assert mobile.locator("#app-sidebar").evaluate("(e)=>e.inert")
                mobile.locator("#nav-toggle").click()
                mobile.locator("#sidebar-categories a[data-category=world]").click()
                expect(mobile.locator("#count")).to_have_text(world_matches())
                expect(mobile.locator("#nav-toggle")).to_have_attribute("aria-expanded","false")
                assert mobile.evaluate("document.documentElement.scrollWidth <= innerWidth + 2"), "Asset view overflows on mobile"
                mobile.locator("#filter-toggle").click()
                expect(mobile.locator("#facet-panel")).to_be_visible()
                mobile.locator("#perspective").select_option("isometric")
                expect(mobile.locator("#perspective")).to_have_value("isometric")
                mobile.locator("#filter-toggle").click()
                expect(mobile.locator("#facet-panel")).to_be_hidden()
                assert "perspective=isometric" in mobile.url
                mobile.set_viewport_size({"width": 1440, "height": 1000})
                expect(mobile.locator("#facet-panel")).to_be_visible()
                assert not mobile.locator("#app-sidebar").evaluate("(e)=>e.inert")
                mobile.set_viewport_size({"width": 390, "height": 844})
                expect(mobile.locator("#facet-panel")).to_be_hidden()
                print("Responsive viewport and keyboard navigation: PASS")
                mobile.goto(url+"builder.html",wait_until="networkidle")
                expect(mobile.locator(".atlas-tool-nav a[aria-current=page]")).to_have_text("Builder / My Bag")
                assert mobile.evaluate("document.documentElement.scrollWidth <= innerWidth + 2"), "Builder overflows on mobile"
                mobile.locator(".atlas-tool-nav a[href='ai-guide.html']").click()
                expect(mobile.locator(".atlas-tool-nav a[aria-current=page]")).to_have_text("Create with AI")
                expect(mobile.locator("#prompt")).to_be_visible()
                assert mobile.evaluate("document.documentElement.scrollWidth <= innerWidth + 2"), "Guide overflows on mobile"
                mobile.locator(".atlas-tool-nav a[href='sky-motion-lab.html']").click()
                expect(mobile.locator(".atlas-tool-nav a[aria-current=page]")).to_have_text("Motion Lab")
                expect(mobile.locator("#motion-stage")).to_be_visible()
                mobile.locator(".atlas-tool-nav a[href='index.html']").click()
                expect(mobile.locator("#count")).to_have_text(published_matches(), timeout=20000)
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
    print("Public browser end-to-end smoke: PASS")


if __name__ == "__main__":
    main()
