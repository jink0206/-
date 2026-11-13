"""JIN:ON 위로 영상 자동 제작기
대본 -> AI 나레이션 -> 노을 배경 -> 한글/영어 자막 -> mp4
사용법: python3 make_video.py [번호 ...]   (번호 없으면 전부)
"""
import asyncio, os, re, subprocess, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import edge_tts

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
FONT = os.path.join(HERE, "assets", "NanumMyeongjo.ttf")
VOICE = "ko-KR-SunHiNeural"
FPS = 30
W, H = 1080, 1920
SW, SH = 270, 480          # 배경은 작게 그려서 키움 (부드러운 느낌 + 속도)
OUTRO = ("여기, 진온이에요.", "Here, it's JIN:ON.")   # 발음용 / 자막용 분리

SCRIPTS = [
    ("01_today", [
        ("오늘 하루도 잘 버텼어요.", "You made it through today."),
        ("그거면 충분해요.", "That is enough."),
        ("잘하지 못해도 괜찮아요.", "It's okay if it wasn't perfect."),
        ("당신은 이미 충분히 애쓰고 있으니까요.", "You are already trying so hard."),
    ], "dusk"),
    ("02_slow", [
        ("느린 건 틀린 게 아니에요.", "Slow doesn't mean wrong."),
        ("꽃도 피는 시기가 다 달라요.", "Flowers bloom in their own time."),
        ("지금은 뿌리를 내리는 중일 거예요.", "Right now, you're growing roots."),
    ], "rose"),
    ("03_rest", [
        ("지치면 잠깐 쉬어가도 돼요.", "If you're tired, it's okay to rest."),
        ("멈추는 것도 앞으로 가는 방법이에요.", "Stopping is also a way forward."),
        ("오늘은 아무것도 안 해도 괜찮아요.", "Today, doing nothing is okay."),
    ], "night"),
    ("04_unsaid", [
        ("괜찮은 척하느라 힘들었죠.", "Pretending to be fine was exhausting."),
        ("다 말하지 않아도 알고 있어요.", "You don't have to say it all. I know."),
        ("오늘은 그냥, 내려놓고 쉬어요.", "Tonight, just let it go and rest."),
    ], "dusk"),
    ("05_notalone", [
        ("아무도 몰라주는 것 같은 날에도", "Even on days it feels no one sees you,"),
        ("당신은 잘하고 있어요.", "you are doing well."),
        ("누군가는 분명 당신 편이에요.", "Someone is surely on your side."),
        ("지금 이 목소리도요.", "Even this voice."),
    ], "rose"),
]

PALETTES = {  # 하늘 위 -> 지평선 색, 해 색
    "dusk":  ([(28, 30, 62), (92, 62, 104), (214, 120, 98), (250, 178, 112)], (255, 214, 150)),
    "rose":  ([(44, 36, 74), (130, 84, 120), (232, 140, 130), (255, 198, 160)], (255, 226, 190)),
    "night": ([(10, 18, 40), (26, 40, 78), (70, 80, 128), (140, 124, 156)], (230, 224, 255)),
}


def dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", path], capture_output=True, text=True)
    return float(r.stdout.strip())


async def tts(text, path):
    com = edge_tts.Communicate(text, VOICE, rate="-12%", pitch="-3Hz",
                               proxy=os.environ.get("HTTPS_PROXY"))
    await com.save(path)


