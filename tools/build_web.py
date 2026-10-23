"""Webアプリ版（GitHub Pages 用）を docs/ に組み立てる。

使い方: python3 tools/build_web.py
  keykoma.html（Claude のアーティファクトとして公開している本体）を、ふつうの Web ページの形に包み直し、
  ホーム画面に追加するための manifest と、電波がなくても動かすための sw.js（サービスワーカー）を添える。
  アイコンがなければ tools/make_icons.js で作る（Node と Playwright が必要）。
"""
import hashlib, json, os, re, shutil, subprocess

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(ROOT, 'docs')
DATA = ['data/scenes.js', 'data/logic-pro.js']
ICONS = ['icons/icon-192.png', 'icons/icon-512.png', 'icons/apple-touch-icon.png']
NAME, SHORT = 'DAWショートカット辞典', 'DAW辞典'
DESC = 'Logic Pro のショートカットを、やりたいことの言葉で探して、押し方をキーボード図で確かめる辞典'
BG = '#E3E5E8'

HEAD = f'''<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{NAME}</title>
<meta name="description" content="{DESC}">
<meta name="theme-color" content="{BG}">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" type="image/png" href="icons/icon-192.png">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="{SHORT}">
<style>html,body{{margin:0}}</style>
</head>
<body>
'''
# サービスワーカーは https（GitHub Pages）と手元の確認用 localhost でだけ登録する
TAIL = '''<script>
if('serviceWorker' in navigator&&(location.protocol==='https:'||location.hostname==='localhost'))navigator.serviceWorker.register('sw.js');
</script>
</body>
</html>
'''

SW = '''// 電波がなくても動かすためのサービスワーカー。tools/build_web.py が作る（手で直さない）
const V='__VERSION__',CORE=__CORE__;
self.addEventListener('install',e=>{e.waitUntil(caches.open('core-'+V).then(c=>c.addAll(CORE)).then(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!=='core-'+V&&k!=='fonts').map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET')return;
  const u=new URL(e.request.url);
  // アプリ本体とデータは保存しておいたものを使う（新しい版は sw.js が変わったときに入れかわる）
  if(u.origin===location.origin){e.respondWith(caches.match(e.request,{ignoreSearch:true}).then(r=>r||fetch(e.request)));return}
  // 字体（Google Fonts）は一度読んだら保存し、次からは保存分を使いつつ裏で新しくする
  if(u.host==='fonts.googleapis.com'||u.host==='fonts.gstatic.com'){
    e.respondWith(caches.open('fonts').then(async c=>{
      const hit=await c.match(e.request);
      const net=fetch(e.request).then(r=>{if(r.ok||r.type==='opaque')c.put(e.request,r.clone());return r}).catch(()=>hit);
      return hit||net;
    }));
  }
});
'''


def main():
    src = open(os.path.join(ROOT, 'keykoma.html'), encoding='utf8').read()
    # アーティファクト用の先頭（<title> と claude 用の meta）は HEAD に置きかえる
    body = re.sub(r'^<title>.*?</title>\s*', '', src, count=1, flags=re.S)
    body = re.sub(r'<meta name="claude:[^>]*>\s*', '', body)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, 'index.html'), 'w', encoding='utf8') as f:
        f.write(HEAD + body.rstrip() + '\n' + TAIL)
    for p in DATA:
        os.makedirs(os.path.dirname(os.path.join(OUT, p)), exist_ok=True)
        shutil.copyfile(os.path.join(ROOT, p), os.path.join(OUT, p))
    if not all(os.path.exists(os.path.join(OUT, p)) for p in ICONS):
        subprocess.run(['node', os.path.join(ROOT, 'tools', 'make_icons.js'), os.path.join(OUT, 'icons')], check=True)
    manifest = {
        'name': NAME, 'short_name': SHORT, 'description': DESC, 'lang': 'ja',
        'start_url': './', 'scope': './', 'display': 'standalone',
        'background_color': BG, 'theme_color': BG,
        'icons': [
            {'src': 'icons/icon-192.png', 'sizes': '192x192', 'type': 'image/png', 'purpose': 'any'},
            {'src': 'icons/icon-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any'},
            {'src': 'icons/icon-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'},
        ],
    }
    with open(os.path.join(OUT, 'manifest.webmanifest'), 'w', encoding='utf8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    core = ['./', 'index.html', 'manifest.webmanifest'] + DATA + ICONS
    # 中身が変わったら版の名前も変わり、利用者の端末の保存分が新しいものに入れかわる
    h = hashlib.sha256()
    for p in core[1:]:
        h.update(open(os.path.join(OUT, p), 'rb').read())
    with open(os.path.join(OUT, 'sw.js'), 'w', encoding='utf8') as f:
        f.write(SW.replace('__VERSION__', h.hexdigest()[:12]).replace('__CORE__', json.dumps(core)))
    open(os.path.join(OUT, '.nojekyll'), 'w').close()  # GitHub Pages にそのまま配らせる
    print('docs/ を作りました（版 ' + h.hexdigest()[:12] + '）')


if __name__ == '__main__':
    main()
