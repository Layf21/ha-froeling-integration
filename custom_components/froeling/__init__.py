"""The Fröling integration."""
from __future__ import annotations

from datetime import timedelta
import logging

import async_timeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.exceptions import ConfigEntryAuthFailed


from .const import DOMAIN
from .froeling_client import Froeling, AuthenticationError


_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]


def auth(usr, pasw):
    """Try to Authenticate and check token"""
    client = Froeling(usr, pasw)
    client.login()
    client.getFacilities()
    return client


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Fröling from a config entry."""

    client = await hass.async_add_executor_job(
        auth, entry.data["username"], entry.data["password"]
    )

    hass.data.setdefault(DOMAIN, {})
    coordinator = FroelingCoordinator(hass, client, entry)
    hass.data[DOMAIN][entry.entry_id] = coordinator
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class FroelingCoordinator(DataUpdateCoordinator):
    """Coordinator class"""

    def __init__(self, hass, client, entry) -> None:
        super().__init__(
            hass, _LOGGER, name="Froeling Data", update_interval=timedelta(seconds=30)
        )
        self.client = client
        self.entry = entry

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """

        try:
            async with async_timeout.timeout(10):
                await self.hass.async_add_executor_job(self.client.getFacilities)
            for facility in self.client.facilities:
                async with async_timeout.timeout(10):
                    await self.hass.async_add_executor_job(facility.update_general_data)
        except AuthenticationError as err:
            raise ConfigEntryAuthFailed from err

        return self.client.facilities
