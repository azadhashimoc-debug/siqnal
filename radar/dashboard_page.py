PAGE = r"""<!doctype html>
<html lang="az"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fürsət Radarı</title>
<style>
:root{--bg:#f6f7f9;--card:#fff;--fg:#1b1f24;--mut:#667085;--line:#e4e7ec;--acc:#2563eb;--acc2:#93c5fd;--ok:#16a34a;--warn:#d97706;--bad:#dc2626;--chip:#eef2ff}
@media(prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#0f1216;--card:#181c22;--fg:#e6e8eb;--mut:#98a2b3;--line:#2a3039;--acc:#60a5fa;--acc2:#1e3a8a;--ok:#4ade80;--warn:#fbbf24;--bad:#f87171;--chip:#1f2937}}
:root[data-theme=dark]{--bg:#0f1216;--card:#181c22;--fg:#e6e8eb;--mut:#98a2b3;--line:#2a3039;--acc:#60a5fa;--acc2:#1e3a8a;--ok:#4ade80;--warn:#fbbf24;--bad:#f87171;--chip:#1f2937}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif}
header{display:flex;gap:6px;flex-wrap:wrap;align-items:center;padding:10px 16px;background:var(--card);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5}
header h1{font-size:17px;margin:0 10px 0 0;white-space:nowrap}
nav{display:flex;gap:2px;flex-wrap:wrap}
nav a{color:var(--mut);padding:7px 11px;border-radius:8px;text-decoration:none}
nav a.on{background:var(--acc);color:#fff}
main{max-width:1150px;margin:0 auto;padding:16px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:16px}
.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px;margin-bottom:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px;min-width:0}
.card h3{margin:0 0 10px;font-size:14px;color:var(--mut);font-weight:600}
.stat b{display:block;font-size:24px}.stat span,.mut{color:var(--mut);font-size:13px}
.stat.link{cursor:pointer}.stat.link:hover{border-color:var(--acc)}
.bar{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px;align-items:center}
input,select,textarea{background:var(--card);color:var(--fg);border:1px solid var(--line);border-radius:8px;padding:7px 10px;font:inherit;min-width:0}
textarea{width:100%;min-height:80px;resize:vertical}
input[type=search]{flex:1;min-width:160px}
table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:8px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--mut);font-weight:500;font-size:13px;white-space:nowrap}tr.click{cursor:pointer}tr.click:hover{background:color-mix(in srgb,var(--acc) 7%,transparent)}
.tag{display:inline-block;padding:0 8px;border-radius:99px;font-size:12px;border:1px solid currentColor;white-space:nowrap}
.gec,.basladim{color:var(--ok)}.izle,.arasdirilir{color:var(--warn)}.reddet,.imtina{color:var(--bad)}.baxildi{color:var(--acc)}.yeni{color:var(--mut)}
.chip{display:inline-block;background:var(--chip);border-radius:6px;padding:0 6px;font-size:12px;color:var(--mut)}
.btn{background:var(--acc);color:#fff;border:0;border-radius:8px;padding:7px 13px;cursor:pointer;font:inherit;text-decoration:none;display:inline-block}
.btn.alt{background:none;color:var(--fg);border:1px solid var(--line)}.btn:disabled{opacity:.5;cursor:default}
.btn.sm{padding:3px 9px;font-size:13px}
h2{font-size:16px;margin:18px 0 6px}ul{padding-left:20px;margin:4px 0}a{color:var(--acc)}
.dim{display:grid;grid-template-columns:120px 1fr 32px;gap:8px;align-items:center;margin:4px 0}
.meter{height:8px;background:var(--line);border-radius:4px;overflow:hidden}.meter i{display:block;height:100%;background:var(--acc)}
.hbar{display:grid;grid-template-columns:160px 1fr 50px;gap:8px;align-items:center;margin:5px 0;font-size:13px}
.spark{display:block}
#login{max-width:340px;margin:80px auto}
.msg{padding:10px 14px;border-radius:8px;background:color-mix(in srgb,var(--warn) 15%,transparent);margin-bottom:12px}
.ok-msg{background:color-mix(in srgb,var(--ok) 15%,transparent)}
.scroll{overflow-x:auto}.right{text-align:right}.nowrap{white-space:nowrap}
.legend{display:flex;gap:14px;font-size:12px;color:var(--mut);margin-top:6px}.legend i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:4px;vertical-align:-1px}
#toast{position:fixed;bottom:16px;left:50%;transform:translateX(-50%);background:var(--fg);color:var(--bg);padding:9px 16px;border-radius:8px;font-size:14px;opacity:0;transition:opacity .2s;pointer-events:none;z-index:9;max-width:90vw}
#toast.show{opacity:1}
.tip{position:fixed;pointer-events:none;background:var(--fg);color:var(--bg);font-size:12px;padding:3px 7px;border-radius:5px;z-index:9;display:none}
.kbd{font:12px monospace;border:1px solid var(--line);border-radius:4px;padding:0 4px;color:var(--mut)}
@media(max-width:640px){.hide-sm{display:none}.dim{grid-template-columns:90px 1fr 28px}.hbar{grid-template-columns:110px 1fr 40px}}
</style></head><body>
<div id="login" class="card" hidden>
  <h2 style="margin-top:0">Daxil ol</h2>
  <p class="mut">DASHBOARD_TOKEN dəyərini yaz.</p>
  <input id="tok" type="password" style="width:100%;margin-bottom:10px" autocomplete="current-password">
  <button class="btn" id="go">Daxil ol</button><p id="lerr" class="mut"></p>
</div>
<div id="app" hidden>
<header><h1>📡 Fürsət Radarı</h1><nav id="nav"></nav><span style="flex:1"></span>
<button class="btn alt sm" id="theme" title="Tema">◐</button>
<button class="btn alt sm" id="out">Çıxış</button></header>
<main id="view"></main></div>
<div id="toast"></div><div class="tip" id="tip"></div>
<script>
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const safeUrl=u=>/^https?:\/\//i.test(u||"")?esc(u):"#";
const ext=(u,t)=>`<a href="${safeUrl(u)}" target="_blank" rel="noopener noreferrer">${t}</a>`;
const store={get:k=>{try{return localStorage.getItem(k)}catch(e){return null}},set:(k,v)=>{try{v==null?localStorage.removeItem(k):localStorage.setItem(k,v)}catch(e){}}};
let token=store.get("radar_tok")||"",META=null;
const ST={yeni:"Yeni",baxildi:"Baxıldı",arasdirilir:"Araşdırılır",basladim:"Başladım",imtina:"İmtina"};
const CAT={PROBLEM_SIKAYET:"Problem/şikayət",REGULYASIYA_QANUN:"Qanun/qayda",BIZNES_TREND:"Biznes trend",GUVEN_DELEDUZLUQ:"Güvən/dələduzluq",BILGI_BOSLUGU:"Bilgi boşluğu"};
const DIMS=[["demand","Tələb"],["competition","Rəqabət"],["willingness_to_pay","Ödəmə gücü"],["timing","Vaxtlama"]];
const TABS=[["overview","Ümumi"],["ideas","İdeyalar"],["topics","Trendlər"],["sources","Mənbələr"],["search","Axtarış"]];
const theme=store.get("radar_theme");if(theme)document.documentElement.dataset.theme=theme;
$("#theme").onclick=()=>{const cur=document.documentElement.dataset.theme||(matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light");
  const n=cur==="dark"?"light":"dark";document.documentElement.dataset.theme=n;store.set("radar_theme",n)};
function toast(m){const t=$("#toast");t.textContent=m;t.classList.add("show");clearTimeout(toast.t);toast.t=setTimeout(()=>t.classList.remove("show"),3200)}
async function api(path,opts={}){
  const r=await fetch(path,{...opts,headers:{"X-Token":token,...(opts.body?{"Content-Type":"application/json"}:{})}});
  if(r.status===401){showLogin("Token yanlışdır");throw new Error("401")}
  if(!r.ok){let m=r.statusText;try{m=(await r.json()).detail||m}catch(e){}throw new Error(m)}
  const ct=r.headers.get("content-type")||"";return ct.includes("json")?r.json():r;
}
async function download(path){const r=await api(path);const b=await r.blob();
  const name=(r.headers.get("content-disposition")||"").match(/filename="([^"]+)"/)?.[1]||"fayl";
  const a=document.createElement("a");a.href=URL.createObjectURL(b);a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}
function showLogin(err){$("#app").hidden=true;$("#login").hidden=false;$("#lerr").textContent=err||"";$("#tok").focus()}
$("#go").onclick=async()=>{token=$("#tok").value;try{await api("/api/meta");store.set("radar_tok",token);start()}catch(e){if(e.message!=="401")$("#lerr").textContent=e.message}};
$("#tok").onkeydown=e=>{if(e.key==="Enter")$("#go").click()};
$("#out").onclick=()=>{token="";store.set("radar_tok",null);showLogin("")};
// ---- routing: #/ideas?q=..  #/idea/5  #/topic/3 ----
function parseHash(){const h=location.hash.replace(/^#\/?/,"");const [path,qs]=h.split("?");const parts=(path||"overview").split("/");
  return {name:parts[0]||"overview",id:parts[1],params:new URLSearchParams(qs||"")}}
const link=(name,id,params)=>"#/"+name+(id!=null?"/"+id:"")+(params&&String(params)?"?"+params:"");
function setParams(p){const r=parseHash();history.replaceState(null,"",link(r.name,r.id,p))}
function nav(active){$("#nav").innerHTML=TABS.map(([k,l])=>`<a href="#/${k}" class="${k===active?"on":""}">${l}</a>`).join("")}
const view=h=>{$("#view").innerHTML=h};
const errBox=e=>view(`<div class="msg">${esc(e.message)}</div>`);
async function route(){const r=parseHash();const tabOf={idea:"ideas",topic:"topics"};nav(tabOf[r.name]||r.name);
  const fn={overview,ideas,topics,sources,search,idea:detail,topic:topicDetail}[r.name]||overview;
  try{await fn(r)}catch(e){if(e.message!=="401")errBox(e)}window.scrollTo(0,0)}
window.addEventListener("hashchange",route);
async function start(){$("#login").hidden=true;$("#app").hidden=false;try{META=await api("/api/meta")}catch(e){META={sources:[],categories:Object.keys(CAT),statuses:Object.keys(ST)}}route()}
// ---- widgets ----
const tag=(d,label)=>`<span class="tag ${esc(d)}">${esc(label||d||"?")}</span>`;
const stTag=s=>tag(s,ST[s]||s);
const day=s=>esc((s||"").slice(0,10));
const opts=(arr,sel,labels={})=>arr.map(v=>`<option value="${esc(v)}" ${v===sel?"selected":""}>${esc(labels[v]||v)}</option>`).join("");
function ago(s){if(!s)return"—";const t=Date.parse(s.replace(" ","T")+(s.includes("Z")||s.includes("+")?"":"Z"));if(isNaN(t))return esc(s);
  const m=Math.round((Date.now()-t)/60000);return m<1?"indicə":m<60?m+" dəq əvvəl":m<1440?Math.round(m/60)+" saat əvvəl":Math.round(m/1440)+" gün əvvəl"}
function spark(s,w=90,h=24){const m=Math.max(1,...s);
  const p=s.map((v,i)=>`${(i*(w/(s.length-1||1))).toFixed(1)},${(h-2-(v/m)*(h-4)).toFixed(1)}`).join(" ");
  return `<svg class="spark" width="${w}" height="${h}" role="img" aria-label="trend"><polyline points="${p}" fill="none" stroke="var(--acc)" stroke-width="1.5"/></svg>`}
function bars(data,keys,colors,h=150){// data: [{day, k1, k2}] stacked columns, hover tooltip
  const w=Math.max(300,data.length*14),bw=w/data.length,max=Math.max(1,...data.map(d=>keys.reduce((a,k)=>a+(d[k]||0),0)));
  let out="";data.forEach((d,i)=>{let y=h-16;const tip=`${d.day}: `+keys.map(k=>`${k} ${d[k]||0}`).join(", ");
    keys.forEach((k,j)=>{const bh=((d[k]||0)/max)*(h-24);y-=bh;out+=`<rect x="${(i*bw+1).toFixed(1)}" y="${y.toFixed(1)}" width="${(bw-2).toFixed(1)}" height="${bh.toFixed(1)}" fill="${colors[j]}" data-tip="${esc(tip)}"/>`});
    out+=`<rect x="${(i*bw).toFixed(1)}" y="0" width="${bw.toFixed(1)}" height="${h-16}" fill="transparent" data-tip="${esc(tip)}"/>`;
    if(i%7===0||(i===data.length-1&&i%7>3))out+=`<text x="${(i*bw+bw/2).toFixed(1)}" y="${h-3}" font-size="10" fill="var(--mut)" text-anchor="middle">${esc(d.day.slice(5))}</text>`});
  return `<svg viewBox="0 0 ${w} ${h}" width="100%" height="${h}" preserveAspectRatio="none">${out}</svg>`}
function hbars(rows,label,val,extra){const m=Math.max(1,...rows.map(val));
  return rows.map(r=>`<div class="hbar"><span>${label(r)}</span><div class="meter"><i style="width:${(val(r)/m*100).toFixed(0)}%"></i></div><span class="right">${val(r)}${extra?extra(r):""}</span></div>`).join("")||`<p class="mut">Məlumat yoxdur.</p>`}
document.addEventListener("mousemove",e=>{const t=e.target.closest?.("[data-tip]"),tip=$("#tip");
  if(!t){tip.style.display="none";return}tip.textContent=t.dataset.tip;tip.style.display="block";tip.style.left=Math.min(e.clientX+12,innerWidth-220)+"px";tip.style.top=(e.clientY+14)+"px"});
// ---- pages ----
async function overview(){
  const o=await api("/api/overview"),d=o.decisions;
  const S=(n,l,href)=>`<div class="card stat ${href?"link":""}" ${href?`data-href="${href}"`:""}><b>${esc(n)}</b><span>${l}</span></div>`;
  const run=o.running_since?`<span class="tag izle">iş gedir · ${ago(new Date(o.running_since*1000).toISOString())}</span>`:"";
  const lc=o.last_collect,lw=o.last_weekly;
  const lcRes=lc&&lc.result?Object.entries(lc.result).map(([k,v])=>`${esc(k)}: ${esc(v)}`).join(", "):"";
  view(`<div class="card" style="margin-bottom:16px"><div class="bar" style="margin:0">
      <div style="flex:1;min-width:220px"><b>Son toplama:</b> ${lc?ago(lc.at):"—"} <span class="mut">${lcRes}</span><br>
      <b>Son həftəlik hesabat:</b> ${lw?ago(lw.at)+` <span class="mut">(${esc(lw.validated)} yoxlandı, ${esc(lw.sent)} göndərildi)</span>`:"—"}
      ${o.pending_actions?`<br><span class="mut">${o.pending_actions} gözləyən əməliyyat (səs/status) növbəti işləmədə yazılacaq</span>`:""}</div>
      ${run}${o.can_trigger?`<button class="btn" id="runc" ${o.running_since?"disabled":""}>↻ İndi topla</button>
      <button class="btn alt" id="runw" ${o.running_since?"disabled":""}>Həftəlik hesabatı indi işlət</button>`:""}</div></div>
    <div class="grid">${S(o.records,"Ümumi qeyd","#/search")}${S(o.records_7d,"Son 7 gündə əlavə olunub","#/search")}
    ${S(o.classified,"Siqnal (təsnif olunmuş)","#/search")}${S(o.unclassified,"Təsnif olunmamış","#/search?category=_none")}
    ${S(o.topics,"Mövzu","#/topics")}${S(o.candidates,"Namizəd trend","#/topics?candidates=1")}
    ${S((d.gec||0)+" / "+(d.izle||0)+" / "+(d.reddet||0),"Keç / İzlə / Rədd","#/ideas")}
    ${S(o.validations_7d+" / "+o.max_validations_per_week,"Həftəlik yoxlama limiti")}
    ${S(o.apify_runs_7d+" / "+o.max_apify_runs_per_week,"Apify limiti (həftə)")}</div>
    <div class="two"><div class="card"><h3>Gündəlik qeydlər (30 gün)</h3>${bars(o.daily,["news","comment"],["var(--acc)","var(--acc2)"])}
      <div class="legend"><span><i style="background:var(--acc)"></i>xəbər</span><span><i style="background:var(--acc2)"></i>şərh</span></div></div>
    <div class="card"><h3>Siqnal kateqoriyaları (30 gün)</h3>${hbars(o.categories,r=>`<a href="#/search?category=${esc(r.category)}">${esc(CAT[r.category]||r.category)}</a>`,r=>r.n,r=>`<span class="mut"> ·${r.avg??"—"}</span>`)}</div></div>
    <div class="two"><div class="card"><h3>Ən yaxşı ideyalar</h3>${o.top_ideas.length?`<table>${o.top_ideas.map(r=>`<tr class="click" data-href="#/idea/${r.id}"><td>${esc(r.problem)}<br><span class="mut">${esc(r.idea)}</span></td><td>${stTag(r.status)}</td><td class="right"><b>${r.score}</b></td></tr>`).join("")}</table>`:`<p class="mut">Hələ "gec" qərarlı ideya yoxdur.</p>`}</div>
    <div class="card"><h3>Ən aktiv mövzular (son 7 gün)</h3>${o.top_topics.length?`<table>${o.top_topics.map(r=>`<tr class="click" data-href="#/topic/${r.id}"><td>${esc(r.name)}</td><td>${spark(r.series,80,22)}</td><td class="right">${r.recent}</td></tr>`).join("")}</table>`:`<p class="mut">Mövzu yoxdur.</p>`}
    ${Object.keys(o.statuses).length?`<h3 style="margin-top:14px">İdeya statusları</h3>`+Object.entries(o.statuses).map(([k,v])=>`<a href="#/ideas?status=${esc(k)}">${stTag(k)}</a> ${v}`).join(" &nbsp; "):""}</div></div>`);
  $$("[data-href]").forEach(e=>e.onclick=ev=>{if(ev.target.closest("a"))return;location.hash=e.dataset.href});
  const trig=async(job,confirmMsg)=>{if(confirmMsg&&!confirm(confirmMsg))return;try{const x=await api("/api/run/"+job,{method:"POST"});toast(x.note);setTimeout(route,1500)}catch(e){toast(e.message)}};
  if($("#runc"))$("#runc").onclick=()=>trig("collect");
  if($("#runw"))$("#runw").onclick=()=>trig("weekly","Həftəlik yoxlama Claude API-yə pul xərcləyir və Telegram-a hesabat göndərir. Davam edək?");
}
async function ideas({params}){
  const P=k=>params.get(k)||"";
  view(`<div class="bar"><input type="search" id="q" placeholder="Problem, ideya, qeyd üzrə axtar…" value="${esc(P("q"))}">
    <select id="decision"><option value="">Qərar: hamısı</option>${opts(["gec","izle","reddet"],P("decision"))}</select>
    <select id="status"><option value="">Status: hamısı</option>${opts(Object.keys(ST),P("status"),ST)}</select>
    <select id="cost"><option value="">Xərc: hamısı</option>${opts(["az","orta","yuksek"],P("cost"))}</select>
    <select id="min_score"><option value="0">Min skor</option>${opts(["5","6","7","8"],P("min_score"),{5:"≥ 5",6:"≥ 6",7:"≥ 7",8:"≥ 8"})}</select>
    <select id="sort">${opts(["score","demand","votes","date"],P("sort")||"score",{score:"Skora görə",demand:"Tələbə görə",votes:"Səsə görə",date:"Ən yeni"})}</select>
    <button class="btn alt" id="csv">⬇ CSV</button></div><div class="mut" id="cnt"></div><div class="card scroll" id="list"></div>`);
  const ids=["q","decision","status","cost","min_score","sort"];
  const cur=()=>{const p=new URLSearchParams();ids.forEach(i=>{const v=$("#"+i).value;if(v&&v!=="0")p.set(i,v)});return p};
  const load=async()=>{const p=cur();setParams(p);const rows=await api("/api/ideas?"+p);
    $("#cnt").textContent=rows.length+" ideya";
    $("#list").innerHTML=rows.length?`<table><tr><th>Problem / ideya</th><th>Qərar</th><th>Status</th><th class="right">Skor</th><th class="hide-sm">T / R / Ö / V</th><th class="hide-sm">Xərc</th><th class="right">Səs</th><th class="hide-sm">Tarix</th></tr>`+
      rows.map(r=>`<tr class="click" data-id="${r.id}"><td><b>${esc(r.problem)}</b><br><span class="mut">${esc(r.idea)}</span>${r.note?`<br><span class="chip">📝 ${esc(r.note.slice(0,80))}</span>`:""}</td>
      <td>${tag(r.decision)}</td><td>${stTag(r.status)}${r.pending?` <span class="mut" title="növbədə">⏳</span>`:""}</td><td class="right"><b>${r.score}</b></td>
      <td class="hide-sm nowrap mut">${DIMS.map(([k])=>r.dims[k]??"–").join(" / ")}</td><td class="hide-sm">${esc(r.costs.join(", ")||"—")}</td>
      <td class="right">${r.votes>0?"+":""}${r.votes}${r.pending_vote?(r.pending_vote==="up"?" ⏳👍":" ⏳👎"):""}</td><td class="mut hide-sm nowrap">${day(r.created_at)}</td></tr>`).join("")+`</table>`
      :`<p class="mut">Bu filtrlərə uyğun ideya yoxdur. Yoxlama agenti bazar ertəsi işləyir.</p>`;
    $$("#list tr.click").forEach(tr=>tr.onclick=()=>location.hash="#/idea/"+tr.dataset.id)};
  let t;$("#q").oninput=()=>{clearTimeout(t);t=setTimeout(()=>load().catch(errBox),250)};
  ids.slice(1).forEach(i=>$("#"+i).onchange=()=>load().catch(errBox));
  $("#csv").onclick=()=>download("/api/ideas.csv?"+cur()).catch(e=>toast(e.message));
  await load();
}
async function detail({id}){
  const r=await api("/api/ideas/"+id),d=r.data||{};
  const claims=x=>(x.claims||[]).map(c=>`<li>${esc(c.text)} ${ext(c.url,"mənbə")}</li>`).join("");
  const sols=(d.solutions||[]).map((s,i)=>`<div class="card" style="margin:8px 0"><b>${i+1}. ${esc(s.title)}</b> ${tag(s.start_cost)} <span class="mut">çətinlik ${esc(s.difficulty)}/5${s.start_cost_text?" · "+esc(s.start_cost_text):""}</span>
    <ul><li>Necə işləyir: ${esc(s.how_it_works)}</li><li>Gəlir modeli: ${esc(s.business_model)}</li><li><b>İlk addım:</b> ${esc(s.first_step)}</li>
    <li>Rəqiblər: ${(s.competitor_urls||[]).map(u=>ext(u,esc(u))).join(", ")||"—"}</li></ul></div>`).join("");
  view(`<div class="bar"><a class="btn alt" href="#/ideas">← Siyahı</a>
    ${r.prev_id?`<a class="btn alt" href="#/idea/${r.prev_id}" title="Əvvəlki (←)">‹</a>`:""}${r.next_id?`<a class="btn alt" href="#/idea/${r.next_id}" title="Növbəti (→)">›</a>`:""}
    <span style="flex:1"></span><button class="btn alt" id="md">⬇ Markdown</button><button class="btn alt" id="copy">Linki kopyala</button></div>
    <div class="two" style="grid-template-columns:minmax(0,2fr) minmax(260px,1fr)">
    <div class="card"><h2 style="margin-top:0">${esc(d.problem)} ${tag(r.decision)}</h2>
    <div class="mut">Ümumi skor: <b>${r.score}</b> · ${day(r.created_at)} · mövzu: <a href="#/topic/${r.topic_id}">${esc(r.topic||r.topic_id)}</a></div>
    <ul>${(d.sub_pains||[]).map(p=>`<li>${esc(p)}</li>`).join("")}</ul>
    ${DIMS.map(([k,l])=>`<div class="dim"><span>${l}</span><div class="meter"><i style="width:${(d[k]?.score||0)*10}%"></i></div><b>${d[k]?.score??"—"}</b></div><ul>${claims(d[k]||{})}</ul>`).join("")}
    ${d.market_size?.estimate?`<p>Bazar ölçüsü: ${esc(d.market_size.estimate)} ${d.market_size.url?ext(d.market_size.url,"mənbə"):""}</p>`:""}
    <h2>Həll yolları</h2>${sols||"<p class='mut'>—</p>"}
    <h2>Risklər</h2><ul>${(d.risks||[]).map(x=>`<li>${esc(x)}</li>`).join("")||"<li class='mut'>—</li>"}</ul>
    ${(d.unverified_claims||[]).length?`<h2>Doğrulanmadı</h2><ul>${d.unverified_claims.map(x=>`<li>${esc(x)}</li>`).join("")}</ul>`:""}
    <h2>Kanıtlar (${r.evidence.length})</h2><ul>${r.evidence.map(e=>`<li>${esc(e.text)} <span class="mut">${day(e.at)}</span> ${ext(e.url,esc(e.source))}</li>`).join("")}</ul></div>
    <div><div class="card" style="margin-bottom:16px"><h3>Status və qeyd</h3>
      <select id="st" style="width:100%;margin-bottom:8px">${opts(Object.keys(ST),r.status,ST)}</select>
      <textarea id="note" placeholder="Öz qeydin: kimlə danışdın, nə öyrəndin, növbəti addım…">${esc(r.note)}</textarea>
      <div class="bar" style="margin:8px 0 0"><button class="btn" id="save">Yadda saxla</button><span class="mut" id="stn">${r.status_pending?"⏳ növbədə":r.status_updated?"yeniləndi: "+day(r.status_updated):""}</span></div></div>
    <div class="card" style="margin-bottom:16px"><h3>Səs: ${r.vote_sum>0?"+":""}${r.vote_sum} <span class="mut">(${r.votes.length} nəfər)</span></h3>
      <button class="btn ${r.pending_vote==="up"?"":"alt"}" id="up">👍 Bəli</button> <button class="btn ${r.pending_vote==="down"?"":"alt"}" id="down">👎 Xeyr</button>
      <p class="mut" id="vn">${r.pending_vote?"⏳ Sənin səsin növbədədir":"Səslər növbəti yoxlamada agentə nümunə kimi verilir."}</p></div>
    ${r.history.length?`<div class="card"><h3>Bu mövzunun əvvəlki yoxlamaları</h3>${r.history.map(h=>`<div><a href="#/idea/${h.id}">#${h.id}</a> ${tag(h.decision)} skor ${h.score} <span class="mut">${day(h.created_at)}</span></div>`).join("")}</div>`:""}
    </div></div><p class="mut">Klaviatura: <span class="kbd">←</span> <span class="kbd">→</span> ideyalar arası keçid.</p>`);
  for(const k of ["up","down"])$("#"+k).onclick=async()=>{try{const x=await api(`/api/ideas/${id}/vote/${k}`,{method:"POST"});toast(x.note);route()}catch(e){toast(e.message)}};
  $("#save").onclick=async()=>{try{await api(`/api/ideas/${id}/status`,{method:"POST",body:JSON.stringify({status:$("#st").value,note:$("#note").value})});
    $("#stn").textContent="⏳ növbədə";toast("Yadda saxlandı. Növbəti işləmədə bazaya yazılacaq.")}catch(e){toast(e.message)}};
  $("#md").onclick=()=>download(`/api/ideas/${id}/report.md`).catch(e=>toast(e.message));
  $("#copy").onclick=()=>{navigator.clipboard?.writeText(location.href).then(()=>toast("Link kopyalandı"),()=>toast(location.href))};
  document.onkeydown=e=>{if(parseHash().name!=="idea"||/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName))return;
    if(e.key==="ArrowLeft"&&r.prev_id)location.hash="#/idea/"+r.prev_id;if(e.key==="ArrowRight"&&r.next_id)location.hash="#/idea/"+r.next_id};
}
async function topics({params}){
  view(`<div class="bar"><input type="search" id="q" placeholder="Mövzu axtar…" value="${esc(params.get("q")||"")}">
    <label class="mut"><input type="checkbox" id="cand" ${params.get("candidates")?"checked":""}> yalnız namizədlər</label></div><div class="card scroll" id="list"></div>`);
  const load=async()=>{const p=new URLSearchParams();if($("#q").value)p.set("q",$("#q").value);if($("#cand").checked)p.set("candidates","1");setParams(p);
    const rows=await api("/api/topics?"+p);
    $("#list").innerHTML=rows.length?`<table><tr><th>Mövzu</th><th>14 gün</th><th class="right">Son 7</th><th class="right hide-sm">Əvvəlki 7</th><th class="right">Artım</th><th class="right hide-sm">Cəmi</th><th></th></tr>`+
    rows.map(r=>`<tr class="click" data-id="${r.id}"><td>${esc(r.name)}${r.candidate_at?` <span class="tag gec">namizəd</span>`:""}</td><td>${spark(r.series)}</td><td class="right">${r.recent}</td><td class="right hide-sm">${r.prev}</td>
    <td class="right">${r.growth==null?(r.recent?`<span class="tag gec">yeni</span>`:"—"):`<span class="${r.growth>=2?"gec":r.growth<1?"reddet":""}">×${r.growth}</span>`}</td><td class="right hide-sm">${r.total}</td>
    <td>${r.validation_id?`<a href="#/idea/${r.validation_id}">hesabat</a>`:""}</td></tr>`).join("")+`</table>`:`<p class="mut">Mövzu tapılmadı.</p>`;
    $$("#list tr.click").forEach(tr=>tr.onclick=e=>{if(!e.target.closest("a"))location.hash="#/topic/"+tr.dataset.id})};
  let t;$("#q").oninput=()=>{clearTimeout(t);t=setTimeout(()=>load().catch(errBox),250)};$("#cand").onchange=()=>load().catch(errBox);await load();
}
async function topicDetail({id}){
  const t=await api("/api/topics/"+id);
  view(`<div class="bar"><a class="btn alt" href="#/topics">← Trendlər</a></div>
    <div class="card" style="margin-bottom:16px"><h2 style="margin-top:0">${esc(t.name)} ${t.candidate_at?`<span class="tag gec">namizəd · ${day(t.candidate_at)}</span>`:""}</h2>
    ${t.summary?`<p>${esc(t.summary)}</p>`:""}<h3>Gündəlik siqnallar (30 gün)</h3>${bars(t.series,["count"],["var(--acc)"],120)}</div>
    <div class="two"><div class="card"><h3>Mənbələr</h3>${hbars(t.sources,r=>esc(r.source),r=>r.n)}</div>
    <div class="card"><h3>Yoxlamalar</h3>${t.validations.length?t.validations.map(v=>`<div><a href="#/idea/${v.id}">#${v.id}</a> ${tag(v.decision)} skor <b>${v.score}</b> <span class="mut">${day(v.created_at)}</span></div>`).join(""):`<p class="mut">Bu mövzu hələ yoxlanmayıb.</p>`}</div></div>
    <div class="card scroll"><h3>Qeydlər (${t.records.length})</h3><table>${t.records.map(r=>`<tr><td>${esc(r.text)} ${ext(r.url,"↗")}</td><td class="nowrap">${esc(r.source)}<br><span class="mut">${esc(r.kind)}</span></td>
      <td class="hide-sm">${esc(CAT[r.category]||r.category||"—")}${r.score!=null?` <span class="mut">${Math.round(r.score)}</span>`:""}</td><td class="mut nowrap">${day(r.at)}</td></tr>`).join("")}</table></div>`);
}
async function sources(){
  const rows=await api("/api/sources");
  view(`<div class="card scroll">${rows.length?`<table><tr><th>Mənbə</th><th>14 gün</th><th class="right">Cəmi</th><th class="right">Son 7 gün</th><th class="right" title="Təsnif olunanların payı">Siqnal %</th><th class="right hide-sm">Ort. skor</th><th>Son qeyd</th><th>Status</th></tr>`+
    rows.map(r=>`<tr class="click" data-s="${esc(r.source)}"><td>${esc(r.source)}</td><td>${spark(r.series,80,22)}</td><td class="right">${r.total}</td><td class="right">${r.last7}</td><td class="right">${r.signal_rate}%</td><td class="right hide-sm">${r.avg_score??"—"}</td><td class="mut nowrap">${ago(r.last_at)}</td>
    <td>${r.disabled?`<span class="tag reddet">söndürülüb</span>`:r.last7===0?`<span class="tag izle">səssiz</span>`:`<span class="tag gec">aktiv</span>`}</td></tr>`).join("")+`</table>`:`<p class="mut">Hələ qeyd yoxdur.</p>`}</div>
    <p class="mut">Sətrə klikləsən həmin mənbənin qeydləri açılır. "Səssiz" = son 7 gündə heç nə gəlməyib.</p>`);
  $$("tr[data-s]").forEach(tr=>tr.onclick=()=>location.hash="#/search?source="+encodeURIComponent(tr.dataset.s));
}
async function search({params}){
  const P=k=>params.get(k)||"",S=META||{sources:[],categories:[]};
  view(`<div class="bar"><input type="search" id="q" placeholder="Qeydlərdə tam mətn axtarışı…" value="${esc(P("q"))}">
    <select id="source"><option value="">Mənbə: hamısı</option>${opts(S.sources,P("source"))}</select>
    <select id="kind"><option value="">Növ: hamısı</option>${opts(["news","comment"],P("kind"),{news:"xəbər",comment:"şərh"})}</select>
    <select id="category"><option value="">Kateqoriya: hamısı</option>${opts([...S.categories,"_none"],P("category"),{...CAT,_none:"Təsnif olunmamış"})}</select>
    <select id="min_score"><option value="">Min skor</option>${opts(["50","60","70","80"],P("min_score"),{50:"≥ 50",60:"≥ 60",70:"≥ 70",80:"≥ 80"})}</select></div>
    <div class="mut" id="cnt"></div><div class="card scroll" id="res"></div><div class="bar" id="pager" style="margin-top:12px"></div>`);
  const ids=["q","source","kind","category","min_score"];let offset=+P("offset")||0;
  const load=async()=>{const p=new URLSearchParams();ids.forEach(i=>{const v=$("#"+i).value;if(v)p.set(i,v)});if(offset)p.set("offset",offset);setParams(p);
    p.set("limit",50);const x=await api("/api/search?"+p),rows=x.rows;
    $("#cnt").textContent=`${x.total} nəticə`+(x.total?` · ${x.offset+1}–${x.offset+rows.length}`:"");
    const hl=s=>{const q=$("#q").value.trim();if(!q)return esc(s);const i=s.toLowerCase().indexOf(q.toLowerCase());return i<0?esc(s):esc(s.slice(0,i))+"<mark>"+esc(s.slice(i,i+q.length))+"</mark>"+esc(s.slice(i+q.length))};
    $("#res").innerHTML=rows.length?`<table><tr><th>Mətn</th><th>Mənbə</th><th class="hide-sm">Kateqoriya / mövzu</th><th>Tarix</th></tr>`+rows.map(r=>`<tr><td>${hl(r.text)} ${ext(r.url,"↗")}</td>
      <td class="nowrap">${esc(r.source)}<br><span class="mut">${esc(r.kind)}</span></td><td class="hide-sm">${esc(CAT[r.category]||r.category||"—")}${r.score!=null?` <span class="mut">${Math.round(r.score)}</span>`:""}${r.topic_id?`<br><a href="#/topic/${r.topic_id}">${esc(r.topic)}</a>`:""}</td><td class="mut nowrap">${day(r.at)}</td></tr>`).join("")+`</table>`:`<p class="mut">Nəticə yoxdur.</p>`;
    $("#pager").innerHTML=(x.offset>0?`<button class="btn alt" id="prev">‹ Əvvəlki</button>`:"")+(x.offset+rows.length<x.total?`<button class="btn alt" id="next">Növbəti ›</button>`:"");
    if($("#prev"))$("#prev").onclick=()=>{offset=Math.max(0,offset-50);load().catch(errBox)};
    if($("#next"))$("#next").onclick=()=>{offset+=50;load().catch(errBox);window.scrollTo(0,0)}};
  let t;$("#q").oninput=()=>{clearTimeout(t);t=setTimeout(()=>{offset=0;load().catch(errBox)},300)};
  ids.slice(1).forEach(i=>$("#"+i).onchange=()=>{offset=0;load().catch(errBox)});await load();
}
(async()=>{if(!token)return showLogin("");try{await api("/api/meta");start()}catch(e){if(e.message!=="401")start()}})();
</script></body></html>
"""
