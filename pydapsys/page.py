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
    def irregular_recording(self) -> bool:
        return len(self.timestamps) == len(self.values)
