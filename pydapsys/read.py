from typing import BinaryIO, Tuple, Dict

from pydapsys.page import DataPage, PageType, TextPage, WaveformPage
from pydapsys.rawio.basic import read_u32, read_f64, read_bool, skip_64, skip_32, read_ubytes
from pydapsys.rawio.embedded import read_str
from pydapsys.rawio.np_embedded import read_f32_nparray, read_f64_nparray, read_u32_nparray
from pydapsys.toc.entry import Entry, EntryType, Folder, Root, StreamType, Stream
from pydapsys.toc.plot import PlotConfig, PlotType, LatencyPlotUnit, PointStyle, RGBA8
from pydapsys.util.structs import CaseInsensitiveDict


def _read_plot_config(file: BinaryIO) -> PlotConfig:
    """
    Reads a plot configuration from a binary file
    :param file: Opened binary file to read from
    :return: The read plot config object
    """
    plot_type = PlotType(read_u32(file))
    hist_interval = read_f64(file)
    latency_unit = LatencyPlotUnit(read_u32(file))
    latency_reference = read_u32(file)
    recording_unit = read_str(file)
    point_style = PointStyle(read_u32(file))
    r, g, b, a = read_ubytes(file, 4)
    hist_begin = read_f64(file)
    return PlotConfig(plot_type, hist_interval, latency_unit, latency_reference, recording_unit, point_style,
                      RGBA8(r=r, g=g, b=b, a=a),
                      hist_begin)


def _read_toc_entry(file: BinaryIO) -> Entry:
    """
    Reads an entry from the table of contents. Children will be read recursively.
    :param file: Opened binary file to read from
    :return: The entry, populated with its children (if any)
    """
    type = EntryType(read_u32(file))
    name = read_str(file)
    skip_32(file)
    id = read_u32(file)
    if type == EntryType.Folder:
        child_count = read_u32(file)
        children = {entry.name: entry for entry in
                    (_read_toc_entry(file) for _ in range(child_count))}
        return Folder(id=id, name=name, children=CaseInsensitiveDict.from_dict(children))
    elif type == EntryType.Stream:
        stream_type = StreamType(read_u32(file))
        plot_config = _read_plot_config(file)
        open_at_start = read_bool(file)
        page_ids = read_u32_nparray(file)
        return Stream(id=id, name=name, stream_type=stream_type, open_at_start=open_at_start, plot_config=plot_config,
                      page_ids=page_ids)
    else:
        raise Exception(f"Unhandled entry type {type}")


def _read_toc(file: BinaryIO) -> Root:
    """
    Reads the Root of the table of contents and recursively all further elements of it.
    :param file: Opened binary file to read from
    :return: The root of the ToC
    """
    root_name = read_str(file)
    skip_64(file)
    element_count = read_u32(file)
    children = {entry.name: entry for entry in
                (_read_toc_entry(file) for _ in range(element_count))}
    footer = read_str(file)
    return Root(name=root_name, footer=footer, children=CaseInsensitiveDict.from_dict(children))


def _read_page(file: BinaryIO) -> DataPage:
    """
    Reads a page. Dynamically creates either a text page or a recording page, depending on the read page type.
    :param file: Opened binary file to read from
    :return: A DataPage, either a TextPage or a RecordingPage, depending on the read page type
    """
    type = PageType(read_u32(file))
    id = read_u32(file)
    ref = read_u32(file, check_null=True)
    if type == PageType.Text:
        comment = read_str(file)
        ts_a = read_f64(file)
        ts_b = read_f64(file, check_null=True)
        return TextPage(type=type, id=id, reference_id=ref, text=comment, timestamp_a=ts_a, timestamp_b=ts_b)
    elif type == PageType.Waveform:
        values = read_f32_nparray(file)
        timestamps = read_f64_nparray(file)
        tail = read_f64(file, check_null=True)
        skip_64(file, count=3)
        return WaveformPage(type=type, id=id, reference_id=ref, values=values, timestamps=timestamps,
                            interval=tail)
    else:
        raise Exception(f"Unhandled page type {type}")


def read_file(file) -> Tuple[Root, Dict[int, DataPage]]:
    """
    Reads a Dapsys recording file and returns the root of the table of contents and an dictionary mapping from a datapage
    id to the respective datapage object
    :param file: File to read from. Must be openable.
    :return: Root of the ToC, DataPage mapping
    """
    with open(file, "br") as file:
        file.seek(0x30)
        page_count = read_u32(file)
        pages = {page.id: page for page in (_read_page(file) for _ in range(page_count))}
        root = _read_toc(file)
    return root, pages
