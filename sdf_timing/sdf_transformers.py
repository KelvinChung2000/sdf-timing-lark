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

from lark import Transformer, v_args
from . import utils


def remove_quotation(s):
    """Remove quotation marks from string."""
    return s.replace('"', '')


class SDFTransformer(Transformer):
    """Streamlined transformer that processes the SDF parse tree into the expected data structure."""
    
    def __init__(self):
        super().__init__()
        # Minimize state - use locals where possible
        self._reset_state()
    
    def _reset_state(self):
        """Reset transformer state for new parsing."""
        self.timings = {'header': {}, 'cells': {}}
        self.delays_list = []
        self.tmp_delay_list = []
        self.tmp_constr_list = []
    
    def sdf_file(self, items):
        """Process the top-level SDF file structure."""
        # Process all items after DELAYFILE token  
        for item in items[1:]:  # Skip "DELAYFILE" token
            if isinstance(item, dict):
                # Determine if it's header or cell data by checking keys
                if any(key in item for key in ['sdfversion', 'design', 'vendor', 'program', 'version', 'divider', 'date', 'voltage', 'process', 'temperature', 'timescale']):
                    self.timings['header'].update(item)
                else:
                    self.timings['cells'].update(item)
        
        return self.timings
    
    def sdf_item(self, items):
        """Process individual SDF items (header or cell)."""
        if len(items) == 1:
            return items[0]
        return {}
    
    def sdf_header(self, items):
        """Process header items into a dictionary."""
        for item in items:
            if isinstance(item, dict):
                self.header.update(item)
        return self.header
    
    def sdf_header_item(self, items):
        """Process header items."""
        if len(items) == 1:
            return items[0]  # voltage, temperature, etc.
        elif len(items) >= 2:
            # header_keyword QSTRING structure
            key = str(items[0]).lower()
            value = remove_quotation(str(items[1])) if len(items) > 1 else ""
            return {key: value}
        return {}
    
    def header_keyword(self, items):
        """Return the header keyword token."""
        return str(items[0])
    
    def voltage(self, items):
        """Process voltage specification."""
        return {'voltage': items[1]}
    
    def rvalue(self, items):
        """Process single value or real triple."""
        if len(items) == 1:
            item = items[0]
            if isinstance(item, dict):
                # It's already a processed real_triple
                return item
            else:
                # Single float value
                return {'min': None, 'avg': float(item), 'max': None}
        else:
            # Multiple items, shouldn't happen with current grammar
            return items[0]
    
    def temperature(self, items):
        """Process temperature specification."""
        return {'temperature': items[1]}
    
    def hierarchy_divider(self, items):
        """Process hierarchy divider."""
        return {'divider': str(items[1])}
    
    def timescale(self, items):
        """Process timescale specification."""
        return {'timescale': str(items[1]) + str(items[2])}
    
    def cell(self, items):
        """Process individual cell definition."""
        celltype = items[1]
        instance = items[2]
        
        self._add_cell(celltype, instance)
        
        if len(items) > 3:  # Has timing information
            self._add_delays_to_cell(celltype, instance, self.delays_list)
        
        self.delays_list = []  # Reset for next cell
        return self.timings['cells']
    
    def celltype(self, items):
        """Process cell type."""
        return remove_quotation(str(items[1]))
    
    def instance(self, items):
        """Process instance name."""
        if len(items) == 1:  # Empty instance
            return None
        elif items[1] == '*':
            return '*'
        else:
            return str(items[1])
    
    # Remove unnecessary pass-through methods - handled by grammar structure
    
    def absolute(self, items):
        """Process absolute delay block."""
        if len(items) > 1:  # Has delay list
            for delay in self.tmp_delay_list:
                delay['is_absolute'] = True
            self.delays_list.extend(self.tmp_delay_list)
            self.tmp_delay_list = []
    
    def increment(self, items):
        """Process increment delay block."""
        for delay in self.tmp_delay_list:
            delay['is_incremental'] = True
        self.delays_list.extend(self.tmp_delay_list)
        self.tmp_delay_list = []
    
    def iopath(self, items):
        """Process IOPATH delay specification."""
        input_port = items[1]
        output_port = items[2] 
        delay_values = items[3]
        
        iopath = utils.add_iopath(input_port, output_port, delay_values)
        self.tmp_delay_list.append(iopath)
        return iopath
    
    def interconnect(self, items):
        """Process INTERCONNECT delay specification."""
        input_port = items[1]
        output_port = items[2]
        delay_values = items[3]
        
        interconnect = utils.add_interconnect(input_port, output_port, delay_values)
        self.tmp_delay_list.append(interconnect)
        return interconnect
    
    def port(self, items):
        """Process PORT delay specification."""
        port_spec = items[1]
        delay_values = items[2]
        
        port = utils.add_port(port_spec, delay_values)
        self.tmp_delay_list.append(port)
        return port
    
    def device(self, items):
        """Process DEVICE delay specification."""
        port_spec = items[1]
        delay_values = items[2]
        
        device = utils.add_device(port_spec, delay_values)
        self.tmp_delay_list.append(device)
        return device
    
    def delval_list(self, items):
        """Process delay value list (1, 2, or 3 real triples)."""
        paths = {}
        
        # Filter out None/empty items
        valid_items = [item for item in items if item is not None and item != {}]
        
        if len(valid_items) == 1:
            paths['nominal'] = valid_items[0]
        elif len(valid_items) == 2:
            paths['fast'] = valid_items[0] 
            paths['slow'] = valid_items[1]
        elif len(valid_items) == 3:
            paths['fast'] = valid_items[0]
            paths['nominal'] = valid_items[1]
            paths['slow'] = valid_items[2]
        else:
            # Fallback for empty list - create a proper structure
            paths['nominal'] = {'min': None, 'avg': None, 'max': None}
            
        return paths
    
    def real_triple(self, items):
        """Process real triple (min:typ:max timing values)."""
        delays_triple = {'min': None, 'avg': None, 'max': None}
        
        if len(items) == 0:
            # Empty case - return proper structure
            return delays_triple
        
        # Handle different real triple formats
        if len(items) == 5:  # FLOAT:FLOAT:FLOAT (5 tokens including colons)
            delays_triple['min'] = float(items[0]) if items[0] != ':' else None
            delays_triple['avg'] = float(items[2]) if items[2] != ':' else None  
            delays_triple['max'] = float(items[4]) if items[4] != ':' else None
        elif len(items) == 4:  # :FLOAT:FLOAT or FLOAT::FLOAT or FLOAT:FLOAT:
            if items[0] == ':':  # :FLOAT:FLOAT
                delays_triple['min'] = None
                delays_triple['avg'] = float(items[1])
                delays_triple['max'] = float(items[3])
            elif items[2] == ':' and items[3] == ':':  # FLOAT::FLOAT
                delays_triple['min'] = float(items[0])
                delays_triple['avg'] = None
                delays_triple['max'] = float(items[3])
            elif items[3] == ':':  # FLOAT:FLOAT:
                delays_triple['min'] = float(items[0])
                delays_triple['avg'] = float(items[2])
                delays_triple['max'] = None
        elif len(items) == 3:  
            # Could be ::FLOAT or :FLOAT: or FLOAT:: or direct FLOAT FLOAT FLOAT
            if items[0] == ':' and items[1] == ':':  # ::FLOAT
                delays_triple['min'] = None
                delays_triple['avg'] = None
                delays_triple['max'] = float(items[2])
            elif items[0] == ':' and items[2] == ':':  # :FLOAT:
                delays_triple['min'] = None
                delays_triple['avg'] = float(items[1])
                delays_triple['max'] = None
            elif items[1] == ':' and items[2] == ':':  # FLOAT::
                delays_triple['min'] = float(items[0])
                delays_triple['avg'] = None
                delays_triple['max'] = None
            else:
                # Direct float values - assume min:avg:max format
                delays_triple['min'] = float(items[0])
                delays_triple['avg'] = float(items[1])
                delays_triple['max'] = float(items[2])
        elif len(items) == 2:  # Two FLOAT values - likely min::max format
            delays_triple['min'] = float(items[0])
            delays_triple['avg'] = None
            delays_triple['max'] = float(items[1])
        elif len(items) == 1:  # Single FLOAT (standalone value)
            # For standalone single values, put in avg field only
            delays_triple['min'] = None
            delays_triple['avg'] = float(items[0])
            delays_triple['max'] = None
        else:
            # Fallback for unexpected cases
            delays_triple['min'] = None
            delays_triple['avg'] = None 
            delays_triple['max'] = None
            
        return delays_triple
    
    def port_spec(self, items):
        """Process port specification."""
        port = {}
        
        if len(items) == 1:
            port['port'] = str(items[0])
            port['port_edge'] = None
        elif len(items) == 2:  # Has port condition (posedge/negedge)
            port['port'] = str(items[1])
            port['port_edge'] = str(items[0]).lower()
        else:
            # Fallback
            port['port'] = str(items[-1])
            port['port_edge'] = None
            
        return port
    
    def port_condition(self, items):
        """Process port condition (posedge/negedge)."""
        return str(items[0])
    
    def timing_port(self, items):
        """Process timing port."""
        if len(items) == 1:
            # Simple port_spec
            port_spec = items[0]
            if isinstance(port_spec, dict):
                port = port_spec.copy()
                port['cond'] = False
                port['cond_equation'] = None
                return port
            else:
                return {'port': str(port_spec), 'port_edge': None, 'cond': False, 'cond_equation': None}
        elif len(items) == 4:  # COND equation port_spec structure
            condition = items[1]  # equation result
            port_spec = items[2]  # port_spec result
            
            if isinstance(port_spec, dict):
                port = port_spec.copy()
                port['cond'] = True
                if isinstance(condition, list):
                    port['cond_equation'] = " ".join(str(x) for x in condition)
                else:
                    port['cond_equation'] = str(condition) if condition else ""
                return port
        return {}
    
    def port_check(self, items):
        """Process port check."""
        if len(items) == 1:
            port = items[0].copy()
            port['cond'] = False
            port['cond_equation'] = None
            return port
        return {}
    
    def cond_check(self, items):
        """Process conditional port check."""
        if len(items) >= 3:
            # Structure: COND equation port_spec
            condition = items[1]  # equation result
            port_spec = items[2]  # port_spec result
            
            if isinstance(port_spec, dict):
                port = port_spec.copy()
                port['cond'] = True
                if isinstance(condition, list):
                    port['cond_equation'] = " ".join(str(x) for x in condition)
                else:
                    port['cond_equation'] = str(condition) if condition else ""
                return port
        return {}
    
    # Timing check handlers
    def setup_check(self, items):
        """Process setup timing check."""
        paths = {'nominal': items[3]}
        tcheck = utils.add_tcheck('setup', items[1], items[2], paths)
        self.tmp_delay_list.append(tcheck)
        return tcheck
    
    def hold_check(self, items):
        """Process hold timing check."""
        paths = {'nominal': items[3]}
        tcheck = utils.add_tcheck('hold', items[1], items[2], paths)
        self.tmp_delay_list.append(tcheck)
        return tcheck
    
    def removal_check(self, items):
        """Process removal timing check."""
        paths = {'nominal': items[3]}
        tcheck = utils.add_tcheck('removal', items[1], items[2], paths)
        self.tmp_delay_list.append(tcheck)
        return tcheck
    
    def recovery_check(self, items):
        """Process recovery timing check."""
        paths = {'nominal': items[3]}
        tcheck = utils.add_tcheck('recovery', items[1], items[2], paths)
        self.tmp_delay_list.append(tcheck)
        return tcheck
    
    def width_check(self, items):
        """Process width timing check."""
        paths = {'nominal': items[2]}
        tcheck = utils.add_tcheck('width', items[1], items[1], paths)
        self.tmp_delay_list.append(tcheck)
        return tcheck
    
    def setuphold_check(self, items):
        """Process setuphold timing check."""
        paths = {'setup': items[3], 'hold': items[4]}
        tcheck = utils.add_tcheck('setuphold', items[1], items[2], paths)
        self.tmp_delay_list.append(tcheck)
        return tcheck
    
    def timing_check_list(self, items):
        """Process timing check list."""
        for item in items:
            if item:
                self.delays_list.extend(self.tmp_delay_list)
        self.tmp_delay_list = []
    
    def cond_delay(self, items):
        """Process conditional delay."""
        condition = items[1]  # delay_condition result
        delays = items[2] if len(items) > 2 else []
        
        # Handle condition - could be string or list
        if isinstance(condition, list):
            condition_str = " ".join(str(x) for x in condition)
        else:
            condition_str = str(condition)
        
        if isinstance(delays, list):
            for delay in delays:
                if isinstance(delay, dict):
                    delay['is_cond'] = True
                    delay['cond_equation'] = condition_str
        
        return delays
    
    def delay_condition(self, items):
        """Process delay condition."""
        if len(items) == 1:
            return items[0]
        return []
    
    def equation(self, items):
        """Process equation for conditions."""
        return [str(item) for item in items]
    
    def equation_item(self, items):
        """Process equation items."""
        return str(items[0])
    
    def path_constraint(self, items):
        """Process path constraint."""
        paths = {'rise': items[3], 'fall': items[4]}
        constr = utils.add_constraint('pathconstraint', items[1], items[2], paths)
        self.tmp_constr_list.append(constr)
        return constr
    
    def constraints_list(self, items):
        """Process constraints list."""
        self.delays_list.extend(self.tmp_constr_list)
        self.tmp_constr_list = []
    
    # Helper methods
    def _add_cell(self, name, instance):
        """Add cell to cells dictionary."""
        if name not in self.timings['cells']:
            self.timings['cells'][name] = {}
        if instance not in self.timings['cells'][name]:
            self.timings['cells'][name][instance] = {}
    
    def _add_delays_to_cell(self, celltype, instance, delays):
        """Add delays to a cell."""
        if delays is None:
            return
        for delay in delays:
            self.timings['cells'][celltype][instance][delay['name']] = delay
    
    # Handle terminal values
    @v_args(inline=True) 
    def STRING(self, value):
        return str(value)
    
    @v_args(inline=True)
    def FLOAT(self, value): 
        return float(value)
    
    @v_args(inline=True)
    def QSTRING(self, value):
        return str(value)
    
    @v_args(inline=True) 
    def QFLOAT(self, value):
        return str(value)