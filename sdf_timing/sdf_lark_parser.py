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

import os
from pathlib import Path
from lark import Lark, LarkError
from .sdf_transformers import SDFTransformer


class SDFLarkParser:
    """Lark-based SDF parser that replaces the PLY implementation."""
    
    def __init__(self):
        """Initialize the parser with the SDF grammar."""
        # Get the path to the grammar file
        grammar_path = Path(__file__).parent / "sdf.lark"
        
        try:
            with open(grammar_path, 'r') as f:
                grammar = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Grammar file not found: {grammar_path}")
        
        # Create the Lark parser with LALR(1) algorithm for performance
        self.parser = Lark(
            grammar,
            parser='lalr',
            start='start',
            transformer=SDFTransformer()
        )
    
    def parse(self, input_text):
        """
        Parse SDF input text and return the timing data structure.
        
        Args:
            input_text (str): The SDF file content as a string
            
        Returns:
            dict: Parsed timing data in the same format as the PLY parser
            
        Raises:
            LarkError: If parsing fails
        """
        try:
            # Parse the input and transform it using our transformer
            result = self.parser.parse(input_text)
            return result
            
        except LarkError as e:
            # Preserve original Lark error with better context
            raise LarkError(f"SDF parsing failed at {getattr(e, 'line', 'unknown')}:{getattr(e, 'column', 'unknown')} - {str(e)}")
        except Exception as e:
            # Re-raise with context but preserve original exception type
            raise type(e)(f"Unexpected error during SDF parsing: {str(e)}") from e
    
    def parse_file(self, filepath):
        """
        Parse an SDF file directly.
        
        Args:
            filepath (str): Path to the SDF file
            
        Returns:
            dict: Parsed timing data
        """
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            return self.parse(content)
        except IOError as e:
            raise Exception(f"Error reading SDF file {filepath}: {str(e)}")


# Thread-local storage for parser instances to ensure thread safety
import threading
_local = threading.local()


def get_parser():
    """Get or create a thread-local parser instance."""
    if not hasattr(_local, 'parser'):
        _local.parser = SDFLarkParser()
    return _local.parser


def parse_sdf(input_text):
    """
    Parse SDF text using the Lark parser.
    
    This function provides the same interface as the original PLY-based parser.
    
    Args:
        input_text (str): SDF content as string
        
    Returns:
        dict: Parsed timing data structure
    """
    # Create a fresh parser instance to avoid state contamination
    parser = SDFLarkParser()
    return parser.parse(input_text)


def parse_sdf_file(filepath):
    """
    Parse an SDF file using the Lark parser.
    
    Args:
        filepath (str): Path to SDF file
        
    Returns:
        dict: Parsed timing data structure
    """
    parser = get_parser()
    return parser.parse_file(filepath)