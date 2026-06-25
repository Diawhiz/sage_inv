from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('', TemplateView.as_view(template_name='login.html'), name='login'),
    path('dashboard/', TemplateView.as_view(template_name='dashboard.html'), name='dashboard'),
    path('vendors/', TemplateView.as_view(template_name='vendors.html'), name='vendors'),
    path('products/', TemplateView.as_view(template_name='products.html'), name='products'),
    path('stock/', TemplateView.as_view(template_name='stock.html'), name='stock'),
    path('report/', TemplateView.as_view(template_name='report.html'), name='report'),
]
