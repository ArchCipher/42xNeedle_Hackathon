import json
import re
from typing import Any, Dict, List, Optional, Tuple

def compile_file(path: str) -> int:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception:
        print('', end='')
        return 2

    result = {
        "pattern_name": None,
        "cast_on": None,
        "valid": True,
        "errors": [],
        "expanded_rows": [],
        "final_stitch_count": None,
        "bind_off": False
    }

    pattern_line = None
    cast_on_line = None
    bind_off_line = None
    first_cast_on_value = None
    first_pattern_name = None
    row_line_map = {}  # source_row -> line number
    seen_rows = set()
    statements = []
    bind_off_seen = False
    row_seen = False
    last_valid_row_number = 0

    # First pass: parse lines, strip comments, classify statements
    for i, line in enumerate(lines):
        line_num = i + 1
        original_line = line
        line = line.rstrip()

        # Handle comments: only outside quoted pattern names
        in_quote = False
        comment_start = None
        for j, c in enumerate(line):
            if c == '"' and (j == 0 or line[j-1] != '\\'):
                in_quote = not in_quote
            elif c == '#' and not in_quote:
                comment_start = j
                break
        if comment_start is not None:
            line = line[:comment_start]

        line = line.strip()

        if not line:
            continue

        stmt = {"line": line_num, "text": line, "type": None, "raw": original_line.rstrip()}

        # Check for pattern
        if line.startswith('pattern '):
            if re.fullmatch(r'pattern\s+"[^"]*"', line):
                if first_pattern_name is None:
                    name_match = re.search(r'"([^"]*)"', line)
                    first_pattern_name = name_match.group(1) if name_match else ""
                    pattern_line = line_num
                else:
                    result["errors"].append({
                        "type": "error",
                        "code": "DUPLICATE_PATTERN",
                        "message": "Duplicate pattern declaration.",
                        "line": line_num,
                        "row": None
                    })
                stmt["type"] = "pattern_valid"
            else:
                result["errors"].append({
                    "type": "error",
                    "code": "MALFORMED_PATTERN",
                    "message": "Malformed pattern declaration.",
                    "line": line_num,
                    "row": None
                })
                stmt["type"] = "pattern_malformed"
        # Check for cast_on
        elif line.startswith('cast_on '):
            if re.fullmatch(r'cast_on\s+[1-9][0-9]*|cast_on\s+0+[1-9][0-9]*', line):
                value = int(line.split()[1])
                if first_cast_on_value is None:
                    first_cast_on_value = value
                    cast_on_line = line_num
                stmt["type"] = "cast_on_valid"
            else:
                result["errors"].append({
                    "type": "error",
                    "code": "MALFORMED_CAST_ON",
                    "message": "Malformed cast_on declaration.",
                    "line": line_num,
                    "row": None
                })
                stmt["type"] = "cast_on_malformed"
        # Check for row
        elif line.startswith('row '):
            row_match = re.match(r'row\s+(\d+):\s*(.*)', line)
            if row_match:
                row_num = int(row_match.group(1))
                if row_num <= 0:
                    result["errors"].append({
                        "type": "error",
                        "code": "MALFORMED_ROW",
                        "message": "Row number must be positive.",
                        "line": line_num,
                        "row": None
                    })
                    stmt["type"] = "row_malformed"
                else:
                    stmt["type"] = "row_valid"
                    stmt["row_num"] = row_num
                    stmt["instructions_text"] = row_match.group(2)
                    row_line_map[row_num] = line_num
            else:
                result["errors"].append({
                    "type": "error",
                    "code": "MALFORMED_ROW",
                    "message": "Malformed row declaration.",
                    "line": line_num,
                    "row": None
                })
                stmt["type"] = "row_malformed"
        # Check for repeat
        elif line.startswith('repeat '):
            stmt["type"] = "repeat"
            stmt["text"] = line
        # Check for bind_off
        elif line == 'bind_off':
            if bind_off_seen:
                result["errors"].append({
                    "type": "error",
                    "code": "DUPLICATE_BIND_OFF",
                    "message": "Duplicate bind_off declaration.",
                    "line": line_num,
                    "row": None
                })
            else:
                bind_off_seen = True
                bind_off_line = line_num
            stmt["type"] = "bind_off_valid"
        elif line.startswith('bind_off '):
            result["errors"].append({
                "type": "error",
                "code": "MALFORMED_BIND_OFF",
                "message": "Malformed bind_off declaration.",
                "line": line_num,
                "row": None
            })
            stmt["type"] = "bind_off_malformed"
        else:
            result["errors"].append({
                "type": "error",
                "code": "UNKNOWN_STATEMENT",
                "message": "Unknown statement.",
                "line": line_num,
                "row": None
            })
            stmt["type"] = "unknown"

        statements.append(stmt)

        # Check order: cast_on after row?
        if stmt["type"] in ["row_valid", "row_malformed"]:
            row_seen = True

        if stmt["type"] in ["cast_on_valid", "cast_on_malformed"] and row_seen:
            result["errors"].append({
                "type": "error",
                "code": "CAST_ON_OUT_OF_ORDER",
                "message": "cast_on appears after a row.",
                "line": line_num,
                "row": None
            })

        # Check bind_off out of order
        if bind_off_seen and stmt["type"] not in ["bind_off_valid", "bind_off_malformed"] and line_num > bind_off_line:
            result["errors"].append({
                "type": "error",
                "code": "BIND_OFF_OUT_OF_ORDER",
                "message": "Statement appears after bind_off.",
                "line": line_num,
                "row": stmt.get("row_num")
            })

    # Set top-level fields
    result["pattern_name"] = first_pattern_name
    result["cast_on"] = first_cast_on_value
    result["bind_off"] = bind_off_seen

    # Missing pattern?
    if first_pattern_name is None and not any(e["code"] == "MALFORMED_PATTERN" for e in result["errors"]):
        result["errors"].append({
            "type": "error",
            "code": "MISSING_PATTERN",
            "message": "Missing pattern declaration.",
            "line": None,
            "row": None
        })

    # Missing cast_on?
    if first_cast_on_value is None and not any(e["code"] == "MALFORMED_CAST_ON" for e in result["errors"]):
        result["errors"].append({
            "type": "error",
            "code": "MISSING_CAST_ON",
            "message": "Missing cast_on declaration.",
            "line": None,
            "row": None
        })

    # Duplicate cast_on?
    cast_on_count = sum(1 for s in statements if s["type"] == "cast_on_valid")
    if cast_on_count > 1:
        for s in statements:
            if s["type"] == "cast_on_valid" and s["line"] != cast_on_line:
                result["errors"].append({
                    "type": "error",
                    "code": "DUPLICATE_CAST_ON",
                    "message": "Duplicate cast_on declaration.",
                    "line": s["line"],
                    "row": None
                })

    # Process rows: check duplicates and order
    valid_rows = []
    for stmt in statements:
        if stmt["type"] == "row_valid":
            row_num = stmt["row_num"]
            if row_num in seen_rows:
                result["errors"].append({
                    "type": "error",
                    "code": "DUPLICATE_ROW",
                    "message": f"Duplicate row number {row_num}.",
                    "line": stmt["line"],
                    "row": row_num
                })
            elif row_num <= last_valid_row_number:
                result["errors"].append({
                    "type": "error",
                    "code": "OUT_OF_ORDER_ROW",
                    "message": f"Row {row_num} is out of order.",
                    "line": stmt["line"],
                    "row": row_num
                })
            else:
                seen_rows.add(row_num)
                last_valid_row_number = row_num
                valid_rows.append(stmt)

    # Parse instructions for each valid row
    supported_stitches = {"yo", "k2tog", "ssk", "inc", "dec"}
    for stmt in valid_rows:
        instr_text = stmt["instructions_text"].strip()
        if not instr_text:
            result["errors"].append({
                "type": "error",
                "code": "MALFORMED_ROW",
                "message": "Empty instruction list.",
                "line": stmt["line"],
                "row": stmt["row_num"]
            })
            continue

        # Split by commas and check for empty parts
        parts = [p.strip() for p in instr_text.split(',')]
        if any(not p for p in parts):
            result["errors"].append({
                "type": "error",
                "code": "MALFORMED_ROW",
                "message": "Empty instruction in list.",
                "line": stmt["line"],
                "row": stmt["row_num"]
            })
            continue

        # Parse instructions, handle brackets
        try:
            instructions = parse_instructions(stmt["line"], parts, result["errors"])
        except:
            result["errors"].append({
                "type": "error",
                "code": "MALFORMED_ROW",
                "message": "Malformed instruction list.",
                "line": stmt["line"],
                "row": stmt["row_num"]
            })
            continue

        # Validate each instruction
        for instr in instructions:
            stitch = instr["stitch"]
            if stitch in ["k", "p"]:
                if not isinstance(instr["count"], int) or instr["count"] <= 0:
                    result["errors"].append({
                        "type": "error",
                        "code": "UNKNOWN_STITCH",
                        "message": f"Invalid stitch count for {stitch}.",
                        "line": stmt["line"],
                        "row": stmt["row_num"]
                    })
            elif stitch not in supported_stitches:
                result["errors"].append({
                    "type": "error",
                    "code": "UNKNOWN_STITCH",
                    "message": f"Unknown stitch {stitch}.",
                    "line": stmt["line"],
                    "row": stmt["row_num"]
                })

        stmt["parsed_instructions"] = instructions

    # Process repeat statements
    repeat_errors = []
    for stmt in statements:
        if stmt["type"] == "repeat":
            line_num = stmt["line"]
            text = stmt["text"]
            # Must match: repeat rows <start>-<end> x<count>
            match = re.match(r'repeat\s+rows\s+(\d+)-(\d+)\s+x(\S+)$', text)
            if not match:
                result["errors"].append({
                    "type": "error",
                    "code": "MALFORMED_REPEAT",
                    "message": "Malformed repeat statement.",
                    "line": line_num,
                    "row": None
                })
                continue

            start_str, end_str, count_str = match.groups()
            start = int(start_str)
            end = int(end_str)

            # Validate range
            range_error = False
            if start <= 0 or end <= 0:
                range_error = True
            if start > end:
                range_error = True
            if not all(row in row_line_map for row in range(start, end+1)):
                range_error = True

            if range_error:
                result["errors"].append({
                    "type": "error",
                    "code": "INVALID_REPEAT_RANGE",
                    "message": "Invalid repeat range.",
                    "line": line_num,
                    "row": None
                })

            # Validate count
            if not re.fullmatch(r'[1-9][0-9]*|0+[1-9][0-9]*', count_str):
                result["errors"].append({
                    "type": "error",
                    "code": "INVALID_REPEAT_COUNT",
                    "message": "Repeat count must be a positive integer.",
                    "line": line_num,
                    "row": None
                })
            else:
                count = int(count_str)

            # If both range and count are valid, we could expand later
            # But for now, just record if there were no errors

    # Sort errors by line, then by code order
    code_priority = [
        "MISSING_PATTERN",
        "MALFORMED_PATTERN",
        "DUPLICATE_PATTERN",
        "MISSING_CAST_ON",
        "MALFORMED_CAST_ON",
        "DUPLICATE_CAST_ON",
        "CAST_ON_OUT_OF_ORDER",
        "UNKNOWN_STATEMENT",
        "MALFORMED_ROW",
        "DUPLICATE_ROW",
        "OUT_OF_ORDER_ROW",
        "UNKNOWN_STITCH",
        "STITCH_UNDERFLOW",
        "STITCH_OVERFLOW",
        "MALFORMED_REPEAT",
        "INVALID_REPEAT_COUNT",
        "INVALID_REPEAT_RANGE",
        "MALFORMED_BIND_OFF",
        "DUPLICATE_BIND_OFF",
        "BIND_OFF_OUT_OF_ORDER"
    ]
    code_index = {code: i for i, code in enumerate(code_priority)}

    def error_key(err):
        line = err.get("line") or float('inf')
        code = err.get("code")
        code_ord = code_index.get(code, float('inf'))
        return (line, code_ord)

    result["errors"].sort(key=error_key)

    # Determine validity
    result["valid"] = len(result["errors"]) == 0
    if not result["valid"]:
        result["expanded_rows"] = []
        result["final_stitch_count"] = None
    else:
        # Perform expansion and simulation
        try:
            expanded_rows = []
            current_index = 1
            start_stitches = result["cast_on"]

            for stmt in statements:
                if stmt["type"] == "row_valid":
                    # Add the original row
                    end_stitches = simulate_row(stmt["parsed_instructions"], start_stitches)
                    if end_stitches is None:  # underflow
                        result["errors"].append({
                            "type": "error",
                            "code": "STITCH_UNDERFLOW",
                            "message": f"Stitch underflow in row {stmt['row_num']}.",
                            "line": stmt["line"],
                            "row": stmt["row_num"]
                        })
                        break
                    if end_stitches > 10000:
                        result["errors"].append({
                            "type": "error",
                            "code": "STITCH_OVERFLOW",
                            "message": f"Stitch overflow in row {stmt['row_num']}.",
                            "line": stmt["line"],
                            "row": stmt["row_num"]
                        })
                        break

                    expanded_rows.append({
                        "expanded_row_index": current_index,
                        "source_row": stmt["row_num"],
                        "instructions": [
                            {"stitch": instr["stitch"], "count": instr["count"]}
                            for instr in stmt["parsed_instructions"]
                        ],
                        "start_stitches": start_stitches,
                        "end_stitches": end_stitches
                    })
                    current_index += 1
                    start_stitches = end_stitches

                elif stmt["type"] == "repeat":
                    # Already validated
                    match = re.match(r'repeat\s+rows\s+(\d+)-(\d+)\s+x(\S+)$', stmt["text"])
                    if match:
                        start_str, end_str, count_str = match.groups()
                        start, end = int(start_str), int(end_str)
                        count = int(count_str)
                        # Add 'count' additional times
                        for _ in range(count):
                            for row_num in range(start, end+1):
                                if row_num in seen_rows:
                                    # Find the statement for this row
                                    row_stmt = next((s for s in statements if s["type"] == "row_valid" and s["row_num"] == row_num), None)
                                    if row_stmt and "parsed_instructions" in row_stmt:
                                        end_stitches = simulate_row(row_stmt["parsed_instructions"], start_stitches)
                                        if end_stitches is None:
                                            result["errors"].append({
                                                "type": "error",
                                                "code": "STITCH_UNDERFLOW",
                                                "message": f"Stitch underflow in row {row_num}.",
                                                "line": row_line_map[row_num],
                                                "row": row_num
                                            })
                                            break
                                        if end_stitches > 10000:
                                            result["errors"].append({
                                                "type": "error",
                                                "code": "STITCH_OVERFLOW",
                                                "message": f"Stitch overflow in row {row_num}.",
                                                "line": row_line_map[row_num],
                                                "row": row_num
                                            })
                                            break

                                        expanded_rows.append({
                                            "expanded_row_index": current_index,
                                            "source_row": row_num,
                                            "instructions": [
                                                {"stitch": instr["stitch"], "count": instr["count"]}
                                                for instr in row_stmt["parsed_instructions"]
                                            ],
                                            "start_stitches": start_stitches,
                                            "end_stitches": end_stitches
                                        })
                                        current_index += 1
                                        start_stitches = end_stitches
                            else:
                                # This should not happen due to prior validation
                                pass
                        else:
                            continue
                        break  # break outer loop if underflow or overflow

            if not result["errors"] or result["errors"][-1]["code"] not in ["STITCH_UNDERFLOW", "STITCH_OVERFLOW"]:
                result["expanded_rows"] = expanded_rows
                result["final_stitch_count"] = start_stitches
            else:
                result["expanded_rows"] = []
                result["final_stitch_count"] = None
                result["valid"] = False
        except:
            result["valid"] = False
            result["expanded_rows"] = []
            result["final_stitch_count"] = None

    # Final validity
    result["valid"] = len(result["errors"]) == 0
    if not result["valid"]:
        result["expanded_rows"] = []
        result["final_stitch_count"] = None

    # Output JSON
    print(json.dumps(result, indent=2))

    return 0 if result["valid"] else 1


