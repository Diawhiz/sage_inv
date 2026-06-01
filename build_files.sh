#!/bin/bash
set -e
pip install --break-system-packages -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='Bright').exists():
    User.objects.create_superuser('Bright', '', 'Bright@25')
    print('Superuser created.')
else:
    print('Superuser already exists.')
"
