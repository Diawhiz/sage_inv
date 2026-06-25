from django.urls import path
from .consumers import ReportConsumer

websocket_urlpatterns = [
    path('ws/reports/', ReportConsumer.as_asgi()),
]
