from behave import given, when, then
from app.eshop import Product


@given('Product named "{name}" with price {price} and availability {availability}')
def create_product(context, name, price, availability):
    context.product = Product(name, int(price), int(availability))


@when("I check product availability for amount {amount}")
def check_availability(context, amount):
    context.result = context.product.is_available(int(amount))


@when("I check product availability for None")
def check_availability_none(context):
    try:
        context.product.is_available(None)
        context.error = False
    except Exception:
        context.error = True


@then("Availability result should be True")
def availability_true(context):
    assert context.result is True


@then("Availability result should be False")
def availability_false(context):
    assert context.result is False


@then("Availability check should fail")
def availability_fail(context):
    assert context.error is True


@when("I buy product amount {amount}")
def buy_product(context, amount):
    context.product.buy(int(amount))


@then("Product availability should be {expected}")
def check_product_amount(context, expected):
    assert context.product.available_amount == int(expected)
