"""Desktop settings share the versioned configuration without overwriting accounts."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .desktop_geometry import Placement, placement_data, placement_from_data
from .models import ProviderError
from .parsers import object_map
from .storage import JsonStore, StorageError


@dataclass(frozen=True, slots=True)
class DesktopSettings:
    placement: Placement | None = None
    reduced_motion: bool = False


class DesktopSettingsStore:
    def __init__(self, data_dir: Path):
        self.store = JsonStore(data_dir / "config.json")

    def load(self) -> DesktopSettings:
        data = self.store.load()
        if data is None or "settings" not in data:
            return DesktopSettings()
        try:
            settings = object_map(data["settings"])
            mode = settings.get("motionMode", "full")
            if mode not in ("full", "reduced"):
                raise ValueError("Invalid motion mode")
            placement = placement_from_data(settings["lastPlacement"]) if settings.get("lastPlacement") is not None else None
            return DesktopSettings(placement, mode == "reduced")
        except (ValueError, ProviderError) as exc:
            raise StorageError("Invalid desktop settings; configuration was preserved") from exc

    def save(self, value: DesktopSettings) -> None:
        data = self.store.load() or {}
        try:
            settings = object_map(data.get("settings", {}))
        except ProviderError as exc:
            raise StorageError("Invalid desktop settings; configuration was preserved") from exc
        settings.update({"lastPlacement": placement_data(value.placement) if value.placement else None,
                         "motionMode": "reduced" if value.reduced_motion else "full"})
        data["settings"] = settings
        self.store.save(data)