def build_audio(name, lines, work):
    """줄별 음성을 만들어 사이에 여백을 두고 이어붙임. 각 줄의 (시작,끝) 반환"""
    items = [(ko, en, ko) for ko, en in lines] + [(OUTRO[0], OUTRO[1], OUTRO[0])]
    t = 1.2
    timings, parts = [], []
    for i, (ko, en, say) in enumerate(items):
        p = os.path.join(work, f"{name}_{i}.mp3")
        asyncio.run(tts(say, p))
        d = dur(p)
        timings.append((ko, en, t, t + d))
        parts.append((p, t))
        t += d + (1.3 if i < len(items) - 2 else 1.8)
    total = t + 1.2
    cmd = ["ffmpeg", "-v", "error", "-y"]
    for p, _ in parts:
        cmd += ["-i", p]
    fil = []
    for i, (_, st) in enumerate(parts):
        fil.append(f"[{i}:a]adelay={int(st*1000)}|{int(st*1000)}[a{i}]")
    mix = "".join(f"[a{i}]" for i in range(len(parts)))
    fil.append(f"{mix}amix=inputs={len(parts)}:normalize=0,apad=whole_dur={total}[v]")
    # 나레이션에 살짝 울림(리버브 느낌)
    fil.append("[v]aecho=0.8:0.6:60|120:0.18|0.10,volume=1.6[nar]")
    # 잔잔한 앰비언트 패드 (코드로 합성)
    chord = [110.0, 164.81, 220.0, 277.18]
    for j, f in enumerate(chord):
        cmd += ["-f", "lavfi", "-t", f"{total}", "-i", f"sine=frequency={f}:sample_rate=44100"]
    n = len(parts)
    pads = "".join(f"[{n+j}:a]" for j in range(len(chord)))
    fil.append(f"{pads}amix=inputs={len(chord)}:normalize=0,lowpass=f=700,"
               f"tremolo=f=0.15:d=0.5,volume=0.07,afade=t=in:d=3,afade=t=out:st={total-3}:d=3[pad]")
    fil.append("[nar][pad]amix=inputs=2:normalize=0,alimiter=limit=0.95[out]")
    wav = os.path.join(work, f"{name}.wav")
    cmd += ["-filter_complex", ";".join(fil), "-map", "[out]", "-t", f"{total}", wav]
    subprocess.run(cmd, check=True)
    return wav, timings, total


def detect_segments(path, n):
    """한 번에 읽은 음성에서 가장 긴 쉼 (n-1)곳을 찾아 n개 구간으로 나눔"""
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", path, "-af", "silencedetect=noise=-30dB:d=0.18",
                        "-f", "null", "-"], capture_output=True, text=True)
    st = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", r.stderr)]
    en = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", r.stderr)]
    total = dur(path)
    gaps = [(e - s, s, e) for s, e in zip(st, en) if s > 0.3 and e < total - 0.1]
    cuts = sorted(sorted(gaps, reverse=True)[: n - 1], key=lambda g: g[1])
    bounds = [0.0] + [x for g in cuts for x in (g[1], g[2])] + [total]
    return [(bounds[2 * i], bounds[2 * i + 1]) for i in range(len(cuts) + 1)]


def build_audio_ext(name, lines, mp3, work):
    """미리 만든 자연스러운 음성(한 파일)을 사용: 자막 타이밍 자동 계산"""
    items = list(lines) + [OUTRO]
    segs = detect_segments(mp3, len(items))
    lead = 1.2
    timings = [(ko, en, lead + a, lead + b) for (ko, en), (a, b) in zip(items, segs)]
    total = lead + dur(mp3) + 2.4
    chord = [110.0, 164.81, 220.0, 277.18]
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", mp3]
    for f in chord:
        cmd += ["-f", "lavfi", "-t", f"{total}", "-i", f"sine=frequency={f}:sample_rate=44100"]
    pads = "".join(f"[{1+j}:a]" for j in range(len(chord)))
    fil = [f"[0:a]adelay={int(lead*1000)}|{int(lead*1000)},apad=whole_dur={total},volume=1.3[nar]",
           f"{pads}amix=inputs={len(chord)}:normalize=0,lowpass=f=700,tremolo=f=0.15:d=0.5,volume=0.05,"
           f"afade=t=in:d=3,afade=t=out:st={total-3}:d=3[pad]",
           "[nar][pad]amix=inputs=2:normalize=0,alimiter=limit=0.95[out]"]
    wav = os.path.join(work, f"{name}.wav")
    cmd += ["-filter_complex", ";".join(fil), "-map", "[out]", "-t", f"{total}", wav]
    subprocess.run(cmd, check=True)
    return wav, timings, total


