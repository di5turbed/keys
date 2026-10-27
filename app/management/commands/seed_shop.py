"""
Наполнение базы демонстрационными данными:
    python manage.py seed_shop

Команду можно запускать повторно — существующие записи не дублируются.
"""

import os
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from app.models import Blog, Category, Product
from app.roles import CLIENT_GROUP, MANAGER_GROUP, add_to_group

CATALOG = {
    ("Шутеры", "Динамичные сетевые и одиночные шутеры от первого и третьего лица."): [
        ("PUBG", "Королевская битва на 100 игроков.", 1299),
        ("Counter-Strike 2", "Легендарный командный тактический шутер.", 1199),
        ("Call of Duty: Modern Warfare III", "Кинематографичная кампания и мультиплеер.", 4499),
        ("Battlefield 2042", "Масштабные сражения до 128 игроков.", 2399),
        ("DOOM Eternal", "Быстрый и жестокий шутер про Палача Рока.", 1899),
    ],
    ("RPG", "Ролевые игры с открытым миром и глубоким сюжетом."): [
        ("The Witcher 3: Wild Hunt", "Приключения ведьмака Геральта.", 999),
        ("Cyberpunk 2077", "Открытый мир Найт-Сити будущего.", 2999),
        ("Baldur's Gate 3", "Пошаговая RPG по правилам D&D.", 3499),
        ("Elden Ring", "Суровый фэнтези-мир от FromSoftware.", 3999),
        ("Skyrim Special Edition", "Северное королевство драконов.", 1499),
    ],
    ("Стратегии", "Глобальные и тактические стратегии в реальном времени и пошаговые."): [
        ("Civilization VI", "Постройте империю, которая выдержит испытание временем.", 1999),
        ("Total War: Warhammer III", "Эпические битвы во вселенной Warhammer.", 3299),
        ("Age of Empires IV", "Классическая RTS в новом исполнении.", 2499),
        ("Stellaris", "Космическая 4X-стратегия.", 1799),
        ("XCOM 2", "Тактическая борьба с инопланетной оккупацией.", 1299),
    ],
    ("Подписки и пополнения", "Подписки на игровые сервисы и карты пополнения кошельков."): [
        ("Xbox Game Pass Ultimate, 1 мес.", "Сотни игр для ПК и консоли.", 1199),
        ("PlayStation Plus Essential, 3 мес.", "Онлайн-игра и ежемесячные игры.", 2499),
        ("Steam Wallet, 1000 ₽", "Карта пополнения кошелька Steam.", 1050),
        ("Nintendo Switch Online, 12 мес.", "Онлайн-игра и классические игры.", 1899),
        ("EA Play, 1 мес.", "Каталог игр Electronic Arts.", 499),
    ],
}

NEWS = [
    ("Открытие нового склада ключей", "Мы расширили ассортимент на 500 позиций.",
     "Благодаря новым партнёрским соглашениям в каталоге появились сотни новых игр. "
     "Все ключи проверены и сопровождаются гарантией активации."),
    ("Осенняя распродажа", "Скидки до 70% на RPG и стратегии.",
     "До конца месяца действуют скидки на популярные ролевые игры и стратегии. "
     "Успейте пополнить библиотеку по выгодной цене."),
    ("Поддержка 24/7", "Техподдержка теперь работает круглосуточно.",
     "Мы запустили круглосуточную поддержку: вопросы по активации ключей решаются в течение 15 минут."),
    ("Подписки Game Pass в наличии", "Пополнили запасы подписок Xbox Game Pass.",
     "Подписки Xbox Game Pass Ultimate снова в наличии. Ключ приходит на e-mail после обработки заказа."),
]

# Демо-учётные записи для проверки ролей (только для учебного стенда).
DEMO_USERS = [
    ("manager", "Manager-Demo-2026", "Менеджер", "manager@cyberkeys.example", MANAGER_GROUP),
    ("client", "Client-Demo-2026", "Клиент", "client@cyberkeys.example", CLIENT_GROUP),
]

PALETTE = [(102, 252, 241), (69, 162, 158), (255, 215, 0), (255, 107, 107)]


def make_cover(path, title, color):
    """Рисует обложку товара (градиент + название), если Pillow доступен."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return False
    w, h = 400, 400
    img = Image.new("RGB", (w, h), (11, 12, 16))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        k = y / h
        draw.line([(0, y), (w, y)], fill=tuple(int(31 + (c - 31) * k * 0.45) for c in color))
    draw.rectangle([10, 10, w - 10, h - 10], outline=color, width=3)
    font = None
    for name in ("arialbd.ttf", "DejaVuSans-Bold.ttf"):
        try:
            font = ImageFont.truetype(name, 30)
            break
        except OSError:
            continue
    font = font or ImageFont.load_default()
    words, lines, line = title.split(), [], ""
    for word in words:
        test = f"{line} {word}".strip()
        if draw.textlength(test, font=font) > w - 60 and line:
            lines.append(line)
            line = word
        else:
            line = test
    lines.append(line)
    y = h // 2 - len(lines) * 20
    for line in lines:
        draw.text(((w - draw.textlength(line, font=font)) / 2, y), line, font=font, fill=(255, 255, 255))
        y += 40
    draw.text((30, h - 50), "КиберКлючи", font=font, fill=color)
    img.save(path)
    return True


class Command(BaseCommand):
    help = "Заполняет каталог, новости и демо-пользователей"

    def handle(self, *args, **options):
        covers_dir = os.path.join(settings.MEDIA_ROOT, "products")
        os.makedirs(covers_dir, exist_ok=True)

        for index, ((cat_name, cat_desc), products) in enumerate(CATALOG.items()):
            category, _ = Category.objects.get_or_create(name=cat_name, defaults={"description": cat_desc})
            color = PALETTE[index % len(PALETTE)]
            for number, (name, short, price) in enumerate(products, 1):
                filename = f"cat{index + 1}_{number}.png"
                image = f"products/{filename}"
                if not make_cover(os.path.join(covers_dir, filename), name, color):
                    image = "temp.jpg"
                product, created = Product.objects.get_or_create(
                    name=name,
                    defaults={
                        "category": category,
                        "short_description": short,
                        "full_description": f"{short}\n\nЦифровой ключ активации. Регион: Россия и СНГ. "
                                            f"Ключ отправляется на e-mail после обработки заказа менеджером.",
                        "price": Decimal(price),
                        "image": image,
                    },
                )
                if not created and product.image.name in ("", "temp.jpg", "banner2.jpg"):
                    product.image = image
                    product.save()

        admin = User.objects.filter(is_superuser=True).order_by("id").first()
        if admin:
            now = timezone.now()
            for days, (title, description, content) in enumerate(NEWS):
                Blog.objects.get_or_create(
                    title=title,
                    defaults={"description": description, "content": content, "author": admin,
                              "posted": now - timedelta(days=days * 3)},
                )

        for username, password, first_name, email, group in DEMO_USERS:
            user, created = User.objects.get_or_create(username=username, defaults={"first_name": first_name, "email": email})
            if created:
                user.set_password(password)
                user.save()
            add_to_group(user, group)

        self.stdout.write(self.style.SUCCESS(
            f"Готово: категорий {Category.objects.count()}, товаров {Product.objects.count()}, "
            f"новостей {Blog.objects.count()}."))
