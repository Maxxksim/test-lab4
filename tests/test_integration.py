import time
import uuid

import boto3
from app.eshop import Product, ShoppingCart, Order, Shipment
import random
from services import ShippingService
from services.repository import ShippingRepository
from services.publisher import ShippingPublisher
from datetime import datetime, timedelta, timezone
from services.config import AWS_ENDPOINT_URL, AWS_REGION, SHIPPING_QUEUE
import pytest


@pytest.mark.parametrize("order_id, shipping_id", [
    ("order_1", "shipping_1"),
    ("order_i2hur2937r9", "shipping_1!!!!"),
    (8662354, 123456),
    (str(uuid.uuid4()), str(uuid.uuid4()))
])
def test_place_order_with_mocked_repo(mocker, order_id, shipping_id):
    mock_repo = mocker.Mock()
    mock_publisher = mocker.Mock()
    shipping_service = ShippingService(mock_repo, mock_publisher)

    mock_repo.create_shipping.return_value = shipping_id

    cart = ShoppingCart()
    cart.add_product(Product(
        available_amount=10,
        name='Product',
        price=random.random() * 10000),
        amount=9
    )

    order = Order(cart, shipping_service, order_id)
    due_date = datetime.now(timezone.utc) + timedelta(seconds=3)
    actual_shipping_id = order.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=due_date
    )

    assert actual_shipping_id == shipping_id, "Actual shipping id must be equal to mock return value"

    mock_repo.create_shipping.assert_called_with(ShippingService.list_available_shipping_type()[0], ["Product"],
                                                 order_id, shipping_service.SHIPPING_CREATED, due_date)
    mock_publisher.send_new_shipping.assert_called_with(shipping_id)


def test_place_order_with_unavailable_shipping_type_fails(dynamo_resource):
    shipping_service = ShippingService(ShippingRepository(), ShippingPublisher())
    cart = ShoppingCart()
    cart.add_product(Product(
        available_amount=10,
        name='Product',
        price=random.random() * 10000),
        amount=9
    )
    order = Order(cart, shipping_service)
    shipping_id = None

    with pytest.raises(ValueError) as excinfo:
        shipping_id = order.place_order(
            "Новий тип доставки",
            due_date=datetime.now(timezone.utc) + timedelta(seconds=3)
        )
    assert shipping_id is None, "Shipping id must not be assigned"
    assert "Shipping type is not available" in str(excinfo.value)


def test_when_place_order_then_shipping_in_queue(dynamo_resource):
    shipping_service = ShippingService(ShippingRepository(), ShippingPublisher())
    cart = ShoppingCart()

    cart.add_product(Product(
        available_amount=10,
        name='Product',
        price=random.random() * 10000),
        amount=9
    )

    order = Order(cart, shipping_service)
    shipping_id = order.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=datetime.now(timezone.utc) + timedelta(minutes=1)
    )

    sqs_client = boto3.client(
        "sqs",
        endpoint_url=AWS_ENDPOINT_URL,
        region_name=AWS_REGION
    )
    queue_url = sqs_client.get_queue_url(QueueName=SHIPPING_QUEUE)["QueueUrl"]
    response = sqs_client.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=10
    )

    messages = response.get("Messages", [])
    assert len(messages) == 1, "Expected 1 SQS message"

    body = messages[0]["Body"]
    assert shipping_id == body


# new 10 tests-------------------------------------------------------------------------------------

def test_place_order_multiple_products_integration(dynamo_resource):
    shipping_service = ShippingService(ShippingRepository(), ShippingPublisher())

    cart = ShoppingCart()
    cart.add_product(Product("Phone", 1000, 10), 2)
    cart.add_product(Product("Tablet", 500, 10), 1)

    order = Order(cart, shipping_service)

    shipping_id = order.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=datetime.now(timezone.utc) + timedelta(minutes=1)
    )

    assert shipping_id is not None


def test_product_amount_decreases_after_order(dynamo_resource):
    product = Product("Laptop", 2000, 5)

    cart = ShoppingCart()
    cart.add_product(product, 3)

    shipping_service = ShippingService(ShippingRepository(), ShippingPublisher())
    order = Order(cart, shipping_service)

    order.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=datetime.now(timezone.utc) + timedelta(minutes=1)
    )

    assert product.available_amount == 2


def test_cart_cleared_after_order(dynamo_resource):
    cart = ShoppingCart()
    cart.add_product(Product("Camera", 800, 10), 1)

    shipping_service = ShippingService(ShippingRepository(), ShippingPublisher())
    order = Order(cart, shipping_service)

    order.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=datetime.now(timezone.utc) + timedelta(minutes=1)
    )

    assert len(cart.products) == 0


def test_empty_cart_order_fails(dynamo_resource):
    cart = ShoppingCart()
    shipping_service = ShippingService(ShippingRepository(), ShippingPublisher())
    order = Order(cart, shipping_service)

    with pytest.raises(Exception):
        order.place_order(
            ShippingService.list_available_shipping_type()[0],
            due_date=datetime.now(timezone.utc) + timedelta(minutes=1)
        )


