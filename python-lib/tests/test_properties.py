# pylint: disable=missing-function-docstring, missing-class-docstring, missing-module-docstring
# pylint: disable=invalid-name
import sys
from unittest.mock import patch
import pytest

#from line_uds.profile import UdsNumericProperty

# class TestUdsNumericProperty:

#     @pytest.fixture()
#     def u16property(self):
#         return UdsNumericProperty("test_u16", 0x0001, size=2, signed=False)

#     @pytest.mark.parametrize("input_value, expected_bytes", [
#         (0, bytearray([0x00, 0x00])),
#         (1, bytearray([0x01, 0x00])),
#         (255, bytearray([0xFF, 0x00])),
#         (256, bytearray([0x00, 0x01])),
#         (65535, bytearray([0xFF, 0xFF])),
#     ])
#     def test_Encode(self, u16property, input_value, expected_bytes):
#         encoded = u16property.encode(input_value)
#         assert encoded == expected_bytes

#     @pytest.mark.parametrize("input_bytes, expected_value", [
#         (bytearray([0x00, 0x00]), 0),
#         (bytearray([0x01, 0x00]), 1),
#         (bytearray([0xFF, 0x00]), 255),
#         (bytearray([0x00, 0x01]), 256),
#         (bytearray([0xFF, 0xFF]), 65535),
#     ])
#     def test_Decode(self, u16property, input_bytes, expected_value):
#         decoded = u16property.decode(input_bytes)
#         assert decoded == expected_value

#     def test_Encoding_Equivalence(self, u16property):
#         test_values = [0, 1, 255, 256, 65535]
#         for val in test_values:
#             encoded = u16property.encode(val)
#             decoded = u16property.decode(encoded)
#             assert decoded == val

#     @pytest.mark.parametrize("size, signed, c_type", [
#         (1, False, 'uint8_t'),
#         (1, True, 'int8_t'),
#         (2, False, 'uint16_t'),
#         (2, True, 'int16_t'),
#         (4, False, 'uint32_t'),
#         (4, True, 'int32_t'),
#         (8, False, 'uint64_t'),
#         (8, True, 'int64_t'),
#     ])
#     def test_GetCType(self, size, signed, c_type):
#         prop = UdsNumericProperty("test_prop", 0x0001, size=size, signed=signed)
#         assert prop.get_ctype() == c_type
