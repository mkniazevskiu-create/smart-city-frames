from __future__ import annotations

from dataclasses import fields
from typing import Dict, List, Type

from frames import (
    InfrastructureObject,
    PowerPlant,
    Substation,
    WaterStation,
    Hospital,
    DataCenter,
    TrafficControl,
)
from kb import build_demo_kb
from queries import cascade_failure, dependency_chain, find_by_type, risk_notes, show_card
from report import save_interactive_report


def print_section(title: str) -> None:
    print("\n" + title)
    print("=" * len(title))


def print_list(title: str, items: List[str]) -> None:
    print("\n" + title)
    print("-" * len(title))
    for x in items:
        print(x)


def _format_table(rows: List[List[str]], headers: List[str]) -> str:
    cols = len(headers)
    widths = [len(headers[i]) for i in range(cols)]
    for r in rows:
        for i in range(cols):
            widths[i] = max(widths[i], len(str(r[i])))

    def fmt_row(r: List[str]) -> str:
        return " | ".join(str(r[i]).ljust(widths[i]) for i in range(cols))

    sep = "-+-".join("-" * widths[i] for i in range(cols))
    out = [fmt_row(headers), sep]
    out.extend(fmt_row([str(x) for x in r]) for r in rows)
    return "\n".join(out)


def report_class_slots() -> str:
    classes: List[Type[InfrastructureObject]] = [
        InfrastructureObject,
        PowerPlant,
        Substation,
        WaterStation,
        Hospital,
        DataCenter,
        TrafficControl,
    ]

    base_fields = [f.name for f in fields(InfrastructureObject)]
    rows: List[List[str]] = []

    for cls in classes:
        cls_fields = [f.name for f in fields(cls)]
        specific = [x for x in cls_fields if x not in base_fields]
        rows.append([
            cls.__name__,
            ", ".join(base_fields),
            ", ".join(specific) if specific else "—",
        ])

    headers = ["Класс (тип фрейма)", "Общие слоты (наследуются)", "Специфические слоты"]
    return _format_table(rows, headers)


def report_objects_and_deps(kb: Dict[str, InfrastructureObject]) -> str:
    rows: List[List[str]] = []
    for obj in kb.values():
        deps = ", ".join(obj.depends_on) if obj.depends_on else "—"
        rows.append([obj.obj_id, obj.type_name, obj.name, str(obj.criticality), deps])

    headers = ["ID", "Тип", "Название", "Критичность", "Зависит от (depends_on)"]
    return _format_table(rows, headers)


def main() -> None:
    kb = build_demo_kb()

    print_section("Демонстрация фреймовой модели критической инфраструктуры умного города")
    print(f"Количество объектов (фреймов) в базе знаний: {len(kb)}")

    # Таблица 1: классы -> слоты
    print_section("Таблица 1. Классы (фреймы) и их слоты")
    print(report_class_slots())

    # Таблица 2: объекты -> зависимости
    print_section("Таблица 2. Объекты базы знаний и зависимости")
    print(report_objects_and_deps(kb))

    # Карточка объекта
    print_section("Пример: карточка объекта (фрейм)")
    print(show_card(kb, "H1"))

    # Поиск объектов по типу
    hospitals = find_by_type(kb, Hospital)
    print_list("Пример запроса: все объекты типа Hospital", [h.short() for h in hospitals])

    # Цепочка зависимостей (вниз)
    chain = dependency_chain(kb, "H1", max_depth=3)
    chain_lines: List[str] = []
    for depth, obj_id in chain:
        chain_lines.append("  " * (depth - 1) + f"→ {kb[obj_id].short()}")
    print_list("Пример запроса: цепочка зависимостей для H1 (что нужно объекту)", chain_lines or ["(нет)"])

    # Каскад отказа (вверх) — самый эффектный сценарий
    impacted = cascade_failure(kb, "PP1", max_depth=5)
    impacted_lines: List[str] = []
    for depth, obj_id in impacted:
        impacted_lines.append("  " * (depth - 1) + f"→ {kb[obj_id].short()}")
    print_list("Пример запроса: каскад отказа при отказе PP1 (кто пострадает)", impacted_lines or ["(никто)"])

    # Мини-правила риска
    notes = risk_notes(kb, "H1")
    print_list("Пример: оценка риска (простые правила)", notes or ["Риск-заметки отсутствуют."])

    # Генерация HTML-отчётов (главная + по одному на каждый объект)
    report_path = save_interactive_report(kb, filepath="report.html", default_focus="H1")
    print("\n✅ Интерактивный отчёт сформирован:", report_path)
    print("Откройте report.html в браузере (двойной клик).")


if __name__ == "__main__":
    main()