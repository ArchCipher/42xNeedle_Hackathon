import json
import sys
def emit_json(data):
    print(json.dumps(data), file=sys.stdout)

def compile_file(input_file):
    try:
        with open(input_file, 'r') as f:
            pattern = f.readline().strip()
            cast_on_line = f.readline().strip()

            if not cast_on_line.isdigit():
                raise ValueError(f"Invalid cast_on value: {cast_on_line}")
            cast_on = int(cast_on_line)

            result = {
                "pattern_name": pattern,
                "cast_on": cast_on,
                "bind_off": False,
                "errors": [],
                "expanded_rows": [],
                "final_stitch_count": cast_on,
                "valid": True
            }
        emit_json(result)
        return 0
    except Exception as e:
        print(str(e), file=sys.stderr)
        return 1