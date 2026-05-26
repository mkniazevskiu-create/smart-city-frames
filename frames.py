from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


def _clamp_int(value: int, lo: int, hi: int) -> int:
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


@dataclass
class InfrastructureObject:
    """
    Базовый фрейм (карточка объекта инфраструктуры).
    Слоты: id, name, location, criticality, owner, depends_on.
    """
    obj_id: str
    name: str
    location: str
    criticality: int  # 1..5
    owner: str = "Муниципалитет"
    depends_on: List[str] = field(default_factory=list)  # list of obj_id

    def __post_init__(self) -> None:
        # Простая валидация (чтобы выглядело взрослее)
        self.criticality = _clamp_int(int(self.criticality), 1, 5)

    @property
    def type_name(self) -> str:
        return self.__class__.__name__

    def short(self) -> str:
        return f"{self.obj_id} ({self.type_name}) — {self.name}"

    def to_dict(self) -> dict:
        # Удобно для вывода/сериализации (если понадобится)
        return {
            "obj_id": self.obj_id,
            "type": self.type_name,
            "name": self.name,
            "location": self.location,
            "criticality": self.criticality,
            "owner": self.owner,
            "depends_on": list(self.depends_on),
        }


@dataclass
class PowerPlant(InfrastructureObject):
    capacity_mw: float = 0.0
    fuel_type: str = "unknown"

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({"capacity_mw": self.capacity_mw, "fuel_type": self.fuel_type})
        return d


@dataclass
class Substation(InfrastructureObject):
    voltage_kv: float = 110.0

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({"voltage_kv": self.voltage_kv})
        return d


@dataclass
class WaterStation(InfrastructureObject):
    capacity_m3h: float = 0.0

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({"capacity_m3h": self.capacity_m3h})
        return d


@dataclass
class Hospital(InfrastructureObject):
    beds: int = 0
    has_backup_generator: bool = False

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({"beds": self.beds, "has_backup_generator": self.has_backup_generator})
        return d


@dataclass
class DataCenter(InfrastructureObject):
    tier: str = "Tier I"
    ups_hours: float = 0.0

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({"tier": self.tier, "ups_hours": self.ups_hours})
        return d


@dataclass
class TrafficControl(InfrastructureObject):
    intersections_served: int = 0

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({"intersections_served": self.intersections_served})
        return d