#!/bin/bash

#g++ -E -P -o temp.hpp $1
#!/bin/bash

# Input file
input_file=$1

# Temporary include directory
tmp_includes="tmp_includes"

# Create the temporary include directory
mkdir -p "$tmp_includes"

# Extract all unique #include directives from the input file
grep '^#include' "$input_file" | awk '{print $2}' | tr -d '<>"' | sort -u | while read -r header; do
    # Create an empty file for each header in the tmp_includes directory
    touch "$tmp_includes/$header"
done

# Preprocess the file with dummy includes
g++ -E -P -I"$tmp_includes" -o temp.hpp "$input_file"

# Clean up the temporary include directory
rm -rf "$tmp_includes"

echo "Preprocessed output written to temp.hpp."


#g++ -E -P -nostdinc -o temp.hpp $1

#gcc -E -dD -P -o temp.hpp $1


python3 main.py temp.hpp > output.py


cl=$(cat output.py | grep class | tr ':' ' ' |awk '{print $2}')
echo "$cl"
echo from output import \* > test.py


for name in $cl
do echo found built class for $name

(cat << EOF
test_object = $name()
print("$name")
print(test_object.get_format_string())
print(test_object.get_size())

print(test_object.__dict__)
EOF
) >> test.py
done


python3 test.py