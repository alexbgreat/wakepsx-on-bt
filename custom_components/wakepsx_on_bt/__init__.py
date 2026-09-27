"""The Wake PSX on Bluetooth integration.

This module is the entry point for Home Assistant. It handles the setup
and unloading of the integration's configuration entries.
"""

from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN

# Serves webhid/extractor.html — the browser-based WebHID MAC extraction tool
# linked from the config flow's "Enter manually" step.
WEBHID_URL_PATH = "/api/wakepsx_on_bt/webhid"
_WEBHID_DIR = Path(__file__).parent / "webhid"
_WEBHID_REGISTERED_KEY = f"{DOMAIN}_webhid_registered"


async def async_register_webhid_static_path(hass: HomeAssistant) -> None:
    """Serve the WebHID extractor page, once per HA run.

    Called from the config flow (before any config entry exists) as well as
    from ``async_setup_entry``, since it may be needed again from an
    already-configured install's "Add another console" flow.
    """
    if hass.data.get(_WEBHID_REGISTERED_KEY):
        return
    # Set before awaiting: two config flows can otherwise both pass the check
    # above while the first registration is still in flight.
    hass.data[_WEBHID_REGISTERED_KEY] = True
    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(WEBHID_URL_PATH, str(_WEBHID_DIR), cache_headers=False)]
        )
    except Exception:
        hass.data[_WEBHID_REGISTERED_KEY] = False
        raise


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when its data is updated by the options flow.

    Registered as an update listener so that changes saved via the options
    flow take effect immediately without requiring a manual HA restart.
    """
    await hass.config_entries.async_reload(entry.entry_id)


# List of supported platforms. We only use the 'button' platform.
PLATFORMS: list[Platform] = [Platform.BUTTON]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Wake PSX on Bluetooth from a config entry.

    Args:
        hass: The Home Assistant instance.
        entry: The configuration entry to setup.

    Returns:
        True if the setup was successful.
    """
    await async_register_webhid_static_path(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # Reload the integration when options-flow writes new data so that
    # async_added_to_hass runs again and recreates ESPHome state subscriptions.
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry when the user removes or reloads the integration.

    Args:
        hass: The Home Assistant instance.
        entry: The configuration entry to unload.

    Returns:
        True if the unloading was successful.
    """
    unload_ok: bool = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return unload_ok