def test_shipping_saved_in_repository(dynamo_resource):
    shipping_repo = ShippingRepository()
    shipping_service = ShippingService(shipping_repo, ShippingPublisher())

    cart = ShoppingCart()
    cart.add_product(Product("Watch", 200, 10), 2)

    order = Order(cart, shipping_service)

    shipping_id = order.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=datetime.now(timezone.utc) + timedelta(minutes=1)
    )

    saved_shipping = shipping_repo.get_shipping(shipping_id)
    assert saved_shipping is not None


def test_all_shipping_types_supported(dynamo_resource):
    shipping_service = ShippingService(ShippingRepository(), ShippingPublisher())

    for shipping_type in ShippingService.list_available_shipping_type():
        cart = ShoppingCart()
        cart.add_product(Product("Book", 30, 10), 1)

        order = Order(cart, shipping_service)

        shipping_id = order.place_order(
            shipping_type,
            due_date=datetime.now(timezone.utc) + timedelta(minutes=1)
        )

        assert shipping_id is not None


def test_past_due_date_fails(dynamo_resource):
    shipping_service = ShippingService(ShippingRepository(), ShippingPublisher())

    cart = ShoppingCart()
    cart.add_product(Product("Printer", 400, 5), 1)

    order = Order(cart, shipping_service)

    with pytest.raises(Exception):
        order.place_order(
            ShippingService.list_available_shipping_type()[0],
            due_date=datetime.now(timezone.utc) - timedelta(minutes=5)
        )


def test_shipping_becomes_overdue_after_due_date(dynamo_resource):
    shipping_service = ShippingService(ShippingRepository(), ShippingPublisher())

    cart = ShoppingCart()
    cart.add_product(Product("Headphones", 150, 10), 1)

    order = Order(cart, shipping_service)

    shipping_id = order.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=datetime.now(timezone.utc) + timedelta(seconds=2)
    )

    shipment = Shipment(shipping_id, shipping_service)

    initial_status = shipment.check_shipping_status()

    time.sleep(3)

    updated_status = shipment.check_shipping_status()

    assert updated_status != initial_status


def test_place_order_idempotency(dynamo_resource):
    shipping_service = ShippingService(ShippingRepository(), ShippingPublisher())

    order_id = "fixed-order-id"

    cart1 = ShoppingCart()
    cart1.add_product(Product("Monitor", 600, 5), 1)

    order1 = Order(cart1, shipping_service, order_id)

    shipping1 = order1.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=datetime.now(timezone.utc) + timedelta(minutes=1)
    )

    cart2 = ShoppingCart()
    cart2.add_product(Product("Monitor", 600, 5), 1)

    order2 = Order(cart2, shipping_service, order_id)

    shipping2 = order2.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=datetime.now(timezone.utc) + timedelta(minutes=1)
    )

    assert shipping1 == shipping2


def test_two_orders_compete_for_same_product(dynamo_resource):
    shipping_service = ShippingService(ShippingRepository(), ShippingPublisher())

    product = Product("GPU", 2000, 1)

    cart1 = ShoppingCart()
    cart1.add_product(product, 1)

    cart2 = ShoppingCart()
    cart2.add_product(product, 1)

    order1 = Order(cart1, shipping_service)
    order2 = Order(cart2, shipping_service)

    shipping_id = order1.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=datetime.now(timezone.utc) + timedelta(minutes=1)
    )

    with pytest.raises(Exception):
        order2.place_order(
            ShippingService.list_available_shipping_type()[0],
            due_date=datetime.now(timezone.utc) + timedelta(minutes=1)
        )

    assert shipping_id is not None

"""
def test_shipping_consistency_between_repo_and_queue(dynamo_resource):
    shipping_repo = ShippingRepository()
    shipping_service = ShippingService(shipping_repo, ShippingPublisher())

    sqs_client = boto3.client("sqs", endpoint_url=AWS_ENDPOINT_URL, region_name=AWS_REGION)
    queue_url = sqs_client.get_queue_url(QueueName=SHIPPING_QUEUE)["QueueUrl"]

    while True:
        resp = sqs_client.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10, WaitTimeSeconds=1)
        msgs = resp.get("Messages", [])
        if not msgs:
            break
        for msg in msgs:
            sqs_client.delete_message(QueueUrl=queue_url, ReceiptHandle=msg["ReceiptHandle"])

    cart = ShoppingCart()
    cart.add_product(Product("Router", 90, 10), 1)

    order = Order(cart, shipping_service)

    shipping_id = order.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=datetime.now(timezone.utc) + timedelta(minutes=1)
    )

    saved = shipping_repo.get_shipping(shipping_id)
    assert saved is not None

    sqs_client = boto3.client(
        "sqs",
        endpoint_url=AWS_ENDPOINT_URL,
        region_name=AWS_REGION
    )

    queue_url = sqs_client.get_queue_url(QueueName=SHIPPING_QUEUE)["QueueUrl"]

    response = sqs_client.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=10
    )

    messages = response.get("Messages", [])

    assert any(shipping_id in msg["Body"] for msg in messages)
"""