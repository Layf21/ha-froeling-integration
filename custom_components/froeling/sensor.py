"""Fröling facility sensors"""
from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
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

    entities: list[SensorEntity] = []

    #Kessel
    entities.append(StateSensor(coordinator, 0, 0))
    entities.append(TemperatureSensor(coordinator, 0, 0, "boilerTemp"))
    #Gewerbe
    entities.append(TemperatureSensor(coordinator, 0, 1, "desiredRoomTemp", "Soll-Temperatur Gewerbe"))
    entities.append(TemperatureSensor(coordinator, 0, 1, "actualFlowTemp", "Ist-Temperatur Gewerbe"))
    #Wohnugnen
    entities.append(TemperatureSensor(coordinator, 0, 2, "desiredRoomTemp", "Soll-Temperatur Wohnungen"))
    entities.append(TemperatureSensor(coordinator, 0, 2, "actualFlowTemp", "Ist-Temperatur Wohnungen"))
    #Puffer
    entities.append(TemperatureSensor(coordinator, 0, 4, "bufferTempTop"))
    entities.append(TemperatureSensor(coordinator, 0, 4, "bufferTempBottom"))
    entities.append(UsageSensor(coordinator, 0, 4, "bufferTankCharge"))
    entities.append(UsageSensor(coordinator, 0, 4, "bufferPumpControl"))

    async_add_entities(entities)


class ValueSensor(CoordinatorEntity, SensorEntity):
    """Sensor for value type measurments in Fröling components"""
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator: FroelingCoordinator, facility, froeling_component_id, value_key, name=None) -> None:
        super().__init__(coordinator)

        self.coordinator = coordinator
        self.facility = facility
        self.component_id = froeling_component_id
        self.value_key = value_key

        fac = self.coordinator.data[self.facility]
        device_info = fac.info["components"][self.component_id]
        value_info = device_info[self.value_key]

        self._attr_unique_id = f"{self.coordinator.entry.entry_id}_{fac.name}_{device_info['componentId']}_{self.value_key}"
        self._attr_device_info = DeviceInfo(
            configuration_url="https://connect-web.froeling.com/",
            identifiers={
                (DOMAIN, fac.id)
            },
            manufacturer="https://www.froeling.com/",
            name="Heizung",
            model=fac.friendly_name
        )

        self._attr_native_value = value_info["value"]
        self._attr_native_unit_of_measurement = value_info["unit"]
        self._attr_name = name or value_info["displayName"]

    @callback
    def _handle_coordinator_update(self) -> None:
        self._attr_native_value = int(
            self.coordinator.data[self.facility].info["components"][self.component_id][
                self.value_key
            ]["value"]
        )
        self.async_write_ha_state()

class StateSensor(CoordinatorEntity, SensorEntity):
    """Sensor for value type measurments in Fröling components"""
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator: FroelingCoordinator, facility, froeling_component_id, name=None) -> None:
        super().__init__(coordinator)

        self.coordinator = coordinator
        self.facility = facility
        self.component_id = froeling_component_id

        fac = self.coordinator.data[self.facility]
        device_info = fac.info["components"][self.component_id]
        value_info = device_info["state"]

        self._attr_unique_id = f"{self.coordinator.entry.entry_id}_{fac.name}_{device_info['componentId']}_state"
        self._attr_device_info = DeviceInfo(
            configuration_url="https://connect-web.froeling.com/",
            identifiers={
                (DOMAIN, fac.id)
            },
            manufacturer="https://www.froeling.com/",
            name="Heizung",
            model=fac.friendly_name
        )

        self._attr_native_value = value_info["displayValue"]
        self._attr_name = name or value_info["displayName"]

    @callback
    def _handle_coordinator_update(self) -> None:
        self._attr_native_value = self.coordinator.data[self.facility].info["components"][self.component_id]["state"]["displayValue"]
        self.async_write_ha_state()

class UsageSensor(ValueSensor):
    _attr_device_class = None

class TemperatureSensor(ValueSensor):
    _attr_device_class = "temperature"