def parse_instructions(line_num: int, parts: List[str], errors: List[Dict]) -> List[Dict]:
    instructions = []
    for part in parts:
        part = part.strip()
        # Check for bracketed repeat: [ ... ] xN
        if part.startswith('[') and '] x' in part:
            # Must have exactly one ']' and then ' x' with no space in xN
            bracket_end = part.find(']')
            if bracket_end == -1:
                errors.append({
                    "type": "error",
                    "code": "MALFORMED_ROW",
                    "message": "Unclosed bracket in instruction.",
                    "line": line_num,
                    "row": None
                })
                continue
            inner = part[1:bracket_end]
            after = part[bracket_end+1:].strip()
            if not after.startswith(' x') or len(after) <= 2:
                errors.append({
                    "type": "error",
                    "code": "MALFORMED_ROW",
                    "message": "Malformed bracketed repeat syntax.",
                    "line": line_num,
                    "row": None
                })
                continue
            count_part = after[2:]
            if not re.fullmatch(r'[1-9][0-9]*|0+[1-9][0-9]*', count_part):
                errors.append({
                    "type": "error",
                    "code": "MALFORMED_ROW",
                    "message": "Bracket repeat count must be positive integer.",
                    "line": line_num,
                    "row": None
                })
                continue
            repeat_count = int(count_part)
            # Parse inner instruction list
            inner_parts = [p.strip() for p in inner.split(',')]
            if any(not p for p in inner_parts):
                errors.append({
                    "type": "error",
                    "code": "MALFORMED_ROW",
                    "message": "Empty instruction in bracketed repeat.",
                    "line": line_num,
                    "row": None
                })
                continue
            inner_instructions = parse_instructions(line_num, inner_parts, errors)
            # Flatten
            for _ in range(repeat_count):
                instructions.extend(inner_instructions)
        elif part.startswith('[') or ']' in part:
            errors.append({
                "type": "error",
                "code": "MALFORMED_ROW",
                "message": "Malformed bracket syntax.",
                "line": line_num,
                "row": None
            })
            continue
        else:
            # Simple stitch
            if part == 'yo' or part == 'k2tog' or part == 'ssk' or part == 'inc' or part == 'dec':
                instructions.append({"stitch": part, "count": 1})
            elif part.startswith('k') and len(part) > 1:
                try:
                    count = int(part[1:])
                    if count <= 0:
                        errors.append({
                            "type": "error",
                            "code": "UNKNOWN_STITCH",
                            "message": f"Invalid stitch count in {part}.",
                            "line": line_num,
                            "row": None
                        })
                        continue
                    instructions.append({"stitch": "k", "count": count})
                except:
                    errors.append({
                        "type": "error",
                        "code": "UNKNOWN_STITCH",
                        "message": f"Unknown stitch {part}.",
                        "line": line_num,
                        "row": None
                    })
            elif part.startswith('p') and len(part) > 1:
                try:
                    count = int(part[1:])
                    if count <= 0:
                        errors.append({
                            "type": "error",
                            "code": "UNKNOWN_STITCH",
                            "message": f"Invalid stitch count in {part}.",
                            "line": line_num,
                            "row": None
                        })
                        continue
                    instructions.append({"stitch": "p", "count": count})
                except:
                    errors.append({
                        "type": "error",
                        "code": "UNKNOWN_STITCH",
                        "message": f"Unknown stitch {part}.",
                        "line": line_num,
                        "row": None
                    })
            else:
                errors.append({
                    "type": "error",
                    "code": "UNKNOWN_STITCH",
                    "message": f"Unknown stitch {part}.",
                    "line": line_num,
                    "row": None
                })
    return instructions


def simulate_row(instructions: List[Dict], start: int) -> Optional[int]:
    # Stitch semantics
    consumes = {
        "k": lambda n: n,
        "p": lambda n: n,
        "yo": lambda n: 0,
        "k2tog": lambda n: 2,
        "ssk": lambda n: 2,
        "inc": lambda n: 1,
        "dec": lambda n: 2
    }
    produces = {
        "k": lambda n: n,
        "p": lambda n: n,
        "yo": lambda n: 1,
        "k2tog": lambda n: 1,
        "ssk": lambda n: 1,
        "inc": lambda n: 2,
        "dec": lambda n: 1
    }

    current = start
    for instr in instructions:
        stitch = instr["stitch"]
        count = instr["count"]
        cons = consumes[stitch](count)
        if cons > current:
            return None  # underflow
        current = current - cons + produces[stitch](count)
        if current > 10000:
            return None  # overflow
    return current
