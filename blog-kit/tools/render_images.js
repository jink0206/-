#!/usr/bin/env node
// HTML(images-src) -> PNG. 사용: node tools/render_images.js <fontsource-noto-sans-kr 폴더> <출력 폴더> [html...]
// 폰트 폴더: npm i @fontsource/noto-sans-kr 후 node_modules/@fontsource/noto-sans-kr
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
(async () => {
  const [fontDir, outDir, ...only] = process.argv.slice(2);
  if (!fontDir || !outDir) { console.error('사용법: render_images.js <폰트폴더> <출력폴더> [html...]'); process.exit(1); }
  const src = path.resolve(__dirname, '..', 'images-src');
  const files = (only.length ? only : fs.readdirSync(src).filter(f => /^\d.*\.html$/.test(f)));
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1080 }, deviceScaleFactor: 2 });
  for (const f of files) {
    await p.goto('file://' + path.join(src, f));
    for (const w of [400, 700, 900]) await p.addStyleTag({ url: 'file://' + path.resolve(fontDir, `${w}.css`) });
    await p.evaluate(() => document.fonts.ready);
    const out = path.join(outDir, f.replace('.html', '.png'));
    const h = await p.evaluate(() => Math.ceil(document.body.getBoundingClientRect().height));
    await p.setViewportSize({ width: 1080, height: h });
    await p.screenshot({ path: out, clip: { x: 0, y: 0, width: 1080, height: h } });
    await p.setViewportSize({ width: 1080, height: 1080 });
    console.log(out);
  }
  await b.close();
})();
