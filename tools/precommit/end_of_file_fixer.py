from __future__ import annotations

import sys


def _is_binary(data: bytes) -> bool:
    return b"\x00" in data


def _ensure_newline_at_eof(data: bytes) -> bytes:
    if not data:
        return data
    if data.endswith(b"\n"):
        return data
    return data + b"\n"


def main(argv: list[str]) -> int:
    changed = False
    for path in argv[1:]:
        try:
            raw = open(path, "rb").read()
        except OSError:
            continue

        if _is_binary(raw):
            continue

        fixed = _ensure_newline_at_eof(raw)
        if fixed != raw:
            with open(path, "wb") as f:
                f.write(fixed)
            changed = True

    return 1 if changed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
