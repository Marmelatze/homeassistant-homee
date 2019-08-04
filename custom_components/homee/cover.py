"""
Support for Homee sensors.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.homee/
"""
import logging

from homeassistant.components.cover import (
    CoverDevice, ENTITY_ID_FORMAT)
from custom_components.homee import (
    HOMEE_NODES, HOMEE_ATTRIBUTES, HOMEE_CUBE, HomeeDevice)

DEPENDENCIES = ['homee']

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Perform the setup for Vera controller devices."""
    devices = []
    for attribute in HOMEE_ATTRIBUTES['cover']:
        devices.append(HomeeCover(hass, HOMEE_NODES[attribute.node_id], attribute, HOMEE_CUBE))
    async_add_devices(devices)

class HomeeCover(HomeeDevice, CoverDevice):
    """Representation of a Homee Cover."""

    def __init__(self, homee_node, homee_attribute, cube):
        """Initialize the cover."""
        self.attribute_id = homee_attribute.id
        self.position = homee_attribute.value
        HomeeDevice.__init__(self, hass, homee_node, cube)
        self.entity_id = ENTITY_ID_FORMAT.format(self.homee_id)
        self.update_state(homee_attribute)

    def update_state(self, attribute):
        """Update the state."""
        if self.attribute_id == attribute.id:
            _LOGGER.info("Attribute value: %s", attribute.value)
            self.position = attribute.value

    @property
    def current_cover_position(self):
        """
        Return current position of cover.

        0 is closed, 100 is fully open.
        """
        if self.position <= 5:
            return 100
        if self.position >= 95:
            return 0
        return (self.position-100)*-1

    async def async_set_cover_position(self, position, **kwargs):
        """Move the cover to a specific position."""
        await self.cube.send_node_command(self._homee_node, self.homee_attribute, position)

    @property
    def is_closed(self):
        """Return if the cover is closed."""
        if self.current_cover_position is not None:
            if self.current_cover_position > 0:
                return False
            else:
                return True

    async def async_open_cover(self, **kwargs):
        """Open the cover."""
        await self.cube.send_node_command(self._homee_node, self.homee_attribute, 0)

    async def async_close_cover(self, **kwargs):
        """Close the cover."""
        await self.cube.send_node_command(self._homee_node, self.homee_attribute, 100)

    def stop_cover(self, **kwargs):
        """Stop the cover."""
        pass
