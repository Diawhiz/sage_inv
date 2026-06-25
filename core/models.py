from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
import datetime


class Region(models.Model):
    """A geographic region (e.g. Osho) that groups several locations."""
    name = models.CharField(max_length=200, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Location(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True, default="")
    contact = models.CharField(max_length=200, blank=True, default="")
    region = models.ForeignKey(
        Region,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='locations',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class User(AbstractUser):
    ROLE_CHOICES = [
        ('ceo', 'CEO'),
        ('coo', 'COO'),
        ('cto', 'CTO'),
        ('cfo', 'CFO'),
        ('regional_manager', 'Regional Manager'),
        ('manager', 'Manager'),
        ('agent', 'Agent'),
        ('staff', 'Staff'),
    ]

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='core_user_set',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='core_user_permissions_set',
        blank=True
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    region = models.ForeignKey(
        Region,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managers',
        help_text='Region this user is in charge of (Regional Manager).',
    )
    assigned_locations = models.ManyToManyField(
        Location,
        blank=True,
        related_name='assigned_users',
        help_text='Specific locations an Agent is allowed to access.',
    )

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    # --- Role identity (each property is True for that role or anyone above it) ---
    @property
    def is_ceo(self):
        return self.role == 'ceo' or self.is_superuser

    @property
    def is_coo(self):
        return self.role == 'coo' or self.is_ceo

    @property
    def is_cto(self):
        return self.role == 'cto' or self.is_ceo

    @property
    def is_cfo(self):
        return self.role == 'cfo' or self.is_ceo

    @property
    def is_regional_manager(self):
        return self.role == 'regional_manager'

    @property
    def is_manager(self):
        return self.role == 'manager' or self.is_coo or self.is_cto

    @property
    def is_agent(self):
        return self.role == 'agent'

    # --- Access scope ---
    @property
    def has_location_access(self):
        """True if the user can access data from ALL locations/regions."""
        return self.is_ceo or self.is_coo or self.is_cto or self.is_cfo

    @property
    def can_access_operations(self):
        """Vendors, Products, Stock, Deliveries."""
        return (
            self.is_ceo or self.is_coo or self.is_manager
            or self.is_regional_manager or self.is_agent
        )

    @property
    def can_access_calculations(self):
        """Reports, Expenses, Payment-related (finance) data."""
        return (
            self.is_ceo or self.is_cto or self.is_cfo
            or self.is_manager or self.is_regional_manager
        )

    @property
    def can_view_stock(self):
        """Stock visibility. CFO gets stock alongside finance."""
        return self.can_access_operations or self.is_cfo

    @property
    def can_register_users(self):
        return self.is_ceo or self.is_superuser


class Vendor(models.Model):
    name = models.CharField(max_length=200)
    contact = models.CharField(max_length=100)
    address = models.TextField()
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='vendors',
        null=True,
        blank=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='products')
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='products',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Stock(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='stock')
    quantity = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='stock_entries',
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['product__name']

    def __str__(self):
        return f"{self.product.name} - {self.quantity} units"


class DeliveryEntry(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='deliveries')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='deliveries')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity = models.PositiveIntegerField(default=1)
    rider = models.CharField(max_length=200, blank=True)
    delivery_location = models.CharField(max_length=300, blank=True)
    date = models.DateField(default=datetime.date.today)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='deliveries',
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.product.name} x{self.quantity} on {self.date}"


class Expense(models.Model):
    description = models.CharField(max_length=300)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=datetime.date.today)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='expenses',
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.description}: {self.amount}"
