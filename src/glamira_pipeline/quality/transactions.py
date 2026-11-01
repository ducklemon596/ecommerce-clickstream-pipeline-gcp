"""Inspect checkout price signs and currency values without locale assumptions."""
from collections import Counter
from dataclasses import dataclass, field
from decimal import Decimal
import math
import re
from typing import Any

from bson import Decimal128

LEADING_NEGATIVE = re.compile(r"^\s*[-−]\s*\d")
LEADING_NUMBER = re.compile(r"^\s*[+\-−]?\s*\d")


@dataclass
class CurrencyCounts:
    """Aggregate safe currency-like values and missing/invalid classifications."""

    values: Counter[str] = field(default_factory=Counter)
    missing: int = 0
    null: int = 0
    empty: int = 0
    invalid: int = 0

    def observe(self, document: dict[str, Any]) -> None:
        """Classify the `currency` key in one event or cart item; return no value."""
        if "currency" not in document:
            self.missing += 1
        elif document["currency"] is None:
            self.null += 1
        elif not isinstance(document["currency"], str):
            self.invalid += 1
        else:
            value = document["currency"].strip()
            if not value:
                self.empty += 1
            elif len(value) > 16 or any(c.isdigit() or ord(c) < 32 for c in value) or "@" in value:
                self.invalid += 1
            else:
                self.values[value] += 1


@dataclass
class TransactionCounts:
    """Track all-event currencies and checkout-only item price-sign checks."""

    top_level_currencies: CurrencyCounts = field(default_factory=CurrencyCounts)
    cart_item_currencies: CurrencyCounts = field(default_factory=CurrencyCounts)
    cart_item_count: int = 0
    malformed_cart_items: int = 0
    checkout_events: int = 0
    checkout_missing_or_invalid_cart: int = 0
    checkout_items: int = 0
    checkout_malformed_items: int = 0
    root_order_amount_present: int = 0
    root_order_amount_nonnull: int = 0
    price_missing: int = 0
    price_null: int = 0
    price_empty: int = 0
    price_string: int = 0
    price_string_negative_sign: int = 0
    price_string_no_leading_number: int = 0
    price_numeric: int = 0
    price_numeric_negative: int = 0
    price_invalid: int = 0

    def observe(self, document: dict[str, Any]) -> None:
        """Count currencies and checkout cart-item price signs in one event."""
        self.top_level_currencies.observe(document)
        is_checkout = document.get("collection") == "checkout_success"
        if is_checkout:
            self.checkout_events += 1
            self.root_order_amount_present += "order_amount" in document
            self.root_order_amount_nonnull += document.get("order_amount") is not None
        cart = document.get("cart_products")
        if not isinstance(cart, list):
            if is_checkout:
                self.checkout_missing_or_invalid_cart += 1
            return
        for item in cart:
            if not isinstance(item, dict):
                self.malformed_cart_items += 1
                if is_checkout:
                    self.checkout_malformed_items += 1
                continue
            self.cart_item_count += 1
            self.cart_item_currencies.observe(item)
            if is_checkout:
                self.checkout_items += 1
                self._observe_price(item)

    def _observe_price(self, item: dict[str, Any]) -> None:
        """Classify one checkout item price without parsing locale-formatted strings."""
        if "price" not in item:
            self.price_missing += 1
            return
        price = item["price"]
        if price is None:
            self.price_null += 1
        elif isinstance(price, str):
            if not price.strip():
                self.price_empty += 1
                return
            self.price_string += 1
            self.price_string_negative_sign += bool(LEADING_NEGATIVE.match(price))
            self.price_string_no_leading_number += not bool(LEADING_NUMBER.match(price))
        elif isinstance(price, bool):
            self.price_invalid += 1
        elif isinstance(price, (int, float, Decimal, Decimal128)):
            number = price.to_decimal() if isinstance(price, Decimal128) else price
            try:
                if isinstance(number, float) and not math.isfinite(number):
                    raise ValueError("Non-finite price")
                if isinstance(number, Decimal) and not number.is_finite():
                    raise ValueError("Non-finite price")
                negative = number < 0
            except (ArithmeticError, ValueError):
                self.price_invalid += 1
                return
            self.price_numeric += 1
            self.price_numeric_negative += negative
        else:
            self.price_invalid += 1
