"""WebSocket consumer that streams live report events to authorized users."""
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async


class ReportConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get('user')
        if user is None or user.is_anonymous:
            await self.close()
            return

        self.groups_joined = await self.resolve_groups(user)
        if not self.groups_joined:
            await self.close()
            return

        for group in self.groups_joined:
            await self.channel_layer.group_add(group, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        for group in getattr(self, 'groups_joined', []):
            await self.channel_layer.group_discard(group, self.channel_name)

    async def report_event(self, event):
        """Forward a broadcast message to the client."""
        await self.send_json({'kind': event['kind'], 'payload': event['payload']})

    @database_sync_to_async
    def resolve_groups(self, user):
        """Which report groups this user is allowed to listen on."""
        if user.has_location_access:
            return ['reports_all']
        if user.is_regional_manager and user.region_id:
            return [f'reports_region_{user.region_id}']
        if user.is_agent:
            return [f'reports_loc_{lid}' for lid in user.assigned_locations.values_list('id', flat=True)]
        if user.location_id:
            return [f'reports_loc_{user.location_id}']
        return []
