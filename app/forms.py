"""
Definition of forms.
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from app.models import Blog, Category, Comment, Order, Product

class BootstrapAuthenticationForm(AuthenticationForm):
    """Authentication form which uses boostrap CSS."""
    username = forms.CharField(label="Логин", widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
class FeedbackForm(forms.Form):
    name = forms.CharField(label='Ваше имя', min_length=2, max_length=100, 
                           widget=forms.TextInput(attrs={'class': 'form-control'}))
    city = forms.CharField(label='Ваш город', required=False, 
                           widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    score = forms.ChoiceField(label='Как вы оцениваете наш сайт?', 
                              choices=[('1', 'Ужасно'), ('2', 'Плохо'), ('3', 'Нормально'), ('4', 'Хорошо'), ('5', 'Отлично')], 
                              widget=forms.RadioSelect)
    
    source = forms.ChoiceField(label='Откуда вы о нас узнали?', 
                               choices=[('search', 'Поисковые системы'), ('social', 'Социальные сети'), ('friends', 'От друзей')],
                               widget=forms.Select(attrs={'class': 'form-control'}))
    
    message = forms.CharField(label='Ваши пожелания', 
                              widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}))
    
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {'text': "Комментарий"}
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Напишите ваш комментарий...'})
        }

class BlogForm(forms.ModelForm):
    image = forms.FileField(label="Картинка", required=False)

    class Meta:
        model = Blog
        fields = ('title', 'description', 'content', 'image')
        labels = {
            'title': "Заголовок", 
            'description': "Краткое содержание", 
            'content': "Полное содержание", 
            'image': "Картинка"
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ('name', 'description')
        labels = {'name': "Название категории", 'description': "Описание категории"}
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ProductForm(forms.ModelForm):
    image = forms.FileField(label="Картинка", required=False)

    class Meta:
        model = Product
        fields = ('name', 'short_description', 'full_description', 'price', 'image', 'category')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'short_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'full_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }

class RegistrationForm(UserCreationForm):
    """Регистрация: логин, имя, e-mail и пароль."""
    first_name = forms.CharField(label="Имя", max_length=150, required=False)
    email = forms.EmailField(label="E-mail", required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'email')

class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ('email', 'comment')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class OrderStatusForm(forms.ModelForm):
    """Форма менеджера для обработки заказа."""
    class Meta:
        model = Order
        fields = ('status', 'manager_note')
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'manager_note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
