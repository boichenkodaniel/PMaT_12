from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


WEEK_THRESHOLD_DAYS = 7
MONTH_THRESHOLD_DAYS = 30


class BookType(str, Enum):
    FICTION = "fiction"
    SCIENCE = "science"
    OTHER = "other"


DAILY_RATE: dict[BookType, int] = {
    BookType.FICTION: 10,
    BookType.SCIENCE: 50,
    BookType.OTHER: 5,
}

WEEKLY_SURCHARGE: dict[BookType, int] = {
    BookType.FICTION: 100,
    BookType.SCIENCE: 200,
    BookType.OTHER: 50,
}

MONTHLY_SURCHARGE: dict[BookType, int] = {
    BookType.FICTION: 500,
    BookType.SCIENCE: 1000,
    BookType.OTHER: 0,
}


@dataclass
class PenaltyInput:
    overdue_days: int
    book_type: BookType


def _resolve_book_type(raw_type: str) -> BookType:
    try:
        return BookType(raw_type)
    except ValueError as exc:
        raise ValueError(
            f"Неизвестный тип книги: '{raw_type}'. "
            f"Допустимые значения: {', '.join(bt.value for bt in BookType)}"
        ) from exc


def calculate_penalty(data: PenaltyInput) -> int:
    if data.overdue_days < 0:
        raise ValueError("Количество дней просрочки не может быть отрицательным")
    if data.overdue_days == 0:
        return 0

    base = data.overdue_days * DAILY_RATE[data.book_type]

    surcharge = 0
    if data.overdue_days > WEEK_THRESHOLD_DAYS:
        surcharge += WEEKLY_SURCHARGE[data.book_type]
    if data.overdue_days > MONTH_THRESHOLD_DAYS:
        surcharge += MONTHLY_SURCHARGE[data.book_type]

    return base + surcharge


def calculate_penalty_from_raw(
    overdue_days: int,
    book_type_str: str,
) -> int:
    book_type = _resolve_book_type(book_type_str)
    input_data = PenaltyInput(
        overdue_days=overdue_days,
        book_type=book_type,
    )
    return calculate_penalty(input_data)