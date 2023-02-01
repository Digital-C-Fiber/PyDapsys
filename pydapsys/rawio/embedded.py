from __future__ import annotations

from typing import BinaryIO, Tuple, overload, Union

from pydapsys.rawio import INT_STRUCTS, FLOAT_STRUCTS
from pydapsys.rawio.basic import read_u32, read_tuple


@overload
def read_array(reader: BinaryIO, type_fmt: INT_STRUCTS, byte_order: str = ...) -> Tuple[int, ...]:
    ...


@overload
def read_array(reader: BinaryIO, type_fmt: FLOAT_STRUCTS, byte_order: str = ...) -> Tuple[float, ...]:
    ...


def read_array(reader: BinaryIO, type_fmt: str, byte_order: str = '<') -> Union[Tuple[int, ...], Tuple[float, ...]]:
    """
    Reads an u32 value as x and then the following x values according to type fmt
    :param reader: Open binary reader
    :param type_fmt: Type fmt of the values
    :param byte_order: byte order
    :return: Tuple containing x values
    """
    value_counts = read_u32(reader, byte_order=byte_order)
    return read_tuple(reader, type_fmt, count=value_counts, check_null=False, byte_order=byte_order)


def read_u32_array(reader: BinaryIO, byte_order: str = '<') -> Tuple[int, ...]:
    """
    Reads a single u32 value as x and then the following x u32 values as an array
    :param reader: Open binary reader
    :param byte_order: byte order
    :return: Tuple containing x int values
    """
    return read_array(reader, 'I', byte_order=byte_order)


def read_f32_array(reader: BinaryIO, byte_order: str = '<') -> Tuple[float, ...]:
    """
    Reads a single u32 value as x and then the following x f32 values as an array
    :param reader: Open binary reader
    :param byte_order: byte order
    :return: Tuple containing x float values
    """
    return read_array(reader, 'f', byte_order=byte_order)


def read_f64_array(reader: BinaryIO, byte_order: str = '<') -> Tuple[float, ...]:
    """
    Reads a single u32 value as x and then the following x f64 values as an array
    :param reader: Open binary reader
    :param byte_order: byte order
    :return: Tuple containing x float values
    """
    return read_array(reader, 'd', byte_order=byte_order)


def read_str(reader: BinaryIO, byte_order='<', encoding='latin_1') -> str:
    """
    Reads a single u32 value as x and then the following x bytes and decodes them as string
    :param reader: Open binary reader
    :param byte_order: byte order
    :param encoding: Encoding to use when decoding the bytes, defaults to 'latin_1'
    :return: The decoded string
    """
    length = read_u32(reader, byte_order=byte_order)
    str_bytes = reader.read(length)
    return str_bytes.decode(encoding=encoding)
