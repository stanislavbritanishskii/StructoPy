
# ============================================================
#  StructoPy generated file
# ============================================================
#
#  Generator: StructoPy
#  Author: Stanislav Britanishskii
#  Repository: https://github.com/stanislavbritanishskii/StructoPy
#
#  This file was automatically generated from C++ struct definitions.
#  Do not modify manually — changes will be overwritten on regeneration.
#
# ============================================================
import struct
from typing import List
from ctypes import (
    c_int8 as int8_t,
    c_uint8 as uint8_t,
    c_int16 as int16_t,
    c_uint16 as uint16_t,
    c_int32 as int32_t,
    c_uint32 as uint32_t,
    c_int64 as int64_t,
    c_uint64 as uint64_t,
    c_char as char,
    c_wchar as wchar_t,
    c_float as float_t,
    c_double as double
)
	

class IncludedStruct:
	def __init__(self):

		self.var1:int = 0
		self.var2:char = 'a'
		self.__format_string_computed__=False
		self.__format_string__ = self.get_format_string()
		
		

		
	def to_struct(self):
		res = bytes()
		res += struct.pack("i", self.var1)
		res += struct.pack("c", self.var2.encode('ascii'))
		return res
		
	def from_struct(self, binary, parsed=False):
		if not parsed:
			format_string = self.get_format_string()
			unpacked = struct.unpack(format_string, binary)
		else:
			unpacked = binary
		pos = 0
		
		self.var1 = unpacked[pos]
		pos += 1
		self.var2 = unpacked[pos].rstrip(b'\\x00').decode('utf-8')
		
		return pos
		
	def get_size(self):
		format_string = self.get_format_string()
		return struct.calcsize(format_string)

	def get_format_string(self, secondary_call=False):
		if self.__format_string_computed__:
			return self.__format_string__[secondary_call:]
	
		format_string = ""
		format_string += 'i'  # var1
		format_string += 'c'  # var2
		format_string = '<' * (not secondary_call) + format_string
		self.__format_string_computed__ = True
		return format_string
		

class Vec3:
	def __init__(self):

		self.x:float = 0
		self.y:float = 0
		self.z:float = 0
		self.__format_string_computed__=False
		self.__format_string__ = self.get_format_string()
		
		

		
	def to_struct(self):
		res = bytes()
		res += struct.pack("f", self.x)
		res += struct.pack("f", self.y)
		res += struct.pack("f", self.z)
		return res
		
	def from_struct(self, binary, parsed=False):
		if not parsed:
			format_string = self.get_format_string()
			unpacked = struct.unpack(format_string, binary)
		else:
			unpacked = binary
		pos = 0
		
		self.x = unpacked[pos]
		pos += 1
		self.y = unpacked[pos]
		pos += 1
		self.z = unpacked[pos]
		pos += 1
		return pos
		
	def get_size(self):
		format_string = self.get_format_string()
		return struct.calcsize(format_string)

	def get_format_string(self, secondary_call=False):
		if self.__format_string_computed__:
			return self.__format_string__[secondary_call:]
	
		format_string = ""
		format_string += 'f'  # x
		format_string += 'f'  # y
		format_string += 'f'  # z
		format_string = '<' * (not secondary_call) + format_string
		self.__format_string_computed__ = True
		return format_string
		

class Timestamp:
	def __init__(self):

		self.seconds:uint32_t = 0
		self.microseconds:uint32_t = 0
		self.__format_string_computed__=False
		self.__format_string__ = self.get_format_string()
		
		

		
	def to_struct(self):
		res = bytes()
		res += struct.pack("I", self.seconds)
		res += struct.pack("I", self.microseconds)
		return res
		
	def from_struct(self, binary, parsed=False):
		if not parsed:
			format_string = self.get_format_string()
			unpacked = struct.unpack(format_string, binary)
		else:
			unpacked = binary
		pos = 0
		
		self.seconds = unpacked[pos]
		pos += 1
		self.microseconds = unpacked[pos]
		pos += 1
		return pos
		
	def get_size(self):
		format_string = self.get_format_string()
		return struct.calcsize(format_string)

	def get_format_string(self, secondary_call=False):
		if self.__format_string_computed__:
			return self.__format_string__[secondary_call:]
	
		format_string = ""
		format_string += 'I'  # seconds
		format_string += 'I'  # microseconds
		format_string = '<' * (not secondary_call) + format_string
		self.__format_string_computed__ = True
		return format_string
		

