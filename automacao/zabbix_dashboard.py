#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# zabbix_dashboard.py
# Painel LOCAL que puxa dados do Zabbix AO VIVO (status de apps, rede, problemas).
#
# O navegador nao chama a API do Zabbix direto (CORS/token). Entao este script
# sobe um mini-servidor local que:
#   - serve o painel HTML
#   - faz de PROXY da API (token fica no servidor; SO metodos *.get = leitura)
#
# Credenciais: pega de ZBX_URL/ZBX_TOKEN (env) ou, se nao tiver, le do ../.mcp.json
# (o token read-only do servidor 'zabbix'). Zero config.
#
# Uso:
#   python zabbix_dashboard.py
#   (depois abra http://localhost:8077)
# -----------------------------------------------------------------------------
import os, re, json, urllib.request, http.server, socketserver, webbrowser, threading

def load_creds():
    url, tok = os.environ.get("ZBX_URL"), os.environ.get("ZBX_TOKEN")
    if url and tok:
        return url, tok
    for p in ("../.mcp.json", ".mcp.json",
              os.path.join(os.path.dirname(__file__), "..", ".mcp.json")):
        try:
            env = json.load(open(p, encoding="utf-8"))["mcpServers"]["zabbix"]["env"]
            return env.get("ZABBIX_URL"), env.get("ZABBIX_TOKEN")
        except Exception:
            pass
    return url or "http://172.17.2.51/api_jsonrpc.php", tok or ""

ZBX_URL, ZBX_TOKEN = load_creds()
PORT = int(os.environ.get("PORT", "8077"))
READ_ONLY = re.compile(r"\.get$")  # so leitura

def zbx(method, params):
    headers = {"Content-Type": "application/json-rpc"}
    if method != "apiinfo.version":   # apiinfo.version DEVE ser chamado sem auth
        headers["Authorization"] = f"Bearer {ZBX_TOKEN}"
    body = json.dumps({"jsonrpc": "2.0", "method": method, "params": params, "id": 1}).encode()
    req = urllib.request.Request(ZBX_URL, data=body, headers=headers)
    return json.loads(urllib.request.urlopen(req, timeout=30).read())

