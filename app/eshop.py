"""E-shop domain models: products, cart, orders and shipments."""

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from services import ShippingService


class Product:
    """Represents a product available for purchase."""

    def __init__(self, name, price, available_amount):
        self.name = name
        self.price = price
        self.available_amount = available_amount

    def is_available(self, requested_amount):
        """Check if requested amount is available."""
        return self.available_amount >= requested_amount

    def buy(self, requested_amount):
        """Decrease available amount after purchase."""
        self.available_amount -= requested_amount

    def __eq__(self, other):
        return self.name == other.name

    def __ne__(self, other):
        return self.name != other.name

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return self.name


class ShoppingCart:
    """Represents a shopping cart with selected products."""

    def __init__(self):
        self.products = {}

    def contains_product(self, product):
        """Check if product is in cart."""
        return product in self.products

    def calculate_total(self):
        """Calculate total price of all products in cart."""
        return sum(p.price * count for p, count in self.products.items())

    def add_product(self, product: Product, amount: int):
        """Add product to cart."""
        if not product.is_available(amount):
            raise ValueError(
                f"Product {product} has only {product.available_amount} items"
            )
        self.products[product] = amount

    def remove_product(self, product):
        """Remove product from cart."""
        if product in self.products:
            del self.products[product]

    def submit_cart_order(self):
        """Submit cart and return purchased product IDs."""

        if not self.products:
            raise Exception("Cannot place order: cart is empty")

        product_ids = []

        for product, count in self.products.items():
            if not product.is_available(count):
                raise Exception(f"Product {product} is out of stock")
            product.buy(count)
            product_ids.append(str(product))

        self.products.clear()
        return product_ids


@dataclass
class Order:
    """Represents an order created from a shopping cart."""

    cart: ShoppingCart
    shipping_service: ShippingService
    order_id: str = str(uuid.uuid4())

    def place_order(self, shipping_type, due_date: datetime = None):
        """Place order and request shipping."""
        if not due_date:
            due_date = datetime.now(timezone.utc) + timedelta(seconds=3)

        product_ids = self.cart.submit_cart_order()

        return self.shipping_service.create_shipping(
            shipping_type,
            product_ids,
            self.order_id,
            due_date,
        )


@dataclass
class Shipment:
    """Represents shipment created by shipping service."""

    shipping_id: str
    shipping_service: ShippingService

    def check_shipping_status(self):
        """Check shipment status."""
        return self.shipping_service.check_status(self.shipping_id)
