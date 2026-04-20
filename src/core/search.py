from __future__ import annotations

from datetime import timedelta
from typing import Optional

from .models import Property, SearchCriteria
from .pricing import calc_total


def _dates_overlap(
    check_in, check_out, unavailable: list[tuple]
) -> bool:
    for start, end in unavailable:
        # overlap: check_in < end AND check_out > start
        if check_in < end and check_out > start:
            return True
    return False


def _matches(prop: Property, c: SearchCriteria) -> bool:
    if prop.status != "active":
        return False
    if prop.max_guests < c.guests:
        return False
    if _dates_overlap(c.check_in, c.check_out, prop.unavailable_dates):
        return False
    if c.districts and prop.district not in c.districts:
        return False
    if c.rooms is not None and prop.rooms < c.rooms:
        return False
    if c.bathrooms is not None and prop.bathrooms < c.bathrooms:
        return False
    if c.need_kitchen and not prop.has_kitchen:
        return False
    if c.need_ac and not prop.has_ac:
        return False
    total = calc_total(prop, c)
    if c.budget_min is not None and total < c.budget_min:
        return False
    if c.budget_max is not None and total > c.budget_max:
        return False
    return True


def search(properties: list[Property], criteria: SearchCriteria) -> list[Property]:
    results = [p for p in properties if _matches(p, criteria)]
    results.sort(key=lambda p: calc_total(p, criteria))
    return results


def search_with_fallback(
    properties: list[Property], criteria: SearchCriteria
) -> tuple[list[Property], Optional[str]]:
    """
    Возвращает (список объектов, текст_о_расслаблении_фильтра | None).
    Пошагово расслабляет фильтры если ничего не найдено.
    """
    results = search(properties, criteria)
    if results:
        return results, None

    # 1. Снять кондиционер
    if criteria.need_ac:
        c = criteria.model_copy(update={"need_ac": None})
        results = search(properties, c)
        if results:
            return results, "Показываю варианты без кондиционера"

    # 2. Расширить бюджет на +15%
    if criteria.budget_max is not None:
        c = criteria.model_copy(update={"budget_max": criteria.budget_max * 1.15})
        results = search(properties, c)
        if results:
            return results, "Показываю варианты немного выше бюджета (+15%)"

    # 3. Снять кухню
    if criteria.need_kitchen:
        c = criteria.model_copy(update={"need_kitchen": None, "need_ac": None})
        results = search(properties, c)
        if results:
            return results, "Показываю варианты без кухни"

    # 4. Уменьшить санузлы до 1
    if criteria.bathrooms and criteria.bathrooms > 1:
        c = criteria.model_copy(update={"bathrooms": 1, "need_kitchen": None, "need_ac": None})
        results = search(properties, c)
        if results:
            return results, "Показываю варианты с 1 санузлом"

    # 5. Соседние даты (±2 дня)
    for delta in [2, -2, 1, -1]:
        new_in = criteria.check_in + timedelta(days=delta)
        new_out = criteria.check_out + timedelta(days=delta)
        if new_in < new_out:
            c = criteria.model_copy(
                update={"check_in": new_in, "check_out": new_out,
                        "need_kitchen": None, "need_ac": None, "bathrooms": None}
            )
            results = search(properties, c)
            if results:
                arrow = "+" if delta > 0 else ""
                return results, f"Показываю варианты при сдвиге дат на {arrow}{delta} дн."

    # 6. Все районы
    if criteria.districts:
        c = criteria.model_copy(
            update={"districts": [], "need_kitchen": None, "need_ac": None,
                    "bathrooms": None, "budget_max": None}
        )
        results = search(properties, c)
        if results:
            return results, "Показываю варианты во всех районах"

    return [], None
