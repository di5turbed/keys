"""
Роли посетителей сайта: Гость, Клиент, Менеджер, Администратор.
Клиент и Менеджер — группы Django, Администратор — суперпользователь.
"""

from functools import wraps

from django.contrib import messages
from django.contrib.auth.models import Group
from django.shortcuts import redirect

CLIENT_GROUP = "Клиент"
MANAGER_GROUP = "Менеджер"


def is_admin(user):
    return user.is_authenticated and user.is_superuser


def is_manager(user):
    return user.is_authenticated and not user.is_superuser and user.groups.filter(name=MANAGER_GROUP).exists()


def is_client(user):
    return user.is_authenticated and not is_admin(user) and not is_manager(user)


def role_name(user):
    if not user.is_authenticated:
        return "Гость"
    if is_admin(user):
        return "Администратор"
    if is_manager(user):
        return "Менеджер"
    return "Клиент"


def add_to_group(user, group_name):
    group, _ = Group.objects.get_or_create(name=group_name)
    user.groups.add(group)


def role_required(check, message):
    """Пускает в представление только пользователей, прошедших проверку роли."""
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f"/login/?next={request.path}")
            if not check(request.user):
                messages.error(request, message)
                return redirect('home')
            return view(request, *args, **kwargs)
        return wrapper
    return decorator


client_required = role_required(is_client, "Эта страница доступна только клиентам.")
manager_required = role_required(is_manager, "Эта страница доступна только менеджерам.")
admin_required = role_required(is_admin, "Эта страница доступна только администратору.")
