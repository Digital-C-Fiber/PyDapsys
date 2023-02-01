from __future__ import annotations

from typing import MutableMapping, Iterator, TypeVar, Generic, Dict, Optional, Callable, Set

_VT = TypeVar("_VT")
_ST = TypeVar("_ST")


class CaseInsensitiveDict(MutableMapping[str, _VT], Generic[_VT]):
    """
    A class  wrapping a dict with string keys in a read-only fashion. Provides case-insensitive access to the items.
    """

    def __init__(self, wrap_dict: Optional[Dict[str, _VT]] = None):
        self._dict = wrap_dict if wrap_dict is not None else dict()

    @staticmethod
    def from_dict(data_dict: Dict[str, _VT]) -> CaseInsensitiveDict[_VT]:
        return CaseInsensitiveDict[_VT](wrap_dict={k.lower(): v for k, v in data_dict.items()})

    @property
    def backing_dict(self) -> Dict[str, _VT]:
        return self._dict

    def __contains__(self, __k: object) -> bool:
        if type(__k) is str:
            return self.transform_key(__k) in self._dict
        return False

    def __setitem__(self, __k: str, __v: _VT) -> None:
        """
        Will always raise an exception
        """
        raise NotImplementedError(
            "__setitem__ is not supported on CaseInsensitiveDict to prevent inconsistent state between views.")

    def __delitem__(self, __k: str) -> None:
        """
        Will always raise an exception
        """
        raise NotImplementedError(
            "__delitem__ is not supported on CaseInsensitiveDict to prevent inconsistent state between views.")

    def __getitem__(self, __k: str) -> _VT:
        return self._dict[self.transform_key(__k)]

    def __len__(self) -> int:
        return len(self._dict)

    def __iter__(self) -> Iterator[str]:
        return iter(self._dict)

    def transform_key(self, __k: str) -> str:
        return __k.lower()

    def select(self, selector: Callable[[str, _VT], bool]) -> CaseInsensitiveDictView[_VT]:
        """
        Returns a view of the dictionary only containing the items for which selector returned true
        :param selector: Function for selecting items that should be present in the dict view
        :return: A dict view
        """
        return CaseInsensitiveDictView(self, {k for k, v in self.items() if selector(k, v)})



class CaseInsensitiveDictView(MutableMapping[str, _VT], Generic[_VT]):
    """
    Provides view capabilities for :class:`pydapsys.util.structs.CaseInsensitiveDict`
    """

    def __init__(self, source: CaseInsensitiveDict[_VT], elements: Set[str]):
        self._source = source
        self._elements = elements

    def __setitem__(self, __k: str, __v: _VT) -> None:
        raise NotImplementedError(
            "__setitem__ is not supported on CaseInsensitiveDictView to prevent inconsistent state between views.")

    def __delitem__(self, __k: str) -> None:
        raise NotImplementedError(
            "__delitem__ is not supported on CaseInsensitiveDictView to prevent inconsistent state between views.")

    def __getitem__(self, __k: str) -> _VT:
        if self._source.transform_key(__k) not in self._elements:
            raise KeyError(f"Key {__k} is not contained in this view")
        return self._source[__k]

    def __len__(self) -> int:
        return len(self._elements)

    def __iter__(self) -> Iterator[str]:
        return iter(self._elements)
