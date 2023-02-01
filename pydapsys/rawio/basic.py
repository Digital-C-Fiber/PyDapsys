from __future__ import annotations

from io import SEEK_CUR
from struct import unpack, calcsize
from typing import BinaryIO, Union, Tuple, Literal, overload, Optional

from pydapsys.rawio import INT_STRUCTS, FLOAT_STRUCTS


def __read_nullaware(reader: BinaryIO, type_fmt: str, count: int, byte_order='<') -> Tuple:
    """
    Reads a number of binary values "null aware": The function will check if the read bytes for each value are unitized.

    Will read x values and compare each bytes with 'CD' * length of block. If the block is unitilized, the value will be set to None.
    Else the bytes will be unpacked.
    Example: To read 8 32-bit ints, the function will read 4 bytes 8 times. Each 4-byte block will be compared with 'CDCDCDCD'.
    If the comparison is true, the value will be set to None. Else it will unpack the bytes to an int.
    :param reader: Open binary reader to read from
    :param type_fmt: Type fmt string
    :param count: Number of values to read
    :param byte_order: byte order
    :return: Tuple containing the read objects
    """
    struct_str = byte_order + type_fmt
    data_size = calcsize(struct_str)
    null_bytes = bytes.fromhex('CD' * data_size)
    return tuple(unpack(struct_str, read_bytes)[0] if read_bytes != null_bytes else None for read_bytes in
                 (reader.read(data_size) for _ in range(count)))


def __read_direct(reader: BinaryIO, type_fmt: str, count: int, byte_order='<') -> Tuple:
    """
    Will read a number of values specified by the type fmt from a binary reader
    :param reader: Open binary reader
    :param type_fmt: Type fmt string of the data to read
    :param count: number of values to read
    :param byte_order: byte order
    :return: Tuple containing the read values
    """
    struct_str = byte_order + type_fmt * count
    return unpack(struct_str, reader.read(calcsize(struct_str)))


@overload
def read_tuple(reader: BinaryIO, type_fmt: INT_STRUCTS, count: int, byte_order: str = ...,
               check_null: Literal[False] = ...) -> Tuple[int, ...]:
    ...


@overload
def read_tuple(reader: BinaryIO, type_fmt: INT_STRUCTS, count: int, byte_order: str = ...,
               check_null: Literal[True] = ...) -> Tuple[Optional[int], ...]:
    ...


@overload
def read_tuple(reader: BinaryIO, type_fmt: FLOAT_STRUCTS, count: int, byte_order: str = ...,
               check_null: Literal[False] = ...) -> Tuple[float, ...]:
    ...


@overload
def read_tuple(reader: BinaryIO, type_fmt: FLOAT_STRUCTS, count: int, byte_order: str = ...,
               check_null: Literal[True] = ...) -> Tuple[Optional[float], ...]:
    ...


# We need this last overload as a fallback for mypy when you call the function with a generic string and / or bool as parameter
@overload
def read_tuple(reader: BinaryIO, type_fmt: str, count: int, byte_order: str = ..., check_null: bool = ...) -> Tuple:
    ...


def read_tuple(reader: BinaryIO, type_fmt: str, count: int, byte_order: str = '<',
               check_null: bool = False) -> Union[
    Tuple[float, ...], Tuple[int, ...], Tuple[Optional[float], ...], Tuple[Optional[int]]]:
    """
    Will read a tuple of values according to type_fmt.
    :param reader: Open binary reader
    :param type_fmt: Type fmt string
    :param count: Number of values to read
    :param byte_order: byte order
    :param check_null: If the function should check if each function is unitilized according to visual C++ (0xCDCDCDCD)
    :return:Tuple containig the read data
    """
    read_func = __read_nullaware if check_null else __read_direct
    unpacked_values = read_func(reader, type_fmt, count, byte_order=byte_order)
    return unpacked_values


@overload
def read_single(reader: BinaryIO, type_fmt: INT_STRUCTS, byte_order: str = ...,
                check_null: Literal[False] = ...) -> int:
    ...


@overload
def read_single(reader: BinaryIO, type_fmt: INT_STRUCTS, byte_order: str = ..., check_null: Literal[True] = ...) -> \
        Optional[int]:
    ...


@overload
def read_single(reader: BinaryIO, type_fmt: FLOAT_STRUCTS, byte_order: str = ...,
                check_null: Literal[False] = ...) -> float:
    ...


