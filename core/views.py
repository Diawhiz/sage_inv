from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, get_user_model
from .models import Vendor, Product, Stock, MissingStock, MissingStockLog, DeliveryEntry, Expense
from .serializers import (
    UserSerializer, VendorSerializer, ProductSerializer,
    StockSerializer, MissingStockSerializer, DeliveryEntrySerializer, ExpenseSerializer,
)

User = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({'error': 'Username and password required'}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=username, password=password)
    if user:
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user': UserSerializer(user).data})
    return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_view(request):
    if not request.user.is_superuser:
        return Response({'error': 'Only superusers can register new users'}, status=status.HTTP_403_FORBIDDEN)

    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email', '')

    if not username or not password:
        return Response({'error': 'Username and password required'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, password=password, email=email)
    return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class VendorViewSet(viewsets.ModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Product.objects.all()
        vendor_id = self.request.query_params.get('vendor')
        if vendor_id:
            qs = qs.filter(vendor_id=vendor_id)
        return qs


class StockViewSet(viewsets.ModelViewSet):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(updated_by=self.request.user)

    def update(self, request, *args, **kwargs):
        stock = self.get_object()
        stock.quantity = request.data.get('quantity', stock.quantity)
        stock.updated_by = request.user
        stock.save()
        return Response(self.get_serializer(stock).data)


class MissingStockViewSet(viewsets.ModelViewSet):
    serializer_class = MissingStockSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_superuser:
            return MissingStock.objects.none()
        return MissingStock.objects.prefetch_related('logs').all()

    def create(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return Response({'error': 'Superusers only'}, status=status.HTTP_403_FORBIDDEN)
        response = super().create(request, *args, **kwargs)
        instance = MissingStock.objects.get(pk=response.data['id'])
        MissingStockLog.objects.create(
            missing_stock=instance,
            quantity=instance.quantity_missing,
            note='Initial report',
            updated_by=request.user,
        )
        return response

    def perform_update(self, serializer):
        old_qty = serializer.instance.quantity_missing
        updated = serializer.save()
        if updated.quantity_missing != old_qty:
            MissingStockLog.objects.create(
                missing_stock=updated,
                quantity=updated.quantity_missing,
                note=self.request.data.get('note', ''),
                updated_by=self.request.user,
            )


class DeliveryEntryViewSet(viewsets.ModelViewSet):
    serializer_class = DeliveryEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = DeliveryEntry.objects.select_related('vendor', 'product', 'created_by')
        date = self.request.query_params.get('date')
        if date:
            qs = qs.filter(date=date)
        return qs

    def perform_create(self, serializer):
        entry = serializer.save(created_by=self.request.user)
        try:
            stock = Stock.objects.get(product=entry.product)
            stock.quantity = max(0, stock.quantity - entry.quantity)
            stock.updated_by = self.request.user
            stock.save()
        except Stock.DoesNotExist:
            pass

    def perform_destroy(self, instance):
        # Restore stock when a delivery entry is deleted
        try:
            stock = Stock.objects.get(product=instance.product)
            stock.quantity += instance.quantity
            stock.save()
        except Stock.DoesNotExist:
            pass
        instance.delete()


class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Expense.objects.all()
        date = self.request.query_params.get('date')
        if date:
            qs = qs.filter(date=date)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
