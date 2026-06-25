from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer

from .models import Region, Location, Vendor, Product, Stock
from .consumers import ReportConsumer

User = get_user_model()

INMEM = {'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'}}


class ScopingTestData(TestCase):
    """Shared fixtures: regions, locations, a shared catalog, per-location stock."""

    @classmethod
    def setUpTestData(cls):
        cls.osho = Region.objects.create(name='Osho')
        cls.lekki = Region.objects.create(name='Lekki')
        cls.osho_a = Location.objects.create(name='Osho Shop A', region=cls.osho)
        cls.osho_b = Location.objects.create(name='Osho Shop B', region=cls.osho)
        cls.lekki_a = Location.objects.create(name='Lekki Shop A', region=cls.lekki)

        # Global catalog: one vendor + one product, used everywhere.
        cls.vilox = Vendor.objects.create(name='Vilox', contact='x', address='y')
        cls.rice = Product.objects.create(name='Vilox Rice', description='', vendor=cls.vilox)

        # Same product, independent stock per location.
        for loc, qty in ((cls.osho_a, 50), (cls.osho_b, 20), (cls.lekki_a, 5)):
            Stock.objects.create(product=cls.rice, location=loc, quantity=qty)

    def auth(self, username, assigned=None, **kwargs):
        kwargs.setdefault('password', 'pass12345!')
        user = User.objects.create_user(username=username, **kwargs)
        if assigned:
            user.assigned_locations.set(assigned)
        client = APIClient()
        client.force_authenticate(user=user)
        return client, user


class CatalogTests(ScopingTestData):
    def test_vendor_and_product_are_global_catalog(self):
        # An agent at one location still sees the shared vendor/product catalog.
        client, _ = self.auth('agent_cat', role='agent', assigned=[self.osho_a])
        self.assertEqual([v['name'] for v in client.get('/api/vendors/').json()], ['Vilox'])
        self.assertEqual([p['name'] for p in client.get('/api/products/').json()], ['Vilox Rice'])

    def test_same_product_holds_independent_stock_per_location(self):
        client, _ = self.auth('ceo_stock', role='ceo')
        rows = client.get('/api/stock/').json()
        by_loc = {r['location_name']: r['quantity'] for r in rows}
        self.assertEqual(by_loc, {'Osho Shop A': 50, 'Osho Shop B': 20, 'Lekki Shop A': 5})


class RoleScopingTests(ScopingTestData):
    def test_cfo_scope_is_finance_and_stock_only(self):
        client, _ = self.auth('cfo', role='cfo')
        # Finance + stock are accessible across all regions...
        self.assertEqual(client.get('/api/stock/').status_code, 200)
        self.assertEqual(client.get('/api/deliveries/').status_code, 200)
        self.assertEqual(client.get('/api/expenses/').status_code, 200)
        # ...but operations (vendors/products management) are not.
        self.assertEqual(client.get('/api/products/').json(), [])
        self.assertEqual(client.get('/api/vendors/').json(), [])

    def test_regional_manager_sees_only_their_region_stock(self):
        client, _ = self.auth('rm', role='regional_manager', region=self.osho)
        names = [s['location_name'] for s in client.get('/api/stock/').json()]
        self.assertCountEqual(names, ['Osho Shop A', 'Osho Shop B'])

    def test_agent_sees_only_assigned_location_stock(self):
        client, _ = self.auth('agent', role='agent', assigned=[self.osho_a])
        rows = client.get('/api/stock/').json()
        self.assertEqual([r['location_name'] for r in rows], ['Osho Shop A'])

    def test_agent_create_stamps_assigned_location(self):
        client, _ = self.auth('agent2', role='agent', assigned=[self.osho_b])
        res = client.post('/api/deliveries/', {
            'vendor': self.vilox.id, 'product': self.rice.id,
            'price': '5.00', 'quantity': 1,
        }, format='json')
        self.assertEqual(res.status_code, 201, res.content)
        self.assertEqual(res.json()['location'], self.osho_b.id)

    def test_delivery_decrements_stock_at_its_location(self):
        client, _ = self.auth('agent3', role='agent', assigned=[self.osho_b])
        client.post('/api/deliveries/', {
            'vendor': self.vilox.id, 'product': self.rice.id,
            'price': '5.00', 'quantity': 3,
        }, format='json')
        # Osho B drops 20 -> 17; other locations untouched.
        self.assertEqual(Stock.objects.get(product=self.rice, location=self.osho_b).quantity, 17)
        self.assertEqual(Stock.objects.get(product=self.rice, location=self.osho_a).quantity, 50)


class MissingStockRemovedTests(ScopingTestData):
    def test_missing_stock_endpoint_gone(self):
        client, _ = self.auth('ceo', role='ceo')
        self.assertEqual(client.get('/api/missing-stock/').status_code, 404)


@override_settings(CHANNEL_LAYERS=INMEM)
class ReportSocketTests(TestCase):
    async def test_cfo_receives_broadcast(self):
        user = await self._make_user()
        communicator = WebsocketCommunicator(ReportConsumer.as_asgi(), '/ws/reports/')
        communicator.scope['user'] = user
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await get_channel_layer().group_send(
            'reports_all',
            {'type': 'report.event', 'kind': 'delivery_created', 'payload': {'id': 1}},
        )
        msg = await communicator.receive_json_from()
        self.assertEqual(msg['kind'], 'delivery_created')
        self.assertEqual(msg['payload']['id'], 1)
        await communicator.disconnect()

    @staticmethod
    async def _make_user():
        from channels.db import database_sync_to_async
        return await database_sync_to_async(User.objects.create_user)(
            username='cfo_ws', password='pass12345!', role='cfo',
        )
