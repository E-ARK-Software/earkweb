#!/bin/bash

# Function to read a configuration value
get_config_value() {
    local config_file="$1"
    local category="$2"
    local key="$3"
    awk -F "=" -v section="$category" -v key="$key" '
    BEGIN {
        in_section = 0
    }
    /^\[/{ 
        in_section = ($0 == "[" section "]")
    }
    in_section && $1 ~ key {
        gsub(/^[ \t]+|[ \t]+$/, "", $2)
        print $2
        exit
    }
    ' "$config_file"
}
