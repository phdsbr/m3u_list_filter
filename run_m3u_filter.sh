#!/usr/bin/env bash

set -e

source "venv/bin/activate"

python3 -u m3u_filter.py --config='m3u_list.conf'
