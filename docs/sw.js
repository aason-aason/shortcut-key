// 電波がなくても動かすためのサービスワーカー。tools/build_web.py が作る（手で直さない）
const V='bc22c788699d',CORE=["./", "index.html", "manifest.webmanifest", "data/scenes.js", "data/logic-pro.js", "icons/icon-192.png", "icons/icon-512.png", "icons/apple-touch-icon.png"];
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
