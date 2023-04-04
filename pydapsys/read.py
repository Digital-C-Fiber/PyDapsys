from typing import BinaryIO, Tuple, Dict

from pydapsys.binaryreader import DapsysBinaryReader
from pydapsys.page import DataPage, PageType, TextPage, WaveformPage
from pydapsys.toc.display import DisplayProperties, PlotType, LatencyPlotUnit, PointStyle, RGBA8
from pydapsys.toc.entry import Entry, EntryType, Folder, Root, StreamType, Stream
from pydapsys.util.structs import CaseInsensitiveDict


class BinaryElementTypeError(Exception):
    ...


class UnknownEntryTypeError(BinaryElementTypeError):
    ...


class UnknownPageTypeError(BinaryElementTypeError):
    ...


def _read_display_properties(file: DapsysBinaryReader) -> DisplayProperties:
    """
    Reads a block of display properties from a binary file
    :param file: Opened binary file to read from
    :return: The read plot config object
    """
    plot_type = PlotType(file.read_u32())
    hist_interval = file.read_f64()
    latency_unit = LatencyPlotUnit(file.read_u32())
    latency_reference = file.read_u32()
    recording_unit = file.read_str()
    point_style = PointStyle(file.read_u32())
    r, g, b, a = file.read_ubytes(4)
    hist_begin = file.read_f64()
    return DisplayProperties(plot_type, hist_interval, latency_unit, latency_reference, recording_unit, point_style,
                             RGBA8(r=r, g=g, b=b, a=a),
                             hist_begin)


def _read_toc_entry(file: DapsysBinaryReader) -> Entry:
    """
    Reads an entry from the table of contents. Children will be read recursively.
    :param file: Opened binary file to read from
    :return: The entry, populated with its children (if any)
    """
    entry_type = EntryType(file.read_u32())
    name = file.read_str()
    file.skip_32()
    entry_id = file.read_u32()
    if entry_type == EntryType.Folder:
        child_count = file.read_u32()
        children = {entry.name: entry for entry in
                    (_read_toc_entry(file) for _ in range(child_count))}
        return Folder(id=entry_id, name=name, children=CaseInsensitiveDict.from_dict(children))
    elif entry_type == EntryType.Stream:
        stream_type = StreamType(file.read_u32())
        display_properties = _read_display_properties(file)
        open_at_start = file.read_bool()
        page_ids = file.read_u32_nparray()
        return Stream(id=entry_id, name=name, stream_type=stream_type, open_at_start=open_at_start,
                      display_properties=display_properties,
                      page_ids=page_ids)
    else:
        raise UnknownEntryTypeError(f"Unhandled entry type {entry_type}")


def _read_toc(file: DapsysBinaryReader) -> Root:
    """
    Reads the Root of the table of contents and recursively all further elements of it.
    :param file: Opened binary file to read from
    :return: The root of the ToC
    """
    root_name = file.read_str()
    file.skip_64()
    element_count = file.read_u32()
    children = {entry.name: entry for entry in
                (_read_toc_entry(file) for _ in range(element_count))}
    footer = file.read_str()
    return Root(name=root_name, footer=footer, children=CaseInsensitiveDict.from_dict(children))


def _read_page(file: DapsysBinaryReader) -> DataPage:
    """
    Reads a page. Dynamically creates either a text page or a recording page, depending on the read page type.
    :param file: Opened binary file to read from
    :return: A DataPage, either a TextPage or a RecordingPage, depending on the read page type
    """
    page_type = PageType(file.read_u32())
    page_id = file.read_u32()
    ref = file.read_u32(check_null=True)
    if page_type == PageType.Text:
        comment = file.read_str()
        ts_a = file.read_f64()
        ts_b = file.read_f64(check_null=True)
        return TextPage(type=page_type, id=page_id, reference_id=ref, text=comment, timestamp_a=ts_a, timestamp_b=ts_b)
    elif page_type == PageType.Waveform:
        values = file.read_f32_nparray()
        timestamps = file.read_f64_nparray()
        tail = file.read_f64(check_null=True)
        file.skip_64(count=3)
        return WaveformPage(type=page_type, id=page_id, reference_id=ref, values=values, timestamps=timestamps,
                            interval=tail)
    else:
        raise UnknownPageTypeError(f"Unhandled page type {page_type}")


def read_from(binio: BinaryIO, byte_order='<') -> Tuple[Root, Dict[int, DataPage]]:
    """Reads a DAPSYS file from a readable binaryio object
    :param binio:  binary io to read from
    :param byte_order: Byte order to use when reading
    :returns: A tuple containing the Root of the table of contents and a dictionary mapping the page ids to their respective pages
    """
    dapsys_io = DapsysBinaryReader(binio, byte_order=byte_order)
    dapsys_io.skip(0x30)
    page_count = dapsys_io.read_u32()
    pages = {page.id: page for page in (_read_page(dapsys_io) for _ in range(page_count))}
    root = _read_toc(dapsys_io)
    return root, pages
