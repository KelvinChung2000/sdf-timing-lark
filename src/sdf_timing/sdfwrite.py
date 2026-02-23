#!/usr/bin/env python3
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


import jinja2

env = jinja2.Environment(loader=jinja2.PackageLoader("sdf_timing", "templates"))



def emit_timingenv_entries(delays: dict) -> str:
    entries = [delays[k] for k in sorted(delays) if delays[k].is_timing_env]
    template = env.get_template("timingenv.j2")
    return template.render(entries=entries)


def emit_timingcheck_entries(delays: dict) -> str:
    entries = [delays[k] for k in sorted(delays) if delays[k].is_timing_check]
    template = env.get_template("timingcheck.j2")
    return template.render(entries=entries)


def emit_delay_entries(delays: dict) -> str:
    sorted_delays = [delays[k] for k in sorted(delays)]
    
    # Filter and categorize entries
    # Logic from original code:
    # if not abs and not inc: continue (skip timing checks etc)
    # if abs: add to absolute
    # else: add to incremental
    
    absolute_entries = []
    incremental_entries = []
    
    for delay in sorted_delays:
        if not delay.is_absolute and not delay.is_incremental:
            continue
        
        if delay.is_absolute:
            absolute_entries.append(delay)
        else:
            incremental_entries.append(delay)

    template = env.get_template("delay.j2")
    return template.render(
        absolute_entries=absolute_entries, incremental_entries=incremental_entries
    )


def emit_sdf(
    timings: object, timescale: str = "1ps", uppercase_celltype: bool = False
) -> str:
    prepared_cells = {}
    # timings is now SDFFile object
    if timings.cells:
        for cell_name in timings.cells:
            prepared_cells[cell_name] = {}
            for instance_name in timings.cells[cell_name]:
                delays = timings.cells[cell_name][instance_name]
                prepared_cells[cell_name][instance_name] = {
                    "delay_entries": emit_delay_entries(delays),
                    "timingcheck_entries": emit_timingcheck_entries(delays),
                    "timingenv_entries": emit_timingenv_entries(delays),
                }

    template = env.get_template("sdf.j2")
    sdf = template.render(
        timescale=timescale,
        cells=prepared_cells,
        uppercase_celltype=uppercase_celltype,
    )

    # fix "None" entries
    sdf = sdf.replace("None", "")
    return sdf
