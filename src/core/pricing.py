from .models import Property, SearchCriteria


def calc_total(prop: Property, criteria: SearchCriteria) -> float:
    return round(prop.price_per_day * criteria.nights, 2)
