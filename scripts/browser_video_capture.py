#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import math
import subprocess
import time
from pathlib import Path


PAGE_MATCH = "st-live/playback?param=cqak6s"


def run_osascript(script: str) -> str:
    lines = [line for line in script.strip().splitlines() if line.strip()]
    cmd = ["osascript"]
    for line in lines:
        cmd.extend(["-e", line])
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def chrome_js(js_code: str, url_match: str = PAGE_MATCH) -> str:
    escaped = (
        js_code.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", " ")
    )
    script = f'''
tell application "Google Chrome"
  repeat with wi from 1 to count of windows
    set w to window wi
    repeat with ti from 1 to count of tabs of w
      set t to tab ti of w
      if (URL of t) contains "{url_match}" then
        return execute t javascript "{escaped}"
      end if
    end repeat
  end repeat
end tell
'''
    return run_osascript(script)


def set_time(target: float, url_match: str = PAGE_MATCH) -> dict:
    return json.loads(
        chrome_js(
            f"""
(() => {{
  const v = document.querySelector('video');
  if (!v) return JSON.stringify({{ok:false, reason:'no-video'}});
  v.pause();
  v.currentTime = {target:.3f};
  return JSON.stringify({{
    ok:true,
    currentTime:v.currentTime,
    duration:v.duration,
    readyState:v.readyState,
    paused:v.paused
  }});
}})()
""",
            url_match=url_match,
        )
    )


def get_state(url_match: str = PAGE_MATCH) -> dict:
    return json.loads(
        chrome_js(
            """
(() => {
  const v = document.querySelector('video');
  if (!v) return JSON.stringify({ok:false, reason:'no-video'});
  return JSON.stringify({
    ok:true,
    currentTime:v.currentTime,
    duration:v.duration,
    readyState:v.readyState,
    paused:v.paused,
    videoWidth:v.videoWidth,
    videoHeight:v.videoHeight
  });
})()
""",
            url_match=url_match,
        )
    )


def prepare_data_url(url_match: str = PAGE_MATCH) -> int:
    result = json.loads(
        chrome_js(
            """
(() => {
  try {
    const v = document.querySelector('video');
    if (!v) return JSON.stringify({ok:false, reason:'no-video'});
    const c = document.createElement('canvas');
    c.width = v.videoWidth;
    c.height = v.videoHeight;
    c.getContext('2d').drawImage(v, 0, 0, c.width, c.height);
    window.__codexFrameDataUrl = c.toDataURL('image/jpeg', 0.92);
    return JSON.stringify({ok:true, length:window.__codexFrameDataUrl.length});
  } catch (e) {
    return JSON.stringify({ok:false, error:String(e)});
  }
})()
""",
            url_match=url_match,
        )
    )
    if not result.get("ok"):
        raise RuntimeError(result)
    return int(result["length"])


def read_data_url_chunks(length: int, url_match: str = PAGE_MATCH, chunk_size: int = 120000) -> str:
    parts: list[str] = []
    total = int(math.ceil(length / float(chunk_size)))
    for index in range(total):
        start = index * chunk_size
        end = min(length, start + chunk_size)
        chunk = chrome_js(
            f"""
(() => {{
  const data = window.__codexFrameDataUrl || '';
  return data.slice({start}, {end});
}})()
""",
            url_match=url_match,
        )
        parts.append(chunk)
    return "".join(parts)


def wait_until_ready(target: float, tolerance: float, max_wait: float, url_match: str = PAGE_MATCH) -> dict:
    deadline = time.time() + max_wait
    last = {}
    while time.time() < deadline:
        last = get_state(url_match=url_match)
        if last.get("ok") and last.get("readyState", 0) >= 2 and abs(last.get("currentTime", 0.0) - target) <= tolerance:
            return last
        time.sleep(0.35)
    return last


def save_data_url(data_url: str, output: Path) -> None:
    _, encoded = data_url.split(",", 1)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(base64.b64decode(encoded))


def load_windows(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def capture_single(
    target: float,
    output: Path,
    tolerance: float,
    settle_wait: float,
    fast_seek_wait: float,
    url_match: str = PAGE_MATCH,
) -> None:
    info = set_time(target, url_match=url_match)
    if not info.get("ok"):
        raise RuntimeError(info)
    if fast_seek_wait > 0:
        time.sleep(fast_seek_wait)
    else:
        wait_until_ready(target=target, tolerance=tolerance, max_wait=8.0, url_match=url_match)
    time.sleep(settle_wait)
    length = prepare_data_url(url_match=url_match)
    save_data_url(read_data_url_chunks(length=length, url_match=url_match), output)


def capture_windows(
    windows: list[dict],
    fps: float,
    output_root: Path,
    tolerance: float,
    settle_wait: float,
    fast_seek_wait: float,
    url_match: str = PAGE_MATCH,
) -> dict:
    manifest: list[dict] = []
    interval = 1.0 / fps
    for window in windows:
        start = float(window["start"])
        end = float(window["end"])
        frame_dir = output_root / f"window_{int(window['id']):03d}_{int(start):04d}_{int(end):04d}"
        frame_dir.mkdir(parents=True, exist_ok=True)
        frame_paths = []
        t = start
        idx = 1
        while t <= end + 1e-6:
            out = frame_dir / f"frame_{idx:04d}.jpg"
            capture_single(
                target=t,
                output=out,
                tolerance=tolerance,
                settle_wait=settle_wait,
                fast_seek_wait=fast_seek_wait,
                url_match=url_match,
            )
            frame_paths.append(str(out))
            t += interval
            idx += 1
        manifest.append(
            {
                "id": window["id"],
                "start": start,
                "end": end,
                "frame_dir": str(frame_dir),
                "frames": frame_paths,
            }
        )
    return {"fps": fps, "windows": manifest}


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture video frames from the live Chrome playback tab.")
    parser.add_argument("--time", type=float, help="Capture a single frame at this second")
    parser.add_argument("--output", help="Single-frame output path")
    parser.add_argument("--windows", help="Action windows JSON path")
    parser.add_argument("--output-root", help="Directory for captured frame windows")
    parser.add_argument("--manifest", help="Output manifest path when using --windows")
    parser.add_argument("--fps", type=float, default=1.0)
    parser.add_argument("--tolerance", type=float, default=0.25)
    parser.add_argument("--settle-wait", type=float, default=0.25)
    parser.add_argument("--fast-seek-wait", type=float, default=0.0, help="If > 0, skip seek polling and sleep this many seconds before capture")
    parser.add_argument("--url-match", default=PAGE_MATCH, help="Substring used to find the target Chrome playback tab")
    args = parser.parse_args()

    if args.time is not None:
        if not args.output:
            raise SystemExit("--time requires --output")
        capture_single(
            target=float(args.time),
            output=Path(args.output),
            tolerance=float(args.tolerance),
            settle_wait=float(args.settle_wait),
            fast_seek_wait=float(args.fast_seek_wait),
            url_match=str(args.url_match),
        )
        print(args.output)
        return

    if args.windows:
        if not args.output_root or not args.manifest:
            raise SystemExit("--windows requires --output-root and --manifest")
        manifest = capture_windows(
            windows=load_windows(Path(args.windows)),
            fps=float(args.fps),
            output_root=Path(args.output_root),
            tolerance=float(args.tolerance),
            settle_wait=float(args.settle_wait),
            fast_seek_wait=float(args.fast_seek_wait),
            url_match=str(args.url_match),
        )
        Path(args.manifest).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(args.manifest)
        return

    raise SystemExit("Use either --time or --windows")


if __name__ == "__main__":
    main()
