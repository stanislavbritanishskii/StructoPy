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

extra_includes=()
endian=""
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
			echo "Usage: $0 [--endian little|big] [-I <include_dir>]... <input.h>"
			exit 0
			;;
		--)
			shift
			break
			;;
		-*)
			echo "Unknown flag: $1" >&2
			echo "Usage: $0 [--endian little|big] [-I <include_dir>]... <input.h>" >&2
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
	echo "Usage: $0 [-I <include_dir>]... <input.h>" >&2
	exit 1
fi
if [ ! -f "$input_file" ]; then
	echo "Error: file '$input_file' not found" >&2
	exit 1
fi

input_dir=$(dirname "$input_file")
stub_dir=$(mktemp -d)
trap 'rm -rf "$stub_dir"' EXIT

# Artifacts go to /tmp/structopy/ so the repo working tree stays clean.
# Fixed path (not mktemp) so the location is predictable across runs.
# Override with STRUCTOPY_ARTIFACT_DIR if you need a different location
# (the test harness uses this to keep parallel runs isolated).
artifact_dir="${STRUCTOPY_ARTIFACT_DIR:-/tmp/structopy}"
mkdir -p "$artifact_dir"

# Resolve main.py relative to this script so run.sh works from any cwd.
script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

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

python3 "$script_dir/main.py" ${endian:+--endian "$endian"} "$artifact_dir/temp.hpp" > "$artifact_dir/output.py"
echo "###### saved resulting python file into $artifact_dir/output.py"

# Smoke-test scaffold: instantiate every generated class.
cl=$(grep '^class ' "$artifact_dir/output.py" | tr ':' ' ' | awk '{print $2}')
echo "$cl"
echo "from output import *" > "$artifact_dir/test.py"
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
(cd "$artifact_dir" && python3 test.py)