class Sensor:
	def __init__(self):

		self.id:uint8_t = 0
		self.value:float = 0
		self.status:int16_t = 0
		self.offset: Vec3 = Vec3()
					
		self.__format_string_computed__=False
		self.__format_string__ = self.get_format_string()
		
		

		
	def to_struct(self):
		res = bytes()
		res += struct.pack("B", self.id)
		res += struct.pack("f", self.value)
		res += struct.pack("h", self.status)
		res += self.offset.to_struct()
		return res
		
	def from_struct(self, binary, parsed=False):
		if not parsed:
			format_string = self.get_format_string()
			unpacked = struct.unpack(format_string, binary)
		else:
			unpacked = binary
		pos = 0
		
		self.id = unpacked[pos]
		pos += 1
		self.value = unpacked[pos]
		pos += 1
		self.status = unpacked[pos]
		pos += 1
		format_string = Vec3().get_format_string()
		
		pos += self.offset.from_struct(unpacked[pos:], True)
		
		return pos
		
	def get_size(self):
		format_string = self.get_format_string()
		return struct.calcsize(format_string)

	def get_format_string(self, secondary_call=False):
		if self.__format_string_computed__:
			return self.__format_string__[secondary_call:]
	
		format_string = ""
		format_string += 'B'  # id
		format_string += 'f'  # value
		format_string += 'h'  # status
		format_string += Vec3().get_format_string(True)
		format_string = '<' * (not secondary_call) + format_string
		self.__format_string_computed__ = True
		return format_string
		

class DeviceInfo:
	def __init__(self):

		self.name:str = '' # expected size 32

		self.val:char = 'a'
		self.type:uint8_t = 0
		self.version:uint16_t = 0
		self.serial:uint32_t = 0
		self.__format_string_computed__=False
		self.__format_string__ = self.get_format_string()
		
		

		
	def to_struct(self):
		res = bytes()
		for i in range(32):
			res += struct.pack("c", self.name[i].encode('ascii') if i < len(self.name) else b'\x00')
		res += struct.pack("c", self.val.encode('ascii'))
		res += struct.pack("B", self.type)
		res += struct.pack("H", self.version)
		res += struct.pack("I", self.serial)
		return res
		
	def from_struct(self, binary, parsed=False):
		if not parsed:
			format_string = self.get_format_string()
			unpacked = struct.unpack(format_string, binary)
		else:
			unpacked = binary
		pos = 0
		
		byte_val = bytes()
		for i in range(32):
			byte_val += unpacked[pos]
			pos += 1
		self.name = byte_val.rstrip(b'\\x00').decode('utf-8')
			
		self.val = unpacked[pos].rstrip(b'\\x00').decode('utf-8')
		
		self.type = unpacked[pos]
		pos += 1
		self.version = unpacked[pos]
		pos += 1
		self.serial = unpacked[pos]
		pos += 1
		return pos
		
	def get_size(self):
		format_string = self.get_format_string()
		return struct.calcsize(format_string)

	def get_format_string(self, secondary_call=False):
		if self.__format_string_computed__:
			return self.__format_string__[secondary_call:]
	
		format_string = ""
		for i in range(32):
			format_string += 'c'  # name
		format_string += 'c'  # val
		format_string += 'B'  # type
		format_string += 'H'  # version
		format_string += 'I'  # serial
		format_string = '<' * (not secondary_call) + format_string
		self.__format_string_computed__ = True
		return format_string
		

