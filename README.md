# PyDapsys - Read DAPSYS recordings with Python

PyDapsys is a package to read neurography recordings made with [DAPSYS](http://dapsys.net/) (Data Acquisition Processor System). It is based on a reverse-engineered specification of the binary data format used by the latest DAPSYS version.

Optionally, the library provides functionality to store loaded data into [Neo](https://github.com/NeuralEnsemble/python-neo) datastrucutres, from where they can be exported into various other formats.

## Installation

Download the latest release from the Github releases page.

### Basic functionalities

Will only offer the data representation of PyDapsys, without ability to convert to Neo. Has only numpy as sole dependency. 

`pip install {name_of_downloaded_wheel}.whl`

### With Neo converters

Install base library with additional dependencies required to load data into Neo datastructures. Writing Neo datastructures to some formats may require additional dependencies. Please see the Neo documentation for further information.

`pip install {name_of_downloaded_wheel}.whl[neo]`

## Usage

### Basics

A Dapsys file is made up of two parts: A sequential list of blocks or **pages**, which store either a text with a timestamp or a waveform with associated timestamps, and a table of contents (toc). The toc consists of **folders** and **streams**. Each page has an id unique in the context of the file. Streams in the toc have an array of ids of the pages belonging to the stream. A stream is either a text stream (referring only to text pages) or a data stream (referring only to recording pages).

#### Load a file

Use `read_file` to get the root of the table of contents and a dictionary which maps from the page ids to the object representing the page itself.

```python
from pydapsys.read import read_file
from pathlib import Path
MY_DAPSYS_FILE = Path(".")/"to"/"my"/"dapsys_file.dps"
toc_root, pages = read_file(MY_DAPSYS_FILE)
```

The `toc_root` object will have children, either folders (which, in turn, can have additional children) or streams. You can access the childrens by using the index-operator. Access to children is case-insensitive. This is done for conveniance and does not inlfuence the correctness, as DAPSYS itself does not allow two objects of the same (case insensitive) name to exist on the same hierachy level. For typed access you can use either `.f` to get folders or `.s` to only get streams:

```python
comment_stream = toc_root["comments"] # Will return the stream Comments, but is typed as generic stream
comment_stream = toc_root.s["coMMents"] # Will return the stream Comments, typed as Stream
top_folder = toc_root.f["Folder"] # will return the folder Folder
top_folder = toc_root.f["comments"] # will fail (exception), because comments is not a folder

# iterate over all folders:
for folder in toc_root.f.values():
    ...

# iterate over all streams:
for stream in toc_root.s.values():
    ...
```

#### Access data from a file

To get text data from a file, get the datastream object from the toc and access  its  `page_ids` property. For conveniance, the `__getitem__`, `__iter__` and `__contains__` methods of stream objects have been overloaded to return the result of the same operation on `page_ids`. From there, you can get the corresponding pages from the `pages` dict:

```python
from pydapsys.toc.entry import StreamType

def get_pages(stream, expected_stream_type: StreamType):
    if stream.entry_type != expected_stream_type:
        raise Exception(f"{stream.name} is not a {expected_stream_type.name} stream, but {stream.stream_type.name}")
    return [pages[page_id] for page_id in stream] # or [pages[page_id] for page_id in stream.page_ids]

text_stream = ...
text_pages = get_pages(text_stream, StreamType.Text)

waveform_stream = ...
waveform_pages = get_pages(waveform_stream, StreamType.Waveform)
```

##### Text pages

A text page consists of three fields:

* `text`: The text stored in the page, string

* `timestamp_a`: The first timestamp of the page, float64 (seconds)

* `timestamp_b`: The second timestamp of the page (float64, seconds), which sometimes is not presented and is thus set to None

##### Waveform pages

Waveform pages consist of three fields:

* `values`: Values of the waveform, float32 (volt)

* `timestamps`: Timestamps corresponding to `values`, float64 (seconds)

* `interval`: Interval between values, float64 (seconds)

In **continuously sampled waveforms**, only the timestamp of the first value will be present, in addition to the sampling `interval`. The timestamps of the other values can be calculated by this two values.

**Irregularly sampled waveforms** will have one timestamp for each value, but no `interval`.

## Neo converters

The module `pydapsys.neo_convert` contains classes to convert a Dapsys recording to the Neo format. **IMPORTANT: importing the module without installing neo first will raise an exception**

As Dapsys files may have different structures, depending on how it was configured and what hardware is used, different converters are required for each file structure.

Currently there is only one converter available, for recordings made using a NI Pulse stimulator.

### NI Pulse stimulator

Converter class for Dapsys recording created using an NI Pulse stimulator. Puts everything into one neo sequence. 
Waveform pages of the continuous recording are merged if the difference between a pair of consecutive pages is less than a specified threshold (`grouping_tolerance`).

```python
from pydapsys.neo_convert.ni_pulse_stim import NIPulseStimulatorToNeo

# convert a recording to a neo block
neo_block = NIPulseStimulatorToNeo(toc_root, pages, grouping_tolerance=1e-9).to_neo()
```

#### Expected file structure

{stim_folder} must be one of "NI Puls Stimulator", "pulse stimulator", "NI Pulse stimulator", but can be changed by adding entries to `NIPulseStimulatorToNeo.stim_foler_names`

* Root
  
  * [Text] Comments -> Converted into a single event called "comments"
  
  * {stim_folder}
    
    * [Text] Pulses -> Converted into one neo event streams, one per unique text
    
    * [Waveform] Continuous recording -> Converted into multiple AnalogSignals
    
    * Responses
      
      * Tracks for All Responses -> Optional. Will silently ignore spike trains if this folder does not exist
        
        * ... [Text] tracks... -> Converted into spike trains


