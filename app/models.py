from django.db import models
from datetime import datetime
from django.urls import reverse
from django.contrib import admin
from django.contrib.auth.models import User

class Blog(models.Model):
    title = models.CharField(max_length=100, unique_for_date="posted", verbose_name="Заголовок")
    description = models.TextField(verbose_name="Краткое содержание")
    content = models.TextField(verbose_name="Полное содержание")
    posted = models.DateTimeField(default=datetime.now(), db_index=True, verbose_name="Опубликована")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    
    image = models.FileField(default='temp.jpg', verbose_name="Путь к картинке")

    class Meta:
        db_table = "Posts"
        verbose_name = "статья блога"
        verbose_name_plural = "статьи блога"

    def __str__(self):
        return self.title

class Comment(models.Model):
    text = models.TextField(verbose_name="Текст комментария")
    date = models.DateTimeField(default=datetime.now(), db_index=True, verbose_name="Дата добавления")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    post = models.ForeignKey(Blog, on_delete=models.CASCADE, verbose_name="Статья")

    def __str__(self):
        return f"Комментарий от {self.author} к {self.post}"

    class Meta:
        db_table = "Comments"
        ordering = ["-date"]
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"

admin.site.register(Comment)

class BlogAdmin(admin.ModelAdmin):
    list_display = ('title', 'posted', 'author')
    search_fields = ('title', 'content')
    list_filter = ('posted', 'author')

class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'date')
    list_filter = ('date', 'author')

try:
    admin.site.register(Blog, BlogAdmin)
    admin.site.register(Comment, CommentAdmin)
except admin.sites.AlreadyRegistered:
    pass

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название категории")
    description = models.TextField(verbose_name="Описание категории")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "категория"
        verbose_name_plural = "категории"

class Product(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    short_description = models.TextField(verbose_name="Краткое описание")
    full_description = models.TextField(verbose_name="Полное описание")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    image = models.FileField(default='temp.jpg', verbose_name="Ссылка на картинку")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Категория")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "товар"
        verbose_name_plural = "товары"

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category')
    list_filter = ('category',)

try:
    admin.site.register(Category, CategoryAdmin)
    admin.site.register(Product, ProductAdmin)
except admin.sites.AlreadyRegistered:
    pass