def make_bg(theme):
    cols, sun = PALETTES[theme]
    ys = np.linspace(0, 1, SH)[:, None]
    xs = np.linspace(0, 1, SW)[None, :]
    stops = np.array(cols, dtype=np.float32)
    pos = np.linspace(0.0, 0.78, len(cols))

    def sky(t):
        warp = 0.015 * np.sin(2 * math.pi * (xs * 1.3 + t * 0.03)) + 0.01 * np.sin(2 * math.pi * (xs * 3 - t * 0.02))
        y = np.clip(ys + warp, 0, 1)
        img = np.zeros((SH, SW, 3), np.float32)
        for c in range(3):
            img[..., c] = np.interp(y, pos, stops[:, c])
        # 해: 천천히 떠오르는 부드러운 빛
        sy = 0.60 - 0.012 * t
        d = np.sqrt(((xs - 0.5) * 0.56) ** 2 + (ys - sy) ** 2)
        glow = np.exp(-(d / 0.11) ** 2)[..., None] * 0.75 + np.exp(-(d / 0.35) ** 2)[..., None] * 0.22
        img += glow * np.array(sun, np.float32) * 0.42
        # 아래쪽은 잔잔한 물결 (수평선 아래 어둡게 + 반짝임)
        horizon = 0.78
        sea = ys > horizon
        shimmer = 0.5 + 0.5 * np.sin(2 * math.pi * (ys * 90 - t * 0.4) + xs * 6)
        refl = np.exp(-((xs - 0.5) / (0.05 + (ys - horizon) * 0.5)) ** 2) * shimmer
        dark = np.clip(1 - (ys - horizon) * 1.4, 0.35, 1)
        img = np.where(sea[..., None], img * dark[..., None] * 0.6 + refl[..., None] * np.array(sun, np.float32) * 0.35, img)
        return np.clip(img, 0, 255)

    vig = 1 - 0.55 * (((xs - 0.5) * 1.4) ** 2 + ((ys - 0.5) * 1.0) ** 2)
    band = 1 - 0.55 * np.exp(-((ys - 0.69) / 0.16) ** 2)      # 자막 뒤를 은은하게 어둡게
    return sky, (vig * band)[..., None].astype(np.float32)


def sub_image(ko, en):
    f_ko = ImageFont.truetype(FONT, 58)
    f_en = ImageFont.truetype(FONT, 38)
    img = Image.new("RGBA", (W, 260), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for txt, f, y, a in ((ko, f_ko, 40, 255), (en, f_en, 138, 215)):
        w = d.textlength(txt, font=f)
        x = (W - w) / 2
        d.text((x + 2, y + 3), txt, font=f, fill=(0, 0, 0, 150))   # 그림자
        d.text((x, y), txt, font=f, fill=(255, 255, 255, a))
    sh = img.filter(ImageFilter.GaussianBlur(0.4))
    return sh


def render(name, lines, theme):
    work = os.path.join(OUT, "work"); os.makedirs(work, exist_ok=True)
    ext = os.path.join(HERE, "assets", "tts", name + ".mp3")
    if os.path.exists(ext):
        wav, timings, total = build_audio_ext(name, lines, ext, work)
    else:
        wav, timings, total = build_audio(name, lines, work)
    print(name, [(round(a, 1), round(b, 1)) for _, _, a, b in timings])
    sky, vig = make_bg(theme)
    subs = [(sub_image(ko, en), a, b) for ko, en, a, b in timings]
    rng = np.random.default_rng(7)
    mp4 = os.path.join(OUT, f"{name}.mp4")
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
                           "-c:v", "libx264", "-preset", "medium", "-crf", "24", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", mp4],
                          stdin=subprocess.PIPE)
    wm_font = ImageFont.truetype(FONT, 30)
    n = int(total * FPS)
    for i in range(n):
        t = i / FPS
        a = sky(t) * vig
        a += rng.normal(0, 1.6, a.shape).astype(np.float32)          # 필름 그레인
        # 처음/끝 페이드
        fade = min(1, t / 1.0, (total - t) / 1.2)
        frame = Image.fromarray(np.clip(a * fade, 0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
        d = ImageDraw.Draw(frame)
        wtxt = "JIN:ON"
        d.text(((W - d.textlength(wtxt, font=wm_font)) / 2, 150), wtxt, font=wm_font, fill=(255, 255, 255))
        for im, s, e in subs:
            alpha = min(1, (t - s + 0.35) / 0.7, (e + 0.9 - t) / 0.7)
            if alpha > 0:
                lay = im.copy()
                lay.putalpha(lay.getchannel("A").point(lambda v, al=alpha: int(v * al)))
                frame.paste(lay, (0, 1180), lay)
        ff.stdin.write(frame.tobytes())
    ff.stdin.close(); ff.wait()
    print("완성:", mp4, f"({total:.1f}초)")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    pick = set(sys.argv[1:])
    for name, lines, theme in SCRIPTS:
        if not pick or name[:2] in pick:
            render(name, lines, theme)
