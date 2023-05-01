from datetime import datetime
from typing import Optional, Iterable

import neo

from pydapsys.file import File
from pydapsys.neo_converters.helper import DapsysToNeoHelper
from pydapsys.neo_converters.interface import INeoConverter
from pydapsys.toc.entry import Folder, Stream, StreamType


class NIPulseStimRecordingConverter(DapsysToNeoHelper, INeoConverter):
    """Converter class for Dapsys recording created using an NI Pulse stimulator. Puts everything into one neo sequence.
    Waveform pages of continuous recording are merged if the difference between a pair of consecutive pages is less than a specified threshold.


    Expected structure is:

    - Root
        - Comments -> Converted into an Event
        - [stim_folder_name]
            - Pulses -> Converted into one neo event streams, one per unique name
            - Continuous recording -> Converted into multiple AnalogSignals
            - Responses
                - Tracks for All Responses -> Optional. If it doesn't exist, there simply will be no spike trains
                    - ...Track text streams... -> Will be converted into one spike train each

    :param file: PyDapsys file object
    :param grouping_tolerance: Maximum delta (in seconds) between two consecutive pages to group them together, defaults to 1e-9
    :type grouping_tolerance: float
    """
    stim_foler_names = ["NI Puls Stimulator", "pulse stimulator", "NI Pulse stimulator"]
    """valid stimulator names for this converter"""

    def __init__(self, file: File, grouping_tolerance=1e-9):
        """constructor method"""
        super().__init__(file)
        self.grouping_tolerance = grouping_tolerance

    @property
    def stimulator_folder(self) -> Folder:
        """
        Returns the folder of the stimulator.

        Looks in :attr:`self.file` for a folder with one of the keys of :attr:`self.stim_folder_names` and returns the first match
        :return:The folder object of the stimulator
        """
        candidates = self.file.toc.folders
        for stim_name in self.stim_foler_names:
            if stim_name in candidates:
                return candidates[stim_name]
        raise Exception(f"Could not find a fitting stimulator name: {self.file.toc.children.keys()}")

    @property
    def comment_stream(self) -> Stream:
        """
        Returns the stream containing the comments of the recording (root/comments)
        :return: Comment stream
        """
        return self.file.toc.s["comments"]

    @property
    def track_textstreams(self) -> Iterable[Stream]:
        """
        Yields the streams containing sorted tracks

        Looks in root/[stimulator]/responses/tracks for all responses/ for any streams and returns them.
        root/[stimulator]/responses must exist, the function will silently ignore missing "tracks for all responses".
        :return: Streams containing sorted tracks
        """
        if "tracks for all responses" in self.stimulator_folder.f["responses"].folders:
            for pulse_stream in self.stimulator_folder.f["responses"].f["tracks for all responses"].streams.values():
                if pulse_stream.stream_type == StreamType.Text:
                    yield pulse_stream

    def to_neo(self, block_name="DAPSYS recording", segment_name="Main segment",
               file_datetime: Optional[datetime] = None, rec_datetime: Optional[datetime] = None) -> neo.Block:
        """
        Attemps to read the data of the recording into a neo structure.
        :param block_name: Name of the neo Block that will be returned
        :param segment_name: Name of the sole sequence contained in the block
        :param file_datetime: File datetime to set on the neo block and sequence. If none, will be set to unix-epoch 0
        :param rec_datetime: Recording datetime to set on the neo block and sequence. If none, will be set to unix-epoch 0
        :return: A neo block structured according to classdoc.
        """
        file_datetime = datetime.fromtimestamp(0) if file_datetime is None else file_datetime
        rec_datetime = datetime.fromtimestamp(0) if rec_datetime is None else rec_datetime
        neo_block = neo.Block(name=block_name, file_datetime=file_datetime, rec_datetime=rec_datetime)
        neo_segment = neo.Segment(name=segment_name, file_datetime=file_datetime, rec_datetime=rec_datetime)
        neo_block.segments.append(neo_segment)
        stim_folder = self.stimulator_folder
        for analogsignal in self.waveformstream_to_analogsignals(stim_folder.s["continuous recording"],
                                                                 tolerance=self.grouping_tolerance):
            analogsignal.set_parent(neo_segment)
            neo_segment.analogsignals.append(analogsignal)
        for track_stream in self.track_textstreams:
            spike_train = self.textstream_to_spiketrain(track_stream, neo_segment.analogsignals[-1].t_stop)
            spike_train.set_parent(neo_segment)
            neo_segment.spiketrains.append(spike_train)
        for pulse in self.textstream_to_events_by_comment_text(stim_folder.s["Pulses"]):
            pulse.set_parent(neo_segment)
            neo_segment.events.append(pulse)
        comments = self.textstream_to_event(self.comment_stream)
        comments.set_parent(neo_segment)
        neo_segment.events.append(comments)
        return neo_block