HTML = r"""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Zabbix — Painel ao vivo</title>
<style>
:root{--bg:#f4f6f9;--card:#fff;--ink:#1f2937;--muted:#6b7280;--line:#e5e7eb;--brand:#b1271b;--brand2:#7a1a12}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 Segoe UI,Roboto,Arial,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:18px}
header{background:linear-gradient(135deg,var(--brand),var(--brand2));color:#fff;border-radius:12px;padding:18px 22px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px}
header h1{margin:0;font-size:19px}header .meta{font-size:12px;opacity:.92}
.tabs{display:flex;gap:8px;margin:16px 0 10px;flex-wrap:wrap}
.tab{background:#fff;border:1px solid var(--line);border-radius:999px;padding:7px 16px;cursor:pointer;font-weight:600;font-size:13px}
.tab.on{background:var(--brand);color:#fff;border-color:var(--brand)}
.ctrl{display:flex;gap:10px;align-items:center;margin-bottom:10px;font-size:13px;color:var(--muted)}
button.act{background:var(--brand);color:#fff;border:0;border-radius:8px;padding:7px 14px;cursor:pointer;font-weight:600}
section{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin-bottom:14px}
h2{margin:0 0 12px;font-size:16px;border-left:4px solid var(--brand);padding-left:9px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:12px}
.cd{background:#fafbfc;border:1px solid var(--line);border-radius:10px;padding:12px;text-align:center}
.cd b{display:block;font-size:26px}.cd span{font-size:12px;color:var(--muted)}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{text-align:left;padding:7px 9px;border-bottom:1px solid var(--line);vertical-align:top}
th{background:#fafafa;color:var(--muted);font-size:11px;text-transform:uppercase}
tr:hover td{background:#fafbfc}
.b{display:inline-block;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:600;white-space:nowrap}
.s5{background:#fee2e2;color:#991b1b}.s4{background:#fee2e2;color:#b91c1c}.s3{background:#fef3c7;color:#92400e}
.s2{background:#fef9c3;color:#854d0e}.s1{background:#dbeafe;color:#1e40af}.s0{background:#f3f4f6;color:#374151}
.ok{background:#dcfce7;color:#166534}.no{background:#fee2e2;color:#991b1b}
.dot{width:9px;height:9px;border-radius:50%;display:inline-block;margin-right:6px}
.dg{background:#16a34a}.dr{background:#dc2626}
.loading{color:var(--muted);padding:20px;text-align:center}
.err{background:#fee2e2;color:#991b1b;padding:10px;border-radius:8px}
small.mut{color:var(--muted)}
</style></head><body><div class="wrap">
<header>
  <div><h1>Zabbix — Painel ao vivo</h1><div class="meta" id="meta">conectando…</div></div>
  <div class="ctrl" style="color:#fff">
    <label style="color:#fff"><input type="checkbox" id="auto"> auto 30s</label>
    <button class="act" onclick="refresh()">Atualizar</button>
  </div>
</header>
<div class="tabs" id="tabs"></div>
<div id="view"></div>
<small class="mut" id="ts"></small>
</div>
<script>
const SEV=['Not classified','Information','Warning','Average','High','Disaster'];
let TAB='resumo', timer=null;
const TABS=[['resumo','Resumo'],['problemas','Problemas'],['apps','Aplicações'],['rede','Rede']];

async function api(method,params){
  const r=await fetch('/api',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({method,params})});
  const j=await r.json();
  if(j.error) throw new Error(typeof j.error==='string'?j.error:JSON.stringify(j.error));
  return j.result;
}
function el(id){return document.getElementById(id)}
function tabsBar(){el('tabs').innerHTML=TABS.map(t=>`<div class="tab ${t[0]==TAB?'on':''}" onclick="go('${t[0]}')">${t[1]}</div>`).join('')}
function go(t){TAB=t;tabsBar();render()}
function tpls(h){return (h.parentTemplates||[]).map(t=>t.name)}
function hasICMP(h){return tpls(h).some(n=>/ICMP Ping/i.test(n))}
function roles(h){return tpls(h).filter(n=>n.startsWith('Role - ')||/by SNMP|Hyper-V Host|MSSQL|PostgreSQL|Docker by|Apache by|Zabbix proxy health|Zabbix server health/.test(n))}

async function getProblems(){
  // trigger.get aceita selectHosts (problem.get nao) e respeita dependencias (skipDependent)
  const t=await api('trigger.get',{filter:{value:1},output:['description','priority','lastchange'],
    selectHosts:['host'],expandDescription:true,monitored:true,skipDependent:true,
    sortfield:'priority',sortorder:'DESC'});
  return t.map(x=>({name:x.description,severity:x.priority,clock:x.lastchange,hosts:x.hosts||[]}));
}
function probByHost(probs){const m={};probs.forEach(p=>(p.hosts||[]).forEach(h=>{(m[h.host]=m[h.host]||[]).push(p)}));return m}

async function render(){
  const v=el('view'); v.innerHTML='<div class="loading">carregando…</div>';
  try{
    if(TAB=='resumo') await viewResumo(v);
    else if(TAB=='problemas') await viewProblemas(v);
    else if(TAB=='apps') await viewApps(v);
    else if(TAB=='rede') await viewRede(v);
    el('ts').textContent='Atualizado '+new Date().toLocaleTimeString('pt-BR');
  }catch(e){ v.innerHTML='<div class="err">Erro: '+e.message+'</div>' }
}

async function viewResumo(v){
  const probs=await getProblems();
  const buckets=[0,0,0,0,0,0]; probs.forEach(p=>buckets[+p.severity]++);
  const hg=await api('host.get',{countOutput:true});
  v.innerHTML=`<section><h2>Resumo</h2>
    <div class="cards">
      <div class="cd"><b>${hg}</b><span>hosts</span></div>
      <div class="cd"><b>${probs.length}</b><span>problemas abertos</span></div>
      <div class="cd"><b style="color:#dc2626">${buckets[5]+buckets[4]}</b><span>High/Disaster</span></div>
      <div class="cd"><b style="color:#d97706">${buckets[3]}</b><span>Average</span></div>
      <div class="cd"><b style="color:#854d0e">${buckets[2]}</b><span>Warning</span></div>
    </div></section>
    <section><h2>Problemas por severidade</h2><table><tr><th>Severidade</th><th>Qtd</th></tr>
    ${[5,4,3,2,1,0].map(i=>`<tr><td><span class="b s${i}">${SEV[i]}</span></td><td>${buckets[i]}</td></tr>`).join('')}
    </table></section>`;
}
async function viewProblemas(v){
  const probs=await getProblems();
  v.innerHTML=`<section><h2>Problemas abertos (${probs.length})</h2><table>
    <tr><th>Sev</th><th>Host</th><th>Problema</th><th>Desde</th></tr>
    ${probs.slice(0,300).map(p=>`<tr><td><span class="b s${p.severity}">${SEV[p.severity]}</span></td>
      <td>${(p.hosts||[]).map(h=>h.host).join(', ')}</td><td>${esc(p.name)}</td>
      <td><small class="mut">${new Date(p.clock*1000).toLocaleString('pt-BR')}</small></td></tr>`).join('')||'<tr><td colspan=4>nenhum 🎉</td></tr>'}
    </table></section>`;
}
async function viewApps(v){
  const hosts=await api('host.get',{search:{host:['-SRV-','AZ-VM']},searchByAny:true,
    output:['host'],selectParentTemplates:['name'],sortfield:'host'});
  const ph=probByHost(await getProblems());
  const rows=hosts.filter(h=>roles(h).length).map(h=>{
    const pr=ph[h.host]||[]; const max=pr.reduce((a,p)=>Math.max(a,+p.severity),0);
    return `<tr><td><span class="dot ${pr.length?'dr':'dg'}"></span>${h.host}</td>
      <td>${roles(h).join('<br>')}</td>
      <td>${pr.length?`<span class="b s${max}">${pr.length} problema(s)</span>`:'<span class="b ok">OK</span>'}</td></tr>`;
  }).join('');
  v.innerHTML=`<section><h2>Aplicações (${hosts.filter(h=>roles(h).length).length} hosts)</h2>
    <table><tr><th>Host</th><th>Templates / Roles</th><th>Status</th></tr>${rows}</table></section>`;
}
async function viewRede(v){
  const hosts=await api('host.get',{search:{host:['-SW0','-FW0','-UPS0','-AP0','-SW1','-AP1','-AP2','-AP3']},
    searchByAny:true,output:['host'],selectParentTemplates:['name'],sortfield:'host'});
  const ph=probByHost(await getProblems());
  const rows=hosts.map(h=>{
    const pr=ph[h.host]||[]; const max=pr.reduce((a,p)=>Math.max(a,+p.severity),0);
    return `<tr><td><span class="dot ${pr.length?'dr':'dg'}"></span>${h.host}</td>
      <td>${tpls(h).join('<br>')}</td>
      <td>${pr.length?`<span class="b s${max}">${pr.length} problema(s)</span>`:'<span class="b ok">OK</span>'}</td></tr>`;
  }).join('');
  v.innerHTML=`<section><h2>Rede (${hosts.length} equipamentos)</h2>
    <table><tr><th>Host</th><th>Templates</th><th>Status</th></tr>${rows}</table></section>`;
}
function esc(s){return (s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}

async function refresh(){await render()}
function setAuto(){const c=el('auto');if(timer)clearInterval(timer);timer=null;if(c.checked)timer=setInterval(render,30000)}

(async function init(){
  tabsBar(); el('auto').onchange=setAuto;
  try{const ver=await api('apiinfo.version',{}); el('meta').textContent='Zabbix '+ver+' — leitura ao vivo';}
  catch(e){el('meta').textContent='erro de conexão: '+e.message}
  render();
})();
</script></body></html>"""

class H(http.server.BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        b = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code); self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, HTML, "text/html; charset=utf-8")
        else:
            self._send(404, "{}")
    def do_POST(self):
        if self.path != "/api":
            return self._send(404, "{}")
        try:
            n = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return self._send(400, json.dumps({"error": "json invalido"}))
        method, params = data.get("method", ""), data.get("params", {})
        if not (READ_ONLY.search(method) or method == "apiinfo.version"):
            return self._send(403, json.dumps({"error": "metodo nao permitido (so leitura)"}))
        try:
            self._send(200, json.dumps(zbx(method, params)))
        except Exception as e:
            self._send(502, json.dumps({"error": str(e)}))
    def log_message(self, *a):
        pass

if __name__ == "__main__":
    if not ZBX_TOKEN:
        print("AVISO: sem token. Defina ZBX_TOKEN ou rode ao lado do .mcp.json.")
    print(f">> Painel: http://localhost:{PORT}   (Zabbix: {ZBX_URL})")
    print(">> Ctrl+C para parar.")
    threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()
    socketserver.TCPServer(("127.0.0.1", PORT), H).serve_forever()
