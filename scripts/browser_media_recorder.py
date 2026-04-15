#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import subprocess
import time
from pathlib import Path


def run_osascript(script: str) -> str:
    lines = [line for line in script.strip().splitlines() if line.strip()]
    cmd = ["osascript"]
    for line in lines:
        cmd.extend(["-e", line])
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def chrome_js(js_code: str, url_match: str | None = None, active_front_tab: bool = False) -> str:
    escaped = (
        js_code.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", " ")
    )
    if active_front_tab:
        script = f'''
tell application "Google Chrome"
  return execute active tab of front window javascript "{escaped}"
end tell
'''
        return run_osascript(script)
    if not url_match:
        raise ValueError("url_match is required unless active_front_tab is enabled")
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


def start_audio_recording(
    start: float,
    duration: float,
    playback_rate: float,
    url_match: str | None = None,
    active_front_tab: bool = False,
) -> dict:
    return json.loads(
        chrome_js(
            f"""
(() => {{
  const v = document.querySelector('video');
  if (!v) return JSON.stringify({{ok:false, reason:'no-video'}});
  if (!v.captureStream) return JSON.stringify({{ok:false, reason:'no-capture-stream'}});
  window.__codexMediaMeta = {{done:false, chunks:0, mime:'audio/webm;codecs=opus'}};
  window.__codexMediaChunks = [];
  v.pause();
  v.currentTime = {start:.3f};
  v.playbackRate = {playback_rate:.3f};
  v.muted = false;
  v.volume = 1;
  const stream = v.captureStream();
  const audioTracks = stream.getAudioTracks();
  if (!audioTracks.length) return JSON.stringify({{ok:false, reason:'no-audio-track'}});
  const audioStream = new MediaStream(audioTracks);
  const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
    ? 'audio/webm;codecs=opus'
    : 'audio/webm';
  const recorder = new MediaRecorder(audioStream, {{ mimeType }});
  const blobs = [];
  recorder.ondataavailable = (event) => {{
    if (event.data && event.data.size) blobs.push(event.data);
  }};
  recorder.onstop = async () => {{
    const blob = new Blob(blobs, {{ type: mimeType }});
    const buffer = new Uint8Array(await blob.arrayBuffer());
    const chunkSize = 96 * 1024;
    const chunks = [];
    for (let i = 0; i < buffer.length; i += chunkSize) {{
      let binary = '';
      const slice = buffer.subarray(i, Math.min(buffer.length, i + chunkSize));
      for (let j = 0; j < slice.length; j += 1) binary += String.fromCharCode(slice[j]);
      chunks.push(btoa(binary));
    }}
    window.__codexMediaChunks = chunks;
    window.__codexMediaMeta = {{
      done: true,
      chunks: chunks.length,
      mime: mimeType,
      bytes: buffer.length,
      startTime: {start:.3f},
      endTime: v.currentTime,
      playbackRate: {playback_rate:.3f},
      requestedDuration: {duration:.3f},
    }};
  }};
  recorder.start(1000);
  v.play();
  window.setTimeout(() => {{
    try {{ recorder.stop(); }} catch (e) {{}}
    v.pause();
  }}, Math.ceil(({duration:.3f} / {playback_rate:.3f}) * 1000));
  return JSON.stringify({{
    ok:true,
    startTime:v.currentTime,
    playbackRate:v.playbackRate,
    wallMs: Math.ceil(({duration:.3f} / {playback_rate:.3f}) * 1000)
  }});
}})()
""",
            url_match=url_match,
            active_front_tab=active_front_tab,
        )
    )


def wait_until_done(timeout: float, url_match: str | None = None, active_front_tab: bool = False) -> dict:
    deadline = time.time() + timeout
    last = {}
    while time.time() < deadline:
        raw = chrome_js(
            """
(() => JSON.stringify(window.__codexMediaMeta || {done:false, reason:'no-meta'}))()
""",
            url_match=url_match,
            active_front_tab=active_front_tab,
        )
        last = json.loads(raw)
        if last.get("done"):
            return last
        time.sleep(1.0)
    return last


def fetch_chunks(count: int, url_match: str | None = None, active_front_tab: bool = False) -> bytes:
    parts: list[bytes] = []
    for index in range(count):
        chunk = chrome_js(
            f"""
(() => (window.__codexMediaChunks && window.__codexMediaChunks[{index}]) || '')()
""",
            url_match=url_match,
            active_front_tab=active_front_tab,
        )
        parts.append(base64.b64decode(chunk))
    return b"".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Record audio from the current Chrome playback tab using captureStream().")
    parser.add_argument("--url-match", help="Substring used to find the target Chrome playback tab")
    parser.add_argument("--active-front-tab", action="store_true", help="Use the active tab of the front Chrome window")
    parser.add_argument("--start", type=float, default=0.0, help="Video start time in seconds")
    parser.add_argument("--duration", type=float, required=True, help="Video duration to capture in seconds")
    parser.add_argument("--playback-rate", type=float, default=2.0, help="Playback speed during capture")
    parser.add_argument("--timeout", type=float, default=120.0, help="Overall wait timeout in seconds")
    parser.add_argument("--output", required=True, help="Output audio file path")
    args = parser.parse_args()
    if not args.active_front_tab and not args.url_match:
        raise SystemExit("Use either --url-match or --active-front-tab")

    started = start_audio_recording(
        start=float(args.start),
        duration=float(args.duration),
        playback_rate=float(args.playback_rate),
        url_match=args.url_match,
        active_front_tab=bool(args.active_front_tab),
    )
    if not started.get("ok"):
        raise SystemExit(json.dumps(started, ensure_ascii=False))

    meta = wait_until_done(
        timeout=float(args.timeout),
        url_match=args.url_match,
        active_front_tab=bool(args.active_front_tab),
    )
    if not meta.get("done"):
        raise SystemExit(json.dumps(meta, ensure_ascii=False))

    payload = fetch_chunks(
        count=int(meta["chunks"]),
        url_match=args.url_match,
        active_front_tab=bool(args.active_front_tab),
    )
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(payload)
    print(json.dumps({"output": str(output), "meta": meta}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
