import os
import json
from flask import request, jsonify
from locust import HttpUser, task, between, events

# persistent config file next to this locustfile
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "locust_config.json")

def load_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    # default config
    return {"method":"GET","path":"/","headers":{},"params":{},"json":None}

def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass

CONFIG = load_config()

INJECT_SNIPPET = """
<style>
    /* Modal/form styles (kept minimal and self-contained) */
    .lcst-card { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; border:1px solid #ddd; border-radius:4px; padding:16px; max-width:900px; margin:0 auto; }
    .lcst-row { display:flex; gap:8px; margin-bottom:8px; }
    .lcst-col { flex:1; }
    .lcst-input, textarea { width:100%; padding:6px 8px; border:1px solid #ccc; border-radius:4px; }
    .lcst-kv-row { display:flex; gap:8px; margin-bottom:6px; }
    .lcst-kv-row input { flex:1; }
    .lcst-btn { display:inline-block; padding:6px 10px; border-radius:4px; background:#337ab7; color:#fff; border:none; cursor:pointer; }
    .lcst-btn.secondary { background:#6c757d; }
</style>
<div id="lcst-custom-config-modal" style="display:none;position:fixed;left:0;top:0;width:100%;height:100%;background:rgba(0,0,0,0.35);z-index:11000">
    <div style="background:#fff;margin:40px auto;padding:12px;border-radius:6px;max-width:1100px;height:85%;overflow:auto;box-shadow:0 6px 18px rgba(0,0,0,0.2)">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
            <h3 style="margin:0">Request Config</h3>
            <div><button id="lcst-custom-close" onclick="document.getElementById('lcst-custom-config-modal').style.display='none'" class="lcst-btn secondary">Close</button></div>
        </div>
        <div id="lcst-custom-form"></div>
    </div>
</div>
<script>
(function(){
    function addKv(container, key='', value=''){
        const div = document.createElement('div');
        div.className = 'lcst-kv-row';
        div.innerHTML = `<input type="text" class="lcst-kv-key" placeholder="Key" value="${key.replace(/"/g,'&quot;')}" />
                                         <input type="text" class="lcst-kv-val" placeholder="Value" value="${value.replace(/"/g,'&quot;')}" />
                                         <button type="button" class="lcst-btn secondary">Remove</button>`;
        div.querySelector('button').addEventListener('click', ()=>div.remove());
        container.appendChild(div);
    }

    function buildForm(config){
        const container = document.getElementById('lcst-custom-form');
        container.innerHTML = `<div class="lcst-card">
            <div class="lcst-row"><div class="lcst-col"><label>HTTP Method</label>
                <select id="lcst-method" class="lcst-input"><option>GET</option><option>POST</option><option>PUT</option><option>DELETE</option></select></div>
                <div class="lcst-col"><label>Path</label><input id="lcst-path" class="lcst-input" type="text" /></div></div>
            <h3>Headers</h3><div id="headers_container"></div><p><button id="add_header" type="button" class="lcst-btn">Add header</button></p>
            <h3>URL Parameters</h3><div id="params_container"></div><p><button id="add_param" type="button" class="lcst-btn">Add param</button></p>
            <h3>JSON Body</h3><textarea id="lcst-json_body" rows="8" class="lcst-input"></textarea>
            <p style="margin-top:12px"><button id="lcst-save" class="lcst-btn">Save</button>
            <button id="lcst-cancel" class="lcst-btn secondary" type="button">Cancel</button></p></div>`;

        document.getElementById('lcst-method').value = config.method || 'GET';
        document.getElementById('lcst-path').value = config.path || '/';
        const headersCont = document.getElementById('headers_container');
        const paramsCont = document.getElementById('params_container');
        headersCont.innerHTML = '';
        paramsCont.innerHTML = '';
        const headers = config.headers || {};
        const params = config.params || {};
        Object.keys(headers).forEach(k=>addKv(headersCont,k,headers[k]));
        Object.keys(params).forEach(k=>addKv(paramsCont,k,params[k]));
        if(Object.keys(headers).length===0) addKv(headersCont);
        if(Object.keys(params).length===0) addKv(paramsCont);
        document.getElementById('lcst-json_body').value = config.json ? JSON.stringify(config.json,null,2) : '';

        document.getElementById('add_header').addEventListener('click', ()=>addKv(headersCont));
        document.getElementById('add_param').addEventListener('click', ()=>addKv(paramsCont));

        document.getElementById('lcst-save').addEventListener('click', async ()=>{
            const hdrs = {};
            headersCont.querySelectorAll('.lcst-kv-row').forEach(r=>{const k=r.querySelector('.lcst-kv-key').value; const v=r.querySelector('.lcst-kv-val').value; if(k && k.trim()) hdrs[k.trim()]=v;});
            const prms = {};
            paramsCont.querySelectorAll('.lcst-kv-row').forEach(r=>{const k=r.querySelector('.lcst-kv-key').value; const v=r.querySelector('.lcst-kv-val').value; if(k && k.trim()) prms[k.trim()]=v;});
            const payload = { method: document.getElementById('lcst-method').value, path: document.getElementById('lcst-path').value, headers: hdrs, params: prms, json_body: document.getElementById('lcst-json_body').value };
            try{ const res = await fetch('/_custom_config', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)}); const j = await res.json(); if(j && j.success){ document.getElementById('lcst-custom-config-modal').style.display='none'; } }catch(e){console.error(e);}    });

        document.getElementById('lcst-cancel').addEventListener('click', ()=>{document.getElementById('lcst-custom-config-modal').style.display='none'});
    }

    function openModal(){ document.getElementById('lcst-custom-config-modal').style.display='block'; fetch('/_custom_config_state').then(r=>r.json()).then(buildForm).catch(e=>console.error(e)); }

    document.addEventListener('DOMContentLoaded', function(){
        // insert the Request Config button into the header (nav/header) on the right side
        function insertButtonIntoHeader(btn){
            var headerElem = document.querySelector('nav, header');
            if(!headerElem) headerElem = document.body;
            // remove existing if elsewhere
            var existing = document.getElementById('lcst-custom-open');
            if(existing && existing.parentNode && existing.parentNode !== headerElem){ existing.parentNode.removeChild(existing); }

            // prefer flex-based alignment
            try{
                var cs = window.getComputedStyle(headerElem);
                if(cs && cs.display && cs.display.indexOf('flex') !== -1){
                    btn.style.marginLeft = 'auto';
                    btn.style.order = '9999';
                    headerElem.appendChild(btn);
                    return true;
                }
            }catch(e){}

            // try to find a right-side container inside the header
            var right = headerElem.querySelector('.header__right, .right, .topbar-actions, .actions, .navbar-right, .Header-right, .lcst-header-right');
            if(right){ right.appendChild(btn); return true; }

            // fallback: absolute-position button inside header bounding box
            try{
                if(window.getComputedStyle(headerElem).position === 'static') headerElem.style.position = 'relative';
                btn.style.position = 'absolute';
                btn.style.right = '12px';
                btn.style.top = '8px';
                headerElem.appendChild(btn);
                return true;
            }catch(e){
                // final fallback: append to header or body
                try{ headerElem.appendChild(btn); return true; }catch(e){ return false; }
            }
        }

        if(!document.getElementById('lcst-custom-open')){
            var btn = document.createElement('button'); btn.id='lcst-custom-open'; btn.className='lcst-btn'; btn.textContent='Request Config';
            btn.addEventListener('click', function(e){ e.preventDefault(); openModal(); });
            insertButtonIntoHeader(btn);
        }
    });
})();
</script>
<script>
        document.getElementById('add_header').addEventListener('click', ()=>addKv(headersCont));
        document.getElementById('add_param').addEventListener('click', ()=>addKv(paramsCont));

        document.getElementById('lcst-save').addEventListener('click', async ()=>{
            // gather headers
            const hdrs = {};
            headersCont.querySelectorAll('.kv-row').forEach(r=>{const k=r.querySelector('.kv-key').value; const v=r.querySelector('.kv-val').value; if(k && k.trim()) hdrs[k.trim()]=v;});
            const prms = {};
            paramsCont.querySelectorAll('.kv-row').forEach(r=>{const k=r.querySelector('.kv-key').value; const v=r.querySelector('.kv-val').value; if(k && k.trim()) prms[k.trim()]=v;});
            const payload = {
                method: document.getElementById('lcst-method').value,
                path: document.getElementById('lcst-path').value,
                headers: hdrs,
                params: prms,
                json_body: document.getElementById('lcst-json_body').value,
            };
            try{
                const res = await fetch('/_custom_config', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
                const j = await res.json();
                if(j && j.success){ document.getElementById('lcst-custom-config-modal').style.display='none'; }
            }catch(e){console.error(e);}
        });

        document.getElementById('lcst-cancel').addEventListener('click', ()=>{document.getElementById('lcst-custom-config-modal').style.display='none'});
    }

    function openModal(){
        document.getElementById('lcst-custom-config-modal').style.display='block';
        fetch('/_custom_config_state').then(r=>r.json()).then(buildForm).catch(e=>console.error(e));
    }
    function closeModal(){document.getElementById('lcst-custom-config-modal').style.display='none'}

    function tryInsert(){
        try{
            var adv = Array.from(document.querySelectorAll('*')).find(function(el){ return /Advanced/i.test(el.textContent) });
            // Prefer moving the existing floating button under the Advanced accordion
            var floating = document.getElementById('lcst-custom-floating');
            if(floating && adv){
                try{
                    // try to locate the accordion root (closest element with MuiAccordion-root)
                    var accordionRoot = adv.closest && adv.closest('.MuiAccordion-root');
                    if(!accordionRoot){
                        // walk up to a reasonable ancestor (h3 -> parent div)
                        accordionRoot = adv.closest && (adv.closest('h3') || adv.closest('div'));
                    }
                    if(accordionRoot && accordionRoot.parentNode){
                        if(accordionRoot.nextSibling) accordionRoot.parentNode.insertBefore(floating, accordionRoot.nextSibling);
                        else accordionRoot.parentNode.appendChild(floating);
                        return true;
                    }
                }catch(e){ /* fallback to creating a link below */ }
            }
            var link = document.getElementById('lcst-custom-link');
            if(!link){
                link = document.createElement('a');
                link.id = 'lcst-custom-link';
                link.href = '#';
                link.textContent = 'Request Config';
                link.style.marginLeft = '8px';
                link.className = 'btn secondary';
                link.onclick = function(e){ e.preventDefault(); openModal(); };
            }
            if(adv && !adv.contains(link)){
                try{
                    if(adv.parentNode){
                        if(adv.nextSibling) adv.parentNode.insertBefore(link, adv.nextSibling);
                        else adv.parentNode.appendChild(link);
                    } else {
                        adv.appendChild(link);
                    }
                }catch(e){
                    try{ adv.appendChild(link); }catch(_){}
                }
                return true;
            }
            var headerElem = document.querySelector('nav, header');
            if(!headerElem) headerElem = document.body;
            if(headerElem && !headerElem.contains(link)){
                // prefer flex alignment
                try{
                    var cs2 = window.getComputedStyle(headerElem);
                    if(cs2 && cs2.display && cs2.display.indexOf('flex') !== -1){ link.style.marginLeft='auto'; headerElem.appendChild(link); return true; }
                }catch(e){}
                var right2 = headerElem.querySelector('.header__right, .right, .topbar-actions, .actions, .navbar-right, .Header-right');
                if(right2){ right2.appendChild(link); return true; }
                try{ if(window.getComputedStyle(headerElem).position === 'static') headerElem.style.position='relative'; link.style.position='absolute'; link.style.right='12px'; link.style.top='8px'; headerElem.appendChild(link); return true; }catch(e){ try{ headerElem.appendChild(link); return true; }catch(e){}};
            }
        }catch(e){/* fail silently */}
        return false;
    }

    document.addEventListener('DOMContentLoaded', function(){
        // Always ensure the floating open button works
        var openBtn = document.getElementById('lcst-custom-open');
        if(openBtn) openBtn.addEventListener('click', function(e){ e.preventDefault(); openModal(); });

        // Try to insert near an 'Advanced' area, otherwise rely on floating button
        if(tryInsert()) return;
        var attempts = 0;
        var tid = setInterval(function(){ attempts++; if(tryInsert() || attempts>10) clearInterval(tid); }, 500);

        // MutationObserver as a fallback to detect UI changes
        try{
            var observer = new MutationObserver(function(){ if(tryInsert()){ observer.disconnect(); } });
            observer.observe(document.body, {childList:true, subtree:true});
        }catch(e){}

        // close button handler (modal exists in DOM from injection)
        var closeBtn = document.getElementById('lcst-custom-close');
        if(closeBtn) closeBtn.addEventListener('click', closeModal);
    });
})();
</script>
"""


