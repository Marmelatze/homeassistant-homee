"""
Support for Homee

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/homee/
"""
import logging
from collections import defaultdict

import voluptuous as vol

from requests.exceptions import RequestException

from homeassistant.util.dt import utc_from_timestamp
from homeassistant.util import (convert, slugify)
from homeassistant.helpers import discovery
from homeassistant.helpers import config_validation as cv
from homeassistant.const import (
    ATTR_ARMED, ATTR_BATTERY_LEVEL, ATTR_LAST_TRIP_TIME, ATTR_TRIPPED,
    EVENT_HOMEASSISTANT_STOP)
from homeassistant.helpers.entity import Entity
from pyhomee.const import CANodeStateAvailable, ATTRIBUTE_TYPES
from .util import get_attr_by_type, get_attr_type

REQUIREMENTS = ['https://github.com/Marmelatze/pyhomee/archive/v0.0.3.zip#pyhomee==0.0.2']

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
    'sensor', 'switch', 'light', 'cover', 'climate', 'binary_sensor'
]

SERVICE_PLAY_HOMEEGRAM = 'play_homeegram'
SERVICE_DESCRIPTIONS = {
    "play_homeegram": {
        "description": "Play Homeegram",
        "fields": {
            "homeegram_id": {
                "description": "The homeegram id",
                "example": "27",
            },
        },
    },
}


# pylint: disable=unused-argument, too-many-function-args
def setup(hass, base_config):
    """Set up for Vera devices."""
    global HOMEE_CUBE
    from pyhomee import HomeeCube
    from pyhomee import const

    def stop_subscription(event):
        """Shutdown Homee subscriptions and subscription thread on exit."""
        _LOGGER.info("Shutting down subscriptions")
        HOMEE_CUBE.stop()

    def play_homeegram(call):
        id = call.data.get("homeegram_id")
        HOMEE_CUBE.play_homeegram(id)

    config = base_config.get(DOMAIN)

    # Get Homee specific configuration.
    hostname = config.get(CONF_CUBE)
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)

    # Initialize the Homee Cube
    HOMEE_CUBE = HomeeCube(hostname, username, password)
    hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, stop_subscription)

    #hass.services.register(DOMAIN, SERVICE_PLAY_HOMEEGRAM, play_homeegram)

    try:
        all_nodes = HOMEE_CUBE.get_nodes()
    except RequestException:
        # There was a network related error connecting to the Vera controller.
        _LOGGER.exception("Error communicating with Homee")
        return False

    group = HOMEE_CUBE.get_group_by_name(HOMEE_IMPORT_GROUP)
    if group:
        group_node_ids = HOMEE_CUBE.get_group_node_ids(group.id)
        nodes = [node for node in all_nodes if node.id in group_node_ids]
    else:
        nodes = all_nodes

    devices = get_devices(nodes)

    for component in HOMEE_COMPONENTS:
        discovery.load_platform(hass, component, DOMAIN, {
            'devices': devices[component]
        }, base_config)

    return True

def get_devices(nodes):
    """Get HASS devices form homee nodes"""
    devices = defaultdict(list)
    for node in nodes:
        HOMEE_NODES[node.id] = node
        node_type = map_homee_node(node)
        if node_type:
            devices[node_type].append({'node': node})
        for attribute in node.attributes:
            if get_attr_type(attribute) not in DISCOVER_SENSOR_ATTRIBUTES:
                devices['sensor'].append({'node': node, 'attribute': attribute})

    return devices


def map_homee_node(node):
    """Map homee nodes to Home Assistant types."""
    from pyhomee import const
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

    def __init__(self, homee_node, cube):
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

    def _update_callback(self, node, attribute):
        """Update the state."""
        if node is not None:
            self._homee_node = node
        if attribute is not None:
            attr_type = get_attr_type(attribute)
            self.attributes[attr_type] = attribute

            self.update_state(attribute)
        self.schedule_update_ha_state()

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def should_poll(self):
        return False

    @property
    def available(self):
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
