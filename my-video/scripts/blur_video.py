#!/usr/bin/env python3
"""영상의 번호판·얼굴 등을 가린다.
사용법: python3 scripts/blur_video.py 입력.mp4 좌표.json 출력.mp4
좌표 JSON: tracks[].keys[] 에 시간(t, 초)과 box 또는 boxes([x0,y0,x1,y1], 1080x1920 기준)를 적는다.
 - interp=true: 키프레임 사이를 직선으로 이어 따라간다(번호판처럼 움직이는 것).
 - interp=false: 가장 가까운 키프레임의 박스를 hold초 동안 유지한다(얼굴 여러 개).
 - mode: pixelate(모자이크) / blur(흐림). pad: 박스 바깥 여백(px).
화면에 구워진 흰 자막이 가려지지 않게, 자막 높이대(y 940~1110)는 흰 글자와 외곽선을 복원한다.
"""
import json, subprocess, sys
import numpy as np
from PIL import Image, ImageFilter

W, H, FPS = 1080, 1920, 30
SUB_Y0, SUB_Y1 = 940, 1110  # 자막이 놓이는 세로 구간


def boxes_at(track, t):
    keys = track["keys"]
    pad = track.get("pad", 20)
    out = []
    if track.get("interp", True):
        if t < keys[0]["t"] - 1e-6 or t > keys[-1]["t"] + 1e-6:
            return out
        for a, b in zip(keys, keys[1:]):
            if a["t"] - 1e-6 <= t <= b["t"] + 1e-6:
                r = 0 if b["t"] == a["t"] else (t - a["t"]) / (b["t"] - a["t"])
                out.append([a["box"][i] + (b["box"][i] - a["box"][i]) * r for i in range(4)])
                break
    else:
        hold = track.get("hold", 0.06)
        best = min(keys, key=lambda k: abs(k["t"] - t))
        if abs(best["t"] - t) <= hold + 1e-6:
            out = [list(b) for b in best["boxes"]]
    return [[max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad)] for x0, y0, x1, y1 in out]


def apply(frame, box, mode):
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    if x1 - x0 < 4 or y1 - y0 < 4:
        return
    region = Image.fromarray(frame[y0:y1, x0:x1].copy())
    if mode == "pixelate":
        n = 8  # 박스를 가로 8칸 정도의 큰 모자이크로
        bs = max(8, (x1 - x0) // n)
        small = region.resize((max(1, (x1 - x0) // bs), max(1, (y1 - y0) // bs)), Image.BILINEAR)
        region = small.resize(region.size, Image.NEAREST)
    else:
        region = region.filter(ImageFilter.GaussianBlur(radius=max(14, (x1 - x0) // 6)))
    new = np.array(region)
    orig = frame[y0:y1, x0:x1]
    # 자막 복원: 검정 외곽선이 붙은 흰 글자만 되살린다(조명·흰 옷의 밝은 조각은 제외)
    ys0, ys1 = max(y0, SUB_Y0) - y0, min(y1, SUB_Y1) - y0
    if ys1 > ys0:
        o = orig[ys0:ys1]
        white = o.min(axis=2) >= 248
        black = o.max(axis=2) < 40
        if white.sum() > 300:
            near_black = np.asarray(Image.fromarray((black * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9))) > 0
            text = white & near_black
            if text.sum() > 300:
                grown = np.asarray(Image.fromarray((text * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(21))) > 0
                keep = text | (grown & black)
                new[ys0:ys1][keep] = o[keep]
    frame[y0:y1, x0:x1] = new


def main():
    src, cfg_path, dst = sys.argv[1:4]
    tracks = json.load(open(cfg_path))["tracks"]
    dec = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(
        ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
         "-i", src, "-map", "0:v", "-map", "1:a?", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
         "-c:a", "copy", "-shortest", dst], stdin=subprocess.PIPE)
    n = 0
    size = W * H * 3
    while True:
        buf = dec.stdout.read(size)
        if len(buf) < size:
            break
        frame = np.frombuffer(buf, dtype=np.uint8).reshape(H, W, 3).copy()
        t = n / FPS
        for tr in tracks:
            for b in boxes_at(tr, t):
                apply(frame, b, tr.get("mode", "blur"))
        enc.stdin.write(frame.tobytes())
        n += 1
    enc.stdin.close(); enc.wait(); dec.wait()
    print(f"완료: {dst} ({n} 프레임)")


if __name__ == "__main__":
    main()
