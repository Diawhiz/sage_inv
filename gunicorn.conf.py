"""
Gunicorn configuration for Heroku deployment.
Optimized for Django with proper worker settings.
"""

import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"

# Worker processes - Uvicorn ASGI workers so HTTP + WebSocket (Channels) are served.
# Keep the default low: each worker consumes DB connection slots, and the Aiven
# plan has a tight connection cap. Scale up via WEB_CONCURRENCY only if the DB
# can afford the extra connections.
workers = int(os.environ.get('WEB_CONCURRENCY', 2))
worker_class = "uvicorn.workers.UvicornWorker"

# Timeout settings
timeout = 120
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get('LOG_LEVEL', 'info')

# Process naming
proc_name = "sageinv"

# Server mechanics
daemon = False
pidfile = None

# SSL (handled by Heroku router)
forwarded_allow_ips = '*'
secure_scheme_headers = {
    'X-FORWARDED-PROTOCOL': 'ssl',
    'X-FORWARDED-PROTO': 'https',
    'X-FORWARDED-SSL': 'on'
}

# Preload app for memory efficiency
preload_app = True


def on_starting(server):
    """Called just before the master process is initialized."""
    pass


def on_reload(server):
    """Called when receiving SIGHUP signal."""
    pass


def when_ready(server):
    """Called just after the server is started."""
    pass


def worker_int(worker):
    """Called when a worker receives SIGINT or SIGQUIT."""
    pass


def on_exit(server):
    """Called just before exiting Gunicorn."""
    pass