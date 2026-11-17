// 사용법
//   node scripts/render-pack.mjs pack            → 고정 스티커(PNG)와 엔딩카드(MP4)를 out/ 에 만든다
//   node scripts/render-pack.mjs post data/post.json → 게시물별 훅 자막·고정 제목·강조 링·가격 라벨(PNG)을 out/post/ 에 만든다
import { bundle } from "@remotion/bundler";
import { renderMedia, renderStill, selectComposition } from "@remotion/renderer";
import { readFileSync, mkdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const browserExecutable = process.env.BROWSER_EXECUTABLE ?? "/opt/pw-browsers/chromium";
const chromiumOptions = { gl: "swangle" };

const catalog = JSON.parse(readFileSync(path.join(root, "src/catalog.json"), "utf8"));
const mode = process.argv[2] ?? "pack";

const serveUrl = await bundle({ entryPoint: path.join(root, "src/index.ts") });

const still = async (id, inputProps, output) => {
  const composition = await selectComposition({ serveUrl, id, inputProps, browserExecutable, chromiumOptions });
  await renderStill({ composition, serveUrl, inputProps, output, imageFormat: "png", browserExecutable, chromiumOptions });
  console.log("PNG ", output);
};

if (mode === "pack") {
  const stickers = path.join(root, "out/stickers");
  const endcards = path.join(root, "out/endcards");
  mkdirSync(stickers, { recursive: true });
  mkdirSync(endcards, { recursive: true });

  for (const s of catalog.stamps) {
    await still(s.id, { label: s.label, main: s.main, tone: s.tone }, path.join(stickers, `${s.file}.png`));
  }
  for (const c of catalog.chips) {
    await still(c.id, { text: c.text }, path.join(stickers, `칩-${c.text.replace(/ /g, "-")}.png`));
  }
  for (const e of catalog.endcards) {
    const inputProps = { label: e.label, main: e.main, tone: e.tone };
    const composition = await selectComposition({ serveUrl, id: e.id, inputProps, browserExecutable, chromiumOptions });
    const output = path.join(endcards, `${e.file}.mp4`);
    await renderMedia({ composition, serveUrl, inputProps, codec: "h264", outputLocation: output, browserExecutable, chromiumOptions });
    console.log("MP4 ", output);
  }
} else if (mode === "post") {
  const dataPath = path.resolve(process.argv[3] ?? "data/post.json");
  const data = JSON.parse(readFileSync(dataPath, "utf8"));
  const out = path.join(root, "out/post");
  mkdirSync(out, { recursive: true });
  for (const h of data.hooks ?? []) {
    await still("hook-caption", { text: h.text }, path.join(out, `훅-${h.file}.png`));
  }
  for (const t of data.titles ?? []) {
    await still("fixed-title", { line1: t.line1, line2: t.line2 }, path.join(out, `제목-${t.file}.png`));
  }
  for (const r of data.rings ?? []) {
    await still("ring", {}, path.join(out, `링-${r.file}.png`));
  }
  for (const p of data.prices ?? []) {
    await still("price-tag", { name: p.name, price: p.price }, path.join(out, `가격-${p.file}.png`));
  }
} else {
  console.error("mode must be 'pack' or 'post'");
  process.exit(1);
}
console.log("done");
