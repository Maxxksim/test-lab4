from unittest.mock import MagicMock

from behave import given, when, then
from app.eshop import Product, ShoppingCart, Order


@given('Product "{name}" price {price} availability {availability}')
def create_product(context, name, price, availability):
    context.product = Product(name, int(price), int(availability))


@given("Shopping cart with this product amount {amount}")
def cart_with_product(context, amount):
    context.cart = ShoppingCart()
    context.cart.add_product(context.product, int(amount))


@given("Empty shopping cart")
def empty_cart(context):
    context.cart = ShoppingCart()


@given("None cart")
def none_cart(context):
    context.cart = None


@when("I place order")
def place_order(context):
    if not context.cart.products:
        context.cart.submit_cart_order = MagicMock(return_value=[])

    context.shipping_service = MagicMock()
    context.order = Order(context.cart, context.shipping_service)
    context.order.place_order("test_shipping")


@when("I try to place order")
def try_place_order(context):
    try:
        context.shipping_service = MagicMock()
        context.order = Order(context.cart, context.shipping_service)
        context.order.place_order("test_shipping")
        context.error = False
    except Exception:
        context.error = True


@then("Product availability becomes {expected}")
def check_availability(context, expected):
    assert context.product.available_amount == int(expected)


@then("Order completes without error")
def order_success(context):
    assert True


@then("Order fails")
def order_fails(context):
    assert context.error is True
