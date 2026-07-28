JS_INTERCEPT = r"""
(() => {
    if (window.__i) return; window.__i = true;
    const set = (k, v) => v && document.documentElement.setAttribute(k, v);
    const saveToken = t => { if (t && t.includes('eyJ')) set('data-token', String(t).replace('Bearer ', '').trim()); };
    const saveOrg = t => { if (typeof t !== 'string') return; const m = t.match(/org_[a-zA-Z0-9]{20,}/); if (m) set('data-org', m[0]); };

    const of = window.fetch;
    window.fetch = function() {
        const u = arguments[0], isOpus = typeof u === 'string' && u.includes('opus.pro');
        if (isOpus && arguments[1] && arguments[1].headers) {
            const h = arguments[1].headers, g = k => typeof h.get === 'function' ? h.get(k) : h[k];
            saveToken(g('authorization') || g('Authorization'));
            saveOrg(g('x-opus-org-id') || g('X-Opus-Org-Id'));
        }
        return of.apply(this, arguments).then(r => {
            if (isOpus) r.clone().text().then(t => { saveOrg(t); try { const d = JSON.parse(t); if (d.access_token) saveToken(d.access_token); } catch(_){} }).catch(()=>{});
            return r;
        });
    };

    const os = XMLHttpRequest.prototype.setRequestHeader;
    XMLHttpRequest.prototype.setRequestHeader = function(k, v) {
        try {
            if (k.toLowerCase() === 'authorization') saveToken(v);
            if (k.toLowerCase() === 'x-opus-org-id') saveOrg(v);
        } catch(_){}
        os.apply(this, arguments);
    };

    const OW = window.Worker;
    window.Worker = function() {
        const w = new OW(...arguments);
        w.addEventListener('message', e => {
            try {
                saveOrg(JSON.stringify(e.data));
                const t = (e.data && e.data.json && e.data.json.access_token) || (e.data && e.data.access_token);
                if (t) saveToken(t);
            } catch(_){}
        });
        return w;
    };
})();
"""

JS_CREATE_KEY = """
const done = arguments[arguments.length - 1];
const [token, orgId, userId] = arguments;
const h = {
    'authorization': 'Bearer ' + token,
    'content-type': 'application/json',
    'x-opus-org-id': orgId,
    'x-opus-user-id': userId,
    'x-opus-device-platform': 'web'
};
Promise.all([
    fetch('https://api.opus.pro/api/api-keys', {method: 'POST', headers: h, body: JSON.stringify({orgId})}).then(r => r.json()),
    fetch('https://api.opus.pro/api/org-credits?q=mine', {headers: h}).then(r => r.json())
]).then(([k, c]) => done({key: k, credits: c})).catch(e => done({error: e.message}));
"""
