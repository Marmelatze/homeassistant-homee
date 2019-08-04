"""
Support for HomeMatic binary sensors.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.homee/
"""
import asyncio
import logging
from homeassistant.components.binary_sensor import BinarySensorDevice
from custom_components.homee import HOMEE_CUBE, HomeeDevice

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['homee']


async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Perform the setup for Vera controller devices."""
    devices = []
    for data in discovery_info['devices']:
        devices.append(HomeeBinarySensor(hass, data['node'], HOMEE_CUBE))
    async_add_devices(devices)


class HomeeBinarySensor(HomeeDevice, BinarySensorDevice):

    def __init__(self, hass, homee_node, cube):
        HomeeDevice.__init__(self, hass, homee_node, cube)

    @property
    def is_on(self):
        return self.get_attr_value('OpenClose', False)

    @property
    def device_class(self):
        return 'opening'

    def update_state(self, attribute):
        """"""
