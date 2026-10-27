"""
Тесты ролей и сценария заказа. Запуск: python manage.py test
"""

from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from app.models import Blog, CartItem, Category, Order, Product
from app.roles import CLIENT_GROUP, MANAGER_GROUP, add_to_group


class ShopTestCase(TestCase):
    PASSWORD = "test-pass-123"

    def setUp(self):
        self.admin = User.objects.create_superuser("admin_t", "a@example.com", self.PASSWORD)
        self.client_user = self.make_user("client_t", CLIENT_GROUP)
        self.other_client = self.make_user("client_2", CLIENT_GROUP)
        self.manager = self.make_user("manager_t", MANAGER_GROUP)
        self.category = Category.objects.create(name="Шутеры", description="...")
        self.product = Product.objects.create(name="Игра", short_description="s", full_description="f",
                                              price=Decimal("100.00"), category=self.category)

    def make_user(self, username, group):
        user = User.objects.create_user(username, f"{username}@example.com", self.PASSWORD)
        add_to_group(user, group)
        return user

    def login(self, user):
        self.client.login(username=user.username, password=self.PASSWORD)


class PublicPagesTest(ShopTestCase):
    def test_guest_pages(self):
        for name in ('home', 'blog', 'contact', 'catalog', 'registration', 'about'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)

    def test_home_shows_three_latest_news(self):
        for i in range(5):
            Blog.objects.create(title=f"Новость {i}", description="d", content="c", author=self.admin)
        response = self.client.get(reverse('home'))
        self.assertEqual(len(response.context['latest_news']), 3)

    def test_registration_makes_client(self):
        self.client.post(reverse('registration'), {
            'username': 'newbie', 'email': 'n@example.com',
            'password1': 'Sup3r-secret-pw', 'password2': 'Sup3r-secret-pw',
        })
        self.assertTrue(User.objects.get(username='newbie').groups.filter(name=CLIENT_GROUP).exists())


class AccessTest(ShopTestCase):
    def test_guest_redirected_to_login(self):
        response = self.client.get(reverse('cart'))
        self.assertRedirects(response, '/login/?next=/cart/', fetch_redirect_response=False)

    def test_role_pages(self):
        cases = [
            (self.client_user, 'cart', 200), (self.client_user, 'manager_orders', 302), (self.client_user, 'admin_panel', 302),
            (self.manager, 'manager_orders', 200), (self.manager, 'cart', 302), (self.manager, 'admin_panel', 302),
            (self.admin, 'admin_panel', 200), (self.admin, 'admin_users', 200), (self.admin, 'cart', 302),
        ]
        for user, name, code in cases:
            self.login(user)
            self.assertEqual(self.client.get(reverse(name)).status_code, code, f"{user} -> {name}")


class OrderFlowTest(ShopTestCase):
    def place_order(self):
        self.login(self.client_user)
        self.client.post(reverse('cart_add', args=[self.product.id]))
        self.client.post(reverse('cart_add', args=[self.product.id]))
        self.client.post(reverse('checkout'), {'email': 'c@example.com', 'comment': ''})
        return Order.objects.get(user=self.client_user)

    def test_checkout_moves_cart_to_order(self):
        order = self.place_order()
        self.assertEqual(order.total, Decimal("200.00"))
        self.assertFalse(CartItem.objects.filter(user=self.client_user).exists())

    def test_client_edits_and_deletes_own_order(self):
        order = self.place_order()
        item = order.items.get()
        self.client.post(reverse('order_edit', args=[order.id]), {'email': 'x@example.com', f'qty_{item.id}': 5})
        self.assertEqual(order.items.get().quantity, 5)
        self.client.post(reverse('order_delete', args=[order.id]))
        self.assertFalse(Order.objects.filter(id=order.id).exists())

    def test_other_client_cannot_touch_order(self):
        order = self.place_order()
        self.login(self.other_client)
        self.assertEqual(self.client.post(reverse('order_delete', args=[order.id])).status_code, 404)
        self.assertEqual(self.client.get(reverse('order_detail', args=[order.id])).status_code, 302)

    def test_manager_changes_status_and_locks_order(self):
        order = self.place_order()
        self.login(self.manager)
        self.client.post(reverse('manager_order', args=[order.id]), {'status': Order.STATUS_PROCESSING, 'manager_note': ''})
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_PROCESSING)
        self.login(self.client_user)
        self.client.post(reverse('order_delete', args=[order.id]))
        self.assertTrue(Order.objects.filter(id=order.id).exists())


class AdminTest(ShopTestCase):
    def test_admin_creates_manager_and_deletes_users(self):
        self.login(self.admin)
        self.client.post(reverse('manager_create'), {
            'username': 'mgr2', 'email': 'm@example.com',
            'password1': 'Sup3r-secret-pw', 'password2': 'Sup3r-secret-pw',
        })
        self.assertTrue(User.objects.get(username='mgr2').groups.filter(name=MANAGER_GROUP).exists())
        self.client.post(reverse('user_delete', args=[self.client_user.id]))
        self.assertFalse(User.objects.filter(id=self.client_user.id).exists())
        self.assertEqual(self.client.post(reverse('user_delete', args=[self.admin.id])).status_code, 404)

    def test_admin_crud_catalog(self):
        self.login(self.admin)
        self.client.post(reverse('product_edit', args=[self.product.id]), {
            'name': 'Новая', 'short_description': 's', 'full_description': 'f',
            'price': '150', 'category': self.category.id,
        })
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Новая')
        self.client.post(reverse('product_delete', args=[self.product.id]))
        self.assertFalse(Product.objects.filter(id=self.product.id).exists())
