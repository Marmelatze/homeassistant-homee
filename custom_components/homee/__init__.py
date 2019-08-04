"""
Support for Homee

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/homee/
"""
import asyncio
import logging
from collections import defaultdict

import voluptuous as vol

from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import discovery
from homeassistant.helpers.entity import Entity
from homeassistant.util import (slugify)
from .util import get_attr_by_type, get_attr_type

REQUIREMENTS = ['pyhomee==0.0.4']

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'homee'

HOMEE_CUBE = None

# attributes that are not added as sensors
DISCOVER_SENSOR_ATTRIBUTES = [
    'DimmingLevel',
    'OnOff',
    'Color',
    'OpenClose',
    'Temperature',
    'TargetTemperature',
    'BatteryLowAlarm',
    'LinkQuality',
    'IdentificationMode',
    'SoftwareRevision'
]

CONF_CUBE = 'cube'
CONF_USERNAME = 'username'
CONF_PASSWORD = 'password'

HOMEE_ID_FORMAT = '{}_{}'

HOMEE_NODES = {}
HOMEE_ATTRIBUTES = defaultdict(list)

HOMEE_IMPORT_GROUP = 'HASS'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_CUBE): cv.string,
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
    }),
}, extra=vol.ALLOW_EXTRA)

HOMEE_COMPONENTS = [
    'sensor', 'switch', 'light', 'cover', 'climate', 'binary_sensor', 'homee'
]


async def async_setup(hass, base_config):
    """Set up for Vera devices."""
    global HOMEE_CUBE
    from pyhomee import HomeeCube
    task = None

    def stop_subscription(event):
        """Shutdown Homee subscriptions and subscription thread on exit."""
        _LOGGER.info("Shutting down homee websocket")
        if task is not None:
            task.cancel()

    async def play_homeegram(call):
        id = call.data.get("homeegram_id")
        await HOMEE_CUBE.play_homeegram(id)

    async def set_mode(call):
        mode = call.data.get("mode")
        component = hass.get_component("homee.cube")
        await component.set_mode(mode)


    config = base_config.get(DOMAIN)

    # Get Homee specific configuration.
    hostname = config.get(CONF_CUBE)
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    hass.services.async_register(DOMAIN, "play_homeegram", play_homeegram)
    #hass.services.async_register(DOMAIN, "set_mode", set_mode)

    # Initialize the Homee Cube
    HOMEE_CUBE = HomeeCube(hostname, username, password)
    HOMEE_CUBE.register_all(create_handle_node_callback(hass, base_config))
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, stop_subscription)

    task = asyncio.get_event_loop().create_task(HOMEE_CUBE.run())

    #hass.services.async_register(DOMAIN, "set_mode", set_mode)



    return True


def create_handle_node_callback(hass, base_config):
    @callback
    async def handle_node_callback(node):
        if node.id in HOMEE_NODES:
            return
        _LOGGER.info("Discovered new node %s: %s" % (node.id, node.name))
        HOMEE_NODES[node.id] = node
        devices = defaultdict(list)
        node_type = map_homee_node(node)
        if node_type:
            devices[node_type].append({'node': node})
        for attribute in node.attributes:
            if get_attr_type(attribute) not in DISCOVER_SENSOR_ATTRIBUTES and node.id != -1:
                devices['sensor'].append({'node': node, 'attribute': attribute})

        discover_routines = []
        for component in HOMEE_COMPONENTS:
            if len(devices[component]) > 0:
                hass.async_create_task(discovery.async_load_platform(hass, component, DOMAIN, {
                    'devices': devices[component],
                }, base_config))
        #asyncio.gather(*discover_routines))
    return handle_node_callback


def map_homee_node(node):
    """Map homee nodes to Home Assistant types."""
    from pyhomee import const
    if node.id == -1:
        return 'sensor'
    if node.profile in const.PROFILE_TYPES[const.DISCOVER_LIGHTS]:
        return 'light'
    if node.profile in const.PROFILE_TYPES[const.DISCOVER_CLIMATE]:
        return 'climate'
    if node.profile in const.PROFILE_TYPES[const.DISCOVER_BINARY_SENSOR]:
        return 'binary_sensor'
    if node.profile in const.PROFILE_TYPES[const.DISCOVER_SWITCH]:
        return 'switch'

    attr_types = [attr.type for attr in node.attributes]
    if const.COVER_POSITION in attr_types:
        return 'cover'

class HomeeDevice(Entity):
    """Representation of a Homee device entity."""

    def __init__(self, hass, homee_node, cube):
        """Initialize the device."""
        self._homee_node = homee_node
        self.cube = cube

        self._name = self._homee_node.name
        # Append device id to prevent name clashes in HA.
        if self._homee_node.id == -1:
            self.homee_id = "homee"
        else:
            self.homee_id = HOMEE_ID_FORMAT.format(
                slugify(self._name), self._homee_node.id)
        self.attributes = dict()
        for attribute in homee_node.attributes:
            attr_type = get_attr_type(attribute)
            self.attributes[attr_type] = attribute

        self.cube.register(self._homee_node, self._update_callback)

    async def _update_callback(self, node, attribute):
        """Update the state."""
        if node is not None:
            self._homee_node = node
        if attribute is not None:
            attr_type = get_attr_type(attribute)
            self.attributes[attr_type] = attribute

            self.update_state(attribute)
        return self.async_schedule_update_ha_state()

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def should_poll(self):
        return False

    @property
    def available(self):
        from pyhomee.const import CANodeStateAvailable
        return self._homee_node.state == CANodeStateAvailable

    def get_attr_value(self, attr_type, default=None):
        attr = self.get_attr(attr_type)
        if attr is None:
            return default
        return attr.value

    def get_attr(self, attr_type):
        return self.attributes.get(attr_type)

    def has_attr(self, attr_type):
        return attr_type in self.attributes

    async def set_attr(self, attr_type, value):
        await self.cube.send_node_command(self._homee_node, self.get_attr(attr_type), value)

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        attr = {}
        for attr_type, attribute in self.attributes.items():
            attr[attr_type] = attribute.value
        if self.has_attr('BatteryLowAlarm'):
            attr['battery_level'] = 100 if self.get_attr_value('BatteryLowAlarm', 0) == 0 else 0

        return attr

    def update_state(self, attribute):
        pass
