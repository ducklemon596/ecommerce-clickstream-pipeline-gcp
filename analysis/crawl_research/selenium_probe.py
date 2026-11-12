"""Research probe: open a few Glamira product pages with plain Selenium and record what loads.

This is a bounded research tool, not the production crawler. It deliberately uses an
unmodified Chrome WebDriver session (no User-Agent spoofing, no stealth patches, no
fingerprint changes). If the site serves a block or challenge page, the probe records
that outcome and stops instead of trying to get around it.

Example:
    uv run --group research python analysis/crawl_research/selenium_probe.py \
        --host www.glamira.co.uk --ids 100002 104054 --out data/crawl_research/selenium_probe.jsonl
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait

LOG = logging.getLogger("selenium_probe")

BLOCK_MARKERS = ("Access Denied", "Powered and protected by", "errors.edgesuite.net")

# Runs inside the page after load. Reads only data the page already exposes.
EXTRACT_JS = r"""
const out = {url: location.href, title: document.title, lang: document.documentElement.lang,
             webdriver: navigator.webdriver,
             body_head: (document.body && document.body.innerText || '').slice(0, 200)};
const lds = [...document.querySelectorAll('script[type="application/ld+json"]')]
  .map(s => { try { return JSON.parse(s.textContent); } catch (e) { return null; } }).filter(Boolean);
const item = lds.find(x => x['@type'] === 'ItemPage');
const p = (item && item.mainEntity) || {};
const bc = lds.find(x => x['@type'] === 'BreadcrumbList');
out.jsonld = {name: p.name, sku: p.sku, mpn: p.mpn, brand: p.brand && p.brand.name,
              price: p.offers && p.offers.price, currency: p.offers && p.offers.priceCurrency,
              availability: p.offers && p.offers.availability, offer_url: p.offers && p.offers.url};
out.breadcrumb = bc ? bc.itemListElement.map(i => i.item.name) : null;
const g = (window.dataLayer || []).find(e => e.event === 'productPage');
out.gtm = g ? g.product : null;
const meta = n => { const e = document.querySelector(`meta[property="${n}"]`); return e && e.content; };
out.meta = {price: meta('product:price:amount'), currency: meta('product:price:currency'), og_title: meta('og:title')};
const c = document.querySelector('link[rel=canonical]'); out.canonical = c && c.href;
out.store = window.__react_app && window.__react_app.store;
const r = window.react_data;
out.react_data = r && typeof r === 'object' ? {
  product_id: r.product_id, name: r.name, sku: r.sku, product_type: r.product_type,
  attribute_set: r.attribute_set, collection: r.collection, gender: r.gender,
  price: r.price, min_price: r.min_price, max_price: r.max_price,
  currency: r.product_price && r.product_price.currencyCode,
  option_parts: (r.options || []).map(o => o.part_type || o.type)} : null;
return out;
"""


def build_driver(headless: bool) -> webdriver.Chrome:
    """Create an unmodified Chrome session; Selenium Manager resolves the driver."""
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1366,900")
    return webdriver.Chrome(options=options)


def probe(driver: webdriver.Chrome, url: str, wait_s: float) -> dict:
    """Load one URL, wait for the page's own data layer, and return extracted fields."""
    started = time.monotonic()
    driver.get(url)
    try:
        WebDriverWait(driver, wait_s).until(
            lambda d: d.execute_script(
                "return document.readyState === 'complete' && "
                "(!!window.react_data || !!(window.dataLayer||[]).find(e=>e.event==='productPage'));"
            )
        )
        waited_ok = True
    except TimeoutException:
        waited_ok = False
    data = driver.execute_script(EXTRACT_JS)
    text = f"{data.get('title', '')} {data.get('body_head', '')}"
    blocked = any(marker in text for marker in BLOCK_MARKERS)
    if str(data.get("url", "")).startswith("chrome-error://"):
        # e.g. ERR_HTTP2_PROTOCOL_ERROR: the server dropped the connection. Treated as a
        # possible soft block, so the run stops rather than retrying.
        status = "connection_error"
    elif blocked:
        status = "blocked"
    elif data.get("gtm") or data.get("jsonld", {}).get("name"):
        status = "ok"
    elif "404" in text or "not found" in text.lower():
        status = "not_found"
    else:
        status = "unknown"
    data.update(
        requested_url=url,
        status=status,
        data_ready=waited_ok,
        elapsed_s=round(time.monotonic() - started, 2),
        observed_at=datetime.now(timezone.utc).isoformat(),
    )
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--host", default="www.glamira.co.uk")
    parser.add_argument("--ids", nargs="+", required=True)
    parser.add_argument("--query", default="", help="Optional query string, e.g. '?alloy=white-585'")
    parser.add_argument("--delay", type=float, default=4.0, help="Seconds between page loads")
    parser.add_argument("--jitter", type=float, default=0.0,
                        help="Extra random delay in [0, jitter] seconds added to --delay (pacing only)")
    parser.add_argument("--wait", type=float, default=20.0, help="Max seconds to wait for page data")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--out", type=Path, required=True, help="JSONL output (keep under ignored data/)")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if len(args.ids) > 20:
        parser.error("research probe is limited to 20 IDs per run")
    args.out.parent.mkdir(parents=True, exist_ok=True)

    try:
        driver = build_driver(args.headless)
    except WebDriverException as exc:
        LOG.error("could not start Chrome WebDriver: %s", exc.msg)
        return 2
    try:
        with args.out.open("a", encoding="utf-8") as fh:
            for i, pid in enumerate(args.ids):
                if i:
                    pause = args.delay + random.uniform(0, args.jitter)
                    LOG.info("sleeping %.1fs", pause)
                    time.sleep(pause)
                url = f"https://{args.host}/catalog/product/view/id/{pid}{args.query}"
                try:
                    row = probe(driver, url, args.wait)
                except WebDriverException as exc:
                    row = {"requested_url": url, "status": "failed", "error": exc.msg}
                row["headless"] = args.headless
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                gtm = row.get("gtm") or {}
                LOG.info("%s -> %s | %s | %s", url, row["status"], gtm.get("name"), gtm.get("category"))
                if row["status"] in ("blocked", "connection_error"):
                    LOG.warning("%s; stopping without retrying", row["status"])
                    return 3
    finally:
        driver.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
