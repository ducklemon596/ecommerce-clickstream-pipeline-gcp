"""English-language Glamira storefronts in crawl priority order.

Ordered by currency (USD, EUR, GBP, then AUD, CAD, SGD, NZD, ZAR, AED) and,
within a currency, by store. Verified on 2026-11-12: each host served
``react_data`` for product 100002 with English names and the listed
``store_code``/currency. The ``currency`` query parameter does not change a
host's currency, so each host is requested in its own currency. Prices differ
per store (not a plain FX conversion), so records keep their store provenance.
"""
from __future__ import annotations

from typing import NamedTuple


class Store(NamedTuple):
    """One storefront: its host, native currency and Magento store code."""

    host: str
    currency: str
    store_code: str


STORES: tuple[Store, ...] = (
    Store("www.glamira.com", "USD", "glus"),
    Store("www.glamira.africa", "USD", "glaf"),
    Store("www.glamira.ie", "EUR", "glie"),
    Store("www.glamira.com.mt", "EUR", "glmt"),
    Store("www.glamira.co.uk", "GBP", "glgb"),
    Store("www.glamira.com.au", "AUD", "glau"),
    Store("www.glamira.ca", "CAD", "glca"),
    Store("www.glamira.sg", "SGD", "glsg"),
    Store("www.glamira.co.nz", "NZD", "glnz"),
    Store("www.glamira.co.za", "ZAR", "glza"),
    Store("www.glamira.ae", "AED", "glae"),
)
