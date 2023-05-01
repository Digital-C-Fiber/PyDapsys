from __future__ import annotations

from typing import Optional


class ToCEntryError(Exception):
    """Generic Exception for errors related to the table of contents and streams"""
    ...


class ToCStreamError(Exception):
    """Exception related to ToC streams"""
    ...


class ToCNoSuchChildError(ToCEntryError):
    def __init__(self, message: Optional[str] = None, this_item: Optional[str] = None,
                 missing_item: Optional[str] = None):
        super().__init__(
            message if message is not None else self.default_message(this_item=this_item, missing_item=missing_item))
        self.this_item = this_item
        self.missing_item = missing_item

    @staticmethod
    def default_message(this_item: Optional[str] = None, missing_item: Optional[str] = None) -> str:
        child_part = 'No such child' if missing_item is None else f'No child named "{missing_item}"'
        this_part = 'in this item' if this_item is None else f'in item "{this_item}"'
        return f"{child_part} {this_part}"


class ToCPathError(Exception):
    ...
