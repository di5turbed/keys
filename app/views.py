"""
Definition of views.
"""

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import ProtectedError
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from app.forms import (BlogForm, CategoryForm, CheckoutForm, CommentForm, FeedbackForm,
                       OrderStatusForm, ProductForm, RegistrationForm)
from app.models import Blog, CartItem, Category, Comment, Order, OrderItem, Product
from app.roles import (CLIENT_GROUP, MANAGER_GROUP, add_to_group, admin_required, client_required,
                       is_admin, is_manager, manager_required, role_name)

# ---------------------------------------------------------------------------
# Общедоступные страницы (Гость)
# ---------------------------------------------------------------------------

def home(request):
    """Главная: организация, аннотация и 3 последние новости."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/index.html',
        {
            'title': 'Главная',
            'latest_news': Blog.objects.order_by('-posted')[:3],
            'categories': Category.objects.all(),
        }
    )

def contact(request):
    """Renders the contact page."""
    assert isinstance(request, HttpRequest)
    return render(request, 'app/contact.html', {'title': 'Контакты'})

def about(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    return render(request, 'app/about.html', {'title': 'О нас'})

def links(request):
    """Renders the links page."""
    assert isinstance(request, HttpRequest)
    return render(request, 'app/links.html', {'title': 'Полезные ссылки'})

def pool(request):
    """Отрисовывает страницу обратной связи (опроса)."""
    assert isinstance(request, HttpRequest)
    data = None

    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            res = dict()
            res['name'] = data['name']
            res['city'] = data['city'] if data['city'] else "Не указан"
            res['score'] = data['score']
            res['source'] = data['source']
            res['message'] = data['message']

            data = res
            form = None
    else:
        form = FeedbackForm()

    return render(
        request,
        'app/pool.html',
        {
            'form': form,
            'data': data,
            'title': 'Обратная связь',
        }
    )

def registration(request):
    """Регистрация гостя: новый пользователь получает роль «Клиент»."""
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == "POST":
        regform = RegistrationForm(request.POST)
        if regform.is_valid():
            user = regform.save(commit=False)
            user.is_staff = False
            user.is_active = True
            user.is_superuser = False
            user.save()
            add_to_group(user, CLIENT_GROUP)
            login(request, user)
            messages.success(request, "Регистрация прошла успешно. Добро пожаловать!")
            return redirect('catalog')
    else:
        regform = RegistrationForm()

    return render(
        request,
        'app/registration.html',
        {
            'regform': regform,
            'title': 'Регистрация',
        }
    )

def blog(request):
    """Страница «Новости»: все новости по убыванию даты."""
    posts = Blog.objects.order_by('-posted')
    return render(
        request,
        'app/blog.html',
        {
            'title': 'Новости',
            'posts': posts,
        }
    )

def blogpost(request, parametr):
    post_1 = get_object_or_404(Blog, id=parametr)
    comments = Comment.objects.filter(post=post_1)

    if request.method == "POST" and request.user.is_authenticated:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment_f = form.save(commit=False)
            comment_f.author = request.user
            comment_f.date = timezone.now()
            comment_f.post = post_1
            comment_f.save()
            return redirect('blogpost', parametr=post_1.id)
    else:
        form = CommentForm()

    return render(
        request,
        'app/blogpost.html',
        {
            'title': post_1.title,
            'post_1': post_1,
            'comments': comments,
            'form': form,
        }
    )

def videopost(request):
    """Отрисовывает страницу с видео-контентом."""
    return render(request, 'app/videopost.html', {'title': 'Видео-обзоры'})

def catalog(request):
    categories = Category.objects.all()
    return render(request, 'app/catalog.html', {'categories': categories, 'title': 'Каталог'})

def category_items(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    items = Product.objects.filter(category=category)
    return render(request, 'app/category_items.html', {'category': category, 'items': items, 'title': category.name})

def product_details(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'app/product_details.html', {'product': product, 'title': product.name})

# ---------------------------------------------------------------------------
# Клиент: корзина и заказы
# ---------------------------------------------------------------------------

@client_required
@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        item.quantity += 1
        item.save()
    messages.success(request, f"«{product.name}» добавлен в корзину.")
    return redirect(request.POST.get('next') or 'cart')

@client_required
def cart(request):
    items = CartItem.objects.filter(user=request.user).select_related('product')
    return render(request, 'app/cart.html', {
        'title': 'Корзина',
        'items': items,
        'total': sum(item.total for item in items),
    })

@client_required
@require_POST
def cart_update(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    try:
        quantity = int(request.POST.get('quantity', 1))
    except ValueError:
        quantity = item.quantity
    if quantity <= 0:
        item.delete()
    else:
        item.quantity = min(quantity, 99)
        item.save()
    return redirect('cart')

@client_required
@require_POST
def cart_remove(request, item_id):
    get_object_or_404(CartItem, id=item_id, user=request.user).delete()
    return redirect('cart')

@client_required
def checkout(request):
    """Оформление заказа из содержимого корзины."""
    items = list(CartItem.objects.filter(user=request.user).select_related('product'))
    if not items:
        messages.error(request, "Корзина пуста.")
        return redirect('cart')

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                order = form.save(commit=False)
                order.user = request.user
                order.save()
                OrderItem.objects.bulk_create([
                    OrderItem(order=order, product=i.product, quantity=i.quantity, price=i.product.price)
                    for i in items
                ])
                CartItem.objects.filter(user=request.user).delete()
            messages.success(request, f"Заказ №{order.id} оформлен.")
            return redirect('order_detail', order_id=order.id)
    else:
        form = CheckoutForm(initial={'email': request.user.email})

    return render(request, 'app/checkout.html', {
        'title': 'Оформление заказа',
        'form': form,
        'items': items,
        'total': sum(item.total for item in items),
    })

@client_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product')
    return render(request, 'app/my_orders.html', {'title': 'Мои заказы', 'orders': orders})

def order_detail(request, order_id):
    """Просмотр заказа: владельцу-клиенту, менеджеру и администратору."""
    if not request.user.is_authenticated:
        return redirect(f"/login/?next={request.path}")
    order = get_object_or_404(Order, id=order_id)
    if order.user != request.user and not (is_manager(request.user) or is_admin(request.user)):
        messages.error(request, "Это не ваш заказ.")
        return redirect('home')
    return render(request, 'app/order_detail.html', {'title': f'Заказ №{order.id}', 'order': order})

@client_required
def order_edit(request, order_id):
    """Клиент редактирует свой новый заказ: количество, e-mail, комментарий."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if not order.is_editable:
        messages.error(request, "Заказ уже в работе у менеджера — изменить его нельзя.")
        return redirect('order_detail', order_id=order.id)

    items = list(order.items.select_related('product'))
    if request.method == "POST":
        form = CheckoutForm(request.POST, instance=order)
        if form.is_valid():
            with transaction.atomic():
                form.save()
                for item in items:
                    try:
                        quantity = int(request.POST.get(f'qty_{item.id}', item.quantity))
                    except ValueError:
                        quantity = item.quantity
                    if quantity <= 0:
                        item.delete()
                    else:
                        item.quantity = min(quantity, 99)
                        item.save()
                if not order.items.exists():
                    order.delete()
                    messages.success(request, "Все позиции удалены — заказ удалён.")
                    return redirect('my_orders')
            messages.success(request, "Заказ обновлён.")
            return redirect('order_detail', order_id=order.id)
    else:
        form = CheckoutForm(instance=order)

    return render(request, 'app/order_edit.html', {
        'title': f'Редактирование заказа №{order.id}',
        'order': order,
        'items': items,
        'form': form,
    })

