from __future__ import annotations

from datetime import date, time

import pytest

from core.services.calendar_availability import (
    CalendarAvailabilityService,
    _compute_available_slots,
)
from core.services.schedule import SchedulePolicy, compose_start_at_utc


def test_compute_available_slots_respects_day_off() -> None:
    policy = SchedulePolicy(days_ahead=1, start_hour=12, end_hour_inclusive=12)
    assert (
        _compute_available_slots(
            policy=policy, is_day_off=True, blocked={"12:00"}, booked=set()
        )
        == []
    )


def test_compute_available_slots_excludes_blocked_and_booked() -> None:
    policy = SchedulePolicy(days_ahead=1, start_hour=12, end_hour_inclusive=14)
    assert _compute_available_slots(
        policy=policy,
        is_day_off=False,
        blocked={"13:00"},
        booked={"12:00"},
    ) == ["14:00"]


@pytest.mark.asyncio
async def test_get_available_slots_considers_day_off_blocked_and_booked(
    monkeypatch,
) -> None:
    # Import module-level repos to monkeypatch their async functions.
    import core.repositories.orders as orders_repo
    import core.repositories.schedule_exceptions as exc_repo

    chosen = date(2026, 2, 12)

    async def fake_is_day_off(*, session, day):  # noqa: ANN001
        assert day == chosen
        return False

    async def fake_list_blocked_slots_for_date(*, session, day):  # noqa: ANN001
        assert day == chosen
        return {time(16, 0)}

    async def fake_list_orders_start_at_between(
        *, session, start_at, end_at
    ):  # noqa: ANN001
        # Book 12:00 on the chosen date.
        return [compose_start_at_utc(chosen_date=chosen, chosen_time=time(12, 0))]

    monkeypatch.setattr(exc_repo, "is_day_off", fake_is_day_off)
    monkeypatch.setattr(
        exc_repo, "list_blocked_slots_for_date", fake_list_blocked_slots_for_date
    )
    monkeypatch.setattr(
        orders_repo, "list_order_start_at_between", fake_list_orders_start_at_between
    )

    svc = CalendarAvailabilityService(
        policy=SchedulePolicy(days_ahead=90, start_hour=12, end_hour_inclusive=20)
    )
    slots = await svc.get_available_slots(session=object(), day=chosen)  # type: ignore[arg-type]
    assert "12:00" not in slots
    assert "16:00" not in slots
    assert "13:00" in slots


@pytest.mark.asyncio
async def test_get_disabled_dates_marks_day_off_and_fully_occupied_dates(
    monkeypatch,
) -> None:
    import core.repositories.orders as orders_repo
    import core.repositories.schedule_exceptions as exc_repo

    today = date(2026, 2, 10)
    policy = SchedulePolicy(
        days_ahead=2, start_hour=12, end_hour_inclusive=12
    )  # only one slot

    async def fake_list_day_off_dates(
        *, session, start_date, end_date_inclusive
    ):  # noqa: ANN001
        assert start_date == today
        assert end_date_inclusive == date(2026, 2, 12)
        return {date(2026, 2, 11)}

    async def fake_list_blocked_slots_between(
        *, session, start_date, end_date_inclusive
    ):  # noqa: ANN001
        # Fully block "today"
        return {today: {time(12, 0)}}

    async def fake_list_orders_start_at_between(
        *, session, start_at, end_at
    ):  # noqa: ANN001
        # Fully book the last day in range.
        return [
            compose_start_at_utc(chosen_date=date(2026, 2, 12), chosen_time=time(12, 0))
        ]

    monkeypatch.setattr(exc_repo, "list_day_off_dates", fake_list_day_off_dates)
    monkeypatch.setattr(
        exc_repo, "list_blocked_slots_between", fake_list_blocked_slots_between
    )
    monkeypatch.setattr(
        orders_repo, "list_order_start_at_between", fake_list_orders_start_at_between
    )

    svc = CalendarAvailabilityService(policy=policy)
    disabled = await svc.get_disabled_dates(session=object(), today=today)  # type: ignore[arg-type]
    assert disabled == {date(2026, 2, 10), date(2026, 2, 11), date(2026, 2, 12)}
