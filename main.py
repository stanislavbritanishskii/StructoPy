import re
import struct
import sys
from collections import OrderedDict

normal_types = {
	'char': 'c',
	'signed char': 'b',
	'unsigned char': 'B',
	'bool': '?',
	'short': 'h',
	'unsigned short': 'H',
	'int': 'i',
	'unsigned int': 'I',
	'long': 'l',
	'unsigned long': 'L',
	'long long': 'q',
	'unsigned long long': 'Q',
	'int8_t': 'b',
	'uint8_t': 'B',
	'int16_t': 'h',
	'uint16_t': 'H',
	'int32_t': 'i',
	'uint32_t': 'I',
	'int64_t': 'q',
	'uint64_t': 'Q',
	'float': 'f',
	'double': 'd'
}
# Endians
# Big >
# little <
ENDIAN = '<'


def find_in_list(lst, value):
	try:
		return lst.index(value)
	except ValueError:
		return -1


class NewClass:
	def __init__(self):
		self.name = ''
		self.name2 = ''
		self.fields = OrderedDict()

	def create_format_string(self, structs):
		res = f'''
		format_string = ""'''
		for field in self.fields:
			if self.fields[field][0] in normal_types:
				if len(self.fields[field]) == 1:
					res += f'''
		format_string += '{normal_types[self.fields[field][0]]}'  # {field}'''
				else:
					res += f'''
		for i in range({self.fields[field][1]}):
			format_string += '{normal_types[self.fields[field][0]]}'  # {field}'''

			if self.fields[field][0] in list(map(lambda x: x.name, structs)):
				if len(self.fields[field]) == 1:
					# struc = next((obj for obj in structs if obj.name == self.fields[field][0]), None)
					res += f'''
		format_string += {self.fields[field][0]}().get_format_string(True)'''
				else:
					res += f'''
		for i in range({self.fields[field][1]}):
			format_string += {self.fields[field][0]}().get_format_string(True)'''

		return res

	def create_get_size(self, structs):
		return f'''
	def get_size(self):
		format_string = self.get_format_string()
		return struct.calcsize(format_string)
'''

	def create_get_format_string(self, structs):
		res = f'''
	def get_format_string(self, secondary_call=False):
		if self.__format_string_computed__:
			return self.__format_string__[secondary_call:]
	{self.create_format_string(structs)}
		format_string = '{ENDIAN}' * (not secondary_call) + format_string
		self.__format_string_computed__ = True
		return format_string
		'''
		return res

	def create_to_struct(self, structs):
		res = ''
		res += '''
		
	def to_struct(self):
		res = bytes()'''
		for field in self.fields:
			if self.fields[field][0] in normal_types:
				if (self.fields[field][0] == 'char'):
					if len(self.fields[field]) == 1:
						res += f'''
		res += struct.pack("{normal_types[self.fields[field][0]]}", self.{field}.encode('ascii'))'''
					else:
						res += f'''
		for i in range({self.fields[field][1]}):
			res += struct.pack("{normal_types[self.fields[field][0]]}", self.{field}[i].encode('ascii') if i < len(self.{field}) else b'\\x00')'''
				else:

					if len(self.fields[field]) == 1:
						res += f'''
		res += struct.pack("{normal_types[self.fields[field][0]]}", self.{field})'''
					else:
						res += f'''
		for i in range({self.fields[field][1]}):
			res += struct.pack("{normal_types[self.fields[field][0]]}", self.{field}[i] if i < len(self.{field}) else 0)'''
			if self.fields[field][0] in list(map(lambda x: x.name, structs)):
				if len(self.fields[field]) == 1:
					res += f'''
		res += self.{field}.to_struct()'''
				else:
					res += f'''
		for i in range({self.fields[field][1]}):
			res += self.{field}[i].to_struct()'''
		res += '''
		return res'''
		return res

	def create_from_struct(self, structs):
		res = f'''
		
	def from_struct(self, binary, parsed=False):
		if not parsed:
			format_string = self.get_format_string()
			unpacked = struct.unpack(format_string, binary)
		else:
			unpacked = binary
		pos = 0
		'''
		for field in self.fields:
			if self.fields[field][0] in normal_types:
				if (self.fields[field][0] == 'char'):
					if len(self.fields[field]) == 1:
						res += f'''
		self.{field} = unpacked[pos].rstrip(b'\\\\x00').decode('utf-8')
		'''
					else:
						res += f'''
		byte_val = bytes()
		for i in range({self.fields[field][1]}):
			byte_val += unpacked[pos]
			pos += 1
		self.{field} = byte_val.rstrip(b'\\\\x00').decode('utf-8')
			'''
				else:
					if len(self.fields[field]) == 1:
						res += f'''
		self.{field} = unpacked[pos]
		pos += 1'''
					else:
						res += f'''
		for i in range({self.fields[field][1]}):
			self.{field}[i] = unpacked[pos]
			pos += 1
				'''
			elif self.fields[field][0] in list(map(lambda x: x.name, structs)):
				res += f'''
		format_string = {self.fields[field][0]}().get_format_string()
		'''
				if len(self.fields[field]) == 1:
					res += f'''
		pos += self.{field}.from_struct(unpacked[pos:], True)
		'''
				else:
					res += f'''
		for i in range({self.fields[field][1]}):
			pos += self.{field}[i].from_struct(unpacked[pos:], True)
		
			'''

		res+= '''
		return pos
		'''

		return res

	def printable(self, structs):
		res = f'''
class {self.name}:
	def __init__(self):
'''
		for field in self.fields:
			if self.fields[field][0] in normal_types:
				val = '0' if self.fields[field][0] not in ['char', 'signed char', 'unsigned char'] else "'a'"
				_type = self.fields[field][0]
				if _type == "double":
					_type = float
				if len(self.fields[field]) == 1:
					res += f'''
		self.{field}:{self.fields[field][0]} = {val}'''
				else:
					if self.fields[field][0] not in ['char', 'signed char', 'unsigned char']:
						res += f'''
		self.{field}: List[{self.fields[field][0]}] = [] # size {self.fields[field][1]}
		for i in range({self.fields[field][1]}):
			self.{field}.append({val})
					'''
					else:
						res += f'''
		self.{field}:str = '' # expected size {self.fields[field][1]}
'''
			else:
				if len(self.fields[field]) == 1:
					res += f'''
		self.{field}: {self.fields[field][0]} = {self.fields[field][0]}()
					'''
				else:
					res += f'''
		self.{field}: List[{self.fields[field][0]}] = [] # size {self.fields[field][1]}
		for i in range({self.fields[field][1]}):
			self.{field}.append({self.fields[field][0]}())
					'''
		res += '''
		self.__format_string_computed__=False
		self.__format_string__ = self.get_format_string()
		
		'''
		res += '\n'
		res += self.create_to_struct(structs)
		res += self.create_from_struct(structs)
		res += self.create_get_size(structs)
		res += self.create_get_format_string(structs)

		return res