@client_required
def order_delete(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if not order.is_editable:
        messages.error(request, "Заказ уже в работе у менеджера — удалить его нельзя.")
        return redirect('order_detail', order_id=order.id)
    if request.method == "POST":
        order.delete()
        messages.success(request, f"Заказ №{order_id} удалён.")
        return redirect('my_orders')
    return render(request, 'app/confirm_delete.html', {
        'title': 'Удаление заказа',
        'object_name': str(order),
        'cancel_url': 'my_orders',
    })

# ---------------------------------------------------------------------------
# Менеджер: управление заказами клиентов
# ---------------------------------------------------------------------------

@manager_required
def manager_orders(request):
    status = request.GET.get('status', '')
    orders = Order.objects.select_related('user').prefetch_related('items__product')
    if status:
        orders = orders.filter(status=status)
    return render(request, 'app/manager_orders.html', {
        'title': 'Заказы',
        'orders': orders,
        'status': status,
        'statuses': Order.STATUS_CHOICES,
    })

@manager_required
def manager_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == "POST":
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, f"Заказ №{order.id}: статус «{order.get_status_display()}».")
            return redirect('manager_orders')
    else:
        form = OrderStatusForm(instance=order)
    return render(request, 'app/manager_order.html', {
        'title': f'Обработка заказа №{order.id}',
        'order': order,
        'form': form,
    })

# ---------------------------------------------------------------------------
# Администратор: каталог, новости, пользователи
# ---------------------------------------------------------------------------

