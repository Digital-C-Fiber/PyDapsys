from dataclasses import dataclass
from enum import IntEnum


class PointStyle(IntEnum):
    """
    Plot point styles
    """
    Simple_Dot = 0x15
    Solid_Circle = 0x0A
    Empty_Circle = 0x09
    Solid_Square = 0x02
    Empty_Square = 0x01
    NA = 0xFFFFFFFF


class LatencyPlotUnit(IntEnum):
    """
    Units used in the latency plot (If applicable)
    """
    MilliSec = 0
    Seconds = 1
    Hertz = 2


class PlotType(IntEnum):
    """
    Plot type
    """
    Normal = 0
    Instantaneous = 1
    Histogram = 2
    Relative_Latency = 3


@dataclass
class RGBA8(object):
    r: int
    g: int
    b: int
    a: int = 0


@dataclass
class PlotConfig(object):
    """Configuration of a stream plot"""
    plot_type: PlotType
    histogram_interval: float
    latency_unit: LatencyPlotUnit
    latency_reference: int
    unit: str
    point_style: PointStyle
    waveform_color: RGBA8
    histogram_begin: float
