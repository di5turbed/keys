from datetime import datetime

from app.models import CartItem
from app.roles import is_admin, is_client, is_manager, role_name


def site(request):
    """Общие для всех страниц данные: роль посетителя и размер корзины."""
    user = request.user
    client = is_client(user)
    return {
        'year': datetime.now().year,
        'is_client': client,
        'is_manager': is_manager(user),
        'is_admin': is_admin(user),
        'role_name': role_name(user),
        'cart_count': sum(CartItem.objects.filter(user=user).values_list('quantity', flat=True)) if client else 0,
    }
