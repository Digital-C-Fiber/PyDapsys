from abc import ABC
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional

import numpy as np
import numpy.typing as npt


class PageType(IntEnum):
    """
    Type of the page
    """
    Waveform = 2
    Text = 3


@dataclass
class DataPage(ABC):
    """
    Shared attributes for various data pages of a Dapsys recording
    """
    type: PageType
    id: int
    reference_id: Optional[int]


@dataclass
class TextPage(DataPage):
    """
    Page containing some text and at least one timestamp.
    """
    text: str
    """Text contained in the page"""
    timestamp_a: float
    """First timestamp"""
    timestamp_b: Optional[float]
    """Second timestamp"""


@dataclass
class WaveformPage(DataPage):
    """
    Page containing datapoints from a recording. In a continuous recording, there will only be one timestamp for the first value,
    but will have an interval for the time between the values. Irregular recordings will have a timestamp for each value,
    but no interval
    """
    values: npt.NDArray[np.float32]
    timestamps: npt.NDArray[np.float64]
    interval: Optional[float]

    @property
    def is_irregular(self) -> bool:
        """
        returns True if the waveform is sampled irregularly
        """
        return self.interval is None

    @property
    def last_timestamp(self) -> float:
        """
        Retunrs the last timestamp of this page:
        If it is an irregular recording, it returns the last timestamp from :attr:`timestamps`
        If it is a regular recording, it calculates the last timestamp from the first timestamp, the length of :attr:`values` and :attr:`interval`
        """
        if self.is_irregular:
            return self.timestamps[-1]
        return self.timestamps[0] + (len(self.values) - 1) * self.interval