class Payload:
	def __init__(self):

		self.data: List[uint8_t] = [] # size 64
		for i in range(64):
			self.data.append(0)
					
		self.length:uint16_t = 0
		self.__format_string_computed__=False
		self.__format_string__ = self.get_format_string()
		
		

		
	def to_struct(self):
		res = bytes()
		for i in range(64):
			res += struct.pack("B", self.data[i] if i < len(self.data) else 0)
		res += struct.pack("H", self.length)
		return res
		
	def from_struct(self, binary, parsed=False):
		if not parsed:
			format_string = self.get_format_string()
			unpacked = struct.unpack(format_string, binary)
		else:
			unpacked = binary
		pos = 0
		
		for i in range(64):
			self.data[i] = unpacked[pos]
			pos += 1
				
		self.length = unpacked[pos]
		pos += 1
		return pos
		
	def get_size(self):
		format_string = self.get_format_string()
		return struct.calcsize(format_string)

	def get_format_string(self, secondary_call=False):
		if self.__format_string_computed__:
			return self.__format_string__[secondary_call:]
	
		format_string = ""
		for i in range(64):
			format_string += 'B'  # data
		format_string += 'H'  # length
		format_string = '<' * (not secondary_call) + format_string
		self.__format_string_computed__ = True
		return format_string
		

class TelemetryPacket:
	def __init__(self):

		self.time: Timestamp = Timestamp()
					
		self.device: DeviceInfo = DeviceInfo()
					
		self.sensors: List[Sensor] = [] # size 8
		for i in range(8):
			self.sensors.append(Sensor())
					
		self.sensor_count:uint8_t = 0
		self.position: Vec3 = Vec3()
					
		self.velocity: Vec3 = Vec3()
					
		self.payload: Payload = Payload()
					
		self.flags:int8_t = 0
		self.counter:uint32_t = 0
		self.__format_string_computed__=False
		self.__format_string__ = self.get_format_string()
		
		

		
	def to_struct(self):
		res = bytes()
		res += self.time.to_struct()
		res += self.device.to_struct()
		for i in range(8):
			res += self.sensors[i].to_struct()
		res += struct.pack("B", self.sensor_count)
		res += self.position.to_struct()
		res += self.velocity.to_struct()
		res += self.payload.to_struct()
		res += struct.pack("b", self.flags)
		res += struct.pack("I", self.counter)
		return res
		
	def from_struct(self, binary, parsed=False):
		if not parsed:
			format_string = self.get_format_string()
			unpacked = struct.unpack(format_string, binary)
		else:
			unpacked = binary
		pos = 0
		
		format_string = Timestamp().get_format_string()
		
		pos += self.time.from_struct(unpacked[pos:], True)
		
		format_string = DeviceInfo().get_format_string()
		
		pos += self.device.from_struct(unpacked[pos:], True)
		
		format_string = Sensor().get_format_string()
		
		for i in range(8):
			pos += self.sensors[i].from_struct(unpacked[pos:], True)
		
			
		self.sensor_count = unpacked[pos]
		pos += 1
		format_string = Vec3().get_format_string()
		
		pos += self.position.from_struct(unpacked[pos:], True)
		
		format_string = Vec3().get_format_string()
		
		pos += self.velocity.from_struct(unpacked[pos:], True)
		
		format_string = Payload().get_format_string()
		
		pos += self.payload.from_struct(unpacked[pos:], True)
		
		self.flags = unpacked[pos]
		pos += 1
		self.counter = unpacked[pos]
		pos += 1
		return pos
		
	def get_size(self):
		format_string = self.get_format_string()
		return struct.calcsize(format_string)

	def get_format_string(self, secondary_call=False):
		if self.__format_string_computed__:
			return self.__format_string__[secondary_call:]
	
		format_string = ""
		format_string += Timestamp().get_format_string(True)
		format_string += DeviceInfo().get_format_string(True)
		for i in range(8):
			format_string += Sensor().get_format_string(True)
		format_string += 'B'  # sensor_count
		format_string += Vec3().get_format_string(True)
		format_string += Vec3().get_format_string(True)
		format_string += Payload().get_format_string(True)
		format_string += 'b'  # flags
		format_string += 'I'  # counter
		format_string = '<' * (not secondary_call) + format_string
		self.__format_string_computed__ = True
		return format_string
		
