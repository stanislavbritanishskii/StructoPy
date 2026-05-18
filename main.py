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


def _py_annotation(c_type):
	"""Map a C type name to a Python annotation token usable in generated code.
	Multi-word C types (e.g. 'unsigned int', 'signed char', 'long long') have
	no direct Python identifier, so collapse them to 'int' — they are all
	integer types and the annotation is cosmetic, not enforced at runtime."""
	if ' ' in c_type:
		return 'int'
	return c_type


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
				# IMPORTANT: prefix every pack with ENDIAN so the per-field byte
				# count matches struct.calcsize(get_format_string()). Without
				# the prefix, codes like 'l'/'L' use NATIVE size (8 bytes on
				# Linux LP64) while the cached format string asks for the
				# standard size (4 bytes), corrupting round-trips.
				code = ENDIAN + normal_types[self.fields[field][0]]
				if (self.fields[field][0] == 'char'):
					if len(self.fields[field]) == 1:
						res += f'''
		res += struct.pack("{code}", self.{field}.encode('ascii'))'''
					else:
						res += f'''
		for i in range({self.fields[field][1]}):
			res += struct.pack("{code}", self.{field}[i].encode('ascii') if i < len(self.{field}) else b'\\x00')'''
				else:

					if len(self.fields[field]) == 1:
						res += f'''
		res += struct.pack("{code}", self.{field})'''
					else:
						res += f'''
		for i in range({self.fields[field][1]}):
			res += struct.pack("{code}", self.{field}[i] if i < len(self.{field}) else 0)'''
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
		self.{field} = unpacked[pos].rstrip(b'\\x00').decode('utf-8')
		pos += 1
		'''
					else:
						res += f'''
		byte_val = bytes()
		for i in range({self.fields[field][1]}):
			byte_val += unpacked[pos]
			pos += 1
		self.{field} = byte_val.rstrip(b'\\x00').decode('utf-8')
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
				ann = _py_annotation(self.fields[field][0])
				if len(self.fields[field]) == 1:
					res += f'''
		self.{field}:{ann} = {val}'''
				else:
					if self.fields[field][0] not in ['char', 'signed char', 'unsigned char']:
						res += f'''
		self.{field}: List[{ann}] = [] # size {self.fields[field][1]}
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
	n = len(contents)
	opening = 0
	res = 0
	while pos + res < n and opening == 0:
		opening += open_close(contents[pos + res], '{}')
		res += 1
	if opening == 0:
		raise ValueError("No opening '{' found in struct definition")
	while pos + res < n and opening != 0:
		opening += open_close(contents[pos + res], '{}')
		res += 1
	if opening != 0:
		raise ValueError("Unmatched '{' in struct definition (missing closing brace)")
	return res


def count_square_brackets(contents, pos):
	n = len(contents)
	opening = 0
	res = 0
	while pos + res < n and opening == 0:
		opening += open_close(contents[pos + res], '[]')
		res += 1
	if opening == 0:
		raise ValueError("No opening '[' found")
	while pos + res < n and opening != 0:
		opening += open_close(contents[pos + res], '[]')
		res += 1
	if opening != 0:
		raise ValueError("Unmatched '['")
	return res


def strip_comments(text):
	"""Strip C/C++ // and /* */ comments AND string/char literals. Lets find_struct
	work on raw headers (gcc -E in run.sh would normally drop comments, but it
	preserves string literals, so we erase those too to keep the 'struct' keyword
	scan from being fooled by `const char *s = "struct Ghost {...}";`)."""
	out = []
	i = 0
	n = len(text)
	while i < n:
		if i + 1 < n and text[i] == '/' and text[i + 1] == '/':
			while i < n and text[i] != '\n':
				i += 1
		elif i + 1 < n and text[i] == '/' and text[i + 1] == '*':
			i += 2
			while i + 1 < n and not (text[i] == '*' and text[i + 1] == '/'):
				i += 1
			i += 2
		elif text[i] == '"' or text[i] == "'":
			quote = text[i]
			i += 1
			while i < n and text[i] != quote:
				if text[i] == '\\' and i + 1 < n:
					i += 2
				else:
					i += 1
			i += 1
		else:
			out.append(text[i])
			i += 1
	return ''.join(out)


def strip_attributes(text):
	"""Strip every __attribute__((...)) occurrence with balanced-paren handling.

	StructoPy already produces packed binary layout (no padding emitted), so
	__attribute__((packed)), aligned(N), etc. are noise to the parser. Removing
	them lets the rest of the parser ignore attribute syntax entirely.
	"""
	out = []
	i = 0
	n = len(text)
	key = '__attribute__'
	klen = len(key)
	while i < n:
		if text.startswith(key, i):
			j = i + klen
			while j < n and text[j] in ' \t\n':
				j += 1
			if j < n and text[j] == '(':
				depth = 0
				while j < n:
					if text[j] == '(':
						depth += 1
					elif text[j] == ')':
						depth -= 1
						if depth == 0:
							j += 1
							break
					j += 1
				i = j
				continue
		out.append(text[i])
		i += 1
	return ''.join(out)


_STRUCT_RE = re.compile(r'\bstruct\b')


def find_struct_start(contents, pos):
	m = _STRUCT_RE.search(contents, pos)
	if m is not None:
		return m.end()
	else:
		return len(contents)


def find_fields(contents, structs, struct_name="<unknown>"):
	res = OrderedDict()
	lines = re.split('[\n;]', contents)
	known_struct_names = [x.name for x in structs] + [x.name2 for x in structs if x.name2]

	for line in lines:
		line = line.strip()
		comment = line.find('//')
		if comment != -1:
			line = line[0:comment].strip()
		if not line:
			continue

		if ':' in line:
			raise ValueError(
				f"Bit fields are not supported (in struct {struct_name!r}): {line!r}. "
				f"Replace with a plain integer field and shift/mask manually."
			)
		if '*' in line:
			raise ValueError(
				f"Pointers are not supported (in struct {struct_name!r}): {line!r}. "
				f"Use uint32_t or uint64_t for opaque handles instead."
			)

		splitted = re.split(r'\s+', line)
		if len(splitted) < 2:
			raise ValueError(
				f"Malformed field (in struct {struct_name!r}): {line!r}"
			)

		# Try longest-prefix match against primitive types so multi-token
		# types like 'unsigned int' and 'unsigned long long' are recognised.
		typ = None
		type_token_count = 0
		for k in range(min(3, len(splitted) - 1), 0, -1):
			candidate = ' '.join(splitted[:k])
			if candidate in normal_types:
				typ = candidate
				type_token_count = k
				break
		if typ is None:
			head = splitted[0]
			for s in structs:
				if head == s.name or (s.name2 and head == s.name2):
					typ = s.name
					type_token_count = 1
					break

		if typ is None:
			raise ValueError(
				f"Unknown type {splitted[0]!r} in struct {struct_name!r}: {line!r}. "
				f"Known primitives: {sorted(normal_types)}. "
				f"Known structs: {known_struct_names or '[]'}."
			)

		name_tok = splitted[type_token_count]
		name = name_tok.split('[')[0]
		res[name] = [typ]
		if '[' in name_tok:
			try:
				size = int(name_tok.split('[')[1].rstrip(']'))
			except ValueError:
				raise ValueError(
					f"Array size must be an integer literal (in struct {struct_name!r}): {line!r}. "
					f"If you used a macro, run the input through the preprocessor first."
				)
			res[name].append(size)

	return res


def find_struct(contents):
	contents = strip_comments(contents)
	contents = strip_attributes(contents)
	res = []
	pos = 0
	n = len(contents)
	while pos < n:
		new_class = NewClass()
		name_start = find_struct_start(contents, pos)
		if name_start >= n:
			break
		# skip whitespace between `struct` and (optional) tag name
		while name_start < n and contents[name_start] in ' \t\n':
			name_start += 1
		if name_start >= n:
			break

		# scan tag name — may be empty for `typedef struct { ... } Name;`
		name_end = name_start
		while name_end < n:
			c = contents[name_end]
			if c.isalnum() or c == '_':
				name_end += 1
			else:
				break

		new_class.name = contents[name_start:name_end]

		# Advance to opening '{', but bail out on ';' first — that's a forward
		# declaration like `struct Foo;` (or `typedef struct Foo Bar;`). Without
		# this check we'd skip past the ';' and consume the body of whatever
		# struct came next, misattributing fields and dropping the real one.
		scan = name_end
		while scan < n and contents[scan] not in '{;':
			scan += 1
		if scan >= n:
			raise ValueError(
				f"Struct {new_class.name or '<anonymous>'!r} has no body (missing '{{')"
			)
		if contents[scan] == ';':
			pos = scan + 1
			continue
		body_start = scan

		body_end = body_start + count_curve_brackets(contents, body_start)
		body = contents[body_start + 1:body_end - 1]

		# After closing '}', look for trailing typedef alias: `} Name;`
		tp = body_end
		while tp < n and contents[tp] in ' \t\n':
			tp += 1
		trailing_start = tp
		while tp < n:
			c = contents[tp]
			if c.isalnum() or c == '_':
				tp += 1
			else:
				break
		trailing_name = contents[trailing_start:tp]

		if not new_class.name:
			if not trailing_name:
				raise ValueError(
					"Anonymous struct without a typedef alias — cannot generate a "
					"Python class. Use 'typedef struct { ... } Name;' or "
					"'struct Name { ... };'."
				)
			new_class.name = trailing_name
		elif trailing_name and trailing_name != new_class.name:
			new_class.name2 = trailing_name

		pos = body_end
		new_class.fields = find_fields(body, res, new_class.name)
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


PREAMBLE = '''
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
'''


USAGE = "Usage: python main.py [--endian little|big] <file>"


def _parse_args(argv):
	endian = None
	positional = []
	i = 0
	while i < len(argv):
		a = argv[i]
		if a == '--endian':
			i += 1
			if i >= len(argv):
				print(f"Error: --endian requires an argument (little|big)\n{USAGE}",
				      file=sys.stderr)
				sys.exit(1)
			endian = argv[i]
			i += 1
		elif a.startswith('--endian='):
			endian = a.split('=', 1)[1]
			i += 1
		elif a in ('-h', '--help'):
			print(USAGE)
			sys.exit(0)
		else:
			positional.append(a)
			i += 1
	return endian, positional


def main():
	global ENDIAN
	endian_arg, positional = _parse_args(sys.argv[1:])
	if not positional:
		print(USAGE, file=sys.stderr)
		sys.exit(1)
	if endian_arg is not None:
		if endian_arg == 'little':
			ENDIAN = '<'
		elif endian_arg == 'big':
			ENDIAN = '>'
		else:
			print(f"Error: --endian must be 'little' or 'big' (got {endian_arg!r})",
			      file=sys.stderr)
			sys.exit(1)
	with open(positional[0], 'r') as f:
		text = f.read()
	try:
		classes = find_struct(text)
		bodies = [c.printable(classes) for c in classes]
	except ValueError as e:
		print(f"StructoPy error: {e}", file=sys.stderr)
		sys.exit(1)
	sys.stdout.write(PREAMBLE)
	for body in bodies:
		sys.stdout.write(body)
		sys.stdout.write("\n")


# print(find_struct(open(sys.argv[1]).read()))


if __name__ == '__main__':
	main()
