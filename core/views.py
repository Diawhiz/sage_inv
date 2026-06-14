from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, get_user_model
from .models import Location, Vendor, Product, Stock, MissingStock, MissingStockLog, DeliveryEntry, Expense
from .serializers import (
    LocationSerializer, UserSerializer, VendorSerializer, ProductSerializer,
    StockSerializer, MissingStockSerializer, DeliveryEntrySerializer, ExpenseSerializer,
)

User = get_user_model()


def get_location_filtered_queryset(user, queryset, request=None, location_field='location'):
    """Filter queryset by user's location access level and optional query param."""
    if user.has_location_access and request:
        selected = request.query_params.get('location')
        if selected:
            return queryset.filter(**{location_field: selected})
        return queryset
    if user.location:
        return queryset.filter(**{location_field: user.location})
    return queryset.none()


def set_location_from_user(user, serializer, data):
    """Auto-assign location from user if user is location-restricted."""
    if not user.has_location_access and user.location:
        data['location'] = user.location.id
    return data


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response(
            {'error': 'Username and password required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(username=username, password=password)
    if user:
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
        })
    return Response(
        {'error': 'Invalid credentials'},
        status=status.HTTP_401_UNAUTHORIZED
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_view(request):
    if not request.user.can_register_users:
        return Response(
            {'error': 'Only CEOs and superusers can register new users'},
            status=status.HTTP_403_FORBIDDEN
        )

    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email', '')
    role = request.data.get('role', 'staff')
    location_id = request.data.get('location')

    if not username or not password:
        return Response(
            {'error': 'Username and password required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if User.objects.filter(username=username).exists():
        return Response(
            {'error': 'Username already exists'},
            status=status.HTTP_400_BAD_REQUEST
        )

    location = None
    if location_id:
        try:
            location = Location.objects.get(id=location_id)
        except Location.DoesNotExist:
            return Response(
                {'error': 'Location not found'},
                status=status.HTTP_400_BAD_REQUEST
            )

    user = User.objects.create_user(
        username=username,
        password=password,
        email=email,
        role=role,
        location=location,
    )
    return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user_view(request):
    return Response(UserSerializer(request.user).data)


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.has_location_access:
            return Location.objects.all()
        if user.location:
            return Location.objects.filter(id=user.location.id)
        return Location.objects.none()


class VendorViewSet(viewsets.ModelViewSet):
    serializer_class = VendorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.can_access_operations:
            return Vendor.objects.none()
        qs = Vendor.objects.all()
        return get_location_filtered_queryset(user, qs, self.request)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.can_access_operations:
            return Product.objects.none()
        qs = Product.objects.all()
        vendor_id = self.request.query_params.get('vendor')
        if vendor_id:
            qs = qs.filter(vendor_id=vendor_id)
        return get_location_filtered_queryset(user, qs, self.request)


class StockViewSet(viewsets.ModelViewSet):
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.can_access_operations:
            return Stock.objects.none()
        qs = Stock.objects.all()
        return get_location_filtered_queryset(user, qs, self.request)

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
        user = self.request.user
        if not user.can_access_missing_stock:
            return MissingStock.objects.none()
        qs = MissingStock.objects.prefetch_related('logs').all()
        return get_location_filtered_queryset(user, qs, self.request)

    def create(self, request, *args, **kwargs):
        if not request.user.can_access_missing_stock:
            return Response(
                {'error': 'CEO and COO only'},
                status=status.HTTP_403_FORBIDDEN
            )
        response = super().create(request, *args, **kwargs)
        instance = MissingStock.objects.get(pk=response.data['id'])
        MissingStockLog.objects.create(
            missing_stock=instance,
            quantity=instance.quantity_missing,
            note='Initial report',
            updated_by=request.user,
            location=instance.location,
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
                location=updated.location,
            )


class DeliveryEntryViewSet(viewsets.ModelViewSet):
    serializer_class = DeliveryEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.can_access_calculations and not user.can_access_operations:
            return DeliveryEntry.objects.none()
        qs = DeliveryEntry.objects.select_related('vendor', 'product', 'created_by')
        date = self.request.query_params.get('date')
        if date:
            qs = qs.filter(date=date)
        return get_location_filtered_queryset(user, qs, self.request)

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
        user = self.request.user
        if not user.can_access_calculations and not user.can_access_operations:
            return Expense.objects.none()
        qs = Expense.objects.all()
        date = self.request.query_params.get('date')
        if date:
            qs = qs.filter(date=date)
        return get_location_filtered_queryset(user, qs, self.request)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
