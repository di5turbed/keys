from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.contrib import admin
from django.contrib.auth.models import User

class Blog(models.Model):
    title = models.CharField(max_length=100, unique_for_date="posted", verbose_name="Заголовок")
    description = models.TextField(verbose_name="Краткое содержание")
    content = models.TextField(verbose_name="Полное содержание")
    posted = models.DateTimeField(default=timezone.now, db_index=True, verbose_name="Опубликована")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    
    image = models.FileField(default='temp.jpg', verbose_name="Путь к картинке")

    class Meta:
        db_table = "Posts"
        ordering = ["-posted"]
        verbose_name = "новость"
        verbose_name_plural = "новости"

    def __str__(self):
        return self.title

class Comment(models.Model):
    text = models.TextField(verbose_name="Текст комментария")
    date = models.DateTimeField(default=timezone.now, db_index=True, verbose_name="Дата добавления")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    post = models.ForeignKey(Blog, on_delete=models.CASCADE, verbose_name="Статья")

    def __str__(self):
        return f"Комментарий от {self.author} к {self.post}"

    class Meta:
        db_table = "Comments"
        ordering = ["-date"]
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"

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
        ordering = ["name"]
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
        ordering = ["name"]
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

class CartItem(models.Model):
    """Позиция в корзине клиента (текущий, ещё не оформленный заказ)."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cart_items", verbose_name="Клиент")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")

    @property
    def total(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.product} x{self.quantity}"

    class Meta:
        unique_together = ("user", "product")
        verbose_name = "позиция корзины"
        verbose_name_plural = "корзина"

class Order(models.Model):
    STATUS_NEW = "new"
    STATUS_PROCESSING = "processing"
    STATUS_DONE = "done"
    STATUS_CANCELED = "canceled"
    STATUS_CHOICES = [
        (STATUS_NEW, "Новый"),
        (STATUS_PROCESSING, "В обработке"),
        (STATUS_DONE, "Выполнен"),
        (STATUS_CANCELED, "Отменён"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders", verbose_name="Клиент")
    created = models.DateTimeField(default=timezone.now, db_index=True, verbose_name="Дата заказа")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW, verbose_name="Статус")
    email = models.EmailField(verbose_name="E-mail для получения ключей")
    comment = models.TextField(blank=True, verbose_name="Комментарий к заказу")
    manager_note = models.TextField(blank=True, verbose_name="Примечание менеджера")

    @property
    def total(self):
        return sum(item.total for item in self.items.all())

    @property
    def is_editable(self):
        """Клиент может менять/удалять заказ, пока его не взял в работу менеджер."""
        return self.status == self.STATUS_NEW

    def __str__(self):
        return f"Заказ №{self.id} ({self.user})"

    class Meta:
        ordering = ["-created"]
        verbose_name = "заказ"
        verbose_name_plural = "заказы"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items", verbose_name="Заказ")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name="Товар")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена на момент заказа")

    @property
    def total(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.product} x{self.quantity}"

    class Meta:
        verbose_name = "позиция заказа"
        verbose_name_plural = "позиции заказа"

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created', 'status')
    list_filter = ('status', 'created')
    inlines = [OrderItemInline]

try:
    admin.site.register(Order, OrderAdmin)
    admin.site.register(CartItem)
except admin.sites.AlreadyRegistered:
    pass
