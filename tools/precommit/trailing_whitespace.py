from __future__ import annotations

import sys


def _is_binary(data: bytes) -> bool:
    return b"\x00" in data


def _fix_trailing_whitespace(data: bytes) -> bytes:
    # Operate on bytes to avoid encoding round-trips.
    out: list[bytes] = []
    for line in data.splitlines(keepends=True):
        if line.endswith(b"\r\n"):
            body = line[:-2].rstrip(b" \t")
            out.append(body + b"\r\n")
        elif line.endswith(b"\n"):
            body = line[:-1].rstrip(b" \t")
            out.append(body + b"\n")
        else:
            out.append(line.rstrip(b" \t"))
    return b"".join(out)


def main(argv: list[str]) -> int:
    changed = False
    for path in argv[1:]:
        try:
            raw = open(path, "rb").read()
        except OSError:
            continue

        if _is_binary(raw):
            continue

        fixed = _fix_trailing_whitespace(raw)
        if fixed != raw:
            with open(path, "wb") as f:
                f.write(fixed)
            changed = True

    return 1 if changed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
