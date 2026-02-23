from lark import Transformer, v_args, Token

from . import utils
from .model import (
    SDFFile, SDFHeader, Values, DelayPaths,
    BaseEntry, Port, Interconnect, Iopath, Device,
    Setup, Hold, Removal, Recovery, Width, SetupHold,
    PathConstraint
)


def remove_quotation(s: str) -> str:
    """Remove quotation marks from string."""
    return s.replace('"', "")


class SDFTransformer(Transformer):
    """
    Streamlined transformer that processes the SDF parse tree
    into the expected data structure.
    """

    def __init__(self) -> None:
        super().__init__()
        # Minimize state - use locals where possible
        self._reset_state()

    def _reset_state(self) -> None:
        """Reset transformer state for new parsing."""
        self.sdf_file_obj = SDFFile()
        self.delays_list = []
        self.tmp_delay_list = []
        self.tmp_constr_list = []

    @v_args(inline=True)
    def sdf_file(self, _tag, *items):
        """Process the top-level SDF file structure."""
        # Process all items
        for item in items:
            if isinstance(item, dict):
                # Header items
                for key, value in item.items():
                    if hasattr(self.sdf_file_obj.header, key):
                        setattr(self.sdf_file_obj.header, key, value)
            # Cells are populated in cell() method directly into self.sdf_file_obj.cells

        return self.sdf_file_obj

    @v_args(inline=True)
    def sdf_item(self, item):
        """Process individual SDF items (header or cell)."""
        return item

    @v_args(inline=True)
    def sdf_header_item(self, item):
        """Pass through header items."""
        return item

    @v_args(inline=True)
    def sdf_version(self, value=None):
        return {"sdfversion": remove_quotation(str(value)) if value else ""}

    @v_args(inline=True)
    def design(self, value=None):
        return {"design": remove_quotation(str(value)) if value else ""}

    @v_args(inline=True)
    def date(self, value=None):
        return {"date": remove_quotation(str(value)) if value else ""}

    @v_args(inline=True)
    def vendor(self, value=None):
        return {"vendor": remove_quotation(str(value)) if value else ""}

    @v_args(inline=True)
    def program(self, value=None):
        return {"program": remove_quotation(str(value)) if value else ""}

    @v_args(inline=True)
    def version(self, value=None):
        return {"version": remove_quotation(str(value)) if value else ""}

    @v_args(inline=True)
    def process(self, value=None):
        return {"process": remove_quotation(str(value)) if value else ""}

    @v_args(inline=True)
    def voltage(self, val):
        """Process voltage specification."""
        return {"voltage": val}

    @v_args(inline=True)
    def rvalue(self, *args):
        """Process single value or real triple."""
        # Handle potential anonymous tokens like '(' ')' if passed, or just value.
        # Robustly find the value (float or Values object)
        item = None
        for arg in args:
            if isinstance(arg, (float, Values)):
                item = arg
                break
            # If token, try converting to float
            if isinstance(arg, Token) and arg.type == 'FLOAT':
                item = float(arg)
                break
            # If arg is None (optional placeholder), ignore or treat as missing

        if item is None:
            return Values(min=None, avg=None, max=None)
        if isinstance(item, Values):
            # It's already a processed real_triple
            return item
        # Single float value (from loop) or passed directly
        return Values(min=None, avg=float(item), max=None)

    @v_args(inline=True)
    def temperature(self, val):
        """Process temperature specification."""
        return {"temperature": val}

    @v_args(inline=True)
    def hierarchy_divider(self, val):
        """Process hierarchy divider."""
        return {"divider": str(val)}

    @v_args(inline=True)
    def timescale(self, val, unit):
        """Process timescale specification."""
        return {"timescale": str(val) + str(unit)}

    @v_args(inline=True)
    def cell(self, celltype, instance, delays=None):
        """Process individual cell definition."""
        # Rule: "(" "CELL" celltype instance [timing_cell_lst] ")"
        # "CELL", "(", ")" are literals.
        # Args: celltype, instance, [delays] (optional)
        
        self._add_cell(str(celltype), str(instance))
        if delays is not None:
            self._add_delays_to_cell(str(celltype), str(instance), self.delays_list)

        self.delays_list = []  # Reset for next cell
        return {}

    @v_args(inline=True)
    def celltype(self, val):
        """Process cell type."""
        return remove_quotation(str(val))

    @v_args(inline=True)
    def instance(self, val=None):
        """Process instance name."""
        if val is None:
            return None
        if val == "*":
            return "*"
        return str(val)

    # Remove unnecessary pass-through methods - handled by grammar structure
    # NOTE: timing_cell_lst, absolute_list, increment_list etc might need handling if not standard?
    # absolute_list: absolute+ -> if no method, returns Tree. But absolute returns None (modifies side effect).
    # So absolute_list should just process children.
    # If absolute returns None, absolute_list might return [None, None].
    # But cell ignores timing_cell_lst return value?
    # cell method:
    # if delays is not None: self._add_delays_to_cell(...)
    # self.delays_list is populated by side-effects in absolute/increment methods (which put in tmp, then move to delays_list).
    # Wait, absolute/increment methods pop from tmp and push to delays_list.
    # Where does tmp come from?
    # iopath/interconnect/etc append to `self.tmp_delay_list`?
    # Let's check `iopath`.
    # iopath returns `iopath` object. Does it append? -> No, returns argument.
    # Wait.
    # `iopath` is a child of `del`.
    # `del` is child of `increment` (in `del+`).
    # `increment` args: `*delays`. These are the `iopath` objects!
    # `increment` method says:
    # for delay in self.tmp_delay_list: ...
    # This implies `increment` expects `tmp_delay_list` to be populated.
    # BUT `iopath` method DOES NOT append to `tmp_delay_list`. It returns the object.
    # `iopath`: `return iopath`.
    # So `self.tmp_delay_list` is EMPTY if `iopath` just returns.
    # This logic is broken if I removed the side-effects from `iopath`?
    # Previous code:
    # `def iopath(self, ...): ... self.tmp_delay_list.append(iopath); return iopath`?
    # Let's check `iopath` in `sdf_transformers.py` (current state).
    # I replaced it recently.
    # I need to verify `iopath` implementation.

    # Helper to flatten args including Trees
    @v_args(inline=True)
    def delay_entry(self, item):
        return item

    @v_args(inline=True)
    def absolute(self, *delays):
        """Process absolute delay block."""
        for d in delays:
             if isinstance(d, (list, tuple)):
                 for sub_d in d:
                     sub_d.is_absolute = True
                     self.delays_list.append(sub_d)
             else:
                 d.is_absolute = True
                 self.delays_list.append(d)

    @v_args(inline=True)
    def increment(self, *delays):
        """Process increment delay block."""
        for d in delays:
             if isinstance(d, (list, tuple)):
                 for sub_d in d:
                     sub_d.is_incremental = True
                     self.delays_list.append(sub_d)
             else:
                 d.is_incremental = True
                 self.delays_list.append(d)

    @v_args(inline=True)
    def iopath(self, input_port: dict, output_port: dict, delay_values: DelayPaths):
        """Process IOPATH delay specification."""
        iopath = Iopath(
            name=f"iopath_{input_port['port']}_{output_port['port']}",
            from_pin=input_port["port"],
            to_pin=output_port["port"],
            from_pin_edge=input_port["port_edge"],
            to_pin_edge=output_port["port_edge"],
            delay_paths=delay_values,
        )
        return iopath

    @v_args(inline=True)
    def interconnect(self, input_port: dict, output_port: dict, delay_values: DelayPaths):
        """Process INTERCONNECT delay specification."""
        interconnect = Interconnect(
            name=f"interconnect_{input_port['port']}_{output_port['port']}",
            from_pin=input_port["port"],
            to_pin=output_port["port"],
            from_pin_edge=input_port["port_edge"],
            to_pin_edge=output_port["port_edge"],
            delay_paths=delay_values,
        )
        return interconnect

    @v_args(inline=True)
    def port(self, port_spec: dict, delay_values: DelayPaths):
        """Process PORT delay specification."""
        port = Port(
            name=f"port_{port_spec['port']}",
            from_pin=port_spec["port"],
            to_pin=port_spec["port"],
            delay_paths=delay_values,
        )
        return port

    @v_args(inline=True)
    def device(self, port_spec: dict, delay_values: DelayPaths):
        """Process DEVICE delay specification."""
        device = Device(
            name=f"device_{port_spec['port']}",
            from_pin=port_spec["port"],
            to_pin=port_spec["port"],
            delay_paths=delay_values,
        )
        return device

    @v_args(inline=True)
    def delval_list(self, *items):
        """Process delay value list (1, 2, or 3 real triples)."""
        paths = DelayPaths()

        # Filter out None/empty items just in case, though inline args usually precise
        valid_items = [item for item in items if item is not None and item != {}]

        if len(valid_items) == 1:
            paths.nominal = valid_items[0]
        elif len(valid_items) == 2:
            paths.fast = valid_items[0]
            paths.slow = valid_items[1]
        elif len(valid_items) == 3:
            paths.fast = valid_items[0]
            paths.nominal = valid_items[1]
            paths.slow = valid_items[2]
        else:
            # Fallback for empty list - create a proper structure
            paths.nominal = Values(min=None, avg=None, max=None)

        return paths

    @v_args(inline=True)
    def real_triple(self, min_val: Token, avg_val: Token, max_val: Token):
        """Process real triple (min:avg:max)."""
        return Values(
            min=float(min_val) if min_val is not None else None,
            avg=float(avg_val) if avg_val is not None else None,
            max=float(max_val) if max_val is not None else None,
        )

    @v_args(inline=True)
    def port_spec(self, *args):
        """Process port specification."""
        # port_spec: STRING (1 arg) | "(" (posedge|negedge) STRING ")"
        # "posedge"/"negedge" are tokens (POSEDGE/NEGEDGE).
        # parens are literals.
        # So args will be:
        # Case 1: [STRING]
        # Case 2: [EDGE_TOKEN, STRING]
        
        port = {}

        if len(args) == 1:
            port["port"] = str(args[0])
            port["port_edge"] = None
        elif len(args) == 2:
            port["port"] = str(args[1])
            port["port_edge"] = str(args[0]).lower()
        else:
             # Should not happen given the grammar
            raise ValueError(f"Invalid port_spec args: {args}")

        return port

    @v_args(inline=True)
    def port_condition(self, token):
        """Process port condition (posedge/negedge)."""
        return str(token)

    @v_args(inline=True)
    def timing_port(self, *args):
        """Process timing port."""
        # Rule: port_spec | "(" "COND" equation port_spec ")"
        # Parens and "COND" are literals.
        # Case 1: [port_spec_result] (1 arg)
        # Case 2: [equation, port_spec_result] (2 args)
        
        if len(args) == 1:
            # Simple port_spec
            port_spec = args[0]
            if isinstance(port_spec, dict):
                port = port_spec.copy()
                port["cond"] = False
                port["cond_equation"] = None
                return port
            return {
                "port": str(port_spec),
                "port_edge": None,
                "cond": False,
                "cond_equation": None,
            }
        
        if len(args) == 2:
            condition = args[0]
            port_spec = args[1]

            if isinstance(port_spec, dict):
                port = port_spec.copy()
                port["cond"] = True
                if isinstance(condition, list):
                    port["cond_equation"] = " ".join(str(x) for x in condition)
                else:
                    port["cond_equation"] = str(condition) if condition else ""
                return port

        return {}

    @v_args(inline=True)
    def port_check(self, port):
        """Process port check."""
        # port_check: "(" PORT port_spec ")" ?? No, rule is `port_check`?
        # Actually grammar does NOT have `port_check` rule! It has `t_check`.
        # Searching grammar... `timing_port` is used.
        # Wait, I saw `port_check` in the file.
        # Line 274: `def port_check(self, items):`
        # Checking `sdf.lark` again...
        # Ah, I don't see `port_check` in `sdf.lark` provided in view_file.
        # The transformers file has it but maybe it's dead code?
        # `t_check: removal_check | ...`
        # `removal_check: ... timing_port ...`
        # `timing_port: port_spec | ...`
        # I don't see `port_check` in the grammar.
        # I will remove it if it is dead code.
        return {}

    @v_args(inline=True)
    def cond_check(self, *args):
        """Process conditional port check."""
        # Similarly `cond_check` is not in the grammar I viewed.
        # `timing_port` rule handles user COND logic.
        # I will remove `cond_check` as well if it's dead code.
        return {}

    # Timing check handlers
    @v_args(inline=True)
    def setup_check(self, to_port: dict, from_port: dict, values: Values):
        """Process setup timing check."""
        paths = DelayPaths(nominal=values)
        tcheck = Setup(
            name=f"setup_{from_port['port']}_{to_port['port']}",
            is_timing_check=True,
            is_cond=from_port.get("cond", False),
            cond_equation=from_port.get("cond_equation"),
            from_pin=from_port["port"],
            to_pin=to_port["port"],
            from_pin_edge=from_port["port_edge"],
            to_pin_edge=to_port["port_edge"],
            delay_paths=paths,
        )
        return tcheck

    @v_args(inline=True)
    def hold_check(self, to_port: dict, from_port: dict, values: Values):
        """Process hold timing check."""
        paths = DelayPaths(nominal=values)
        tcheck = Hold(
            name=f"hold_{from_port['port']}_{to_port['port']}",
            is_timing_check=True,
            is_cond=from_port.get("cond", False),
            cond_equation=from_port.get("cond_equation"),
            from_pin=from_port["port"],
            to_pin=to_port["port"],
            from_pin_edge=from_port["port_edge"],
            to_pin_edge=to_port["port_edge"],
            delay_paths=paths,
        )
        return tcheck

    @v_args(inline=True)
    def removal_check(self, to_port: dict, from_port: dict, values: Values):
        """Process removal timing check."""
        paths = DelayPaths(nominal=values)
        tcheck = Removal(
            name=f"removal_{from_port['port']}_{to_port['port']}",
            is_timing_check=True,
            is_cond=from_port.get("cond", False),
            cond_equation=from_port.get("cond_equation"),
            from_pin=from_port["port"],
            to_pin=to_port["port"],
            from_pin_edge=from_port["port_edge"],
            to_pin_edge=to_port["port_edge"],
            delay_paths=paths,
        )
        return tcheck

    @v_args(inline=True)
    def recovery_check(self, to_port: dict, from_port: dict, values: Values):
        """Process recovery timing check."""
        paths = DelayPaths(nominal=values)
        tcheck = Recovery(
            name=f"recovery_{from_port['port']}_{to_port['port']}",
            is_timing_check=True,
            is_cond=from_port.get("cond", False),
            cond_equation=from_port.get("cond_equation"),
            from_pin=from_port["port"],
            to_pin=to_port["port"],
            from_pin_edge=from_port["port_edge"],
            to_pin_edge=to_port["port_edge"],
            delay_paths=paths,
        )
        return tcheck

    @v_args(inline=True)
    def width_check(self, port: dict, values: Values):
        """Process width timing check."""
        paths = DelayPaths(nominal=values)
        # Width check usually uses the same port for from/to logic in utils
        tcheck = Width(
            name=f"width_{port['port']}_{port['port']}",
            is_timing_check=True,
            is_cond=port.get("cond", False),
            cond_equation=port.get("cond_equation"),
            from_pin=port["port"],
            to_pin=port["port"],
            from_pin_edge=port["port_edge"],
            to_pin_edge=port["port_edge"],
            delay_paths=paths,
        )
        return tcheck

    @v_args(inline=True)
    def setuphold_check(self, to_port: dict, from_port: dict, setup_val: Values, hold_val: Values):
        """Process setuphold timing check."""
        paths = DelayPaths(setup=setup_val, hold=hold_val)
        tcheck = SetupHold(
            name=f"setuphold_{from_port['port']}_{to_port['port']}",
            is_timing_check=True,
            is_cond=from_port.get("cond", False),
            cond_equation=from_port.get("cond_equation"),
            from_pin=from_port["port"],
            to_pin=to_port["port"],
            from_pin_edge=from_port["port_edge"],
            to_pin_edge=to_port["port_edge"],
            delay_paths=paths,
        )
        return tcheck

    @v_args(inline=True)
    def t_check(self, item):
        return item

    @v_args(inline=True)
    def timing_check_list(self, *items):
        """Process timing check list."""
        self.delays_list.extend(items)

    @v_args(inline=True)
    def cond_delay(self, condition, *delays):
        """Process conditional delay."""
        for delay in delays:
            if hasattr(delay, "is_cond"):
                delay.is_cond = True
                delay.cond_equation = condition
        return delays

    @v_args(inline=True)
    def delay_entry(self, item):
        """Unwrap delay entry."""
        return item

    @v_args(inline=True)
    def delay_condition(self, eq):
        """Process delay condition."""
        return eq

    @v_args(inline=True)
    def equation(self, *items):
        """Process equation for conditions."""
        return " ".join(str(item) for item in items)

    @v_args(inline=True)
    def equation_item(self, item):
        """Process equation items."""
        return str(item)

    @v_args(inline=True)
    def path_constraint(self, to_port: dict, from_port: dict, rise_val: Values, fall_val: Values):
        """Process path constraint."""
        # Rule: "(" "PATHCONSTRAINT" port_spec port_spec rvalue rvalue ")" -> args=[to, from, rise, fall]
        paths = DelayPaths(rise=rise_val, fall=fall_val)
        constr = PathConstraint(
            name=f"pathconstraint_{from_port['port']}_{to_port['port']}",
            is_timing_env=True,
            from_pin=from_port["port"],
            to_pin=to_port["port"],
            from_pin_edge=from_port["port_edge"],
            to_pin_edge=to_port["port_edge"],
            delay_paths=paths,
        )
        return constr

    @v_args(inline=True)
    def constraints_list(self, *items):
        """Process constraints list."""
        self.delays_list.extend(items)

    # Helper methods
    def _add_cell(self, name, instance):
        """Add cell to cells dictionary."""
        if name not in self.sdf_file_obj.cells:
            self.sdf_file_obj.cells[name] = {}
        if instance not in self.sdf_file_obj.cells[name]:
            self.sdf_file_obj.cells[name][instance] = {}

    def _add_delays_to_cell(self, celltype, instance, delays):
        """Add delays to a cell."""
        if delays is None:
            return
        for delay in delays:
            self.sdf_file_obj.cells[celltype][instance][delay.name] = delay

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

    def equation(self, items):
        """Flatten equation tokens into a string."""
        return " ".join(str(item) for item in items)

    @v_args(inline=True)
    def operator(self, token):
        """Return operator string."""
        return str(token)

    @v_args(inline=True)
    def delay_condition(self, *args):
        """Handle delay condition."""
        # args can be (equation,) or (LPAR, equation, RPAR)
        # We just want the equation string.
        # But wait, grammar is: "(" equation ")" | equation
        # If we inline, we get tokens.
        # If we don't inline, we get [equation] or [LPAR, equation, RPAR].
        # Let's iterate and find the equation string.
        for arg in args:
            if isinstance(arg, str) and arg not in ("(", ")"):
                return arg
        # If not found (shouldn't happen if equation returns string), join everything?
        # Actually, equation returns string.
        # if arg is equation string, return it.
        return "".join(str(a) for a in args if str(a) not in ("(", ")"))
