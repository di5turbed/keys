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
    path('new_category/', views.new_category, name='new_category'),
    path('new_product/', views.new_product, name='new_product'),
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