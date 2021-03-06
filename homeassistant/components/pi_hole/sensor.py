"""Support for getting statistical data from a Pi-hole system."""
import logging

from homeassistant.const import CONF_NAME
from homeassistant.helpers.entity import Entity

from .const import (
    ATTR_BLOCKED_DOMAINS,
    DATA_KEY_API,
    DATA_KEY_COORDINATOR,
    DOMAIN as PIHOLE_DOMAIN,
    SENSOR_DICT,
    SENSOR_LIST,
)

LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Pi-hole sensor."""
    name = entry.data[CONF_NAME]
    hole_data = hass.data[PIHOLE_DOMAIN][name]
    sensors = [
        PiHoleSensor(
            hole_data[DATA_KEY_API],
            hole_data[DATA_KEY_COORDINATOR],
            name,
            sensor_name,
            entry.entry_id,
        )
        for sensor_name in SENSOR_LIST
    ]
    async_add_entities(sensors, True)


class PiHoleSensor(Entity):
    """Representation of a Pi-hole sensor."""

    def __init__(self, api, coordinator, name, sensor_name, server_unique_id):
        """Initialize a Pi-hole sensor."""
        self.api = api
        self.coordinator = coordinator
        self._name = name
        self._condition = sensor_name
        self._server_unique_id = server_unique_id

        variable_info = SENSOR_DICT[sensor_name]
        self._condition_name = variable_info[0]
        self._unit_of_measurement = variable_info[1]
        self._icon = variable_info[2]

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._name} {self._condition_name}"

    @property
    def unique_id(self):
        """Return the unique id of the sensor."""
        return f"{self._server_unique_id}/{self._condition_name}"

    @property
    def device_info(self):
        """Return the device information of the sensor."""
        return {
            "identifiers": {(PIHOLE_DOMAIN, self._server_unique_id)},
            "name": self._name,
            "manufacturer": "Pi-hole",
        }

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return self._unit_of_measurement

    @property
    def state(self):
        """Return the state of the device."""
        try:
            return round(self.api.data[self._condition], 2)
        except TypeError:
            return self.api.data[self._condition]

    @property
    def device_state_attributes(self):
        """Return the state attributes of the Pi-hole."""
        return {ATTR_BLOCKED_DOMAINS: self.api.data["domains_being_blocked"]}

    @property
    def available(self):
        """Could the device be accessed during the last update call."""
        return self.coordinator.last_update_success

    @property
    def should_poll(self):
        """No need to poll. Coordinator notifies entity of updates."""
        return False

    async def async_update(self):
        """Get the latest data from the Pi-hole API."""
        await self.coordinator.async_request_refresh()
