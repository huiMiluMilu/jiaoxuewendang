#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image


DEFAULT_KEYWORDS = [
    "点击",
    "点一下",
    "去点",
    "点开",
    "点这里",
    "选择",
    "输入",
    "填写",
    "打开",
    "下载",
    "保存",
    "下一步",
    "确定",
    "上传",
    "注册",
    "认证",
    "名字",
    "名称",
    "类目",
    "这里",
    "这个地方",
    "右边这里",
    "下面这里",
    "添加",
    "详情",
    "修改",
    "创建",
]


@dataclass
class Segment:
    start: float
    end: float
    text: str


@dataclass
class Window:
    start: float
    end: float
    reasons: list[str]
    texts: list[str]

    def to_dict(self) -> dict:
        return {
            "start": round(self.start, 2),
            "end": round(self.end, 2),
            "reasons": self.reasons,
            "texts": self.texts,
        }


def load_segments(path: Path) -> list[Segment]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "segments" in data:
        data = data["segments"]
    return [
        Segment(
            start=float(item["start"]),
            end=float(item["end"]),
            text=str(item["text"]).strip(),
        )
        for item in data
        if str(item.get("text", "")).strip()
    ]


def build_windows(
    segments: Iterable[Segment],
    keywords: list[str],
    padding_before: float,
    padding_after: float,
    merge_gap: float,
) -> list[Window]:
    windows: list[Window] = []
    for seg in segments:
        matched = [kw for kw in keywords if kw in seg.text]
        if not matched:
            continue
        current = Window(
            start=max(0.0, seg.start - padding_before),
            end=seg.end + padding_after,
            reasons=matched,
            texts=[seg.text],
        )
        if windows and current.start <= windows[-1].end + merge_gap:
            prev = windows[-1]
            prev.end = max(prev.end, current.end)
            prev.reasons = sorted(set(prev.reasons + current.reasons))
            prev.texts.extend(current.texts)
        else:
            windows.append(current)
    return windows


def run_ffmpeg_extract(
    ffmpeg_bin: str,
    source: str,
    window: Window,
    fps: float,
    out_dir: Path,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg_bin,
        "-protocol_whitelist",
        "file,crypto,data,https,tcp,tls",
        "-y",
        "-ss",
        f"{window.start:.2f}",
        "-to",
        f"{window.end:.2f}",
        "-i",
        source,
        "-vf",
        f"fps={fps}",
        str(out_dir / "frame_%04d.jpg"),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def changed_ratio(img_a: Path, img_b: Path, sample_size: tuple[int, int] = (480, 270)) -> tuple[float, float]:
    arr_a = np.asarray(Image.open(img_a).convert("RGB").resize(sample_size), dtype=np.int16)
    arr_b = np.asarray(Image.open(img_b).convert("RGB").resize(sample_size), dtype=np.int16)
    diff = np.abs(arr_a - arr_b)
    per_pixel = diff.mean(axis=2)
    changed = per_pixel > 18
    return float(per_pixel.mean()), float(changed.mean())


def analyze_window_frames(frame_dir: Path, window: Window, fps: float) -> dict:
    frames = sorted(frame_dir.glob("frame_*.jpg"))
    pairs: list[dict] = []
    if not frames:
        return {"frames": [], "pairs": []}
    for idx in range(1, len(frames)):
        score, ratio = changed_ratio(frames[idx - 1], frames[idx])
        timestamp = window.start + idx / fps
        pairs.append(
            {
                "from": frames[idx - 1].name,
                "to": frames[idx].name,
                "timestamp": round(timestamp, 2),
                "mean_diff": round(score, 4),
                "changed_ratio": round(ratio, 4),
            }
        )
    candidate_frames = [frames[0].name]
    candidate_frames.extend(
        pair["to"]
        for pair in pairs
        if pair["changed_ratio"] >= 0.01 or pair["mean_diff"] >= 6.0
    )
    if frames[-1].name not in candidate_frames:
        candidate_frames.append(frames[-1].name)
    return {
        "frames": candidate_frames,
        "pairs": pairs,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build action windows and screenshot candidates from transcript.")
    parser.add_argument("--transcript", required=True, help="Path to transcript_segments_fast.json or transcript_segments.json")
    parser.add_argument("--output", required=True, help="Path to output JSON")
    parser.add_argument("--source", help="Fresh playable m3u8 URL or local playlist path")
    parser.add_argument("--frames-root", help="Directory to write extracted frames")
    parser.add_argument("--ffmpeg-bin", default="/Users/shihui/Library/Python/3.14/lib/python/site-packages/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1")
    parser.add_argument("--fps", type=float, default=4.0)
    parser.add_argument("--padding-before", type=float, default=2.0)
    parser.add_argument("--padding-after", type=float, default=2.5)
    parser.add_argument("--merge-gap", type=float, default=2.0)
    parser.add_argument("--keywords", nargs="*", default=DEFAULT_KEYWORDS)
    parser.add_argument("--extract", action="store_true", help="Actually extract frames for each action window")
    args = parser.parse_args()

    transcript = Path(args.transcript)
    output = Path(args.output)
    frames_root = Path(args.frames_root) if args.frames_root else None

    segments = load_segments(transcript)
    windows = build_windows(
        segments=segments,
        keywords=args.keywords,
        padding_before=args.padding_before,
        padding_after=args.padding_after,
        merge_gap=args.merge_gap,
    )

    results: list[dict] = []
    for idx, window in enumerate(windows, start=1):
        item = {
            "id": idx,
            **window.to_dict(),
        }
        if args.extract:
            if not args.source or not frames_root:
                raise SystemExit("--extract requires --source and --frames-root")
            frame_dir = frames_root / f"window_{idx:03d}_{math.floor(window.start):04d}_{math.floor(window.end):04d}"
            run_ffmpeg_extract(
                ffmpeg_bin=args.ffmpeg_bin,
                source=args.source,
                window=window,
                fps=args.fps,
                out_dir=frame_dir,
            )
            analysis = analyze_window_frames(frame_dir, window=window, fps=args.fps)
            item["frame_dir"] = str(frame_dir)
            item["candidate_frames"] = analysis["frames"]
            item["frame_pairs"] = analysis["pairs"]
        results.append(item)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"windows={len(results)}")
    print(output)


if __name__ == "__main__":
    main()
