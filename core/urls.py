from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from . import views


@api_view(['GET'])
@permission_classes([AllowAny])
def ping(request):
    return Response({'status': 'ok', 'message': 'API is reachable'})


router = DefaultRouter()
router.register(r'regions', views.RegionViewSet, basename='region')
router.register(r'locations', views.LocationViewSet, basename='location')
router.register(r'vendors', views.VendorViewSet, basename='vendor')
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'stock', views.StockViewSet, basename='stock')
router.register(r'deliveries', views.DeliveryEntryViewSet, basename='delivery')
router.register(r'expenses', views.ExpenseViewSet, basename='expense')

urlpatterns = [
    path('auth/login/', views.login_view, name='login'),
    path('auth/register/', views.register_view, name='register'),
    path('user/', views.current_user_view, name='current_user'),
    path('', include(router.urls)),
    path('ping/', ping, name='ping'),
]
