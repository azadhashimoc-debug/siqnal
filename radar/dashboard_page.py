PAGE = r"""<!doctype html>
<html lang="az"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fürsət Radarı</title>
<style>
:root{--bg:#f6f7f9;--card:#fff;--fg:#1b1f24;--mut:#667085;--line:#e4e7ec;--acc:#2563eb;--ok:#16a34a;--warn:#d97706;--bad:#dc2626}
@media(prefers-color-scheme:dark){:root{--bg:#0f1216;--card:#181c22;--fg:#e6e8eb;--mut:#98a2b3;--line:#2a3039;--acc:#60a5fa;--ok:#4ade80;--warn:#fbbf24;--bad:#f87171}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif}
header{display:flex;gap:8px;flex-wrap:wrap;align-items:center;padding:12px 16px;background:var(--card);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:2}
header h1{font-size:17px;margin:0 12px 0 0}
nav button{background:none;border:0;color:var(--mut);padding:8px 12px;border-radius:8px;cursor:pointer;font:inherit}
nav button.on{background:var(--acc);color:#fff}
main{max-width:1100px;margin:0 auto;padding:16px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}
.stat b{display:block;font-size:26px}.stat span,.mut{color:var(--mut);font-size:13px}
.bar{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
input,select{background:var(--card);color:var(--fg);border:1px solid var(--line);border-radius:8px;padding:8px 10px;font:inherit;min-width:0}
input[type=search]{flex:1;min-width:160px}
table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:9px 8px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--mut);font-weight:500;font-size:13px}tr.click{cursor:pointer}tr.click:hover{background:color-mix(in srgb,var(--acc) 8%,transparent)}
.tag{display:inline-block;padding:1px 8px;border-radius:99px;font-size:12px;border:1px solid currentColor}
.gec{color:var(--ok)}.izle{color:var(--warn)}.reddet{color:var(--bad)}
.btn{background:var(--acc);color:#fff;border:0;border-radius:8px;padding:8px 14px;cursor:pointer;font:inherit}
.btn.alt{background:none;color:var(--fg);border:1px solid var(--line)}
h2{font-size:16px;margin:18px 0 6px}ul{padding-left:20px;margin:4px 0}a{color:var(--acc)}
.dim{display:grid;grid-template-columns:130px 1fr 40px;gap:8px;align-items:center;margin:4px 0}
.meter{height:8px;background:var(--line);border-radius:4px;overflow:hidden}.meter i{display:block;height:100%;background:var(--acc)}
.spark{display:inline-block;vertical-align:middle}
#login{max-width:340px;margin:80px auto}
.msg{padding:10px 14px;border-radius:8px;background:color-mix(in srgb,var(--warn) 15%,transparent);margin-bottom:12px}
.scroll{overflow-x:auto}
</style></head><body>
<div id="login" class="card" hidden>
  <h2 style="margin-top:0">Daxil ol</h2>
  <p class="mut">DASHBOARD_TOKEN dəyərini yaz.</p>
  <input id="tok" type="password" style="width:100%;margin-bottom:10px" autocomplete="current-password">
  <button class="btn" id="go">Daxil ol</button><p id="lerr" class="mut"></p>
</div>
<div id="app" hidden>
<header><h1>📡 Fürsət Radarı</h1>
<nav id="nav"></nav><span style="flex:1"></span><button class="btn alt" id="out">Çıxış</button></header>
<main id="view"></main></div>
<script>
const $=s=>document.querySelector(s);
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const safeUrl=u=>/^https?:\/\//i.test(u||"")?esc(u):"#";
let token="";try{token=localStorage.getItem("radar_tok")||""}catch(e){}
const TABS=[["overview","Ümumi"],["ideas","İdeyalar"],["topics","Trendlər"],["sources","Mənbələr"],["search","Axtarış"]];
let tab="overview";
async function api(path,opts={}){
  const r=await fetch(path,{...opts,headers:{"X-Token":token}});
  if(r.status===401){showLogin("Token yanlışdır");throw new Error("401")}
  if(!r.ok){let m=r.statusText;try{m=(await r.json()).detail||m}catch(e){}throw new Error(m)}
  return r.json();
}
function showLogin(err){$("#app").hidden=true;$("#login").hidden=false;$("#lerr").textContent=err||""}
function start(){$("#login").hidden=true;$("#app").hidden=false;nav();go(tab)}
$("#go").onclick=async()=>{token=$("#tok").value;try{await api("/api/overview");try{localStorage.setItem("radar_tok",token)}catch(e){}start()}catch(e){}};
$("#out").onclick=()=>{token="";try{localStorage.removeItem("radar_tok")}catch(e){}showLogin("")};
function nav(){$("#nav").innerHTML=TABS.map(([k,l])=>`<button data-k="${k}" class="${k===tab?"on":""}">${l}</button>`).join("");
  document.querySelectorAll("#nav button").forEach(b=>b.onclick=()=>{tab=b.dataset.k;nav();go(tab)})}
const view=h=>{$("#view").innerHTML=h};
const err=e=>view(`<div class="msg">${esc(e.message)}</div>`);
async function go(t,arg){try{await ({overview,ideas,topics,sources,search,detail})[t](arg)}catch(e){if(e.message!=="401")err(e)}}
const tag=d=>`<span class="tag ${esc(d)}">${esc(d||"?")}</span>`;
function spark(s){const w=84,h=22,m=Math.max(1,...s);
  const p=s.map((v,i)=>`${(i*(w/(s.length-1||1))).toFixed(1)},${(h-1-(v/m)*(h-2)).toFixed(1)}`).join(" ");
  return `<svg class="spark" width="${w}" height="${h}"><polyline points="${p}" fill="none" stroke="var(--acc)" stroke-width="1.5"/></svg>`}
async function overview(){
  const o=await api("/api/overview"),d=o.decisions;
  const S=(n,l)=>`<div class="card stat"><b>${esc(n)}</b><span>${l}</span></div>`;
  view(`<div class="grid">${S(o.records,"Ümumi qeyd")}${S(o.records_7d,"Son 7 gün")}${S(o.classified,"Təsnif olunmuş")}
    ${S(o.topics,"Mövzu")}${S(o.candidates,"Namizəd trend")}
    ${S((d.gec||0)+" / "+(d.izle||0)+" / "+(d.reddet||0),"Keç / İzlə / Rədd")}
    ${S(o.validations_7d+" / "+o.max_validations_per_week,"Həftəlik yoxlama limiti")}
    ${S(o.apify_runs_7d+" / "+o.max_apify_runs_per_week,"Apify limiti")}</div>
    <p class="mut">Son qeyd: ${esc(o.last_record||"—")}. Məlumat Modal Volume-dan oxunur, hər 3 saatdan bir yenilənir.</p>`);
}
async function ideas(){
  view(`<div class="bar"><input type="search" id="q" placeholder="Axtar…"><select id="dec"><option value="">Bütün qərarlar</option>
    <option value="gec">gec</option><option value="izle">izle</option><option value="reddet">reddet</option></select>
    <select id="srt"><option value="score">Skora görə</option><option value="votes">Səsə görə</option><option value="date">Tarixə görə</option></select>
    <select id="ms"><option value="0">Min skor: hamısı</option><option value="5">≥ 5</option><option value="6">≥ 6</option><option value="7">≥ 7</option></select></div>
    <div class="card scroll" id="list"></div>`);
  const load=async()=>{
    const p=new URLSearchParams({q:$("#q").value,decision:$("#dec").value,sort:$("#srt").value,min_score:$("#ms").value});
    const rows=await api("/api/ideas?"+p);
    $("#list").innerHTML=rows.length?`<table><tr><th>Problem / ideya</th><th>Qərar</th><th>Skor</th><th>Xərc</th><th>Səs</th><th>Tarix</th></tr>`+
      rows.map(r=>`<tr class="click" data-id="${r.id}"><td><b>${esc(r.problem)}</b><br><span class="mut">${esc(r.idea)}</span></td>
      <td>${tag(r.decision)}</td><td>${r.score}</td><td>${esc(r.cost||"—")}</td><td>${r.votes>0?"+":""}${r.votes}</td><td class="mut">${esc((r.created_at||"").slice(0,10))}</td></tr>`).join("")+`</table>`
      :`<p class="mut">Hələ ideya yoxdur. Yoxlama agenti bazar ertəsi işləyir.</p>`;
    document.querySelectorAll("#list tr.click").forEach(tr=>tr.onclick=()=>{tab="ideas";go("detail",tr.dataset.id)});
  };
  let t;$("#q").oninput=()=>{clearTimeout(t);t=setTimeout(()=>load().catch(err),250)};
  ["dec","srt","ms"].forEach(i=>$("#"+i).onchange=()=>load().catch(err));await load();
}
async function detail(id){
  const r=await api("/api/ideas/"+id),d=r.data||{};
  const dims=[["demand","Tələb"],["competition","Rəqabət"],["willingness_to_pay","Ödəmə gücü"],["timing","Vaxtlama"]];
  const claims=x=>(x.claims||[]).map(c=>`<li>${esc(c.text)} <a href="${safeUrl(c.url)}" target="_blank" rel="noopener noreferrer">mənbə</a></li>`).join("");
  const sols=(d.solutions||[]).map((s,i)=>`<div class="card" style="margin:8px 0"><b>${i+1}. ${esc(s.title)}</b> <span class="mut">(${esc(s.start_cost)}, çətinlik ${esc(s.difficulty)}/5${s.start_cost_text?", "+esc(s.start_cost_text):""})</span>
    <ul><li>Necə işləyir: ${esc(s.how_it_works)}</li><li>Gəlir modeli: ${esc(s.business_model)}</li><li>İlk addım: ${esc(s.first_step)}</li>
    <li>Rəqiblər: ${(s.competitor_urls||[]).map(u=>`<a href="${safeUrl(u)}" target="_blank" rel="noopener noreferrer">${esc(u)}</a>`).join(", ")||"—"}</li></ul></div>`).join("");
  view(`<p><button class="btn alt" id="back">← Geri</button></p>
    <div class="card"><h2 style="margin-top:0">${esc(d.problem)} ${tag(r.decision)}</h2>
    <div class="mut">Ümumi skor: <b>${r.score}</b> · ${esc((r.created_at||"").slice(0,10))}</div>
    <ul>${(d.sub_pains||[]).map(p=>`<li>${esc(p)}</li>`).join("")}</ul>
    ${dims.map(([k,l])=>`<div class="dim"><span>${l}</span><div class="meter"><i style="width:${(d[k]?.score||0)*10}%"></i></div><b>${d[k]?.score??"—"}</b></div><ul>${claims(d[k]||{})}</ul>`).join("")}
    ${d.market_size?.estimate?`<p>Bazar ölçüsü: ${esc(d.market_size.estimate)}</p>`:""}
    <h2>Həll yolları</h2>${sols||"<p class='mut'>—</p>"}
    <h2>Risklər</h2><ul>${(d.risks||[]).map(x=>`<li>${esc(x)}</li>`).join("")}</ul>
    ${(d.unverified_claims||[]).length?`<h2>Doğrulanmadı</h2><ul>${d.unverified_claims.map(x=>`<li>${esc(x)}</li>`).join("")}</ul>`:""}
    <h2>Kanıtlar</h2><ul>${r.evidence.map(e=>`<li>${esc(e.text)} <a href="${safeUrl(e.url)}" target="_blank" rel="noopener noreferrer">${esc(e.source)}</a></li>`).join("")}</ul>
    <h2>Səs (${r.votes.reduce((a,v)=>a+v.vote,0)})</h2>
    <button class="btn" id="up">👍</button> <button class="btn alt" id="down">👎</button> <span id="vn" class="mut"></span></div>`);
  $("#back").onclick=()=>go("ideas");
  for(const k of ["up","down"])$("#"+k).onclick=async()=>{try{const x=await api(`/api/ideas/${id}/vote/${k}`,{method:"POST"});$("#vn").textContent=x.note}catch(e){$("#vn").textContent=e.message}};
}
async function topics(){
  const rows=await api("/api/topics");
  view(`<div class="card scroll">${rows.length?`<table><tr><th>Mövzu</th><th>14 gün</th><th>Son 7 gün</th><th>Əvvəlki 7</th><th>Cəmi</th><th></th></tr>`+
    rows.map(r=>`<tr><td>${esc(r.name)}${r.candidate_at?` <span class="tag gec">namizəd</span>`:""}</td><td>${spark(r.series)}</td><td>${r.recent}</td><td>${r.prev}</td><td>${r.total}</td>
    <td>${r.validation_id?`<a href="#" data-v="${r.validation_id}">hesabat</a>`:""}</td></tr>`).join("")+`</table>`:`<p class="mut">Hələ mövzu yoxdur.</p>`}</div>`);
  document.querySelectorAll("a[data-v]").forEach(a=>a.onclick=e=>{e.preventDefault();tab="ideas";nav();go("detail",a.dataset.v)});
}
async function sources(){
  const rows=await api("/api/sources");
  view(`<div class="card scroll"><table><tr><th>Mənbə</th><th>Cəmi</th><th>Son 7 gün</th><th>Son qeyd</th><th>Status</th></tr>`+
    rows.map(r=>`<tr><td>${esc(r.source)}</td><td>${r.total}</td><td>${r.last7}</td><td class="mut">${esc(r.last_at)}</td>
    <td>${r.disabled?`<span class="tag reddet">söndürülüb</span>`:`<span class="tag gec">aktiv</span>`}</td></tr>`).join("")+`</table></div>`);
}
async function search(){
  view(`<div class="bar"><input type="search" id="q" placeholder="Qeydlərdə tam mətn axtarışı…" autofocus>
    <select id="kind"><option value="">Növ: hamısı</option><option value="news">xəbər</option><option value="comment">şərh</option></select></div><div class="card scroll" id="res"><p class="mut">Axtarış sözü yaz.</p></div>`);
  const load=async()=>{const p=new URLSearchParams({q:$("#q").value,kind:$("#kind").value,limit:50});const rows=await api("/api/search?"+p);
    $("#res").innerHTML=rows.length?`<table><tr><th>Mətn</th><th>Mənbə</th><th>Kateqoriya</th><th>Tarix</th></tr>`+rows.map(r=>`<tr><td>${esc(r.text)} <a href="${safeUrl(r.url)}" target="_blank" rel="noopener noreferrer">↗</a></td>
      <td>${esc(r.source)}<br><span class="mut">${esc(r.kind)}</span></td><td>${esc(r.category||"—")}${r.score!=null?` <span class="mut">${Math.round(r.score)}</span>`:""}</td><td class="mut">${esc((r.at||"").slice(0,10))}</td></tr>`).join("")+`</table>`:`<p class="mut">Nəticə yoxdur.</p>`};
  let t;$("#q").oninput=()=>{clearTimeout(t);t=setTimeout(()=>load().catch(err),300)};$("#kind").onchange=()=>load().catch(err);await load();
}
(async()=>{if(!token)return showLogin("");try{await api("/api/overview");start()}catch(e){if(e.message!=="401"){start()}}})();
</script></body></html>
"""