@overload
def read_single(reader: BinaryIO, type_fmt: FLOAT_STRUCTS, byte_order: str = ..., check_null: Literal[True] = ...) -> \
        Optional[float]:
    ...


# We need this last overload as a fallback for mypy when you call the function with a generic string and / or bool as parameter
@overload
def read_single(reader: BinaryIO, type_fmt: str, byte_order: str = ..., check_null: bool = ...) -> Optional[
    Union[float, int]]:
    ...


def read_single(reader: BinaryIO, type_fmt: str, byte_order: str = '<',
                check_null: bool = False) -> \
        Optional[Union[float, int]]:
    """
    Will read a single value according to type_fmt.
    :param reader: Open binary reader
    :param type_fmt: Type fmt string
    :param byte_order: byte order
    :param check_null: If the function should check if each function is unitilized according to visual C++ (0xCDCDCDCD)
    :return:Tuple containig the read data
    """
    return read_tuple(reader, type_fmt, 1, byte_order=byte_order, check_null=check_null)[0]


@overload
def read_u32(reader: BinaryIO, check_null: Literal[False] = ...,
             byte_order: str = ...) -> int:
    ...


@overload
def read_u32(reader: BinaryIO, check_null: Literal[True] = ..., byte_order: str = ...) -> Optional[int]:
    ...


def read_u32(reader: BinaryIO, check_null=False, byte_order='<') -> Optional[int]:
    """
    Will read a single u32 value
    :param reader: Open binary reader
    :param check_null: Wether to check for null
    :param byte_order:
    :return: An int or none.
    """
    return read_single(reader, 'I', check_null=check_null, byte_order=byte_order)


@overload
def read_f32(reader: BinaryIO, check_null: Literal[False] = ...,
             byte_order: str = ...) -> float:
    ...


@overload
def read_f32(reader: BinaryIO, check_null: Literal[True] = ..., byte_order: str = ...) -> Optional[float]:
    ...


def read_f32(reader: BinaryIO, check_null=False, byte_order='<') -> Optional[float]:
    """
    Will read a single f32 value
    :param reader: Open binary reader
    :param check_null: Wether to check for null
    :param byte_order:
    :return: A float or none.
    """
    return read_single(reader, 'f', check_null=check_null, byte_order=byte_order)


@overload
def read_f64(reader: BinaryIO, check_null: Literal[False] = ...,
             byte_order: str = ...) -> float:
    ...


@overload
def read_f64(reader: BinaryIO, check_null: Literal[True] = ..., byte_order: str = ...) -> \
        Optional[float]:
    ...


def read_f64(reader: BinaryIO, check_null=False, byte_order='<') -> Optional[float]:
    """
    Will read a single f64 value
    :param reader: Open binary reader
    :param check_null: Wether to check for null
    :param byte_order:
    :return: A float or none.
    """
    return read_single(reader, 'd', check_null=check_null, byte_order=byte_order)


def read_ubyte(reader: BinaryIO, byte_order: str = '<') -> int:
    """
    Reads the value of a single byte as usigned value
    :param reader: Open binary reader
    :param byte_order: byte order
    :return: An integer representing the value of the read byte
    """
    return read_single(reader, 'B', check_null=False, byte_order=byte_order)


def read_ubytes(reader: BinaryIO, count: int, byte_order: str = '<') -> Tuple[int, ...]:
    """
    Reads the multiple bytes as usigned value
    :param reader: Open binary reader
    :param count: Number of bytes to read
    :param byte_order: byte order to use when reading
    :return: A tuple of integer values representing the individual usnigned values of the read bytes
    """
    return read_tuple(reader, 'B', count, check_null=False, byte_order=byte_order)


def skip_32(reader: BinaryIO, count=1):
    """
    Advances the reader in 32-bit steps
    :param reader: Open binary reader
    :param count: Number of 32-bit blocks to skip, defaults to 1
    """
    reader.seek(4 * count, SEEK_CUR)


def skip_64(reader: BinaryIO, count=1):
    """
    Advances the reader in 64-bit steps
    :param reader: Open binary reader
    :param count: Number of 64-bit blocks to skip, defaults to 1
    """
    reader.seek(8 * count, SEEK_CUR)


def read_bool(reader: BinaryIO) -> bool:
    """
    Reads a dapsys bool (reads 1 byte, then skips 3 additional bytes)
    :param reader: Open binary reader
    :return: Value of the read bool
    """
    v = reader.read(1)
    reader.seek(3, SEEK_CUR)
    return v != 0
