#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import subprocess
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


@dataclass
class DiffCandidate:
    from_frame: str
    to_frame: str
    timestamp: float
    mean_diff: float
    changed_ratio: float
    bbox: list[int] | None
    bbox_area_ratio: float
    event_type: str
    keep_before: bool
    keep_after: bool
    confidence: float

    def to_dict(self) -> dict:
        return {
            "from_frame": self.from_frame,
            "to_frame": self.to_frame,
            "timestamp": round(self.timestamp, 2),
            "mean_diff": round(self.mean_diff, 4),
            "changed_ratio": round(self.changed_ratio, 4),
            "bbox": self.bbox,
            "bbox_area_ratio": round(self.bbox_area_ratio, 4),
            "event_type": self.event_type,
            "keep_before": self.keep_before,
            "keep_after": self.keep_after,
            "confidence": round(self.confidence, 3),
        }


def load_windows(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_ffmpeg_extract(ffmpeg_bin: str, source: str, start: float, end: float, fps: float, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg_bin,
        "-protocol_whitelist",
        "file,crypto,data,https,tcp,tls",
        "-y",
        "-ss",
        f"{start:.2f}",
        "-to",
        f"{end:.2f}",
        "-i",
        source,
        "-vf",
        f"fps={fps}",
        str(out_dir / "frame_%04d.jpg"),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _roi_bounds(size: tuple[int, int], top: int, right: int, bottom: int, left: int) -> tuple[int, int, int, int]:
    width, height = size
    return (
        max(0, left),
        max(0, top),
        max(left + 1, width - right),
        max(top + 1, height - bottom),
    )


def _grow_mask(mask: np.ndarray, iterations: int = 1) -> np.ndarray:
    grown = mask.astype(bool)
    for _ in range(iterations):
        padded = np.pad(grown, 1, mode="constant", constant_values=False)
        expanded = np.zeros_like(grown)
        for dy in range(3):
            for dx in range(3):
                expanded |= padded[dy : dy + grown.shape[0], dx : dx + grown.shape[1]]
        grown = expanded
    return grown


def _component_boxes(mask: np.ndarray, min_pixels: int = 16) -> list[tuple[int, int, int, int, int]]:
    height, width = mask.shape
    visited = np.zeros_like(mask, dtype=bool)
    boxes: list[tuple[int, int, int, int, int]] = []
    for y in range(height):
        for x in range(width):
            if not mask[y, x] or visited[y, x]:
                continue
            stack = [(x, y)]
            visited[y, x] = True
            min_x = max_x = x
            min_y = max_y = y
            pixels = 0
            while stack:
                cx, cy = stack.pop()
                pixels += 1
                min_x = min(min_x, cx)
                max_x = max(max_x, cx)
                min_y = min(min_y, cy)
                max_y = max(max_y, cy)
                for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                    if 0 <= nx < width and 0 <= ny < height and mask[ny, nx] and not visited[ny, nx]:
                        visited[ny, nx] = True
                        stack.append((nx, ny))
            if pixels >= min_pixels:
                boxes.append((min_x, min_y, max_x, max_y, pixels))
    return boxes


def _frame_metrics(img: Image.Image, bounds: tuple[int, int, int, int]) -> tuple[float, float, float]:
    crop = img.crop(bounds).convert("L").resize((480, 270))
    arr = np.asarray(crop, dtype=np.float32) / 255.0
    gx = float(np.abs(np.diff(arr, axis=1)).mean() * 255.0)
    gy = float(np.abs(np.diff(arr, axis=0)).mean() * 255.0)
    bright = float(arr.mean())
    std = float(arr.std() * 255.0)
    return bright, std, gx + gy


def _is_invalid_loading_frame(img: Image.Image, bounds: tuple[int, int, int, int]) -> bool:
    bright, std, edge_score = _frame_metrics(img, bounds)
    return bright >= 0.933 and std <= 54.0 and edge_score <= 2.25


def _tight_band(scores: np.ndarray, min_len: int, max_len: int, threshold_ratio: float) -> tuple[int, int]:
    if scores.size == 0 or float(scores.max()) <= 0.0:
        return 0, max(0, scores.size - 1)
    peak = int(scores.argmax())
    threshold = float(scores[peak]) * threshold_ratio
    lo = hi = peak
    while lo > 0 and scores[lo - 1] >= threshold:
        lo -= 1
    while hi + 1 < scores.size and scores[hi + 1] >= threshold:
        hi += 1
    if (hi - lo + 1) < min_len:
        half = max(0, min_len // 2)
        lo = max(0, peak - half)
        hi = min(scores.size - 1, lo + min_len - 1)
        lo = max(0, hi - min_len + 1)
    if (hi - lo + 1) > max_len:
        half = max(0, max_len // 2)
        lo = max(0, peak - half)
        hi = min(scores.size - 1, lo + max_len - 1)
        lo = max(0, hi - max_len + 1)
    return lo, hi


def _shrink_large_component(
    per_pixel: np.ndarray,
    mask: np.ndarray,
    box: tuple[int, int, int, int],
) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    crop_mask = mask[y0 : y1 + 1, x0 : x1 + 1]
    crop_diff = per_pixel[y0 : y1 + 1, x0 : x1 + 1]
    if crop_mask.size == 0:
        return box
    diff_scale = crop_diff / max(1.0, float(crop_diff.max()))
    activity = crop_mask.astype(np.float32) + diff_scale * 0.35
    rows = activity.sum(axis=1)
    cols = activity.sum(axis=0)
    height = crop_mask.shape[0]
    width = crop_mask.shape[1]
    tall_box = height >= max(28, width * 1.5)
    wide_box = width >= max(60, height * 1.8)
    large_box = (width * height) >= 9000
    if not (tall_box or wide_box or large_box):
        return box
    row_min = 10 if tall_box else 12
    row_max = max(row_min, min(height, int(height * (0.22 if tall_box else 0.4))))
    row_threshold = 0.48 if tall_box else 0.38
    inner_y0, inner_y1 = _tight_band(rows, min_len=row_min, max_len=row_max, threshold_ratio=row_threshold)
    rows_activity = activity[inner_y0 : inner_y1 + 1, :]
    cols = rows_activity.sum(axis=0)
    col_min = 14 if wide_box else 18
    col_max = max(col_min, min(width, int(width * (0.5 if wide_box else 0.78))))
    col_threshold = 0.34 if wide_box else 0.30
    inner_x0, inner_x1 = _tight_band(cols, min_len=col_min, max_len=col_max, threshold_ratio=col_threshold)
    pad_x = 3 if width <= 140 else 5
    pad_y = 3 if height <= 90 else 5
    return (
        max(0, x0 + inner_x0 - pad_x),
        max(0, y0 + inner_y0 - pad_y),
        min(mask.shape[1] - 1, x0 + inner_x1 + pad_x),
        min(mask.shape[0] - 1, y0 + inner_y1 + pad_y),
    )


def _best_component_box(
    mask: np.ndarray,
    per_pixel: np.ndarray,
) -> tuple[int, int, int, int] | None:
    grown = _grow_mask(mask, iterations=1)
    components = _component_boxes(grown)
    if not components:
        return None
    best_box: tuple[int, int, int, int] | None = None
    best_score = -1.0
    total_area = float(mask.shape[0] * mask.shape[1])
    for x0, y0, x1, y1, pixels in components:
        width = x1 - x0 + 1
        height = y1 - y0 + 1
        area = width * height
        if width < 4 or height < 4:
            continue
        fill_ratio = pixels / float(max(1, area))
        area_ratio = area / total_area
        aspect_penalty = 0.0
        if height > width * 4 or width > height * 6:
            aspect_penalty = 0.18
        size_penalty = 0.0
        if area_ratio > 0.12:
            size_penalty = 0.35
        elif area_ratio > 0.08:
            size_penalty = 0.18
        score = pixels * (0.55 + fill_ratio) * (1.15 - size_penalty - aspect_penalty)
        if 0.001 <= area_ratio <= 0.05:
            score *= 1.12
        if score > best_score:
            best_score = score
            best_box = (x0, y0, x1, y1)
    if best_box is None:
        return None
    return _shrink_large_component(per_pixel, grown, best_box)


def diff_bbox(
    img_a: Path,
    img_b: Path,
    roi_top: int,
    roi_right: int,
    roi_bottom: int,
    roi_left: int,
    mask_bottom_left_width: int,
    mask_bottom_left_height: int,
    mask_bottom_right_width: int,
    mask_bottom_right_height: int,
    sample_size: tuple[int, int] = (480, 270),
    pixel_threshold: float = 22.0,
) -> tuple[float, float, list[int] | None, float, bool]:
    orig_a = Image.open(img_a).convert("RGB")
    orig_b = Image.open(img_b).convert("RGB")
    rx0, ry0, rx1, ry1 = _roi_bounds(orig_a.size, roi_top, roi_right, roi_bottom, roi_left)
    crop_a = orig_a.crop((rx0, ry0, rx1, ry1)).resize(sample_size)
    crop_b = orig_b.crop((rx0, ry0, rx1, ry1)).resize(sample_size)
    arr_a = np.asarray(crop_a, dtype=np.int16)
    arr_b = np.asarray(crop_b, dtype=np.int16)
    per_pixel = np.abs(arr_a - arr_b).mean(axis=2)
    if mask_bottom_left_width and mask_bottom_left_height:
        sx = sample_size[0] / max(1, (rx1 - rx0))
        sy = sample_size[1] / max(1, (ry1 - ry0))
        w = min(sample_size[0], int(mask_bottom_left_width * sx))
        h = min(sample_size[1], int(mask_bottom_left_height * sy))
        per_pixel[sample_size[1] - h :, :w] = 0
    if mask_bottom_right_width and mask_bottom_right_height:
        sx = sample_size[0] / max(1, (rx1 - rx0))
        sy = sample_size[1] / max(1, (ry1 - ry0))
        w = min(sample_size[0], int(mask_bottom_right_width * sx))
        h = min(sample_size[1], int(mask_bottom_right_height * sy))
        per_pixel[sample_size[1] - h :, sample_size[0] - w :] = 0
    mask = per_pixel > pixel_threshold
    changed_ratio = float(mask.mean())
    mean_diff = float(per_pixel.mean())
    invalid_after = _is_invalid_loading_frame(orig_b, (rx0, ry0, rx1, ry1))
    if not mask.any():
        return mean_diff, changed_ratio, None, 0.0, invalid_after

    best_box = _best_component_box(mask, per_pixel)
    if best_box is None:
        ys, xs = np.where(mask)
        x0, x1 = int(xs.min()), int(xs.max())
        y0, y1 = int(ys.min()), int(ys.max())
    else:
        x0, y0, x1, y1 = best_box
    if (x1 - x0) < 4 or (y1 - y0) < 4:
        return mean_diff, changed_ratio, None, 0.0, invalid_after

    roi_w = rx1 - rx0
    roi_h = ry1 - ry0
    scale_x = roi_w / sample_size[0]
    scale_y = roi_h / sample_size[1]
    box = [
        int(rx0 + x0 * scale_x),
        int(ry0 + y0 * scale_y),
        int(max(8, (x1 - x0 + 1) * scale_x)),
        int(max(8, (y1 - y0 + 1) * scale_y)),
    ]
    area_ratio = (box[2] * box[3]) / float(orig_a.size[0] * orig_a.size[1])
    return mean_diff, changed_ratio, box, float(area_ratio), invalid_after


def classify_event(mean_diff: float, changed_ratio: float, bbox: list[int] | None, bbox_area_ratio: float) -> tuple[str, bool, bool, float]:
    if changed_ratio >= 0.18 or bbox_area_ratio >= 0.12 or (changed_ratio >= 0.08 and bbox_area_ratio >= 0.1):
        return "page_change", False, True, min(0.98, 0.55 + changed_ratio * 1.5)
    if bbox and changed_ratio >= 0.008:
        confidence = min(0.95, 0.45 + changed_ratio * 8 + min(0.18, bbox_area_ratio))
        return "local_change", True, True, confidence
    if mean_diff >= 7.0 and changed_ratio >= 0.004:
        return "small_change", False, True, min(0.78, 0.4 + changed_ratio * 10)
    return "ignore", False, False, 0.0


def detect_candidates(
    frame_dir: Path,
    fps: float,
    window_start: float,
    roi_top: int,
    roi_right: int,
    roi_bottom: int,
    roi_left: int,
    mask_bottom_left_width: int,
    mask_bottom_left_height: int,
    mask_bottom_right_width: int,
    mask_bottom_right_height: int,
    pixel_threshold: float,
    min_gap_seconds: float,
) -> list[DiffCandidate]:
    frames = sorted(frame_dir.glob("frame_*.jpg"))
    selected: list[DiffCandidate] = []
    last_kept_time = -999.0
    for idx in range(1, len(frames)):
        mean_diff, changed_ratio, bbox, bbox_area_ratio, invalid_after = diff_bbox(
            frames[idx - 1],
            frames[idx],
            roi_top=roi_top,
            roi_right=roi_right,
            roi_bottom=roi_bottom,
            roi_left=roi_left,
            mask_bottom_left_width=mask_bottom_left_width,
            mask_bottom_left_height=mask_bottom_left_height,
            mask_bottom_right_width=mask_bottom_right_width,
            mask_bottom_right_height=mask_bottom_right_height,
            pixel_threshold=pixel_threshold,
        )
        timestamp = window_start + idx / fps
        event_type, keep_before, keep_after, confidence = classify_event(
            mean_diff=mean_diff,
            changed_ratio=changed_ratio,
            bbox=bbox,
            bbox_area_ratio=bbox_area_ratio,
        )
        if invalid_after:
            continue
        if event_type == "ignore":
            continue
        candidate = DiffCandidate(
            from_frame=frames[idx - 1].name,
            to_frame=frames[idx].name,
            timestamp=timestamp,
            mean_diff=mean_diff,
            changed_ratio=changed_ratio,
            bbox=bbox,
            bbox_area_ratio=bbox_area_ratio,
            event_type=event_type,
            keep_before=keep_before,
            keep_after=keep_after,
            confidence=confidence,
        )
        if timestamp - last_kept_time < min_gap_seconds and selected:
            if candidate.confidence > selected[-1].confidence:
                selected[-1] = candidate
                last_kept_time = timestamp
            continue
        selected.append(candidate)
        last_kept_time = timestamp
    return selected


def draw_box(src: Path, dst: Path, bbox: list[int] | None) -> None:
    img = Image.open(src).convert("RGB")
    if bbox:
        draw = ImageDraw.Draw(img)
        x, y, w, h = bbox
        for offset in range(5):
            draw.rectangle((x - offset, y - offset, x + w + offset, y + h + offset), outline=(220, 32, 32), width=2)
    dst.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst, quality=92)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract dense screenshot events from action windows.")
    parser.add_argument("--windows", required=True, help="Path to action_windows.json")
    parser.add_argument("--source", help="Fresh playable m3u8 URL")
    parser.add_argument("--output", required=True, help="Path to output event JSON")
    parser.add_argument("--frames-root", required=True, help="Directory for dense raw frames")
    parser.add_argument("--annotated-root", required=True, help="Directory for boxed screenshots")
    parser.add_argument("--ffmpeg-bin", default="/Users/shihui/Library/Python/3.14/lib/python/site-packages/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1")
    parser.add_argument("--fps", type=float, default=4.0)
    parser.add_argument("--roi-top", type=int, default=110)
    parser.add_argument("--roi-right", type=int, default=94)
    parser.add_argument("--roi-bottom", type=int, default=100)
    parser.add_argument("--roi-left", type=int, default=24)
    parser.add_argument("--mask-bottom-left-width", type=int, default=240)
    parser.add_argument("--mask-bottom-left-height", type=int, default=180)
    parser.add_argument("--mask-bottom-right-width", type=int, default=220)
    parser.add_argument("--mask-bottom-right-height", type=int, default=160)
    parser.add_argument("--pixel-threshold", type=float, default=22.0)
    parser.add_argument("--min-gap-seconds", type=float, default=0.7)
    parser.add_argument("--reuse-existing-frames", action="store_true", help="Use frames already present in frame_dir and skip extraction")
    args = parser.parse_args()

    windows = load_windows(Path(args.windows))
    frames_root = Path(args.frames_root)
    annotated_root = Path(args.annotated_root)
    results: list[dict] = []
    for window in windows:
        frame_dir = frames_root / f"window_{int(window['id']):03d}_{math.floor(window['start']):04d}_{math.floor(window['end']):04d}"
        has_frames = frame_dir.exists() and any(frame_dir.glob("frame_*.jpg"))
        if not (args.reuse_existing_frames and has_frames):
            if not args.source:
                raise SystemExit("--source is required unless --reuse-existing-frames is used with populated frame directories")
            run_ffmpeg_extract(
                ffmpeg_bin=args.ffmpeg_bin,
                source=args.source,
                start=float(window["start"]),
                end=float(window["end"]),
                fps=float(args.fps),
                out_dir=frame_dir,
            )
        candidates = detect_candidates(
            frame_dir=frame_dir,
            fps=float(args.fps),
            window_start=float(window["start"]),
            roi_top=args.roi_top,
            roi_right=args.roi_right,
            roi_bottom=args.roi_bottom,
            roi_left=args.roi_left,
            mask_bottom_left_width=args.mask_bottom_left_width,
            mask_bottom_left_height=args.mask_bottom_left_height,
            mask_bottom_right_width=args.mask_bottom_right_width,
            mask_bottom_right_height=args.mask_bottom_right_height,
            pixel_threshold=float(args.pixel_threshold),
            min_gap_seconds=float(args.min_gap_seconds),
        )
        window_out = {
            "id": window["id"],
            "start": window["start"],
            "end": window["end"],
            "reasons": window.get("reasons", []),
            "texts": window.get("texts", []),
            "frame_dir": str(frame_dir),
            "events": [],
        }
        for event_idx, event in enumerate(candidates, start=1):
            prefix = f"window_{int(window['id']):03d}_event_{event_idx:03d}"
            before_out = annotated_root / f"{prefix}_before.jpg"
            after_out = annotated_root / f"{prefix}_after.jpg"
            if event.keep_before:
                draw_box(frame_dir / event.from_frame, before_out, event.bbox)
            if event.keep_after:
                draw_box(frame_dir / event.to_frame, after_out, event.bbox if event.event_type != "page_change" else None)
            item = event.to_dict()
            if event.keep_before:
                item["before_image"] = str(before_out)
            if event.keep_after:
                item["after_image"] = str(after_out)
            window_out["events"].append(item)
        results.append(window_out)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"windows={len(results)}")
    print(output)


if __name__ == "__main__":
    main()
