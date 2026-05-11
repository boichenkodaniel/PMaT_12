from __future__ import annotations


class NotFoundError(Exception):
    def __init__(self, detail: str):
        self.detail = detail


class ConflictError(Exception):
    def __init__(self, detail: str):
        self.detail = detail
