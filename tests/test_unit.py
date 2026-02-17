import unittest

from unittest.mock import MagicMock

from app.eshop import ShoppingCart, Product, Order


class TestProduct(unittest.TestCase):
    def setUp(self):
        self.product = Product(name='Test', price=123.45, available_amount=21)
        self.cart = ShoppingCart()

    def tearDown(self):
        self.cart.remove_product(self.product)

    def test_mock_add_product(self):
        self.product.is_available = MagicMock()
        self.cart.add_product(self.product, 12345)
        self.product.is_available.assert_called_with(12345)
        self.product.is_available.reset_mock()

    def test_add_available_amount(self):
        self.cart.add_product(self.product, 11)
        self.assertEqual(self.cart.contains_product(self.product), True, 'Продукт успішно доданий до корзини')

    def test_add_non_available_amount(self):
        with self.assertRaises(ValueError):
            self.cart.add_product(self.product, 22)
        self.assertEqual(self.cart.contains_product(self.product), False, 'Продукт не доданий до корзини')

    def test_is_available_true(self):
        self.assertTrue(self.product.is_available(10), "Продукт доступний для покупки менше доступної кількості")

    def test_is_available_false(self):
        self.assertFalse(self.product.is_available(100), "Продукт недоступний для покупки більше наявної кількості")

    def test_buy_reduces_amount(self):
        initial = self.product.available_amount
        self.product.buy(5)
        self.assertEqual(self.product.available_amount, initial - 5, "Кількість продукту зменшилась після покупки")

    def test_buy_zero_amount(self):
        initial = self.product.available_amount
        self.product.buy(0)
        self.assertEqual(self.product.available_amount, initial, "Кількість продукту не змінилась при купівлі 0")


class TestShoppingCart(unittest.TestCase):
    def setUp(self):
        self.product = Product(name='Test', price=123.45, available_amount=21)
        self.cart = ShoppingCart()

    def tearDown(self):
        self.cart.remove_product(self.product)

    def test_calculate_total(self):
        self.cart.add_product(self.product, 2)
        total = 2 * self.product.price
        self.assertEqual(self.cart.calculate_total(), total, "Загальна сума корзини вірна")

    def test_contains_product_false(self):
        self.assertFalse(self.cart.contains_product(self.product), "Продукт ще не доданий до корзини")

    def test_remove_product(self):
        self.cart.add_product(self.product, 1)
        self.cart.remove_product(self.product)
        self.assertFalse(self.cart.contains_product(self.product), "Продукт видалено з корзини")

    def test_add_invalid_type_amount(self):
        with self.assertRaises(TypeError):
            self.cart.add_product(self.product, None)


class TestOrder(unittest.TestCase):
    def setUp(self):
        self.product = Product(name='Test', price=123.45, available_amount=21)
        self.cart = ShoppingCart()
        self.cart.add_product(self.product, 5)
        self.mock_shipping_service = MagicMock()
        self.order = Order(self.cart, self.mock_shipping_service)

        self.mock_shipping_type = "Тестова служба доставки"

    def test_place_order_reduces_product_and_clears_cart(self):
        self.order.place_order(self.mock_shipping_type)
        self.assertEqual(self.product.available_amount, 16, "Після submit_cart_order кількість продукту зменшилась")
        self.assertEqual(len(self.cart.products), 0, "Корзина очищена після submit_cart_order")


if __name__ == '__main__':
    unittest.main()
