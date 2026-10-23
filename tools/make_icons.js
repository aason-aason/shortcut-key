// tools/icon.html をアイコンの PNG（512・192・180）に書き出す。使い方: node tools/make_icons.js <出力フォルダ>
const path = require('path');
const { chromium } = require(require('child_process').execSync('npm root -g').toString().trim() + '/playwright');
(async () => {
  const out = process.argv[2] || 'docs/icons';
  require('fs').mkdirSync(out, { recursive: true });
  const b = await chromium.launch();
  for (const [size, name] of [[512, 'icon-512.png'], [192, 'icon-192.png'], [180, 'apple-touch-icon.png']]) {
    const p = await b.newPage({ viewport: { width: 512, height: 512 }, deviceScaleFactor: size / 512 });
    await p.goto('file://' + path.resolve(__dirname, 'icon.html'));
    await p.evaluate(() => document.fonts.ready);
    await p.waitForTimeout(500);
    await p.screenshot({ path: path.join(out, name) });
    await p.close();
  }
  await b.close();
})();
