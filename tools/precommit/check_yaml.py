from __future__ import annotations

import sys

import yaml


def main(argv: list[str]) -> int:
    ok = True
    for path in argv[1:]:
        try:
            text = open(path, encoding="utf-8").read()
        except OSError as e:
            print(f"{path}: {e}", file=sys.stderr)
            ok = False
            continue

        try:
            yaml.safe_load(text)
        except Exception as e:  # noqa: BLE001 - report YAML parse error
            print(f"{path}: invalid yaml: {e}", file=sys.stderr)
            ok = False

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
