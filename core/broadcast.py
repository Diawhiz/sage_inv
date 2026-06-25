"""Helpers for pushing report events to connected WebSocket clients."""
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def broadcast_report_event(kind, payload, location):
    """Fan a report event out to the relevant report groups.

    Sent to:
      - ``reports_all``            -> global finance/exec roles
      - ``reports_region_<id>``    -> the location's regional manager
      - ``reports_loc_<id>``       -> users scoped to that location
    """
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    groups = ['reports_all']
    if location is not None:
        groups.append(f'reports_loc_{location.id}')
        if location.region_id:
            groups.append(f'reports_region_{location.region_id}')

    message = {'type': 'report.event', 'kind': kind, 'payload': payload}
    for group in groups:
        async_to_sync(channel_layer.group_send)(group, message)