@admin_required
def admin_panel(request):
    return render(request, 'app/admin_panel.html', {
        'title': 'Панель администратора',
        'stats': {
            'categories': Category.objects.count(),
            'products': Product.objects.count(),
            'news': Blog.objects.count(),
            'clients': User.objects.filter(groups__name=CLIENT_GROUP).count(),
            'managers': User.objects.filter(groups__name=MANAGER_GROUP).count(),
            'orders': Order.objects.count(),
        },
    })

def _form_page(request, form, title, submit, cancel_url):
    return render(request, 'app/form_page.html', {
        'title': title,
        'form': form,
        'submit': submit,
        'cancel_url': cancel_url,
    })

def _delete_page(request, obj, cancel_url, success_url):
    if request.method == "POST":
        try:
            obj.delete()
            messages.success(request, f"«{obj}» удалён.")
        except ProtectedError:
            messages.error(request, f"«{obj}» нельзя удалить: он есть в заказах клиентов.")
        return redirect(success_url)
    return render(request, 'app/confirm_delete.html', {
        'title': 'Подтверждение удаления',
        'object_name': str(obj),
        'cancel_url': cancel_url,
    })

# --- Категории

@admin_required
def admin_categories(request):
    return render(request, 'app/admin_categories.html', {
        'title': 'Категории каталога',
        'categories': Category.objects.all(),
    })

@admin_required
def new_category(request):
    form = CategoryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Категория добавлена.")
        return redirect('admin_categories')
    return _form_page(request, form, 'Новая категория', 'Добавить категорию', 'admin_categories')

@admin_required
def category_edit(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    form = CategoryForm(request.POST or None, instance=category)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Категория сохранена.")
        return redirect('admin_categories')
    return _form_page(request, form, f'Категория «{category}»', 'Сохранить', 'admin_categories')

@admin_required
def category_delete(request, category_id):
    return _delete_page(request, get_object_or_404(Category, id=category_id), 'admin_categories', 'admin_categories')

# --- Товары

@admin_required
def admin_products(request):
    return render(request, 'app/admin_products.html', {
        'title': 'Товары каталога',
        'products': Product.objects.select_related('category').order_by('category__name', 'name'),
    })

@admin_required
def new_product(request):
    form = ProductForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Товар добавлен.")
        return redirect('admin_products')
    return _form_page(request, form, 'Новый товар', 'Добавить товар', 'admin_products')

@admin_required
def product_edit(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Товар сохранён.")
        return redirect('admin_products')
    return _form_page(request, form, f'Товар «{product}»', 'Сохранить', 'admin_products')

@admin_required
def product_delete(request, product_id):
    return _delete_page(request, get_object_or_404(Product, id=product_id), 'admin_products', 'admin_products')

# --- Новости

@admin_required
def admin_news(request):
    return render(request, 'app/admin_news.html', {
        'title': 'Новости',
        'posts': Blog.objects.order_by('-posted'),
    })

@admin_required
def newpost(request):
    """Метод для добавления новой статьи администратором."""
    form = BlogForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        post_f = form.save(commit=False)
        post_f.author = request.user
        post_f.posted = timezone.now()
        post_f.save()
        messages.success(request, "Новость опубликована.")
        return redirect('admin_news')
    return _form_page(request, form, 'Добавить новость', 'Опубликовать', 'admin_news')

@admin_required
def news_edit(request, post_id):
    post = get_object_or_404(Blog, id=post_id)
    form = BlogForm(request.POST or None, request.FILES or None, instance=post)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Новость сохранена.")
        return redirect('admin_news')
    return _form_page(request, form, f'Новость «{post}»', 'Сохранить', 'admin_news')

@admin_required
def news_delete(request, post_id):
    return _delete_page(request, get_object_or_404(Blog, id=post_id), 'admin_news', 'admin_news')

# --- Пользователи

@admin_required
def admin_users(request):
    users = User.objects.filter(is_superuser=False).prefetch_related('groups').order_by('username')
    rows = [{'user': u, 'role': role_name(u)} for u in users]
    return render(request, 'app/admin_users.html', {'title': 'Пользователи', 'rows': rows})

@admin_required
def manager_create(request):
    """Регистрация пользователя с ролью «Менеджер»."""
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        add_to_group(user, MANAGER_GROUP)
        messages.success(request, f"Менеджер «{user.username}» зарегистрирован.")
        return redirect('admin_users')
    return _form_page(request, form, 'Регистрация менеджера', 'Зарегистрировать', 'admin_users')

@admin_required
def user_delete(request, user_id):
    # Администраторов через этот интерфейс удалить нельзя — только клиентов и менеджеров.
    user = get_object_or_404(User, id=user_id, is_superuser=False)
    return _delete_page(request, user, 'admin_users', 'admin_users')
