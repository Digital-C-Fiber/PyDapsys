class ExtraDependencyNotFoundError(Exception):
    package_name = "PyDapsys"

    def __init__(self, missing_name: str, missing_pypi: str, extra_name=None, msg=None, extra_msg=None):
        self.missing_name = missing_name
        self.missing_pypi = missing_pypi
        self.extra_name = extra_name
        self.msg = msg
        self.extra_msg = extra_msg

    def __str__(self):
        if self.msg is not None:
            return self.msg
        extra_text = f" Make sure that you installed the package-extra '{self.extra_name}' with {self.package_name}." if self.extra_name is not None else ""
        return f"Could not import the {self.missing_name} (pypi: '{self.missing_pypi}') package.{extra_text}{f' {self.extra_msg}' if self.extra_msg is not None else ''}"


try:
    import neo
except ImportError as e:
    raise ExtraDependencyNotFoundError("Neo", "neo", extra_name="neo") from e

from helper import DapsysToNeoHelper
from interface import INeoConverter
from ni_pulse_stim import NIPulseStimRecordingConverter
