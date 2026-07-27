#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROTOTIPO LOCAL — NOC Geomap (parecido com o painel customizado).

Puxa dados ao vivo da API do Zabbix e gera uma pagina HTML autossuficiente
(Leaflet + JSON embutido) com: mapa geografico, marcadores por tipo/severidade,
cards de KPI no topo, painel "Top Impactos", legenda, detalhe do host ao clicar
e export CSV. Abre por duplo-clique (precisa de internet para os tiles do mapa).

  python gen_noc_geomap.py

>>> COORDENADAS: como o inventario ainda nao tem lat/long, os 3 sites (bgp/scl/spo)
    usam coordenadas PLACEHOLDER na tabela SITE_COORDS abaixo. AJUSTE para as
    cidades reais das unidades (ou me passe as cidades que eu acerto).
"""
import os
import ssl
import json
import html
import datetime as dt
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ---- coordenadas por site (PLACEHOLDER — AJUSTAR para as unidades reais) --------
SITE_COORDS = {
    "spo": (-23.5505, -46.6333, "Sao Paulo/SP"),
    "scl": (-22.0087, -47.8909, "Sao Carlos/SP"),
    "bgp": (-22.9519, -46.5419, "Braganca Paulista/SP"),
}
DEFAULT_COORD = (-15.78, -47.93, "Brasil (sem site)")

# grupos de rede (switches / APs / firewalls)
NET_GROUPS = ["22", "23", "24", "25", "26", "41", "42", "43", "27", "28", "29", "30", "31"]

# ---- API ----------------------------------------------------------------------
def load_credentials():
    url = os.environ.get("ZABBIX_URL")
    token = os.environ.get("ZABBIX_TOKEN")
    if url and token:
        return url, token
    env = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]["zabbix"]["env"]
    return env["ZABBIX_URL"], env["ZABBIX_TOKEN"]


URL, TOKEN = load_credentials()
_SSL = ssl.create_default_context()
_SSL.check_hostname = False
_SSL.verify_mode = ssl.CERT_NONE


def api(method, params=None):
    payload = {"jsonrpc": "2.0", "method": method, "params": params or {}, "id": 1}
    req = urllib.request.Request(URL, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json-rpc",
                                          "Authorization": f"Bearer {TOKEN}"})
    with urllib.request.urlopen(req, timeout=60, context=_SSL) as r:
        resp = json.load(r)
    if "error" in resp:
        raise RuntimeError(f"{method}: {resp['error']}")
    return resp["result"]


# ---- coleta -------------------------------------------------------------------
def tag_val(tags, key, default=""):
    for t in tags:
        if t.get("tag") == key:
            return t["value"]
    return default


def jitter(hostid, base_lat, base_lon):
    # todos os hosts do site ficam na coordenada da cidade -> 1 cluster limpo por site
    # (clicar no cluster abre/spiderfy os equipamentos). Micro-offset so p/ nao empilhar exato.
    h = int(hostid)
    dlat = ((h * 73 % 20) - 10) / 100000.0   # ~ +-0.0001 grau (~10 m)
    dlon = ((h * 137 % 20) - 10) / 100000.0
    return round(base_lat + dlat, 6), round(base_lon + dlon, 6)


def collect():
    hosts = api("host.get", {"groupids": NET_GROUPS, "output": ["hostid", "host", "name", "status"],
                             "selectTags": ["tag", "value"]})
    hids = [h["hostid"] for h in hosts]

    # problemas ativos (problem.get nao tem selectHosts -> mapeia trigger->host)
    probs = api("problem.get", {"hostids": hids, "source": 0, "object": 0,
                                "output": ["eventid", "name", "severity", "clock", "objectid"]})
    trig_ids = list({p["objectid"] for p in probs})
    trig_host = {}
    if trig_ids:
        for t in api("trigger.get", {"triggerids": trig_ids, "output": ["triggerid"],
                                     "selectHosts": ["hostid"]}):
            trig_host[t["triggerid"]] = [h["hostid"] for h in t.get("hosts", [])]
    by_host_probs = {}
    for p in probs:
        for hid in trig_host.get(p["objectid"], []):
            by_host_probs.setdefault(hid, []).append(
                {"name": p["name"], "sev": int(p["severity"]), "clock": int(p["clock"])})

    # metricas ICMP (up / loss / latencia)
    items = api("item.get", {"hostids": hids, "output": ["hostid", "key_", "lastvalue"],
                             "search": {"key_": "icmp"}})
    metrics = {}
    for it in items:
        metrics.setdefault(it["hostid"], {})[it["key_"]] = it["lastvalue"]

    recs = []
    for h in hosts:
        hid = h["hostid"]
        tags = h.get("tags", [])
        site = tag_val(tags, "site", "?").lower()
        tipo = tag_val(tags, "infra", "outro").lower()
        base = SITE_COORDS.get(site, DEFAULT_COORD)
        lat, lon = jitter(hid, base[0], base[1])
        hp = sorted(by_host_probs.get(hid, []), key=lambda x: -x["sev"])
        worst = hp[0]["sev"] if hp else -1
        m = metrics.get(hid, {})
        up = m.get("icmpping")
        loss = m.get("icmppingloss")
        lat_ms = m.get("icmppingsec")
        loss_f = round(float(loss), 1) if loss not in (None, "") else None
        latms_f = round(float(lat_ms) * 1000, 1) if lat_ms not in (None, "") else None
        up_i = int(float(up)) if up not in (None, "") else None

        if h["status"] == "1":
            state = "desconhecido"
        elif worst >= 4:
            state = "critico"
        elif worst >= 2:
            state = "problema"
        elif worst >= 1:
            state = "atencao"
        elif up_i == 0:
            state = "offline"
        else:
            state = "online"

        recs.append({
            "id": hid, "host": h["host"], "name": h["name"],
            "site": site, "sitelabel": base[2], "tipo": tipo,
            "lat": lat, "lon": lon, "state": state, "worst": worst,
            "probs": hp[:5], "nprobs": len(hp),
            "loss": loss_f, "latms": latms_f, "up": up_i,
        })
    return recs


# ---- HTML ---------------------------------------------------------------------
PAGE = """<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NOC Geomap — Capricornio Textil</title>
<style>__LEAFLET_CSS__</style>
<style>__MCLUSTER_CSS__</style>
<script>__LEAFLET_JS__</script>
<script>__MCLUSTER_JS__</script>
<style>
:root{--bg:#0f172a;--panel:#111827cc;--card:#1e293b;--ink:#e5e7eb;--muted:#94a3b8;--line:#334155;--brand:#b1271b;
--green:#22c55e;--amber:#f59e0b;--orange:#fb923c;--red:#ef4444;--dark:#991b1b;--grey:#64748b;--blue:#3b82f6;--purple:#a855f7;}
*{box-sizing:border-box}html,body{margin:0;height:100%}
body{background:var(--bg);color:var(--ink);font:13px/1.4 Segoe UI,Roboto,Arial,sans-serif;overflow:hidden;display:flex;flex-direction:column;height:100vh}
.top{display:flex;align-items:center;gap:12px;padding:8px 14px;background:#0b1220;border-bottom:1px solid var(--line)}
.top h1{font-size:15px;margin:0;font-weight:600}
.top .spacer{flex:1}
.btn{background:#1e293b;border:1px solid var(--line);color:var(--ink);border-radius:8px;padding:6px 12px;font-size:12px;cursor:pointer}
.btn:hover{background:#334155}
.kpis{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;padding:10px 14px;background:#0b1220;border-bottom:1px solid var(--line)}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px;display:flex;gap:10px;align-items:center}
.kpi .ic{width:36px;height:36px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:18px}
.kpi b{display:block;font-size:22px;line-height:1}.kpi span{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.03em}
.kpi small{color:var(--muted);font-size:11px}
.stage{position:relative;flex:1;min-height:0}
#map{position:absolute;inset:0;background:#0f172a}
.float{position:absolute;z-index:800;background:var(--panel);backdrop-filter:blur(6px);border:1px solid var(--line);border-radius:12px;box-shadow:0 8px 24px #0008}
.impacts{top:14px;right:14px;width:320px;padding:12px 14px;max-height:60%;overflow:auto}
.impacts h3{margin:0 0 10px;font-size:13px;display:flex;justify-content:space-between;align-items:center}
.imp{display:flex;gap:10px;align-items:center;padding:8px;border:1px solid var(--line);border-radius:10px;margin-bottom:8px;cursor:pointer}
.imp:hover{background:#1e293b}
.imp .rank{width:22px;height:22px;border-radius:6px;background:#334155;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:12px}
.imp .info{flex:1;min-width:0}.imp .info b{font-size:12px;display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.imp .info small{color:var(--muted);font-size:11px}
.imp .score{font-weight:700;color:var(--red)}
.legend{bottom:14px;left:14px;padding:12px 14px;font-size:12px}
.legend .row{display:flex;gap:14px;flex-wrap:wrap}
.legend .li{display:flex;align-items:center;gap:6px;color:var(--muted)}
.dot{width:11px;height:11px;border-radius:50%;display:inline-block}
.detail{top:14px;left:14px;width:300px;padding:14px;display:none}
.detail h3{margin:0 0 4px;font-size:14px}.detail .sub{color:var(--muted);font-size:11px;margin-bottom:10px}
.detail .mrow{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--line)}
.detail .mrow span{color:var(--muted)}
.badge{display:inline-block;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:600}
.pill{padding:2px 8px;border-radius:6px;font-size:11px;font-weight:600}
.warnbar{background:#78350f;color:#fed7aa;padding:6px 14px;font-size:12px;text-align:center;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.leaflet-container{background:#0f172a}
</style></head><body>
<div id="jserr" style="display:none;position:fixed;bottom:0;left:0;right:0;z-index:99999;background:#7f1d1d;color:#fff;padding:8px 14px;font:12px Consolas,monospace"></div>
<script>window.addEventListener('error',function(ev){var d=document.getElementById('jserr');if(!d)return;d.style.display='block';d.textContent='JS erro: '+(ev.message||ev.error)+'  ('+(ev.lineno||'?')+':'+(ev.colno||'?')+')';});</script>
<div class="warnbar">Equipamentos agrupados por site (Sao Paulo / Sao Carlos / Braganca Paulista) — clique no cluster para expandir. Posicao por cidade do site (nao GPS por equipamento). Dados capturados em __GERADO__.</div>
<div class="top">
  <span style="width:10px;height:10px;border-radius:50%;background:var(--brand);display:inline-block"></span>
  <h1>NOC Geomap — Capricornio Textil</h1>
  <span class="spacer"></span>
  <button class="btn" onclick="exportCSV()">Exportar CSV</button>
  <button class="btn" onclick="fitAll()">Ver tudo</button>
</div>
<div class="kpis" id="kpis"></div>
<div class="stage">
  <div id="map"></div>
  <div class="float impacts"><h3>Top Impactos Agora <span class="pill" style="background:#7f1d1d">ao vivo</span></h3><div id="impacts"></div></div>
  <div class="float detail" id="detail"></div>
  <div class="float legend">
    <div style="margin-bottom:8px;color:var(--muted)">Status</div>
    <div class="row" id="leg-status"></div>
    <div style="margin:10px 0 8px;color:var(--muted)">Tipos de equipamento</div>
    <div class="row" id="leg-tipo"></div>
  </div>
</div>
<script>
const DATA = __DATA__;
const STATE = {
  online:{c:'#22c55e',l:'Online'}, atencao:{c:'#f59e0b',l:'Atencao'},
  problema:{c:'#fb923c',l:'Problema'}, critico:{c:'#ef4444',l:'Critico'},
  offline:{c:'#991b1b',l:'Offline'}, desconhecido:{c:'#64748b',l:'Desconhecido'}
};
const TIPO = {switch:'🔀', ap:'📶', firewall:'🛡️', router:'🌐', server:'🖥️', proxy:'🧭', outro:'●'};

const map = L.map('map',{zoomControl:true,attributionControl:false}).setView([-24,-49],5);
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',{maxZoom:19}).addTo(map);

const markers=[];
function icon(d){
  const col=STATE[d.state].c, ring=d.state==='critico';
  const em=TIPO[d.tipo]||'●';
  const pulse = ring? `<span style="position:absolute;inset:-6px;border-radius:50%;border:2px solid ${col};animation:pz 1.4s infinite"></span>`:'';
  return L.divIcon({className:'',html:`<div style="position:relative">${pulse}
    <div style="width:26px;height:26px;border-radius:50%;background:${col};border:2px solid #0b1220;
    display:flex;align-items:center;justify-content:center;font-size:13px;box-shadow:0 2px 6px #000a">${em}</div></div>`,
    iconSize:[26,26],iconAnchor:[13,13]});
}
const ORDER=['online','desconhecido','atencao','problema','offline','critico'];
function worstOf(list){ let w='online'; list.forEach(d=>{ if(ORDER.indexOf(d.state)>ORDER.indexOf(w)) w=d.state; }); return w; }
const st=document.createElement('style');st.textContent='@keyframes pz{0%{transform:scale(.7);opacity:1}100%{transform:scale(1.9);opacity:0}}';document.head.appendChild(st);

// 1 marcador por site (agregado por cidade)
const SITES={};
DATA.forEach(d=>{ (SITES[d.site]=SITES[d.site]||{list:[]}).list.push(d); });
const siteMarkers=[];
Object.values(SITES).forEach(o=>{
  o.lat=o.list.reduce((a,d)=>a+d.lat,0)/o.list.length;
  o.lon=o.list.reduce((a,d)=>a+d.lon,0)/o.list.length;
  const w=worstOf(o.list), col=STATE[w].c;
  const nprob=o.list.filter(d=>d.state!=='online'&&d.state!=='desconhecido').length;
  const label=(o.list[0].sitelabel||'').split('/')[0];
  const ring=(w==='critico'||w==='offline')?`<span style="position:absolute;inset:-8px;border-radius:50%;border:2px solid ${col};animation:pz 1.4s infinite"></span>`:'';
  const hres=`<div style="position:relative;text-align:center">${ring}
    <div style="width:48px;height:48px;border-radius:50%;background:${col}ee;border:3px solid #0b1220;color:#0b1220;font-weight:800;font-size:17px;display:flex;align-items:center;justify-content:center;box-shadow:0 3px 10px #000b">${o.list.length}</div>
    <div style="margin-top:3px;font-size:11px;font-weight:700;color:#e5e7eb;text-shadow:0 1px 3px #000;white-space:nowrap">${label}</div></div>`;
  const m=L.marker([o.lat,o.lon],{icon:L.divIcon({className:'',html:hres,iconSize:[48,66],iconAnchor:[24,24]})}).addTo(map);
  m.on('click',()=>showSite(o));
  m.bindTooltip(`${label} — ${o.list.length} equip. · ${nprob} incidente(s)`,{direction:'top'});
  siteMarkers.push(m);
});
function fitAll(){ if(siteMarkers.length) map.fitBounds(L.featureGroup(siteMarkers).getBounds().pad(0.5)); }
fitAll();
// corrige o dimensionamento do mapa apos o layout flex assentar (tiles no tamanho certo)
setTimeout(()=>{ map.invalidateSize(); fitAll(); }, 250);
window.addEventListener('resize',()=>map.invalidateSize());

function showSite(o){
  const el=document.getElementById('detail'), w=worstOf(o.list), col=STATE[w].c;
  const label=(o.list[0].sitelabel||'').split('/')[0];
  const rows=[...o.list].sort((a,b)=>ORDER.indexOf(b.state)-ORDER.indexOf(a.state)).map(d=>`
    <div class="mrow" style="cursor:pointer" onclick='focusHost("${d.id}")'>
      <span><span class="dot" style="background:${STATE[d.state].c}"></span> ${d.host}</span>
      <b style="font-size:11px">${d.tipo}${d.nprobs?` · ${d.nprobs}!`:''}</b></div>`).join('');
  el.style.display='block';
  el.innerHTML=`<h3>${label} <span class="badge" style="background:${col}33;color:${col}">${o.list.length} equip.</span></h3>
   <div class="sub">Clique num equipamento para ver detalhes</div>
   <div style="max-height:54vh;overflow:auto">${rows}</div>
   <div style="text-align:right;margin-top:8px"><button class="btn" onclick="document.getElementById('detail').style.display='none'">Fechar</button></div>`;
}

// KPIs
const total=DATA.length, online=DATA.filter(d=>d.state==='online').length;
const crit=DATA.filter(d=>d.state==='critico'||d.state==='offline').length;
const sitesAf=[...new Set(DATA.filter(d=>['critico','problema','offline','atencao'].includes(d.state)).map(d=>d.site))];
const sites=[...new Set(DATA.map(d=>d.site))];
const health=Math.max(0,Math.round(100 - DATA.reduce((a,d)=>a+({critico:14,offline:14,problema:6,atencao:2,online:0,desconhecido:1}[d.state]||0),0)));
const kpis=[
 {ic:'🖥️',c:'#3b82f6',b:total,s:'Dispositivos',sm:online+' online'},
 {ic:'🚨',c:'#ef4444',b:crit,s:'Problemas',sm:'criticos'},
 {ic:'📍',c:'#f59e0b',b:sitesAf.length,s:'Sites afetados',sm:sitesAf.join(', ').toUpperCase()||'—'},
 {ic:'🗂️',c:'#3b82f6',b:sites.length,s:'Sites',sm:'monitorados'},
 {ic:'❤️',c:'#a855f7',b:health+'/100',s:'Operational Health',sm:health>85?'saudavel':(health>60?'degradada':'critica')},
 {ic:'🔗',c:'#22c55e',b:correl(),s:'Correlacoes',sm:'incidentes ligados'}
];
document.getElementById('kpis').innerHTML=kpis.map(k=>`<div class="kpi">
 <div class="ic" style="background:${k.c}22;color:${k.c}">${k.ic}</div>
 <div><b>${k.b}</b><span>${k.s}</span><br><small>${k.sm}</small></div></div>`).join('');

function correl(){ // sites com switch em problema + colaterais
  let n=0;
  sites.forEach(s=>{ const sw=DATA.some(d=>d.site===s&&d.tipo==='switch'&&['critico','offline'].includes(d.state));
    const col=DATA.filter(d=>d.site===s&&d.tipo!=='switch'&&['critico','offline'].includes(d.state)).length;
    if(sw&&col) n++; }); return n;
}

// Top impactos
function score(d){ return ({critico:100,offline:95,problema:50,atencao:20,online:0,desconhecido:5}[d.state]||0)
  + (d.loss||0)*0.4 + Math.min((d.latms||0)/10,20); }
const topList=[...DATA].filter(d=>score(d)>0).sort((a,b)=>score(b)-score(a)).slice(0,8);
document.getElementById('impacts').innerHTML = topList.map((d,i)=>`
 <div class="imp" onclick='focusHost("${d.id}")'>
   <div class="rank">${i+1}</div>
   <div class="info"><b>${d.host}</b><small>${d.nprobs} incidente(s)${d.loss!=null?` · Loss ${d.loss}%`:''}${d.latms!=null?` · ${d.latms} ms`:''}</small></div>
   <div class="score">${Math.round(score(d))}</div>
 </div>`).join('') || '<div style="color:var(--muted)">Sem impactos no momento 🎉</div>';

// legendas
document.getElementById('leg-status').innerHTML=Object.values(STATE).map(s=>`<span class="li"><span class="dot" style="background:${s.c}"></span>${s.l}</span>`).join('');
document.getElementById('leg-tipo').innerHTML=Object.entries(TIPO).map(([k,v])=>`<span class="li">${v} ${k}</span>`).join('');

// detalhe
function showDetail(d){
  const el=document.getElementById('detail');
  const probs=d.probs.map(p=>`<div class="mrow"><span>Sev ${p.sev}</span><b style="font-size:11px">${p.name}</b></div>`).join('')||'<div class="mrow"><span>Sem incidentes</span><b>OK</b></div>';
  el.style.display='block';
  el.innerHTML=`<h3>${d.host} <span class="badge" style="background:${STATE[d.state].c}33;color:${STATE[d.state].c}">${STATE[d.state].l}</span></h3>
   <div class="sub">${d.name} · ${d.tipo} · ${d.sitelabel}</div>
   <div class="mrow"><span>Disponibilidade (ICMP)</span><b>${d.up==null?'—':(d.up?'UP':'DOWN')}</b></div>
   <div class="mrow"><span>Perda ICMP</span><b>${d.loss==null?'—':d.loss+'%'}</b></div>
   <div class="mrow"><span>Latencia</span><b>${d.latms==null?'—':d.latms+' ms'}</b></div>
   <div class="mrow"><span>Incidentes ativos</span><b>${d.nprobs}</b></div>
   ${probs}
   <div style="text-align:right;margin-top:8px"><button class="btn" onclick="document.getElementById('detail').style.display='none'">Fechar</button></div>`;
}
function focusHost(id){ const d=DATA.find(x=>x.id===id); if(!d)return; map.setView([d.lat,d.lon],13); showDetail(d); }

function exportCSV(){
  const rows=[['Host','Nome','Tipo','Site','Estado','Incidentes','Loss(%)','Latencia(ms)','UP']];
  DATA.forEach(d=>rows.push([d.host,d.name,d.tipo,d.site,d.state,d.nprobs,d.loss??'',d.latms??'',d.up??'']));
  const csv=rows.map(r=>r.map(c=>`"${String(c).replace(/"/g,'""')}"`).join(';')).join('\\n');
  const a=document.createElement('a');a.href='data:text/csv;charset=utf-8,\\uFEFF'+encodeURIComponent(csv);
  a.download='noc-geomap.csv';a.click();
}
</script></body></html>"""


def main():
    print("Coletando dados do Zabbix ...")
    recs = collect()
    print(f"  {len(recs)} hosts.")
    now = dt.datetime.now().strftime("%d/%m/%Y %H:%M")
    vend = ROOT / "automacao" / "vendor" / "leaflet"
    lcss = (vend / "leaflet.css").read_text(encoding="utf-8")
    ljs = (vend / "leaflet.js").read_text(encoding="utf-8")
    mcss = ((vend / "MarkerCluster.css").read_text(encoding="utf-8") + "\n"
            + (vend / "MarkerCluster.Default.css").read_text(encoding="utf-8"))
    mjs = (vend / "markercluster.js").read_text(encoding="utf-8")
    doc = (PAGE.replace("__LEAFLET_CSS__", lcss)
               .replace("__MCLUSTER_CSS__", mcss)
               .replace("__LEAFLET_JS__", ljs)
               .replace("__MCLUSTER_JS__", mjs)
               .replace("__DATA__", json.dumps(recs, ensure_ascii=False))
               .replace("__GERADO__", html.escape(now)))
    out = ROOT / "noc-geomap.html"
    out.write_text(doc, encoding="utf-8")
    print(f"Gerado: {out}")


if __name__ == "__main__":
    main()
