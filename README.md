# PyDapsys - Read DAPSYS recordings with Python

[![PyPI](https://img.shields.io/pypi/v/pydapsys?style=for-the-badge)](https://pypi.org/project/pydapsys/)

PyDapsys is a package to read neurography recordings made with [DAPSYS](http://dapsys.net/) (Data Acquisition Processor System). It is based on a reverse-engineered specification of the binary data format used by the latest DAPSYS version.

Optionally, the library provides functionality to store loaded data into [Neo](https://github.com/NeuralEnsemble/python-neo) datastructures, from where they can be exported into various other formats.

## Installation

Either download the wheel file for offline installation or use pypi.

### Basic functionalities

Will only offer the data representation of PyDapsys, without ability to convert to Neo. Has only numpy as sole dependency. 

`pip install pydapsys`

`pip install {name_of_downloaded_wheel}.whl`

### With Neo converters

Install base library with additional dependencies required to load data into Neo datastructures. Writing Neo datastructures to some formats may require additional dependencies. Please see the Neo documentation for further information.

`pip install pydapsys[neo]`

`pip install {name_of_downloaded_wheel}.whl[neo]`

## Usage

### Quickstart

A DAPSYS file is made up of two parts: A sequential list of blocks or **pages**, which store either a text with a timestamp or a waveform with associated timestamps, and a table of contents (toc). The toc consists of **folders** and **streams**. Each page has an id unique in the context of the file. Streams in the toc have an array of ids of the pages belonging to the stream. A stream is either a text stream (referring only to text pages) or a data stream (referring only to recording pages).

#### Load a file
Use `File.from_binary` to read from a BinaryIO object.
```python
from pydapsys import read_file
from pathlib import Path
MY_DAPSYS_FILE = Path(".")/"to"/"my"/"dapsys_file.dps"
with open(MY_DAPSYS_FILE, 'rb') as file:
    file = read_file(file)
```
The `File` object has two fields, the root of the table of contents and a dictionary mapping the page ids to their respective pages.
##### Inspect file structure
To inspect the ToC structure of a loaded file, use the `structure` property of the toc `Root`, preferable together with `pprint`:
```python
import pprint
pprint.PrettyPrinter(indent=4).pprint(file.toc.structure)
```
This will print the structure, names and types of all elements in the table of contents. For Streams, the number of associated pages it also printed after their type.
#### Access data from a file
To access data, use the `File.get_data` method. The method takes a path from the toc structure (WITHOUT THE NAME OF THE ROOT!) and will return all associated pages.
Please note, that the path is  case insensitive
```python
from pydapsys.toc import StreamType
my_texts = list(file.get_data("myrecording/my text stream", stype=StreamType.Text))
my_waveforms = list(file.get_data("myrecording/somewhere else/ my waveform stream", stype=StreamType.Waveform))
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
from pydapsys.neo_converters import NIPulseStimRecordingConverter

# convert a recording to a neo block
neo_block = NIPulseStimRecordingConverter(file, grouping_tolerance=1e-9).to_neo()
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
