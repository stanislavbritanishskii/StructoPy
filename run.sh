#!/bin/bash
# StructoPy driver: preprocess a C/C++ header, generate output.py, smoke-test it.
#
# Usage: ./run.sh [-I <include_dir>]... <input.h>
#
# Behaviour:
#   - User (""-form, transitively reachable) includes are resolved normally.
#   - System (<>-form) includes are stubbed to empty files so the preprocessor
#     does not pull in C++ standard library headers that StructoPy can't parse.
#   - Classification uses `gcc -M -MG -nostdinc`: GCC walks the include tree
#     itself; anything it cannot resolve is treated as a system header to stub.

set -euo pipefail

USAGE="Usage: $0 [-o <output.py>] [--endian little|big] [-I <include_dir>]... <input.h>"

extra_includes=()
endian=""
output_file=""
while [ $# -gt 0 ]; do
	case "$1" in
		-I)
			shift
			[ $# -gt 0 ] || { echo "Error: -I requires a directory argument" >&2; exit 1; }
			extra_includes+=("-I" "$1")
			shift
			;;
		-I*)
			extra_includes+=("$1")
			shift
			;;
		-o)
			shift
			[ $# -gt 0 ] || { echo "Error: -o requires a path argument" >&2; exit 1; }
			output_file="$1"
			shift
			;;
		-o*)
			output_file="${1#-o}"
			shift
			;;
		--endian)
			shift
			[ $# -gt 0 ] || { echo "Error: --endian requires an argument (little|big)" >&2; exit 1; }
			endian="$1"
			shift
			;;
		--endian=*)
			endian="${1#--endian=}"
			shift
			;;
		-h|--help)
			echo "$USAGE"
			exit 0
			;;
		--)
			shift
			break
			;;
		-*)
			echo "Unknown flag: $1" >&2
			echo "$USAGE" >&2
			exit 1
			;;
		*)
			break
			;;
	esac
done

if [ -n "$endian" ] && [ "$endian" != "little" ] && [ "$endian" != "big" ]; then
	echo "Error: --endian must be 'little' or 'big' (got '$endian')" >&2
	exit 1
fi

input_file="${1:-}"
if [ -z "$input_file" ]; then
	echo "$USAGE" >&2
	exit 1
fi
if [ ! -f "$input_file" ]; then
	echo "Error: file '$input_file' not found" >&2
	exit 1
fi

# Default output: same basename as input with .py extension, in cwd.
# (e.g. `./run.sh path/to/foo.h` -> `./foo.py`.) -o overrides.
if [ -z "$output_file" ]; then
	input_basename=$(basename "$input_file")
	output_file="${input_basename%.*}.py"
fi

input_dir=$(dirname "$input_file")
stub_dir=$(mktemp -d)
trap 'rm -rf "$stub_dir"' EXIT

# Throwaway artifacts (preprocessed header, smoke-test scaffold) go to
# /tmp/structopy/ so the repo working tree stays clean. The actual deliverable
# is $output_file — that's the file the caller actually wants. Override the
# scratch location with STRUCTOPY_ARTIFACT_DIR if you need it elsewhere
# (the test harness uses this to keep parallel runs isolated).
artifact_dir="${STRUCTOPY_ARTIFACT_DIR:-/tmp/structopy}"
mkdir -p "$artifact_dir"

# Resolve main.py relative to this script so run.sh works from any cwd.
script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

# Ensure the output directory exists; resolve to an absolute path for the
# collision check below.
output_parent=$(dirname "$output_file")
mkdir -p "$output_parent"
output_abs="$(cd "$output_parent" && pwd)/$(basename "$output_file")"

# Refuse to write the generated module on top of the generator script.
# Bash's `> $output_file` truncates before python3 runs, so a collision
# (e.g. running `./run.sh main.h` from a directory that also contains a copy
# of the generator named main.py) would silently empty the generator.
if [ "$output_abs" = "$script_dir/main.py" ]; then
	echo "Error: output file '$output_file' would overwrite the generator at '$script_dir/main.py'." >&2
	echo "       Use -o <other_path> to write the generated module somewhere else." >&2
	exit 1
fi

# 1. Discover the full transitive include tree.
#    -nostdinc removes default system paths, -MG makes missing headers non-fatal.
deps_raw=$(gcc -M -MG -nostdinc -I"$input_dir" "${extra_includes[@]}" "$input_file" 2>/dev/null)
deps=$(printf '%s\n' "$deps_raw" \
	| sed 's/^[^:]*://' \
	| tr -d '\\' \
	| tr ' \t' '\n\n' \
	| sed '/^$/d' \
	| sort -u)

# 2. Classify: existing file under a user include root → user; otherwise → system.
#    User search roots: $input_dir plus any -I <path> the caller passed in.
user_roots=("$input_dir")
i=0
while [ $i -lt ${#extra_includes[@]} ]; do
	if [ "${extra_includes[$i]}" = "-I" ]; then
		user_roots+=("${extra_includes[$((i+1))]}")
		i=$((i+2))
	else
		user_roots+=("${extra_includes[$i]#-I}")
		i=$((i+1))
	fi
done

is_user_header() {
	local h="$1"
	for root in "${user_roots[@]}"; do
		if [ -f "$root/$h" ]; then
			return 0
		fi
	done
	return 1
}

# 3. Create empty stubs for each system header, preserving subdir structure.
stubbed=()
while IFS= read -r dep; do
	[ -z "$dep" ] && continue
	# Skip the input file itself, which gcc lists alongside deps.
	if [ "$dep" = "$input_file" ] || [ "$(basename "$dep")" = "$(basename "$input_file")" ]; then
		continue
	fi
	if ! is_user_header "$dep"; then
		mkdir -p "$stub_dir/$(dirname "$dep")"
		: > "$stub_dir/$dep"
		stubbed+=("$dep")
	fi
done <<< "$deps"

if [ ${#stubbed[@]} -gt 0 ]; then
	echo "Stubbed ${#stubbed[@]} system header(s): ${stubbed[*]}"
fi

# 4. Real preprocess: user includes resolve normally, system ones expand to nothing.
gcc -E -P -nostdinc -I"$input_dir" "${extra_includes[@]}" -I"$stub_dir" "$input_file" -o "$artifact_dir/temp.hpp"

echo "Preprocessed output written to $artifact_dir/temp.hpp"

python3 "$script_dir/main.py" ${endian:+--endian "$endian"} "$artifact_dir/temp.hpp" > "$output_file"
echo "###### saved resulting python file into $output_file"

# Smoke-test scaffold: instantiate every generated class. Lives in /tmp; the
# scaffold imports output.py from the directory it's written next to.
output_dir=$(cd "$(dirname "$output_file")" && pwd)
output_module=$(basename "$output_file" .py)
cl=$(grep '^class ' "$output_file" | tr ':' ' ' | awk '{print $2}')
echo "$cl"
echo "from $output_module import *" > "$artifact_dir/test.py"
for name in $cl; do
	echo "found built class for $name"
	cat >> "$artifact_dir/test.py" <<EOF
test_object = $name()
print("$name")
print(test_object.get_format_string())
print(test_object.get_size())
print(test_object.__dict__)
EOF
done
(cd "$artifact_dir" && PYTHONPATH="$output_dir:${PYTHONPATH:-}" python3 test.py)
