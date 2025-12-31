#!/bin/bash

# Configuration defaults
DEFAULT_STORIES="examples/example_7/three_features.json"
DEFAULT_DURATION=50
DEFAULT_PLAN="1-50:2,4,4,2"
HIGHLIGHT="FEATURE-1"

# Run the simulation using the local virtual environment
# This ensures Tkinter and Heatmap support works correctly
./.venv/bin/python -m devcyclesim.src.cli run \
    --stories-file "$DEFAULT_STORIES" \
    --duration "$DEFAULT_DURATION" \
    --resource-plan "$DEFAULT_PLAN" \
    --plot \
    --highlight-feature "$HIGHLIGHT" \
    "$@"
