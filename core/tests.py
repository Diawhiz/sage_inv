from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer

from .models import Region, Location, Vendor, Product
from .consumers import ReportConsumer

User = get_user_model()

INMEM = {'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'}}


class ScopingTestData(TestCase):
    """Shared fixtures: two regions, locations, and one product per location."""

    @classmethod
    def setUpTestData(cls):
        cls.osho = Region.objects.create(name='Osho')
        cls.lekki = Region.objects.create(name='Lekki')
        cls.osho_a = Location.objects.create(name='Osho Shop A', region=cls.osho)
        cls.osho_b = Location.objects.create(name='Osho Shop B', region=cls.osho)
        cls.lekki_a = Location.objects.create(name='Lekki Shop A', region=cls.lekki)

        for loc in (cls.osho_a, cls.osho_b, cls.lekki_a):
            v = Vendor.objects.create(name=f'V-{loc.name}', contact='x', address='y', location=loc)
            Product.objects.create(name=f'P-{loc.name}', description='', vendor=v, location=loc)

    def auth(self, username, assigned=None, **kwargs):
        kwargs.setdefault('password', 'pass12345!')
        user = User.objects.create_user(username=username, **kwargs)
        if assigned:
            user.assigned_locations.set(assigned)
        client = APIClient()
        client.force_authenticate(user=user)
        return client, user


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

    def test_regional_manager_sees_only_their_region(self):
        client, _ = self.auth('rm', role='regional_manager', region=self.osho)
        names = [p['location_name'] for p in client.get('/api/products/').json()]
        self.assertCountEqual(names, ['Osho Shop A', 'Osho Shop B'])

    def test_agent_sees_only_assigned_locations(self):
        client, _ = self.auth('agent', role='agent', assigned=[self.osho_a])
        rows = client.get('/api/products/').json()
        self.assertEqual([r['location_name'] for r in rows], ['Osho Shop A'])

    def test_agent_create_stamps_assigned_location(self):
        client, _ = self.auth('agent2', role='agent', assigned=[self.osho_b])
        vendor = Vendor.objects.filter(location=self.osho_b).first()
        res = client.post('/api/products/', {
            'name': 'New', 'description': 'd', 'price': '5.00', 'vendor': vendor.id,
        }, format='json')
        self.assertEqual(res.status_code, 201, res.content)
        self.assertEqual(res.json()['location'], self.osho_b.id)


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
