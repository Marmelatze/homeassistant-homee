"""
Support for Homee sensors.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.homee/
"""
import logging
import re

from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import ENTITY_ID_FORMAT
from custom_components.homee import (
    HomeeDevice, HOMEE_ATTRIBUTES, HOMEE_CUBE)
from homeassistant.util import slugify
from homee import get_attr_type

DEPENDENCIES = ['homee']

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Perform the setup for Homee controller devices."""
    devices = []
    for data in discovery_info['devices']:
        devices.append(HomeeSensor(data.get('node'), data.get('attribute'), HOMEE_CUBE))
    add_devices(devices)


class HomeeSensor(HomeeDevice, Entity):
    """Representation of a Homee Sensor."""

    def __init__(self, homee_node, homee_attribute, cube):
        """Initialize the sensor."""
        self.homee_attribute = homee_attribute
        self.current_value = homee_attribute.value
        self.attribute_id = homee_attribute.id

        HomeeDevice.__init__(self, homee_node, cube)
        self._name = "{} {}".format(self._homee_node.name, re.sub("([a-z])([A-Z])", "\g<1> \g<2>", get_attr_type(homee_attribute)))
        self.entity_id = ENTITY_ID_FORMAT.format("{}_{}_{}".format(self.homee_id, slugify(get_attr_type(homee_attribute)), homee_attribute.id))

    @property
    def state(self):
        """Return the name of the sensor."""
        return self.current_value

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        if self.homee_attribute.unit == "n/a":
            return None
        return self.homee_attribute.unit

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        attr = {}

        return attr

    def update_state(self, attribute):
        """Update the state."""
        if self.attribute_id == attribute.id:
            self.current_value = attribute.value
