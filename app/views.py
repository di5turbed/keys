"""
Definition of views.
"""

from datetime import datetime
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpRequest
from django.contrib.auth.forms import UserCreationForm

from app.forms import BlogForm, CategoryForm, CommentForm, FeedbackForm, ProductForm
from app.models import Blog, Category, Comment, Product

def home(request):
    """Renders the home page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/index.html',
        {
            'title':'Home Page',
            'year':datetime.now().year,
        }
    )

def contact(request):
    """Renders the contact page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/contact.html',
        {
            'title':'Contact',
            'message':'Your contact page.',
            'year':datetime.now().year,
        }
    )

def about(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/about.html',
        {
            'title':'About',
            'message':'Your application description page.',
            'year':datetime.now().year,
        }
    )
def links(request):
    """Renders the links page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/links.html',
        {
            'title':'Полезные ссылки',
            'year':datetime.now().year,
        }
    )
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
            'year': datetime.now().year,
        }
    )
def registration(request):
    """Отрисовывает страницу регистрации."""
    if request.method == "POST":
        regform = UserCreationForm(request.POST)
        if regform.is_valid():
            reg_f = regform.save(commit=False)
            reg_f.is_staff = False 
            reg_f.is_active = True 
            reg_f.is_superuser = False 
            reg_f.date_joined = datetime.now()
            reg_f.last_login = datetime.now()
            reg_f.save()
            return redirect('home')
    else:
        regform = UserCreationForm()
        
    return render(
        request,
        'app/registration.html',
        {
            'regform': regform,
            'title': 'Регистрация',
            'year': datetime.now().year,
        }
    )

def blog(request):
    """Отрисовывает страницу со списком постов (ленту)."""
    posts = Blog.objects.all()
    return render(
        request,
        'app/blog.html',
        {
            'title': 'Новости индустрии',
            'posts': posts,
            'year': datetime.now().year,
        }
    )

def blogpost(request, parametr):
    post_1 = Blog.objects.get(id=parametr)
    comments = Comment.objects.filter(post=parametr)
    
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment_f = form.save(commit=False)
            comment_f.author = request.user
            comment_f.date = datetime.now()
            comment_f.post = post_1
            comment_f.save()
            return redirect('blogpost', parametr=post_1.id)
    else:
        form = CommentForm()

    return render(
        request,
        'app/blogpost.html',
        {
            'post_1': post_1,
            'comments': comments,
            'form': form,
            'year': datetime.now().year,
        }
    )

def newpost(request):
    """Метод для добавления новой статьи администратором."""
    if request.method == "POST":
        form = BlogForm(request.POST, request.FILES)
        if form.is_valid():
            post_f = form.save(commit=False)
            post_f.author = request.user
            post_f.posted = datetime.now()
            post_f.save()
            return redirect('blog')
    else:
        form = BlogForm()
        
    return render(
        request,
        'app/newpost.html',
        {
            'form': form,
            'title': 'Добавить пост',
            'year': datetime.now().year,
        }
    )

def videopost(request):
    """Отрисовывает страницу с видео-контентом."""
    return render(
        request,
        'app/videopost.html',
        {
            'title': 'Видео-обзоры',
            'year': datetime.now().year,
        }
    )

def catalog(request):
    categories = Category.objects.all()
    return render(request, 'app/catalog.html', {'categories': categories, 'title': 'Каталог'})

def category_items(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    items = Product.objects.filter(category=category)
    return render(request, 'app/category_items.html', {'category': category, 'items': items})

def product_details(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'app/product_details.html', {'product': product})

def new_category(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('catalog')
    else:
        form = CategoryForm()
    return render(request, 'app/new_category.html', {'form': form, 'title': 'Новая категория'})

def new_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('catalog')
    else:
        form = ProductForm()
    return render(request, 'app/new_product.html', {'form': form, 'title': 'Новый товар'})