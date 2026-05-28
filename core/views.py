from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, get_user_model
from django.shortcuts import get_object_or_404
from .models import Vendor, Product, Stock, MissingStock
from .serializers import (
    UserSerializer, VendorSerializer, ProductSerializer,
    StockSerializer, MissingStockSerializer
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
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        })
    return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_view(request):
    if not request.user.is_superuser:
        return Response({'error': 'Only superusers can register new users'},
                        status=status.HTTP_403_FORBIDDEN)

    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email', '')

    if not username or not password:
        return Response({'error': 'Username and password required'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, password=password, email=email)
    return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)  # ← added .data


class VendorViewSet(viewsets.ModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]


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
    queryset = MissingStock.objects.all()
    serializer_class = MissingStockSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only superusers can see missing stock
        if not self.request.user.is_superuser:
            return MissingStock.objects.none()
        return super().get_queryset()

    def create(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return Response({'error': 'Superusers only'}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)