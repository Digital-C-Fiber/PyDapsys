from io import SEEK_CUR
from struct import calcsize, unpack
from typing import BinaryIO, Tuple, overload, Literal, Optional, Union

import numpy as np
import numpy.typing as npt

INT_STRUCTS = Literal['b', 'B', 'h', 'H', 'i', 'I', 'l', 'L', 'n', 'N', 'P']
FLOAT_STRUCTS = Literal['e', 'f', 'd']


class DapsysBinaryReader:
    def __init__(self, binio: BinaryIO, byte_order='<'):
        if not binio.readable():
            raise ValueError("Argument 'binio' is not readable")
        self.binio = binio
        self.byte_order = byte_order

    def _read_nullaware(self, type_fmt: str, count: int) -> Tuple:
        """
        Reads a number of binary values "null aware": The function will check if the read bytes for each value are unitized.

        Will read x values and compare each bytes with 'CD' * length of block. If the block is unitilized, the value will be set to None.
        Else the bytes will be unpacked.
        Example: To read 8 32-bit ints, the function will read 4 bytes 8 times. Each 4-byte block will be compared with 'CDCDCDCD'.
        If the comparison is true, the value will be set to None. Else it will unpack the bytes to an int.
        :param type_fmt: Type fmt string
        :param count: Number of values to read
        :return: Tuple containing the read objects
        """
        struct_str = self.byte_order + type_fmt
        data_size = calcsize(struct_str)
        null_bytes = bytes.fromhex('CD' * data_size)
        return tuple(unpack(struct_str, read_bytes)[0] if read_bytes != null_bytes else None for read_bytes in
                     (self.binio.read(data_size) for _ in range(count)))

    def _read_direct(self, type_fmt: str, count: int) -> Tuple:
        """
        Will read a number of values specified by the type fmt from a binary reader
        :param type_fmt: Type fmt string of the data to read
        :param count: number of values to read
        :return: Tuple containing the read values
        """
        struct_str = self.byte_order + type_fmt * count
        return unpack(struct_str, self.binio.read(calcsize(struct_str)))

    @overload
    def read_tuple(self, type_fmt: INT_STRUCTS, count: int,
                   check_null: Literal[False] = ...) -> Tuple[int, ...]:
        ...

    @overload
    def read_tuple(self, type_fmt: INT_STRUCTS, count: int,
                   check_null: Literal[True] = ...) -> Tuple[Optional[int], ...]:
        ...

    @overload
    def read_tuple(self, type_fmt: FLOAT_STRUCTS, count: int,
                   check_null: Literal[False] = ...) -> Tuple[float, ...]:
        ...

    @overload
    def read_tuple(self, type_fmt: FLOAT_STRUCTS, count: int,
                   check_null: Literal[True] = ...) -> Tuple[Optional[float], ...]:
        ...

    # We need this last overload as a fallback for mypy when you call the function with a generic string and / or bool as parameter
    @overload
    def read_tuple(self, type_fmt: str, count: int, check_null: bool = ...) -> Tuple:
        ...

    def read_tuple(self, type_fmt: str, count: int,
                   check_null: bool = False) -> Union[
        Tuple[float, ...], Tuple[int, ...], Tuple[Optional[float], ...], Tuple[Optional[int]]]:
        """
        Will read a tuple of values according to type_fmt.
        :param type_fmt: Type fmt string
        :param count: Number of values to read
        :param check_null: If the function should check if each function is unitilized according to visual C++ (0xCDCDCDCD)
        :return:Tuple containig the read data
        """
        read_func = self._read_nullaware if check_null else self._read_direct
        unpacked_values = read_func(type_fmt, count)
        return unpacked_values

    @overload
    def read_single(self, type_fmt: INT_STRUCTS,
                    check_null: Literal[False] = ...) -> int:
        ...

    @overload
    def read_single(self, type_fmt: INT_STRUCTS, check_null: Literal[True] = ...) -> \
            Optional[int]:
        ...

    @overload
    def read_single(self, type_fmt: FLOAT_STRUCTS,
                    check_null: Literal[False] = ...) -> float:
        ...

    @overload
    def read_single(self, type_fmt: FLOAT_STRUCTS,
                    check_null: Literal[True] = ...) -> \
            Optional[float]:
        ...

    # We need this last overload as a fallback for mypy when you call the function with a generic string and / or bool as parameter
    @overload
    def read_single(self, type_fmt: str, check_null: bool = ...) -> Optional[
        Union[float, int]]:
        ...

    def read_single(self, type_fmt: str,
                    check_null: bool = False) -> \
            Optional[Union[float, int]]:
        """
        Will read a single value according to type_fmt.
        :param type_fmt: Type fmt string
        :param check_null: If the function should check if each function is unitilized according to visual C++ (0xCDCDCDCD)
        :return:Tuple containig the read data
        """
        return self.read_tuple(type_fmt, 1, check_null=check_null)[0]

    @overload
    def read_u32(self, check_null: Literal[False] = ...) -> int:
        ...

    @overload
    def read_u32(self, check_null: Literal[True] = ...) -> Optional[int]:
        ...

    def read_u32(self, check_null=False) -> Optional[int]:
        """
        Will read a single u32 value
        :param check_null: Wether to check for null
        :return: An int or none.
        """
        return self.read_single('I', check_null=check_null)

    @overload
    def read_f32(self, check_null: Literal[False] = ...) -> float:
        ...

    @overload
    def read_f32(self, check_null: Literal[True] = ...) -> Optional[float]:
        ...

    def read_f32(self, check_null=False) -> Optional[float]:
        """
        Will read a single f32 value
        :param check_null: Wether to check for null
        :return: A float or none.
        """
        return self.read_single('f', check_null=check_null)

    @overload
    def read_f64(self, check_null: Literal[False] = ...) -> float:
        ...

    @overload
    def read_f64(self, check_null: Literal[True] = ...) -> Optional[float]:
        ...

    def read_f64(self, check_null=False) -> Optional[float]:
        """
        Will read a single f64 value
        :param check_null: Wether to check for null
        :return: A float or none.
        """
        return self.read_single('d', check_null=check_null)

    def read_ubyte(self) -> int:
        """
        Reads the value of a single byte as usigned value
        :return: An integer representing the value of the read byte
        """
        return self.read_single('B', check_null=False)

    def read_ubytes(self, count: int) -> Tuple[int, ...]:
        """
        Reads the multiple bytes as usigned value
        :param count: Number of bytes to read
        :return: A tuple of integer values representing the individual usnigned values of the read bytes
        """
        return self.read_tuple('B', count, check_null=False)

    def skip(self, byte_count: int):
        if self.binio.seekable():
            self.binio.seek(byte_count, SEEK_CUR)
        else:
            self.binio.read(byte_count)

    def skip_32(self, count=1):
        """
        Advances the reader in 32-bit steps
        :param count: Number of 32-bit blocks to skip, defaults to 1
        """
        self.skip(4 * count)

    def skip_64(self, count=1):
        """
        Advances the reader in 64-bit steps
        :param count: Number of 64-bit blocks to skip, defaults to 1
        """
        self.skip(8 * count)

    def read_bool(self) -> bool:
        """
        Reads a dapsys bool (reads 1 byte, then skips 3 additional bytes)
        :return: Value of the read bool
        """
        v = self.binio.read(1)
        self.skip(3)
        return v != 0

    @overload
    def read_array(self, type_fmt: INT_STRUCTS) -> Tuple[int, ...]:
        ...

    @overload
    def read_array(self, type_fmt: FLOAT_STRUCTS) -> Tuple[float, ...]:
        ...

    def read_array(self, type_fmt: str) -> Union[Tuple[int, ...], Tuple[float, ...]]:
        """
        Reads an u32 value as x and then the following x values according to type fmt
        :param type_fmt: Type fmt of the values
        :return: Tuple containing x values
        """
        value_counts = self.read_u32()
        return self.read_tuple(type_fmt, count=value_counts, check_null=False, )

    def read_u32_array(self) -> Tuple[int, ...]:
        """
        Reads a single u32 value as x and then the following x u32 values as an array
        :return: Tuple containing x int values
        """
        return self.read_array('I')

    def read_f32_array(self) -> Tuple[float, ...]:
        """
        Reads a single u32 value as x and then the following x f32 values as an array
        :return: Tuple containing x float values
        """
        return self.read_array('f')

    def read_f64_array(self) -> Tuple[float, ...]:
        """
        Reads a single u32 value as x and then the following x f64 values as an array
        :return: Tuple containing x float values
        """
        return self.read_array('d')

    def read_str(self, encoding='latin_1') -> str:
        """
        Reads a single u32 value as x and then the following x bytes and decodes them as string
        :param encoding: Encoding to use when decoding the bytes, defaults to 'latin_1'
        :return: The decoded string
        """
        length = self.read_u32()
        str_bytes = self.binio.read(length)
        return str_bytes.decode(encoding=encoding)

    def _read_nparray(self, dtype: np.dtype) -> npt.NDArray:
        """
        Reads an u32 value as x and then uses numpy fromfile to read x following values of the specified type
        :param dtype: Dtype of the values to read
        :return: Numpy array containing the values read
        """
        value_counts = self.read_u32()
        raw_data = self.binio.read(value_counts * dtype.itemsize)
        return np.frombuffer(raw_data, dtype=dtype.newbyteorder(self.byte_order))

    def read_f32_nparray(self) -> npt.NDArray[np.float32]:
        """
        Reads an u32 value as x and then uses numpy fromfile to read x following f32 values of the specified type
        :return: Numpy array containing the read np.float32 values
        """
        return self._read_nparray(np.dtype(np.float32))

    def read_f64_nparray(self) -> npt.NDArray[np.float64]:
        """
        Reads an u32 value as x and then uses numpy fromfile to read x following f64 values of the specified type
        :return: Numpy array containing the read np.float64 values
        """
        return self._read_nparray(np.dtype(np.float64))

    def read_u32_nparray(self) -> npt.NDArray[np.uint32]:
        """
        Reads an u32 value as x and then uses numpy fromfile to read x following u32 values of the specified type
        :return: Numpy array containing the read np.uint32 values
        """
        return self._read_nparray(np.dtype(np.uint32))
