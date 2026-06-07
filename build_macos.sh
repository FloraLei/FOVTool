#!/bin/bash
# Quick build wrapper - macOS
# Calls scripts/build_macos.sh

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"
./scripts/build_macos.sh
