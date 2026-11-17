// SRT → 남편의 리뷰생활 자막 스타일(주아체·흰 글씨·굵은 검정 외곽선)로 영상에 입힌다.
// 사용법: node scripts/burn-subs.mjs <입력.mp4> <자막.srt> <출력.mp4> [--size 92] [--y 0.53] [--outline 9] [--pitch 100]
// 주의: 입력 영상에 이미 자막이 구워져 있으면 겹친다. 자막 없는 원본 클립에 쓸 것.
import { execFileSync } from "node:child_process";
import { readFileSync, writeFileSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const fontsDir = path.resolve(here, "../assets/fonts");

const args = process.argv.slice(2);
const flag = (name, def) => {
  const i = args.indexOf(name);
  return i >= 0 ? Number(args[i + 1]) : def;
};
const pos = args.filter((a, i) => !a.startsWith("--") && !args[i - 1]?.startsWith("--"));
const [input, srtPath, output] = pos;
if (!input || !srtPath || !output) {
  console.error("사용법: node scripts/burn-subs.mjs <입력.mp4> <자막.srt> <출력.mp4> [--size 92] [--y 0.53] [--outline 9] [--pitch 100]");
  process.exit(1);
}

// 참고 영상에서 잰 값: 1080x1920 기준, 한 줄 자막의 세로 중심 ≈ 53%, 글자 높이 ≈ 73px, 외곽선 ≈ 7px
const SIZE = flag("--size", 92);
const OUTLINE = flag("--outline", 9);
const PITCH = flag("--pitch", 100); // 두 줄일 때 줄 간격(px)
const CY = Math.round(1920 * flag("--y", 0.53));

const ts = (s) => {
  const m = s.match(/(\d+):(\d+):(\d+)[,.](\d+)/);
  const t = +m[1] * 3600 + +m[2] * 60 + +m[3] + +m[4].padEnd(3, "0") / 1000;
  const cs = Math.round(t * 100);
  const h = Math.floor(cs / 360000), mi = Math.floor((cs % 360000) / 6000);
  const se = Math.floor((cs % 6000) / 100), c = cs % 100;
  return `${h}:${String(mi).padStart(2, "0")}:${String(se).padStart(2, "0")}.${String(c).padStart(2, "0")}`;
};

const blocks = readFileSync(srtPath, "utf8").replace(/\r/g, "").trim().split(/\n\s*\n/);
const events = blocks
  .flatMap((b) => {
    const lines = b.split("\n");
    const ti = lines.findIndex((l) => l.includes("-->"));
    if (ti < 0) return [];
    const [a, z] = lines[ti].split("-->").map((x) => x.trim());
    const rows = lines.slice(ti + 1).filter((l) => l.trim());
    // 줄마다 따로 배치해서 줄 간격을 PITCH로 고정한다 (여러 줄이면 중심이 CY)
    return rows.map((text, k) => {
      const y = Math.round(CY + (k - (rows.length - 1) / 2) * PITCH);
      return `Dialogue: 0,${ts(a)},${ts(z)},Sub,,0,0,0,,{\\an5\\pos(540,${y})}${text}`;
    });
  });

const ass = `[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Jua,${SIZE},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,${OUTLINE},0,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
${events.join("\n")}
`;

const tmp = mkdtempSync(path.join(tmpdir(), "subs-"));
const assPath = path.join(tmp, "subs.ass");
writeFileSync(assPath, ass);

const esc = (p) => p.replace(/\\/g, "/").replace(/:/g, "\\:");
execFileSync(
  "ffmpeg",
  [
    "-y", "-loglevel", "error", "-i", input,
    "-vf", `ass=${esc(assPath)}:fontsdir=${esc(fontsDir)}`,
    "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
    "-c:a", "copy", output,
  ],
  { stdio: "inherit" },
);
console.log(`완료: ${output} (자막 줄 ${events.length}개)`);
