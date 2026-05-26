from __future__ import annotations

from collections import deque
from typing import Dict, List, Set, Tuple, Type

from frames import InfrastructureObject


def show_card(kb: Dict[str, InfrastructureObject], obj_id: str) -> str:
    obj = kb.get(obj_id)
    if obj is None:
        return f"[ОШИБКА] Объект '{obj_id}' не найден."

    d = obj.to_dict()
    lines: List[str] = []
    lines.append("=" * 70)
    lines.append(f"{d['obj_id']} — {d['name']}  [{d['type']}]")
    lines.append(f"Расположение: {d['location']}")
    lines.append(f"Владелец: {d['owner']}")
    lines.append(f"Критичность (1..5): {d['criticality']}")
    lines.append("-" * 70)

    base_keys = {"obj_id", "type", "name", "location", "criticality", "owner", "depends_on"}
    extra_keys = [k for k in d.keys() if k not in base_keys]

    if extra_keys:
        lines.append("Специфические слоты (атрибуты типа объекта):")
        for k in extra_keys:
            lines.append(f"  • {k}: {d[k]}")
        lines.append("-" * 70)

    deps = d.get("depends_on", [])
    if deps:
        lines.append("Зависит от (depends_on):")
        for dep_id in deps:
            dep = kb.get(dep_id)
            dep_name = dep.short() if dep else dep_id
            lines.append(f"  → {dep_name}")
    else:
        lines.append("Зависит от (depends_on): нет")

    lines.append("=" * 70)
    return "\n".join(lines)


def find_by_type(kb: Dict[str, InfrastructureObject], cls: Type[InfrastructureObject]) -> List[InfrastructureObject]:
    return [obj for obj in kb.values() if isinstance(obj, cls)]


def dependency_chain(kb: Dict[str, InfrastructureObject], start_id: str, max_depth: int = 3) -> List[Tuple[int, str]]:
    """
    Цепочка зависимостей "вниз" (что нужно объекту):
    start -> depends_on -> depends_on ...
    Возвращает список (глубина, obj_id) без повторов.
    """
    if start_id not in kb:
        return []

    visited: Set[str] = {start_id}
    out: List[Tuple[int, str]] = []
    q = deque([(start_id, 0)])

    while q:
        current, depth = q.popleft()
        if depth >= max_depth:
            continue

        for dep_id in kb[current].depends_on:
            if dep_id in visited:
                continue
            visited.add(dep_id)
            out.append((depth + 1, dep_id))
            if dep_id in kb:
                q.append((dep_id, depth + 1))

    return out


def cascade_failure(kb: Dict[str, InfrastructureObject], failed_id: str, max_depth: int = 5) -> List[Tuple[int, str]]:
    """
    Каскад отказа "вверх" (кто пострадает, если объект failed_id выйдет из строя).
    Это демонстрация влияния отказа на критическую инфраструктуру.
    """
    if failed_id not in kb:
        return []

    reverse: Dict[str, List[str]] = {k: [] for k in kb.keys()}
    for obj in kb.values():
        for dep in obj.depends_on:
            if dep in reverse:
                reverse[dep].append(obj.obj_id)

    visited: Set[str] = {failed_id}
    out: List[Tuple[int, str]] = []
    q = deque([(failed_id, 0)])

    while q:
        current, depth = q.popleft()
        if depth >= max_depth:
            continue

        for impacted_id in reverse.get(current, []):
            if impacted_id in visited:
                continue
            visited.add(impacted_id)
            out.append((depth + 1, impacted_id))
            q.append((impacted_id, depth + 1))

    return out


def risk_notes(kb: Dict[str, InfrastructureObject], obj_id: str) -> List[str]:
    """
    Мини-правила (простые, но "экспертные"):
    1) Если объект — Hospital, критичность >= 4 и нет резервного генератора -> высокий риск.
    2) Если depends_on >= 3 -> повышенная уязвимость.
    """
    obj = kb.get(obj_id)
    if not obj:
        return []

    notes: List[str] = []
    d = obj.to_dict()

    # Правило 1
    if d.get("type") == "Hospital":
        if d.get("criticality", 1) >= 4 and not d.get("has_backup_generator", False):
            notes.append("Высокий риск: критичная больница без резервного генератора.")

    # Правило 2
    deps = d.get("depends_on", [])
    if isinstance(deps, list) and len(deps) >= 3:
        notes.append("Повышенная уязвимость: объект зависит от 3+ внешних ресурсов/объектов.")

    return notes