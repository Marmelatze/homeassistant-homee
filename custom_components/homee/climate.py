"""
Support for Homee sensors.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/climate.homee/
"""
import asyncio
import logging
from typing import List

from homeassistant.components.climate import ClimateDevice, ENTITY_ID_FORMAT
from homeassistant.components.climate.const import SUPPORT_TARGET_TEMPERATURE, SUPPORT_PRESET_MODE, CURRENT_HVAC_HEAT, \
    CURRENT_HVAC_COOL, CURRENT_HVAC_OFF
from custom_components.homee import HOMEE_CUBE, HomeeDevice
from homeassistant.const import TEMP_CELSIUS, ATTR_TEMPERATURE

DEPENDENCIES = ['homee']

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Perform the setup for Vera controller devices."""
    devices = []
    for data in discovery_info['devices']:
        devices.append(HomeeThermostat(hass, data['node'], HOMEE_CUBE))
    async_add_devices(devices)


class HomeeThermostat(HomeeDevice, ClimateDevice):
    @property
    def supported_features(self):
        """Return the list of supported features."""
        if self.has_attr('CurrentValvePosition'):
            return SUPPORT_TARGET_TEMPERATURE
        return SUPPORT_TARGET_TEMPERATURE

    @property
    def temperature_unit(self):
        """Return the unit of measurement that is used."""
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self.get_attr_value('Temperature', 0)

    @property
    def target_temperature(self):
        return self.get_attr_value('TargetTemperature', 0)

    @property
    def current_humidity(self):
        return self.get_attr_value('RelativeHumidity')

    @property
    def min_temp(self):
        """Return the minimum temperature - 4.5 means off."""
        return 4.5

    @property
    def max_temp(self):
        """Return the maximum temperature - 30.5 means on."""
        return 30.5

    @property
    def hvac_mode(self) -> str:
        position = self.get_attr_value('CurrentValvePosition')
        if position is None:
            return CURRENT_HVAC_OFF
        elif position > 0:
            return CURRENT_HVAC_HEAT
        else:
            return CURRENT_HVAC_COOL

    @property
    def hvac_modes(self) -> List[str]:
        return [CURRENT_HVAC_OFF, CURRENT_HVAC_COOL, CURRENT_HVAC_HEAT]

    def __init__(self, hass, homee_node, cube):
        HomeeDevice.__init__(self, hass, homee_node, cube)
        self.entity_id = ENTITY_ID_FORMAT.format(self.homee_id)

    def update_state(self, attribute):
        """Update the state."""

    async def async_set_temperature(self, **kwargs):
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return None
        await self.cube.send_node_command(self._homee_node, self.get_attr('TargetTemperature'), temperature)
