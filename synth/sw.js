const C='sy5k-v1',F=['./','index.html','manifest.json','icon-180.png','../fonts/InterDisplay-Black.woff2','../fonts/JetBrainsMono-400.woff2','../fonts/JetBrainsMono-700.woff2'];
self.addEventListener('install',e=>e.waitUntil(caches.open(C).then(c=>c.addAll(F)).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(clients.claim()));
self.addEventListener('fetch',e=>e.respondWith(fetch(e.request).then(r=>{const cp=r.clone();caches.open(C).then(c=>c.put(e.request,cp));return r}).catch(()=>caches.match(e.request))));