def _inject_into_index(app):
    @app.after_request
    def _inject(response):
        try:
            path = (request.path or "")
            # don't inject into our JSON endpoints or static files
            if path.startswith('/_custom_config') or path.startswith('/_custom_config_state') or path.startswith('/static'):
                return response

            ct = (response.content_type or '')
            if 'text/html' in ct.lower():
                html = response.get_data(as_text=True)
                if '</body>' in html:
                    html = html.replace('</body>', INJECT_SNIPPET + '</body>')
                    response.set_data(html)
        except Exception:
            pass
        return response


def _register_routes(app):
    # POST -> save config
    def _save_config():
        try:
            data = request.get_json(force=True) or {}
            method = data.get('method', 'GET')
            path = data.get('path', '/')
            headers = data.get('headers', {}) or {}
            params = data.get('params', {}) or {}
            json_body = data.get('json_body')
            try:
                parsed = json.loads(json_body) if isinstance(json_body, str) and json_body.strip() else None
            except Exception:
                parsed = None

            CONFIG['method'] = method
            CONFIG['path'] = path
            CONFIG['headers'] = headers
            CONFIG['params'] = params
            CONFIG['json'] = parsed
            save_config(CONFIG)
            return jsonify(success=True)
        except Exception as e:
            return jsonify(success=False, error=str(e)), 400

    # GET -> return current config
    def _get_state():
        return jsonify(CONFIG)

    # register routes on the Locust/Flask app
    app.add_url_rule('/_custom_config', '_custom_config', _save_config, methods=['POST'])
    app.add_url_rule('/_custom_config_state', '_custom_config_state', _get_state, methods=['GET'])


