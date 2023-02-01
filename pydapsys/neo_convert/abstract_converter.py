from abc import ABC, abstractmethod
from typing import Mapping, Sequence, Union, Optional, Iterable, List, Dict

import neo
import numpy as np
import numpy.typing as npt
import quantities as pq
from pydapsys.neoconverter import recording_segment_end

from pydapsys.page import DataPage, WaveformPage
from pydapsys.toc.entry import Root, Stream, StreamType
from pydapsys.util.floats import float_comp


class DapsysToNeoConverter(ABC):
    """ Converter to put Dapsys recordings into the neo structure

    This abstract base class provides common functionalities to transform Dapsys streams into common neo structures
    :param toc: Root of the table of contents
    :type toc: class:`pydapsys.toc.entry.Root`
    :param pages: Mapping between the id of the data page and itself
    :type toc: class:`typing.Mapping[int, pydapsys.page.DataPage]`
    """

    def __init__(self, toc: Root, pages: Mapping[int, DataPage]):
        self.toc = toc
        self.pages = pages

    @abstractmethod
    def to_neo(self) -> neo.Block:
        """
        Create a neo structure based on the given recording
        :return: A neo block containing the data from the recording
        """
        ...

    def _pageids_to_event(self, page_ids: Union[Sequence[int], npt.NDArray[np.uint32]], name: str = "") -> neo.Event:
        """Converts data from a sequence (or numpy array) of page ids to a neo event.
        The labels will be taken from the page text and the event times from the first timestamp (timestamp_a)
        :param page_ids: Page ids of the comment pages
        :param name: name of the returned neo event
        :return: A neo event containing the text of the comment pages as labels and their first timestamps as times
        """
        times = np.empty(len(page_ids), dtype=np.float64)
        comments = np.empty(len(page_ids), dtype=str)
        for i in range(len(page_ids)):
            times[i] = self.pages[page_ids[i]].timestamp_a
            comments[i] = self.pages[page_ids[i]].comment
        return neo.Event(times=times, labels=comments, units=pq.second, name=name, copy=False)

    def textstream_to_event(self, stream: Stream, name: Optional[str] = None) -> neo.Event:
        """Converts data from a text stream to a neo event.

        Labels of the event will be the text from the pages and the event times the first timestamp (timestamp_a) from them.

        :param stream: Stream to convert
        :param name: name of the returned neo event, defaults to the name of the passed stream
        :return: A neo event containing the text of the streams comment pages as labels and their first timestamps as times
        """
        if stream.stream_type != StreamType.Text:
            raise ValueError(f"StreamType.Text required for this operation, not {stream.stream_type.name}")
        return self._pageids_to_event(stream.page_ids, name=stream.name if name is None else name)

    def _pageids_to_spiketrain(self, page_ids: Union[Sequence[int], npt.NDArray[np.uint32]], t_stop: float,
                               name: str = "") -> neo.SpikeTrain:
        """Puts data from comment pages into a spike train. Requires an additional parameter t_stop for the equally named,
         required parameter on :class:`neo.SpikeTrain`. t_stop must be greater than the last timestamp of the train.

         The times of the spike train will be taken from the timestamp_a of the given comment pages.

        :param page_ids:  Page ids of the comment pages
        :param t_stop: t_stop parameter to set on :class:`neo.SpikeTrain`
        :param name: Name of the spike train, optional.
        :return: A spike train build from the comment pages
        """
        return neo.SpikeTrain(
            times=np.fromiter((comment.timestamp_a for comment in (self.pages[pid] for pid in page_ids)),
                              dtype=np.float64, count=len(page_ids)), name=name, units=pq.second, t_stop=t_stop,
            copy=False)

    def textstream_to_spiketrain(self, stream: Stream, t_stop: float, name: Optional[str] = None) -> neo.SpikeTrain:
        """Puts data from a text stream into a spike train. Requires an additional parameter t_stop for the equally named,
         required parameter on :class:`neo.SpikeTrain`. t_stop must be greater than the last timestamp of the train.

         The times of the spike train will be taken from the timestamp_a of the streams comment pages.
        :param stream: The stream to convert
        :param t_stop: t_stop parameter to set on :class:`neo.SpikeTrain`
        :param name: Name of the spike train. Will default to the name of the stream
        :return: A spike train build from the given text stream
        """
        if stream.stream_type != StreamType.Text:
            raise ValueError(f"StreamType.Text required for this operation, not {stream.stream_type.name}")
        return self._pageids_to_spiketrain(stream.page_ids, t_stop, name=stream.name if name is None else name)

    def _pageids_to_events_by_comment_text(self, page_ids: Union[Sequence[int], npt.NDArray[np.uint32]]) -> Iterable[
        neo.Event]:
        """Orders a number of comment pages by their text and emits one event for each unique text.
        The times are loaded from the comment pages timestamp_a, will have no labels and the name of the events will be
        the unique text.
        :param page_ids: Ids of the comment pages
        :return: An iterable of neo events
        """
        comment_string_to_timestamps: Dict[str, List[float]] = dict()
        for comment in (self.pages[pid] for pid in page_ids):
            comment_string_to_timestamps.setdefault(comment.comment, list()).append(comment.timestamp_a)
        for comment_string, comment_timestamps in comment_string_to_timestamps.items():
            yield neo.Event(times=np.array(comment_timestamps, dtype=np.float64), units=pq.second, name=comment_string,
                            copy=False)

    def textstream_to_events_by_comment_text(self, stream: Stream) -> Iterable[neo.Event]:
        """Orders the comment pages of a text stream by their text and emits one event for each unique text.
        The times are loaded from the comment pages timestamp_a, will have no labels and the name of the events will be
        the unique text.
        :param stream: A text stream to convert
        :return: An iterable of neo events
        """
        if stream.stream_type != StreamType.Text:
            raise ValueError(f"StreamType.Text required for this operation, not {stream.stream_type.name}")
        return self._pageids_to_events_by_comment_text(stream.page_ids)

    def _group_recordingsegments(self, rec_pages: Iterable[WaveformPage], tolerance: float = 1e-5) -> Iterable[
        List[WaveformPage]]:
        """Groups consecutive recording pages into lists, if the difference between the end of the last page and the start
        of the next one is less than the threshold and they have the same sampling interval
        :param rec_pages: Recording pages to group. Must be in orderly sequence.
        :param tolerance: Tolerance for grouping, defaults to 1e-5
        :return: An iterable of lists containing grouped recording pages
        """
        page_iter = iter(rec_pages)
        current_set: List[WaveformPage] = [next(page_iter)]
        for page in page_iter:
            if not (float_comp(current_set[-1].interval, page.interval) and \
                    not float_comp(recording_segment_end(current_set[-1]) + current_set[-1].interval,
                                   page.timestamps[0], epsilon=tolerance)):
                current_set.append(page)
            else:
                yield current_set
                current_set = [page]
        yield current_set

    def waveformstream_to_analogsignals(self, stream: Stream, tolerance: float = 1e-5) -> Iterable[neo.AnalogSignal]:
        """ Groups consecutive pages of a waveform stream together, based on the given tolerance and creates one
        AnalogSignal from each group.

        :param stream: Data stream to convert
        :param tolerance: Tolerance for grouping
        :return: Analog signals created from grouped recording pages
        """
        if stream.stream_type != StreamType.Waveform:
            raise ValueError(f"StreamType.Waveform required for this operation, not {stream.stream_type.name}")
        for segment_group in self._group_recordingsegments((self.pages[pid] for pid in stream.page_ids),
                                                           tolerance=tolerance):
            continuous = np.concatenate(list(segment.values for segment in segment_group)).ravel()
            yield neo.AnalogSignal(continuous, pq.volt,
                                   t_start=segment_group[0].timestamps[0] * pq.second,
                                   sampling_period=segment_group[0].interval * pq.second, copy=False)
