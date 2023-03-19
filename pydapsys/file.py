from __future__ import annotations

from dataclasses import dataclass
from typing import BinaryIO, Iterable, Optional, overload, Literal, Union

from pydapsys.page import DataPage, TextPage, WaveformPage
from pydapsys.read import read_from
from pydapsys.toc.entry import Root, Stream, StreamType
from pydapsys.toc.exceptions import ToCEntryError, ToCStreamError


class ToCEEntryIsNotAStreamError(ToCEntryError):
    def __init__(self, element="Target element"):
        super().__init__(f"{element} is not a stream")
        self.element = element


class ToCInvalidStreamTypeError(ToCStreamError):
    def __init__(self, element="Target stream", is_type: Optional[str] = None, expected_type: Optional[str] = None):
        super().__init__(
            f"{element} has unexpected type{f' {is_type}' if is_type is not None else ''}{f', expected type {expected_type}' if expected_type is not None else ''}")
        self.element = element
        self.is_type = is_type
        self.expected_type = expected_type


@dataclass
class File:
    toc: Root
    pages: dict[int, DataPage]

    @overload
    def get_data(self, path: str, stype: Literal[None] = ...) -> Iterable[DataPage]:
        ...

    @overload
    def get_data(self, path: str, stype: Literal[StreamType.Text] = ...) -> Iterable[TextPage]:
        ...

    @overload
    def get_data(self, path: str, stype: Literal[StreamType.Waveform] = ...) -> Iterable[WaveformPage]:
        ...

    def get_data(self, path: str, stype: Optional[StreamType] = None) -> Union[
        Iterable[DataPage], Iterable[TextPage], Iterable[WaveformPage]]:
        entry = self.toc.path(path)
        if not isinstance(entry, Stream):
            raise ToCEEntryIsNotAStreamError(element=path)
        if stype is not None and entry.stream_type != stype:
            raise ToCInvalidStreamTypeError(element=path, is_type=entry.stream_type.name, expected_type=stype.name)
        for pid in entry.page_ids:
            yield self.pages[pid]

    @staticmethod
    def from_binary(binio: BinaryIO, byte_order='<') -> File:
        toc_root, pages = read_from(binio, byte_order=byte_order)
        return File(toc_root, pages)
