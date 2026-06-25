"""Custom data for the Unfold admin dashboard."""
from datetime import date

from django.db.models import Sum
from django.utils.translation import gettext_lazy as _

from .models import Region, Location, Product, DeliveryEntry, Expense


def dashboard_callback(request, context):
    """Inject KPI cards rendered by templates/admin/index.html."""
    today = date.today()
    expenses_today = Expense.objects.filter(date=today).aggregate(t=Sum('amount'))['t'] or 0

    context["dashboard_cards"] = [
        {"title": _("Regions"), "value": Region.objects.count(), "icon": "map"},
        {"title": _("Locations"), "value": Location.objects.count(), "icon": "location_on"},
        {"title": _("Products"), "value": Product.objects.count(), "icon": "inventory_2"},
        {"title": _("Deliveries today"),
         "value": DeliveryEntry.objects.filter(date=today).count(),
         "icon": "local_shipping"},
        {"title": _("Expenses today"), "value": f"₦{expenses_today:,.2f}", "icon": "payments"},
    ]
    return context
