import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth.models import User
from polls.models import UserProfile

# Профили
for user in User.objects.all():
    UserProfile.objects.get_or_create(user=user)
    print(f'Создан профиль для пользователя: {user.username}')

print('Готово!')