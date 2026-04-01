#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


STEP_HEADING_RE = re.compile(r"^### (步骤\d+：.+)$", re.MULTILINE)
IMAGE_RE = re.compile(r"window_(\d+)_event_(\d+)_(?:before|after)\.jpg")
TIMESTAMP_LINE_RE = re.compile(r"^【视频回放时点\d{2}：\d{2}：\d{2}】$")


def format_timestamp(seconds: float) -> str:
    total = max(0, int(round(seconds)))
    hours = total // 3600
    minutes = (total % 3600) // 60
    secs = total % 60
    return f"【视频回放时点{hours:02d}：{minutes:02d}：{secs:02d}】"


def load_lookup(path: Path) -> dict[tuple[int, int], float]:
    data = json.loads(path.read_text(encoding="utf-8"))
    lookup: dict[tuple[int, int], float] = {}
    for window in data:
        for idx, event in enumerate(window.get("events", []), start=1):
            lookup[(int(window["id"]), idx)] = float(event["timestamp"])
    return lookup


def main() -> int:
    parser = argparse.ArgumentParser(description="Inject replay timestamps into each step heading of a teaching markdown doc.")
    parser.add_argument("--markdown-file", required=True)
    parser.add_argument("--dense-events", required=True)
    args = parser.parse_args()

    markdown_path = Path(args.markdown_file).resolve()
    dense_events_path = Path(args.dense_events).resolve()
    text = markdown_path.read_text(encoding="utf-8")
    lookup = load_lookup(dense_events_path)

    lines = text.splitlines()
    output: list[str] = []
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        output.append(line)
        heading_match = STEP_HEADING_RE.match(line)
        if not heading_match:
            idx += 1
            continue

        block_end = idx + 1
        while block_end < len(lines) and not lines[block_end].startswith("### "):
            block_end += 1
        block_lines = lines[idx + 1 : block_end]

        image_match = None
        for block_line in block_lines:
            image_match = IMAGE_RE.search(block_line)
            if image_match:
                break

        if image_match:
            key = (int(image_match.group(1)), int(image_match.group(2)))
            timestamp = lookup.get(key)
            if timestamp is not None:
                if block_lines and TIMESTAMP_LINE_RE.match(block_lines[0]):
                    block_lines = block_lines[1:]
                output.append(format_timestamp(timestamp))
                if block_lines and block_lines[0].strip():
                    output.append("")
                output.extend(block_lines)
                idx = block_end
                continue

        output.extend(block_lines)
        idx = block_end

    markdown_path.write_text("\n".join(output) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
