from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import IntEnum
from typing import Dict

import numpy as np
import numpy.typing as npt

from pydapsys.toc.display import DisplayProperties
from pydapsys.toc.exceptions import ToCNoSuchChildError, ToCPathError
from pydapsys.util.structs import CaseInsensitiveDict, CaseInsensitiveDictView


class EntryType(IntEnum):
    """
    Type of an entry in the table of contents
    """
    Folder = 1,
    Stream = 2


@dataclass
class Entry(ABC):
    """
    Represents an entry of the table of contents
    """
    name: str
    """name of the entry in the ToC"""
    id: int
    """ToC id of the entry"""

    @property
    @abstractmethod
    def entry_type(self) -> EntryType:
        """Type of the entry"""
        ...


@dataclass
class ChildContainer:
    """
    Abstract class for ToC entries that have children (Folders and root)
    """
    children: CaseInsensitiveDict[Entry]
    """Children of this entry"""

    @property
    def f(self) -> CaseInsensitiveDictView[Folder]:
        """View containing only sub folders of this entry"""
        return self.folders

    @property
    def folders(self) -> CaseInsensitiveDictView[Folder]:
        """View containing only sub folders of this entry"""
        return self.children.select(lambda _, v: v.entry_type == EntryType.Folder)

    @property
    def s(self) -> CaseInsensitiveDictView[Stream]:
        """View containing only streams of this entry"""
        return self.streams

    @property
    def streams(self) -> CaseInsensitiveDictView[Stream]:
        """View containing only streams of this entry"""
        return self.children.select(lambda _, v: v.entry_type == EntryType.Stream)

    @property
    def structure(self) -> Dict:
        """Returns a dictionary with subdictionaries and strings describing the structure of this objects children"""
        d = dict()
        for v in self.children.values():
            d[v.name] = v.structure if isinstance(v, ChildContainer) else f"{v.stream_type.name};{len(v.page_ids)}"
        return d

    def path(self, path: str) -> Entry:
        """Returns the Entry from the given relative path.
        :param path: Relative path to the target entry
        :returns: the target entry
        """
        splits = path.split('/', 1)
        selected_entry = self[splits[0]]
        if len(splits) == 1:
            return selected_entry
        elif isinstance(selected_entry, ChildContainer):
            return selected_entry.path(splits[1])
        raise ToCPathError(f"Cannot resolve path '{path}', as '{selected_entry.name}' does not have any children")

    def __getitem__(self, item: str) -> Entry:
        if not self.__contains__(item):
            raise ToCNoSuchChildError(missing_item=item)
        return self.children[item]

    def __contains__(self, item: str) -> bool:
        return item in self.children


@dataclass
class Folder(ChildContainer, Entry):
    """
    Represents a folder in the ToC
    """

    @property
    def entry_type(self) -> EntryType:
        return EntryType.Folder


@dataclass
class Root(ChildContainer):
    """The root of the table of contents. It differentiates from a :class:`pydapsys.toc.entry.Folder`,
    as it does not have a ToC id and contains the footer string of the file."""
    name: str
    """name of the root"""
    footer: str
    """footer string. Usually contains the version and serial number of the Dapsys program the recording was created from"""


class StreamType(IntEnum):
    """
    Type of a stream
    """
    Waveform = 2
    Text = 3


@dataclass
class Stream(Entry):
    """
    Stream entry in the ToC.
    """
    stream_type: StreamType
    """Type of the stream"""
    open_at_start: bool
    """Indicates if Dapsys should open this stream at start"""
    page_ids: npt.NDArray[np.uint32]
    """Pages belonging to this tream"""
    display_properties: DisplayProperties
    """Display properties of this stream"""

    @property
    def entry_type(self) -> EntryType:
        return EntryType.Stream

    def __getitem__(self, item) -> int:
        return self.page_ids[item]

    def __iter__(self):
        return iter(self.page_ids)

    def __contains__(self, item):
        return item in self.page_ids
