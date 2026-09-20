"""Page fixtures for the Kroger grocery-order flow tests.

Each fixture is a page snapshot in the shape the BrowserDriver protocol
produces: url + elements. Elements are dicts with selector/text/visible.
"""

LOGIN = {
    "url": "https://www.kroger.com/signin",
    "elements": [
        {"selector": "#email", "text": "", "visible": True},
        {"selector": "#password", "text": "", "visible": True},
        {"selector": "#signin-btn", "text": "Sign In", "visible": True},
        {"selector": None, "text": "Email Address", "visible": True},
        {"selector": None, "text": "Password", "visible": True},
        {"selector": None, "text": "Sign In", "visible": True},
    ],
}

ACCOUNT = {
    "url": "https://www.kroger.com/account",
    "elements": [
        {"selector": ".account-name", "text": "Hi, Mom", "visible": True},
        {"selector": ".cart-link", "text": "Cart", "visible": True},
        {"selector": None, "text": "My Account", "visible": True},
        {"selector": None, "text": "Recent Purchases", "visible": True},
        {"selector": None, "text": "Start Shopping", "visible": True},
    ],
}

SEARCH_RESULTS = {
    "url": "https://www.kroger.com/search?q=milk",
    "elements": [
        {"selector": ".product-grid", "text": "", "visible": True},
        {"selector": ".product-card", "text": "Kroger Whole Milk 1 gal", "visible": True},
        {"selector": ".product-price", "text": "$3.49", "visible": True},
        {"selector": ".add-btn", "text": "Add to Cart", "visible": True},
        {"selector": None, "text": "Search Results", "visible": True},
        {"selector": None, "text": "milk", "visible": True},
    ],
}

PRODUCT = {
    "url": "https://www.kroger.com/p/kroger-whole-milk/0001111041700",
    "elements": [
        {"selector": ".product-title", "text": "Kroger Whole Milk 1 gal", "visible": True},
        {"selector": ".product-price", "text": "$3.49", "visible": True},
        {"selector": "#add-to-cart", "text": "Add to Cart", "visible": True},
        {"selector": None, "text": "1 gal", "visible": True},
        {"selector": None, "text": "Add to List", "visible": True},
    ],
}

CART = {
    "url": "https://www.kroger.com/cart",
    "elements": [
        {"selector": ".cart-item", "text": "Kroger Whole Milk 1 gal", "visible": True},
        {"selector": ".cart-total", "text": "$3.49", "visible": True},
        {"selector": "#checkout-btn", "text": "Checkout", "visible": True},
        {"selector": None, "text": "Shopping Cart", "visible": True},
        {"selector": None, "text": "Estimated Total", "visible": True},
    ],
}

CHECKOUT = {
    "url": "https://www.kroger.com/checkout",
    "elements": [
        {"selector": ".order-summary", "text": "", "visible": True},
        {"selector": ".pickup-time", "text": "Tomorrow 10 AM", "visible": True},
        {"selector": ".payment-method", "text": "Visa •••• 4242", "visible": True},
        {"selector": ".order-total", "text": "$3.49", "visible": True},
        {"selector": "#place-order", "text": "Place Order", "visible": True},
        {"selector": None, "text": "Review Order", "visible": True},
        {"selector": None, "text": "Pickup", "visible": True},
    ],
}

# --- edge cases ---

CHECKOUT_WRONG_HOST = {
    "url": "https://kroger-savings.com/checkout",
    "elements": CHECKOUT["elements"],
}

CART_HIGH_TOTAL = {
    "url": "https://www.kroger.com/cart",
    "elements": [
        {"selector": ".cart-item", "text": "Kroger Whole Milk 1 gal", "visible": True},
        {"selector": ".cart-total", "text": "$247.83", "visible": True},
        {"selector": "#checkout-btn", "text": "Checkout", "visible": True},
        {"selector": None, "text": "Shopping Cart", "visible": True},
        {"selector": None, "text": "Estimated Total", "visible": True},
    ],
}

CHECKOUT_HIGH_TOTAL = {
    "url": "https://www.kroger.com/checkout",
    "elements": [
        {"selector": ".order-summary", "text": "", "visible": True},
        {"selector": ".pickup-time", "text": "Tomorrow 10 AM", "visible": True},
        {"selector": ".payment-method", "text": "Visa •••• 4242", "visible": True},
        {"selector": ".order-total", "text": "$247.83", "visible": True},
        {"selector": "#place-order", "text": "Place Order", "visible": True},
        {"selector": None, "text": "Review Order", "visible": True},
        {"selector": None, "text": "Pickup", "visible": True},
    ],
}

UNRECOGNIZED = {
    "url": "https://www.kroger.com/weekly-ad",
    "elements": [
        {"selector": None, "text": "Weekly Ad", "visible": True},
        {"selector": None, "text": "Coupons", "visible": True},
    ],
}


def load_flow():
    """Load the Kroger grocery-order flow JSON."""
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    with open(root / "flows" / "examples" / "kroger-grocery-order.json", encoding="utf-8") as f:
        return json.load(f)
