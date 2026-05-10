from __future__ import annotations

import pytest

from app.penalty import (
    BookType,
    DAILY_RATE,
    MONTHLY_SURCHARGE,
    WEEKLY_SURCHARGE,
    PenaltyInput,
    calculate_penalty,
    calculate_penalty_from_raw,
)


class TestCalculatePenalty:
    def test_no_overdue_returns_zero(self):
        data = PenaltyInput(overdue_days=0, book_type=BookType.FICTION)
        assert calculate_penalty(data) == 0

    def test_negative_days_raises(self):
        data = PenaltyInput(overdue_days=-5, book_type=BookType.FICTION)
        with pytest.raises(ValueError, match="отрицательным"):
            calculate_penalty(data)

    def test_fiction_one_day(self):
        data = PenaltyInput(overdue_days=1, book_type=BookType.FICTION)
        assert calculate_penalty(data) == 1 * DAILY_RATE[BookType.FICTION]

    def test_fiction_exactly_week_no_surcharge(self):
        days = 7
        data = PenaltyInput(overdue_days=days, book_type=BookType.FICTION)
        assert calculate_penalty(data) == days * DAILY_RATE[BookType.FICTION]

    def test_fiction_over_week(self):
        days = 8
        data = PenaltyInput(overdue_days=days, book_type=BookType.FICTION)
        expected = days * DAILY_RATE[BookType.FICTION] + WEEKLY_SURCHARGE[BookType.FICTION]
        assert calculate_penalty(data) == expected

    def test_fiction_exactly_month_no_monthly_surcharge(self):
        days = 30
        data = PenaltyInput(overdue_days=days, book_type=BookType.FICTION)
        expected = days * DAILY_RATE[BookType.FICTION] + WEEKLY_SURCHARGE[BookType.FICTION]
        assert calculate_penalty(data) == expected

    def test_fiction_over_month(self):
        days = 31
        data = PenaltyInput(overdue_days=days, book_type=BookType.FICTION)
        expected = (
            days * DAILY_RATE[BookType.FICTION]
            + WEEKLY_SURCHARGE[BookType.FICTION]
            + MONTHLY_SURCHARGE[BookType.FICTION]
        )
        assert calculate_penalty(data) == expected

    def test_science_exactly_week_no_surcharge(self):
        days = 7
        data = PenaltyInput(overdue_days=days, book_type=BookType.SCIENCE)
        assert calculate_penalty(data) == days * DAILY_RATE[BookType.SCIENCE]

    def test_science_over_week(self):
        days = 10
        data = PenaltyInput(overdue_days=days, book_type=BookType.SCIENCE)
        expected = days * DAILY_RATE[BookType.SCIENCE] + WEEKLY_SURCHARGE[BookType.SCIENCE]
        assert calculate_penalty(data) == expected

    def test_science_exactly_month_no_monthly_surcharge(self):
        days = 30
        data = PenaltyInput(overdue_days=days, book_type=BookType.SCIENCE)
        expected = days * DAILY_RATE[BookType.SCIENCE] + WEEKLY_SURCHARGE[BookType.SCIENCE]
        assert calculate_penalty(data) == expected

    def test_science_over_month(self):
        days = 31
        data = PenaltyInput(overdue_days=days, book_type=BookType.SCIENCE)
        expected = (
            days * DAILY_RATE[BookType.SCIENCE]
            + WEEKLY_SURCHARGE[BookType.SCIENCE]
            + MONTHLY_SURCHARGE[BookType.SCIENCE]
        )
        assert calculate_penalty(data) == expected

    def test_other_type(self):
        days = 5
        data = PenaltyInput(overdue_days=days, book_type=BookType.OTHER)
        expected = days * DAILY_RATE[BookType.OTHER]
        assert calculate_penalty(data) == expected

    def test_other_exactly_week_no_surcharge(self):
        days = 7
        data = PenaltyInput(overdue_days=days, book_type=BookType.OTHER)
        assert calculate_penalty(data) == days * DAILY_RATE[BookType.OTHER]

    def test_other_over_week(self):
        days = 14
        data = PenaltyInput(overdue_days=days, book_type=BookType.OTHER)
        expected = days * DAILY_RATE[BookType.OTHER] + WEEKLY_SURCHARGE[BookType.OTHER]
        assert calculate_penalty(data) == expected

    def test_other_exactly_month_no_monthly_surcharge(self):
        days = 30
        data = PenaltyInput(overdue_days=days, book_type=BookType.OTHER)
        expected = days * DAILY_RATE[BookType.OTHER] + WEEKLY_SURCHARGE[BookType.OTHER]
        assert calculate_penalty(data) == expected

    def test_other_over_month_no_monthly_surcharge(self):
        days = 45
        data = PenaltyInput(overdue_days=days, book_type=BookType.OTHER)
        expected = days * DAILY_RATE[BookType.OTHER] + WEEKLY_SURCHARGE[BookType.OTHER]
        assert calculate_penalty(data) == expected


class TestCalculatePenaltyFromRaw:
    def test_raw_fiction(self):
        assert calculate_penalty_from_raw(3, "fiction") == 3 * DAILY_RATE[BookType.FICTION]

    def test_raw_science(self):
        assert calculate_penalty_from_raw(2, "science") == 2 * DAILY_RATE[BookType.SCIENCE]

    def test_raw_other(self):
        assert calculate_penalty_from_raw(4, "other") == 4 * DAILY_RATE[BookType.OTHER]

    def test_raw_unknown_type_raises(self):
        with pytest.raises(ValueError, match="Неизвестный тип книги"):
            calculate_penalty_from_raw(4, "cooking")

    def test_raw_negative_days_raises(self):
        with pytest.raises(ValueError, match="отрицательным"):
            calculate_penalty_from_raw(-1, "fiction")

    def test_raw_zero_days(self):
        assert calculate_penalty_from_raw(0, "science") == 0