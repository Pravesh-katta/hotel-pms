from datetime import date

from .models import RatePlan, RatePlanRate, SeasonalRate


def get_rate(hotel, room_type, target_date, source=None):
    """
    Resolve the nightly rate for a room type on a specific date.
    Priority: SeasonalRate > RatePlanRate.base_rate
    Plan selection: source-matched plan > default plan > highest priority
    """
    # Find matching rate plan
    rate_plan = _find_best_rate_plan(hotel, source)
    if not rate_plan:
        return room_type.base_rate

    # Get rate plan rate for this room type
    try:
        rate_plan_rate = RatePlanRate.objects.get(rate_plan=rate_plan, room_type=room_type)
    except RatePlanRate.DoesNotExist:
        return room_type.base_rate

    # Check seasonal override
    seasonal = SeasonalRate.objects.filter(
        rate_plan_rate=rate_plan_rate,
        start_date__lte=target_date,
        end_date__gte=target_date,
    ).first()

    if seasonal:
        return seasonal.rate

    return rate_plan_rate.base_rate


def get_rates_for_stay(hotel, room_type, check_in, check_out, source=None):
    """
    Returns a list of (date, rate) tuples for each night of the stay.
    """
    from datetime import timedelta

    rates = []
    current = check_in
    while current < check_out:
        rate = get_rate(hotel, room_type, current, source)
        rates.append((current, rate))
        current += timedelta(days=1)
    return rates


def _find_best_rate_plan(hotel, source=None):
    plans = RatePlan.objects.filter(hotel=hotel, is_active=True)

    if source:
        source_plan = plans.filter(source=source).order_by("-priority").first()
        if source_plan:
            return source_plan

    default_plan = plans.filter(is_default=True).first()
    if default_plan:
        return default_plan

    return plans.order_by("-priority").first()
