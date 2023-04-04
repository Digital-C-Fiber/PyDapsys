from io import BytesIO
from typing import io

import pytest

from pydapsys.binaryreader import DapsysBinaryReader
from pydapsys.read import _read_page
from tests.testdata.pages import textpage_a, TextPageTest


@pytest.mark.parametrize("testcase", [(textpage_a,)])
def test__read_text_page(testcase: TextPageTest):
    testcase = testcase[0]
    reader = DapsysBinaryReader(BytesIO(testcase.binary))
    read_text_page = _read_page(reader)
    assert read_text_page == testcase.expected
