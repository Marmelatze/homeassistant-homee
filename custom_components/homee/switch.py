"""
Support for Homee sensors.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.homee/
"""
import logging

from homeassistant.components.switch import ENTITY_ID_FORMAT, SwitchDevice
from homeassistant.util import slugify
from custom_components.homee import (
    HOMEE_CUBE, HomeeDevice)

DEPENDENCIES = ['homee']

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Perform the setup for Vera controller devices."""
    devices = []
    for data in discovery_info['devices']:
        from pyhomee import const
        node = data['node']
        # handle double switch
        if node.profile == const.CANodeProfileDoubleOnOffSwitch:
            state_attributes = list(filter(lambda a: a.type == const.ATTRIBUTE_TYPES['OnOff'], node.attributes))
            for idx, attr in enumerate(state_attributes):
                devices.append(HomeeSwitch(node, HOMEE_CUBE, idx, attr))
        else:
            devices.append(HomeeSwitch(node, HOMEE_CUBE))
    add_devices(devices)

class HomeeSwitch(HomeeDevice, SwitchDevice):
    """Representation of a Homee Switch."""

    def __init__(self, homee_node, cube, idx=0, state_attr=None):
        """Initialize the switch."""
        HomeeDevice.__init__(self, homee_node, cube)
        if state_attr is not None:
            self._state_attr = state_attr
            # make sure OnOff attribute is the selected
            self.homee_id = "{}_{}_{}".format(slugify(self._name), self._homee_node.id, state_attr.id)
            self._name = "{} {}".format(self._name, idx + 1)
        else:
            self._state_attr = self.get_attr("OnOff")
        self.entity_id = ENTITY_ID_FORMAT.format(self.homee_id)
        _LOGGER.info(self.entity_id)
        self._state = False
        self.update_state(self._state_attr)

    def update_state(self, attribute):
        """Update the state."""
        if attribute.id == self._state_attr.id:
            self._state = attribute.value


    def turn_on(self, **kwargs):
        """Turn device on."""
        self.cube.send_node_command(self._homee_node, self._state_attr, 1)

    def turn_off(self, **kwargs):
        """Turn device off."""
        self.cube.send_node_command(self._homee_node, self._state_attr, 0)

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

