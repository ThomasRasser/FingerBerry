#!/bin/bash

echo "Project structure with Python functions and classes:"
echo

find . -type d ! -path '*/.*' | sort | while read -r dir; do
    indent=$(echo "$dir" | awk -F'/' '{print NF-1}')
    printf "%*s📁 %s\n" $((indent * 2)) "" "$(basename "$dir")"

    find "$dir" -maxdepth 1 -mindepth 1 -type f -name "*.py" ! -name ".*" | sort | while read -r file; do
        file_indent=$((indent + 1))
        printf "%*s📄 %s\n" $((file_indent * 2)) "" "$(basename "$file")"

        grep -En '^\s*(def|class) ' "$file" | while read -r line; do
            lineno=$(echo "$line" | cut -d: -f1)
            content=$(echo "$line" | cut -d: -f2-)
            def_indent=$((file_indent + 1))
            printf "%*s🔹 %s (line %s)\n" $((def_indent * 2)) "" "$content" "$lineno"
        done
    done
done
