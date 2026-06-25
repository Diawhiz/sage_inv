web: gunicorn sage_inv.asgi:application -k uvicorn.workers.UvicornWorker --config gunicorn.conf.py
release: python manage.py migrate --noinput && python manage.py collectstatic --noinput
