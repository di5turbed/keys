from django.db import migrations

ROLE_GROUPS = ["Клиент", "Менеджер"]


def create_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    User = apps.get_model('auth', 'User')
    for name in ROLE_GROUPS:
        Group.objects.get_or_create(name=name)
    # Уже зарегистрированные обычные пользователи становятся клиентами.
    clients = Group.objects.get(name="Клиент")
    for user in User.objects.filter(is_superuser=False, groups__isnull=True):
        user.groups.add(clients)


def remove_groups(apps, schema_editor):
    apps.get_model('auth', 'Group').objects.filter(name__in=ROLE_GROUPS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0010_shop_orders'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_groups, remove_groups),
    ]