# Add the injector when the web app exists (works for single-process web UI)
def _on_init_inject(environment, **kw):
    try:
        app = environment.web_ui.app
        _inject_into_index(app)
        try:
            _register_routes(app)
        except Exception:
            pass
    except Exception as e:
        print("[locust-custom] failed to register index injector:", e)


events.init.add_listener(_on_init_inject)


class WebsiteUser(HttpUser):
    """Locust user that performs a configurable request.

    Use the Locust web UI (http://localhost:8089) to set the Host, number of users,
    and spawn rate. Click the "Custom Config" link in the main UI (under Advanced)
    to open a modal where you can edit method/path/headers/params/body inline.
    """

    # After each task the virtual user pauses for a random interval between 1 and 3 seconds.
    # Locust repeatedly runs available tasks for each WebsiteUser, with waits inserted by wait_time.
    wait_time = between(1, 3)

    @task
    def flexible_request(self):
        method = CONFIG.get("method", "GET").upper()
        path = CONFIG.get("path", "/")
        headers = CONFIG.get("headers") or {}
        json_body = CONFIG.get("json")
        params = CONFIG.get("params") or {}

        if method == "GET":
            self.client.get(path, headers=headers, params=params, name=f"{method} {path}")
        else:
            # for POST/PUT/DELETE etc. use request so we can pass json data and params
            self.client.request(method, path, headers=headers, json=json_body, params=params, name=f"{method} {path}")
