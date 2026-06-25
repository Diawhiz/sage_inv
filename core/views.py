from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, get_user_model
from .models import Region, Location, Vendor, Product, Stock, DeliveryEntry, Expense
from .serializers import (
    RegionSerializer, LocationSerializer, UserSerializer, VendorSerializer,
    ProductSerializer, StockSerializer, DeliveryEntrySerializer, ExpenseSerializer,
)
from .broadcast import broadcast_report_event

User = get_user_model()


def allowed_location_ids(user):
    """Resolve the set of Location ids a user may access, or None for ALL."""
    if user.has_location_access:
        return None  # global roles see everything
    if user.is_regional_manager and user.region_id:
        return list(
            Location.objects.filter(region_id=user.region_id).values_list('id', flat=True)
        )
    if user.is_agent:
        return list(user.assigned_locations.values_list('id', flat=True))
    if user.location_id:
        return [user.location_id]
    return []


def get_location_filtered_queryset(user, queryset, request=None, location_field='location'):
    """Filter queryset by the user's location access level and optional query params."""
    allowed = allowed_location_ids(user)
    if allowed is None:
        # Global access: honor optional explicit filters.
        if request:
            selected = request.query_params.get('location')
            if selected:
                return queryset.filter(**{location_field: selected})
            region = request.query_params.get('region')
            if region:
                return queryset.filter(**{f'{location_field}__region': region})
        return queryset
    if not allowed:
        return queryset.none()
    return queryset.filter(**{f'{location_field}__in': allowed})


def default_location_for(user):
    """The Location a write should be stamped with for a location-restricted user."""
    if user.location_id:
        return user.location_id
    if user.is_agent:
        return user.assigned_locations.values_list('id', flat=True).first()
    return None


def location_save_kwargs(user, serializer):
    """Extra save() kwargs that stamp location for location-restricted users."""
    if not user.has_location_access and not serializer.validated_data.get('location'):
        loc_id = default_location_for(user)
        if loc_id:
            return {'location_id': loc_id}
    return {}


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


class RegionViewSet(viewsets.ModelViewSet):
    serializer_class = RegionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.has_location_access:
            return Region.objects.all()
        if user.is_regional_manager and user.region_id:
            return Region.objects.filter(id=user.region_id)
        if user.location and user.location.region_id:
            return Region.objects.filter(id=user.location.region_id)
        return Region.objects.none()


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        allowed = allowed_location_ids(user)
        if allowed is None:
            qs = Location.objects.all()
            region = self.request.query_params.get('region')
            return qs.filter(region=region) if region else qs
        return Location.objects.filter(id__in=allowed)


class VendorViewSet(viewsets.ModelViewSet):
    serializer_class = VendorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Vendors are a global catalog shared across every location.
        if not self.request.user.can_access_operations:
            return Vendor.objects.none()
        return Vendor.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Products are a global catalog; per-location quantities live on Stock.
        if not self.request.user.can_access_operations:
            return Product.objects.none()
        qs = Product.objects.all()
        vendor_id = self.request.query_params.get('vendor')
        if vendor_id:
            qs = qs.filter(vendor_id=vendor_id)
        return qs

    def perform_create(self, serializer):
        serializer.save()


class StockViewSet(viewsets.ModelViewSet):
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.can_view_stock:
            return Stock.objects.none()
        qs = Stock.objects.all()
        return get_location_filtered_queryset(user, qs, self.request)

    def perform_create(self, serializer):
        serializer.save(updated_by=self.request.user, **location_save_kwargs(self.request.user, serializer))

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        stock = self.get_object()
        serializer = self.get_serializer(stock, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
        return Response(serializer.data)


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
        entry = serializer.save(
            created_by=self.request.user,
            **location_save_kwargs(self.request.user, serializer),
        )
        self._adjust_stock(entry.product_id, entry.location_id, -entry.quantity, self.request.user)
        broadcast_report_event('delivery_created', DeliveryEntrySerializer(entry).data, entry.location)

    def perform_destroy(self, instance):
        # Return the delivered units to the stock row they were taken from.
        self._adjust_stock(instance.product_id, instance.location_id, instance.quantity, None)
        payload = {'id': instance.id}
        location = instance.location
        instance.delete()
        broadcast_report_event('delivery_deleted', payload, location)

    @staticmethod
    def _adjust_stock(product_id, location_id, delta, user):
        """Adjust the quantity of the stock row for this product at this location."""
        qs = Stock.objects.filter(product_id=product_id, location_id=location_id)
        stock = qs.first()
        if stock is None:
            return
        stock.quantity = max(0, stock.quantity + delta)
        if user is not None:
            stock.updated_by = user
        stock.save()


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
        expense = serializer.save(
            created_by=self.request.user,
            **location_save_kwargs(self.request.user, serializer),
        )
        broadcast_report_event('expense_created', ExpenseSerializer(expense).data, expense.location)
