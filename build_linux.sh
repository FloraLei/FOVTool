#!/bin/bash
# Quick build wrapper - Linux
# Calls scripts/build_linux.sh

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"
./scripts/build_linux.sh
