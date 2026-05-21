# CLI Calculator
# Snapshot: agent flexible-mode run (mock calculator spec), May 2026.
# Restore active entrypoint: cp backups/knit_calculator.py knit.py
# Original compiler CLI: git restore knit.py

import sys

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("usage: knit.py <command> num1 num2", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    try:
        num1 = float(sys.argv[2])
        num2 = float(sys.argv[3])
    except ValueError:
        print("invalid input", file=sys.stderr)
        sys.exit(1)

    if command == 'add':
        result = num1 + num2
    elif command == 'sub':
        result = num1 - num2
    elif command == 'mul':
        result = num1 * num2
    elif command == 'div':
        try:
            result = num1 / num2
        except ZeroDivisionError:
            print("division by zero", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"unknown command: {command}", file=sys.stderr)
        sys.exit(1)

    print(result)
