#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw


OCR_SWIFT = Path(__file__).with_name("vision_ocr.swift")
IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")


@dataclass
class OcrBox:
    text: str
    x: int
    y: int
    w: int
    h: int

    @property
    def x2(self) -> int:
        return self.x + self.w

    @property
    def y2(self) -> int:
        return self.y + self.h

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2


@dataclass
class StepRule:
    target_labels: list[str]
    context_labels: list[str]
    region: str
    allow_infer_action_column: bool = False
    allow_plain_copy: bool = True


STEP_RULES: dict[str, StepRule] = {
    "frame_667_boxed.jpg": StepRule(["小程序"], [], "center"),
    "frame_703_boxed.jpg": StepRule(["创建测试号", "测试号"], [], "right"),
    "frame_816_boxed.jpg": StepRule(["AI小程序成长计划"], [], "left"),
    "frame_925_boxed.jpg": StepRule(["领取"], [], "right"),
    "frame_964_boxed.jpg": StepRule(["一键创建"], [], "right"),
    "frame_1019_boxed.jpg": StepRule(["修改"], ["小程序名称"], "right", allow_infer_action_column=True),
    "frame_1215_boxed.jpg": StepRule([], [], "center"),
    "frame_1308_boxed.jpg": StepRule(["下一步"], [], "center"),
    "frame_1388_boxed.jpg": StepRule(["详情"], ["服务类目"], "right", allow_infer_action_column=True),
    "frame_1421_boxed.jpg": StepRule([], [], "center"),
    "frame_1657_boxed.jpg": StepRule(["版本管理"], [], "left"),
    "frame_1686_boxed.jpg": StepRule(["成员管理"], [], "left"),
    "frame_1694_boxed.jpg": StepRule(["AppID", "开发管理"], [], "left"),
    "frame_1786_boxed.jpg": StepRule(["广告管理"], [], "center"),
}


def normalize_text(text: str) -> str:
    cleaned = re.sub(r"[\s`'\"“”‘’·•,，。:：;；()（）<>《》/\\|+_-]", "", text)
    return cleaned.lower()


def load_ocr(image_path: Path) -> list[OcrBox]:
    result = subprocess.run(
        ["swift", str(OCR_SWIFT), str(image_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    boxes: list[OcrBox] = []
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) != 5:
            continue
        text, x, y, w, h = parts
        boxes.append(OcrBox(text=text, x=int(x), y=int(y), w=int(w), h=int(h)))
    return boxes


def region_score(box: OcrBox, region: str, width: int) -> float:
    if region == "left":
        return 1.0 - (box.cx / width)
    if region == "right":
        return box.cx / width
    return 1.0 - abs(box.cx - width / 2) / max(width / 2, 1)


def box_match_score(box: OcrBox, label: str) -> float:
    target = normalize_text(label)
    text = normalize_text(box.text)
    if not target or not text:
        return 0.0
    if text == target:
        return 3.0
    if target in text:
        return 2.4
    if text in target:
        return 1.8
    return 0.0


def select_context_box(boxes: list[OcrBox], labels: list[str], image_width: int) -> OcrBox | None:
    best: tuple[float, OcrBox] | None = None
    for box in boxes:
        score = max((box_match_score(box, label) for label in labels), default=0.0)
        if score <= 0:
            continue
        score += region_score(box, "left", image_width) * 0.2
        if best is None or score > best[0]:
            best = (score, box)
    return best[1] if best else None


def infer_action_column_box(boxes: list[OcrBox], context_box: OcrBox, image_width: int) -> tuple[int, int, int, int] | None:
    action_boxes = [box for box in boxes if normalize_text(box.text) in {"修改", "下载", "详情"} and box.cx > image_width * 0.7]
    if not action_boxes:
        return None
    avg_x = int(sum(box.x for box in action_boxes) / len(action_boxes))
    avg_w = int(sum(box.w for box in action_boxes) / len(action_boxes))
    avg_h = int(sum(box.h for box in action_boxes) / len(action_boxes))
    y = int(context_box.cy - avg_h / 2 - 6)
    return (avg_x - 10, y, avg_w + 20, avg_h + 12)


def select_target_box(rule: StepRule, boxes: list[OcrBox], image_size: tuple[int, int]) -> tuple[int, int, int, int] | None:
    width, _ = image_size
    context_box = select_context_box(boxes, rule.context_labels, width) if rule.context_labels else None
    candidates: list[tuple[float, OcrBox]] = []
    for box in boxes:
        target_score = max((box_match_score(box, label) for label in rule.target_labels), default=0.0)
        if target_score <= 0:
            continue
        score = target_score + region_score(box, rule.region, width) * 0.6
        if context_box is not None:
            distance = abs(box.cy - context_box.cy)
            score += max(0.0, 1.6 - distance / 180.0)
        candidates.append((score, box))

    if candidates:
        _, chosen = max(candidates, key=lambda item: item[0])
        pad_x = 18 if chosen.w < 120 else 14
        pad_y = 12 if chosen.h < 40 else 10
        if rule.region == "left":
            pad_x = 24
        return (
            max(0, chosen.x - pad_x),
            max(0, chosen.y - pad_y),
            chosen.w + pad_x * 2,
            chosen.h + pad_y * 2,
        )

    if context_box is not None and rule.allow_infer_action_column:
        return infer_action_column_box(boxes, context_box, width)
    return None


def resolve_raw_source(image_path: Path) -> Path:
    if "_boxed" not in image_path.name:
        return image_path
    candidate = image_path.parent.parent / "frames" / image_path.name.replace("_boxed", "")
    return candidate if candidate.exists() else image_path


def draw_box(src: Path, dst: Path, bbox: tuple[int, int, int, int] | None) -> None:
    img = Image.open(src).convert("RGB")
    if bbox is not None:
        draw = ImageDraw.Draw(img)
        x, y, w, h = bbox
        for offset in range(4):
            draw.rectangle((x - offset, y - offset, x + w + offset, y + h + offset), outline=(220, 32, 32), width=2)
    dst.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst, quality=92)


def iter_image_refs(markdown_path: Path) -> list[Path]:
    refs: list[Path] = []
    text = markdown_path.read_text(encoding="utf-8")
    for match in IMAGE_RE.finditer(text):
        path = Path(match.group(1))
        if path.exists():
            refs.append(path)
    return refs


def main() -> int:
    parser = argparse.ArgumentParser(description="Refine teaching-doc screenshot boxes with OCR-driven control targeting.")
    parser.add_argument("--markdown-file", required=True)
    args = parser.parse_args()

    markdown_path = Path(args.markdown_file).resolve()
    image_paths = iter_image_refs(markdown_path)
    for image_path in image_paths:
        rule = STEP_RULES.get(image_path.name)
        if rule is None:
            continue
        raw_source = resolve_raw_source(image_path)
        if not raw_source.exists():
            continue
        if not rule.target_labels:
            shutil.copy2(raw_source, image_path)
            continue
        boxes = load_ocr(raw_source)
        bbox = select_target_box(rule, boxes, Image.open(raw_source).size)
        if bbox is None and rule.allow_plain_copy:
            shutil.copy2(raw_source, image_path)
            continue
        draw_box(raw_source, image_path, bbox)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
