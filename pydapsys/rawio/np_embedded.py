from __future__ import annotations

from typing import BinaryIO

import numpy as np
from numpy import typing as npt

from pydapsys.rawio.basic import read_u32


def _read_nparray(reader: BinaryIO, dtype: np.dtype, byte_order='<') -> npt.NDArray:
    """
    Reads an u32 value as x and then uses numpy fromfile to read x following values of the specified type
    :param reader: Open binary reader
    :param dtype: Dtype of the values to read
    :param byte_order: byte order to use when reading
    :return: Numpy array containing the values read
    """
    value_counts = read_u32(reader, byte_order=byte_order)
    return np.fromfile(reader, dtype=dtype.newbyteorder(byte_order), count=value_counts)


def read_f32_nparray(reader: BinaryIO, byte_order='<') -> npt.NDArray[np.float32]:
    """
    Reads an u32 value as x and then uses numpy fromfile to read x following f32 values of the specified type
    :param reader: Open binary reader
    :param byte_order: byte order to use when reading
    :return: Numpy array containing the read np.float32 values
    """
    return _read_nparray(reader, np.dtype(np.float32), byte_order=byte_order)


def read_f64_nparray(reader: BinaryIO, byte_order='<') -> npt.NDArray[np.float64]:
    """
    Reads an u32 value as x and then uses numpy fromfile to read x following f64 values of the specified type
    :param reader: Open binary reader
    :param byte_order: byte order to use when reading
    :return: Numpy array containing the read np.float64 values
    """
    return _read_nparray(reader, np.dtype(np.float64), byte_order=byte_order)


def read_u32_nparray(reader: BinaryIO, byte_order='<') -> npt.NDArray[np.uint32]:
    """
    Reads an u32 value as x and then uses numpy fromfile to read x following u32 values of the specified type
    :param reader: Open binary reader
    :param byte_order: byte order to use when reading
    :return: Numpy array containing the read np.uint32 values
    """
    return _read_nparray(reader, np.dtype(np.uint32), byte_order=byte_order)
