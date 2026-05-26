from __future__ import annotations

from typing import Dict

from frames import (
    DataCenter,
    Hospital,
    InfrastructureObject,
    PowerPlant,
    Substation,
    TrafficControl,
    WaterStation,
)


def build_demo_kb() -> Dict[str, InfrastructureObject]:
    """
    Демонстрационная база знаний (8–10 объектов достаточно для курсовой).
    Все связи задаются через depends_on (список obj_id).
    """
    kb: Dict[str, InfrastructureObject] = {}

    kb["PP1"] = PowerPlant(
        obj_id="PP1",
        name="Электростанция «Северная»",
        location="Северный район",
        criticality=5,
        capacity_mw=250.0,
        fuel_type="газ",
        depends_on=[],
    )

    kb["SS1"] = Substation(
        obj_id="SS1",
        name="Подстанция «Центральная»",
        location="Центр города",
        criticality=5,
        voltage_kv=110.0,
        depends_on=["PP1"],
    )

    kb["WS1"] = WaterStation(
        obj_id="WS1",
        name="Насосная станция «Восточная»",
        location="Восточный район",
        criticality=4,
        capacity_m3h=1200.0,
        depends_on=["SS1"],
    )

    kb["H1"] = Hospital(
        obj_id="H1",
        name="Городская больница №1",
        location="Центр города",
        criticality=5,
        beds=600,
        has_backup_generator=False,
        depends_on=["SS1", "WS1"],
    )

    kb["DC1"] = DataCenter(
        obj_id="DC1",
        name="Дата-центр «CityData»",
        location="Южный район",
        criticality=4,
        tier="Tier II",
        ups_hours=2.0,
        depends_on=["SS1"],
    )

    kb["TC1"] = TrafficControl(
        obj_id="TC1",
        name="Центр управления светофорами",
        location="Центр города",
        criticality=4,
        intersections_served=180,
        depends_on=["SS1", "DC1"],
    )

    # Дополнительные объекты (делают каскад отказа нагляднее)
    kb["H2"] = Hospital(
        obj_id="H2",
        name="Детская больница",
        location="Западный район",
        criticality=5,
        beds=350,
        has_backup_generator=True,
        depends_on=["SS1", "WS1"],
    )

    kb["WS2"] = WaterStation(
        obj_id="WS2",
        name="Станция водоочистки",
        location="Северный район",
        criticality=4,
        capacity_m3h=900.0,
        depends_on=["SS1"],
    )

    kb["DC2"] = DataCenter(
        obj_id="DC2",
        name="Узел экстренной связи",
        location="Центр города",
        criticality=5,
        tier="Tier III",
        ups_hours=6.0,
        depends_on=["SS1"],
    )

    return kb