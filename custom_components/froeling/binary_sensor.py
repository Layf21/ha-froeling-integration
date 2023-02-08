"""Fröling facility sensors"""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.core import callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from . import FroelingCoordinator

_LOGGER = logging.getLogger(__name__)

ATTRIBUTION = "Data provided by Fröling-Connect UI."


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
    ) -> None:
    """Set up sensor entities."""

    coordinator: FroelingCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[BinarySensorEntity] = []

    entities.append(ActiveSensor(coordinator, 0, 0))
    entities.append(ActiveSensor(coordinator, 0, 1))
    entities.append(ActiveSensor(coordinator, 0, 2))
    entities.append(ActiveSensor(coordinator, 0, 4))

    async_add_entities(entities)

class ActiveSensor(CoordinatorEntity, BinarySensorEntity):
    """Sensor for temperature measurments in Fröling components"""

    _attr_attribution = ATTRIBUTION
    _attr_device_class = "running"
    _attr_icon = "mdi:heating-coil"

    def __init__(self, coordinator: FroelingCoordinator, facility, froeling_component_id) -> None:
        super().__init__(coordinator)

        self.coordinator = coordinator
        self.facility = facility
        self.component_id = froeling_component_id

        fac = self.coordinator.data[self.facility]
        device_info = fac.info["components"][self.component_id]

        self._attr_unique_id = f"{self.coordinator.entry.entry_id}_{fac.name}_{device_info['componentId']}_active"
        self._attr_device_info = DeviceInfo(
            configuration_url="https://connect-web.froeling.com/",
            identifiers={
                (DOMAIN, fac.id)
            },
            manufacturer="https://www.froeling.com/",
            name="Heizung",
            model=fac.friendly_name
        )

        self._attr_name = f"{device_info['componentId']} Aktiv"

    @callback
    def _handle_coordinator_update(self) -> None:
        self._attr_is_on = self.coordinator.data[self.facility].info["components"][self.component_id]["active"]
        self.async_write_ha_state()
