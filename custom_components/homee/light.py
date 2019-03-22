"""
Support for Homee sensors.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.homee/
"""
import logging

from homeassistant.components.light import (
    ATTR_BRIGHTNESS, ENTITY_ID_FORMAT,
    SUPPORT_BRIGHTNESS, SUPPORT_COLOR, Light)
from custom_components.homee import (
    HOMEE_NODES, HOMEE_ATTRIBUTES, HOMEE_CUBE, HomeeDevice)

DEPENDENCIES = ['homee']

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Perform the setup for Vera controller devices."""
    devices = []
    for attribute in HOMEE_ATTRIBUTES['light']:
        devices.append(HomeeLight(HOMEE_NODES[attribute.node_id], HOMEE_CUBE))
    add_devices(devices)


class HomeeLight(HomeeDevice, Light):
    """Representation of a Homee Light."""

    def __init__(self, homee_node, cube):
        """Initialize the switch."""
        HomeeDevice.__init__(self, homee_node, cube)
        self.entity_id = ENTITY_ID_FORMAT.format(self.homee_id)

    def update_state(self, attribute):
        """"""

    def turn_on(self, **kwargs):
        """Turn device on."""
        if ATTR_BRIGHTNESS in kwargs and self.has_attr('DimmingLevel'):
            self.cube.send_node_command(self._homee_node, self.get_attr('DimmingLevel'),
                                        (kwargs[ATTR_BRIGHTNESS] / 255) * 100)
        else:
            self.cube.send_node_command(self._homee_node, self.get_attr('OnOff'), 1)

    def turn_off(self, **kwargs):
        """Turn device off."""
        self.cube.send_node_command(self._homee_node, self.get_attr('OnOff'), 0)

    @property
    def is_on(self):
        """Return true if device is on."""
        return self.get_attr_value('OnOff', False)

    @property
    def brightness(self):
        """Return the brightness of the light."""
        return (self.get_attr_value('DimmingLevel') / 100) * 255

    @property
    def rgb_color(self):
        """Return the color of the light."""
        return self.get_attr_value('Color')

    @property
    def supported_features(self):
        """Flag supported features."""
        if self.has_attr('Color'):
            return SUPPORT_BRIGHTNESS | SUPPORT_COLOR
        return SUPPORT_BRIGHTNESS
