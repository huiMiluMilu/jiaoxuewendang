#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


IMAGE_PATTERN = re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<path>[^)]+)\)")


@dataclass
class PublishChunk:
    kind: str
    content: str | None = None
    image_path: Path | None = None
    caption: str | None = None


def build_create_command(args: argparse.Namespace, markdown: str) -> list[str]:
    cmd = [
        "lark-cli",
        "docs",
        "+create",
        "--as",
        args.identity,
        "--title",
        args.title,
        "--markdown",
        markdown,
    ]
    if args.folder_token:
        cmd.extend(["--folder-token", args.folder_token])
    if args.wiki_space:
        cmd.extend(["--wiki-space", args.wiki_space])
    if args.wiki_node:
        cmd.extend(["--wiki-node", args.wiki_node])
    return cmd


def build_update_command(identity: str, doc_id: str, markdown: str) -> list[str]:
    return [
        "lark-cli",
        "docs",
        "+update",
        "--as",
        identity,
        "--doc",
        doc_id,
        "--mode",
        "append",
        "--markdown",
        markdown,
    ]


def build_media_command(identity: str, doc_id: str, rel_file: str, caption: str | None) -> list[str]:
    cmd = [
        "lark-cli",
        "docs",
        "+media-insert",
        "--as",
        identity,
        "--doc",
        doc_id,
        "--file",
        rel_file,
    ]
    if caption:
        cmd.extend(["--caption", caption])
    return cmd


def run_json_command(cmd: list[str], cwd: Path | None = None) -> dict:
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd) if cwd else None)
    if result.returncode != 0:
        sys.stderr.write(result.stderr or result.stdout)
        raise SystemExit(result.returncode)
    return json.loads(result.stdout)


def resolve_local_image(image_ref: str, markdown_dir: Path) -> Path | None:
    candidate = Path(image_ref).expanduser()
    if candidate.is_absolute():
        return candidate if candidate.exists() else None
    joined = (markdown_dir / candidate).resolve()
    return joined if joined.exists() else None


def split_markdown(markdown: str, markdown_dir: Path) -> tuple[list[PublishChunk], list[str]]:
    chunks: list[PublishChunk] = []
    local_images: list[str] = []
    cursor = 0
    for match in IMAGE_PATTERN.finditer(markdown):
        image_path = resolve_local_image(match.group("path").strip(), markdown_dir)
        if image_path is None:
            continue
        before = markdown[cursor : match.start()]
        if before:
            chunks.append(PublishChunk(kind="text", content=before))
        caption = match.group("alt").strip() or image_path.stem
        chunks.append(PublishChunk(kind="image", image_path=image_path, caption=caption))
        local_images.append(str(image_path))
        cursor = match.end()
    tail = markdown[cursor:]
    if tail:
        chunks.append(PublishChunk(kind="text", content=tail))
    if not chunks:
        chunks.append(PublishChunk(kind="text", content=markdown))
    return chunks, local_images


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish a generated teaching doc markdown file to Lark Docs.")
    parser.add_argument("--markdown-file", required=True, help="Local markdown file to publish")
    parser.add_argument("--title", help="Lark doc title; defaults to the markdown filename")
    parser.add_argument("--identity", default="user", choices=["user", "bot"], help="Lark identity type")
    parser.add_argument("--folder-token", help="Optional parent folder token")
    parser.add_argument("--wiki-space", help="Optional wiki space ID")
    parser.add_argument("--wiki-node", help="Optional wiki node token")
    parser.add_argument("--output", help="Optional path to save the raw JSON result")
    parser.add_argument("--image-manifest-output", help="Optional JSON path to save local image paths detected in markdown")
    args = parser.parse_args()

    markdown_path = Path(args.markdown_file).expanduser().resolve()
    if not markdown_path.exists():
        raise SystemExit(f"markdown file not found: {markdown_path}")

    markdown = markdown_path.read_text(encoding="utf-8")
    if not markdown.strip():
        raise SystemExit(f"markdown file is empty: {markdown_path}")
    chunks, local_images = split_markdown(markdown, markdown_path.parent)

    title = args.title or markdown_path.stem
    args.title = title
    first_text_index = next(
        (idx for idx, chunk in enumerate(chunks) if chunk.kind == "text" and chunk.content and chunk.content.strip()),
        None,
    )
    first_text = chunks[first_text_index].content if first_text_index is not None else "\n"
    payload = run_json_command(build_create_command(args, first_text))
    doc_id = payload["data"]["doc_id"]

    image_results: list[dict] = []
    for idx, chunk in enumerate(chunks):
        if chunk.kind == "text":
            text = chunk.content or ""
            if not text.strip():
                continue
            if idx == first_text_index:
                continue
            run_json_command(build_update_command(args.identity, doc_id, text))
            continue
        if chunk.kind == "image" and chunk.image_path:
            rel_file = f"./{chunk.image_path.name}"
            image_payload = run_json_command(
                build_media_command(args.identity, doc_id, rel_file, chunk.caption),
                cwd=chunk.image_path.parent,
            )
            image_results.append(
                {
                    "path": str(chunk.image_path),
                    "caption": chunk.caption,
                    "result": image_payload.get("data", {}),
                }
            )

    payload["image_results"] = image_results
    if args.output:
        output_path = Path(args.output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.image_manifest_output:
        manifest_path = Path(args.image_manifest_output).expanduser().resolve()
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps({"images": local_images}, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
