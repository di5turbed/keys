"""
Definition of urls for keys.
"""

from datetime import datetime
from django.urls import path
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from app import forms, views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', views.home, name='home'),
    path('contact/', views.contact, name='contact'),
    path('about/', views.about, name='about'),
    path('links/', views.links, name='links'),
    path('pool/', views.pool, name='pool'),
    path('registration/', views.registration, name='registration'),
    path('blog/', views.blog, name='blog'),
    path('newpost/', views.newpost, name='newpost'),
    path('catalog/', views.catalog, name='catalog'),
    path('catalog/<int:category_id>/', views.category_items, name='category_items'),
    path('product/<int:product_id>/', views.product_details, name='product_details'),

    # Клиент
    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/update/<int:item_id>/', views.cart_update, name='cart_update'),
    path('cart/remove/<int:item_id>/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout, name='checkout'),
    path('my_orders/', views.my_orders, name='my_orders'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('order/<int:order_id>/edit/', views.order_edit, name='order_edit'),
    path('order/<int:order_id>/delete/', views.order_delete, name='order_delete'),

    # Менеджер
    path('orders/', views.manager_orders, name='manager_orders'),
    path('orders/<int:order_id>/', views.manager_order, name='manager_order'),

    # Администратор
    path('panel/', views.admin_panel, name='admin_panel'),
    path('panel/categories/', views.admin_categories, name='admin_categories'),
    path('new_category/', views.new_category, name='new_category'),
    path('panel/categories/<int:category_id>/edit/', views.category_edit, name='category_edit'),
    path('panel/categories/<int:category_id>/delete/', views.category_delete, name='category_delete'),
    path('panel/products/', views.admin_products, name='admin_products'),
    path('new_product/', views.new_product, name='new_product'),
    path('panel/products/<int:product_id>/edit/', views.product_edit, name='product_edit'),
    path('panel/products/<int:product_id>/delete/', views.product_delete, name='product_delete'),
    path('panel/news/', views.admin_news, name='admin_news'),
    path('panel/news/<int:post_id>/edit/', views.news_edit, name='news_edit'),
    path('panel/news/<int:post_id>/delete/', views.news_delete, name='news_delete'),
    path('panel/users/', views.admin_users, name='admin_users'),
    path('panel/users/new_manager/', views.manager_create, name='manager_create'),
    path('panel/users/<int:user_id>/delete/', views.user_delete, name='user_delete'),

    path('blogpost/<int:parametr>/', views.blogpost, name='blogpost'),
    path('videopost/', views.videopost, name='videopost'),
    path('login/',
     LoginView.as_view(
         template_name='app/login.html',
         authentication_form=forms.BootstrapAuthenticationForm,
         extra_context={
             'title': 'Авторизация',
             'year' : datetime.now().year,
         }
     ),
     name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('admin/', admin.site.urls),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)