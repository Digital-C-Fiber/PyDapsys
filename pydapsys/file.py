from __future__ import annotations

from dataclasses import dataclass
from typing import BinaryIO

from pydapsys.page import DataPage
from pydapsys.read import read_from
from pydapsys.toc.entry import Root


@dataclass
class File:
    toc_root: Root
    pages: dict[int, DataPage]

    @staticmethod
    def from_binary(binio: BinaryIO, byte_order='<') -> File:
        toc_root, pages = read_from(binio, byte_order=byte_order)
        return File(toc_root, pages)
