from behave import given, when, then
from eshop import Product, ShoppingCart, Order


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
    context.order = Order(context.cart)
    context.order.place_order()


@when("I try to place order")
def try_place_order(context):
    try:
        context.order = Order(context.cart)
        context.order.place_order()
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
