"""
Support for HomeMatic binary sensors.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.homee/
"""
import logging
from homeassistant.components.binary_sensor import BinarySensorDevice
from custom_components.homee import HOMEE_CUBE, HomeeDevice

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['homee']

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Perform the setup for Vera controller devices."""
    devices = []
    for data in discovery_info['devices']:
        devices.append(HomeeBinarySensor(data['node'], HOMEE_CUBE))
    add_devices(devices)

class HomeeBinarySensor(HomeeDevice, BinarySensorDevice):

    def __init__(self, homee_node, cube):
        HomeeDevice.__init__(self, homee_node, cube)

    @property
    def is_on(self):
        return self.get_attr_value('OpenClose', False)

    @property
    def device_class(self):
        return 'opening'

    def update_state(self, attribute):
        """"""
