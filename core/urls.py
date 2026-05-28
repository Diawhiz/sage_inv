from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([AllowAny])
def ping(request):
    return Response({'status': 'ok', 'message': 'API is reachable'})

router = DefaultRouter()
router.register(r'vendors', views.VendorViewSet, basename='vendor')
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'stock', views.StockViewSet, basename='stock')
router.register(r'missing-stock', views.MissingStockViewSet, basename='missing-stock')

urlpatterns = [
    path('auth/login/', views.login_view, name='login'),
    path('auth/register/', views.register_view, name='register'),
    path('', include(router.urls)),
    path('ping/', ping, name='ping'),
]