def open_close(char: str, brackets: str = '{}') -> int:
	if char not in brackets:
		return 0
	if char == brackets[0]:
		return 1
	else:
		return -1


def count_curve_brackets(contents, pos):
	opening = 0
	res = 0
	while opening == 0 and pos < len(contents):
		opening += open_close(contents[pos + res], '{}')
		res += 1
	while opening != 0 and pos < len(contents):
		opening += open_close(contents[pos + res], '{}')
		res += 1
	return res


def count_square_brackets(contents, pos):
	opening = 0
	res = 0
	while opening == 0 and pos < len(contents):
		opening += open_close(contents[pos + res], '[]')
		res += 1
	while opening != 0 and pos < len(contents):
		opening += open_close(contents[pos + res], '[]')
		res += 1
	return res


def find_struct_start(contents, pos):
	# pos1 = contents.find('typedef', pos)
	pos2 = contents.find('struct', pos)
	# if pos1 != -1 and pos2 != -1:
	if pos2 != -1:
		return pos2 + len('struct')
	else:
		return len(contents)


def find_fields(contents, structs):
	res = OrderedDict()
	lines = re.split('[\n;]', contents)
	for line in lines:
		line = line.strip()
		comment = line.find('//')

		if comment != -1:
			line = line[0:comment]
		if not line:
			continue

		separators = r'\s+'
		splitted = re.split(separators, line)
		# print(splitted)
		correct = False
		if len(splitted) > 1:

			if splitted[0] in normal_types:
				typ = splitted[0]
				correct = True
			elif any(splitted[0] == x.name for x in structs):
				typ = splitted[0]
				correct = True
			elif any(splitted[0] == x.name2 for x in structs):
				typ = next(x.name for x in structs if splitted[0] == x.name2)
				correct = True
			if correct:
				res[splitted[1].split('[')[0]] = [typ]
				if splitted[1].find('[') != -1:
					res[splitted[1].split('[')[0]].append(int(splitted[1].split('[')[1].strip(']')))

	return res


def find_struct(contents):
	res = []
	pos = 0
	while pos < len(contents):
		new_class = NewClass()
		name_start = find_struct_start(contents, pos)
		if name_start == len(contents):
			break
		while contents[name_start] in '\t \n' and name_start < len(contents):
			name_start += 1

		name_end = name_start

		while 'a' <= (contents[name_end]).lower() <= 'z' or contents[name_end] in '0123456789_' and name_end < len(
				contents):
			name_end += 1

		if name_end == len(contents):
			break
		body_start = name_end

		new_class.name = contents[name_start:name_end]

		while not open_close(contents[body_start], '{}') and body_start < len(contents):
			body_start += 1
		body_end = body_start + count_curve_brackets(contents, body_start)
		body = contents[body_start + 1:body_end - 1]
		pos = body_end

		# end_pos = contents.find(';', body_end)
		# if end_pos != -1:
		# 	print(end_pos)
		# 	new_class.name2 = contents[body_end + 1:end_pos].split()[-1]
		new_class.fields = find_fields(body, res)
		res.append(new_class)
	return res


# return contents[pos + len('typedef struct') + 1:]

def not_a_word(index, text):
	if index < 0:
		return True
	if index >= len(text):
		return True
	if text[index] in '[]{}<> \t\n':
		return True
	return False


def main():
	if len(sys.argv) < 2:
		print("Usage: python main.py <file>")
		return
	print('''
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
	''')
	f = open(sys.argv[1], 'r')
	text = f.read()
	f.close()
	# new_text = replace_defines_in_hpp(text)

	# find_struct(open(sys.argv[1]).read())
	classes = find_struct(text)
	for c in classes:
		print(c.printable(classes))


# print(find_struct(open(sys.argv[1]).read()))


if __name__ == '__main__':
	main()
