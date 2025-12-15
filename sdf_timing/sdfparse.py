#!/usr/bin/env python3
# coding: utf-8
#
# Copyright 2020-2022 F4PGA Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

from . import sdfwrite
from .sdf_lark_parser import parse_sdf


def emit(input, timescale='1ps'):
    return sdfwrite.emit_sdf(input, timescale)


def parse(input):
    """
    Parse SDF input text using Lark parser.
    
    Args:
        input (str): SDF content as string
        
    Returns:
        dict: Parsed timing data structure
    """
    return parse_sdf(input)


def main():
    """Main entry point for command line usage."""
    import sys
    import json
    
    if len(sys.argv) != 2:
        print("Usage: sdf_timing_parse <sdf_file>")
        sys.exit(1)
    
    sdf_file = sys.argv[1]
    
    try:
        with open(sdf_file, 'r') as f:
            content = f.read()
        
        result = parse(content)
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"Error parsing SDF file: {e}")
        sys.exit(1)
