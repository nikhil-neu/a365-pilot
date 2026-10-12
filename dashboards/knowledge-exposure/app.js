'use strict';
const M=window.KnowledgeModel,$=id=>document.getElementById(id);
let data,selected,sort={key:'name',direction:1};
function el(tag,text,cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;}
const value=x=>x===null||x===undefined?'Unknown':Array.isArray(x)?(x.length?x.join(', '):'None recorded'):typeof x==='object'?JSON.stringify(x):String(x);
const label=id=>data.labels.find(l=>l.id===id)?.name||'Unknown';
const state=x=>x===null?'Unknown':x?'Yes':'No';
const evidence=o=>`${o.evidence.source} · ${o.evidence.checkedAt||'Timestamp unavailable'}`;
function option(select,v,t){const o=el('option',t);o.value=v;select.append(o);}
function load(d){M.validate(d);data=d;selected=d.agents[0]?.packageId;sort={key:'name',direction:1};$('error').hidden=true;
$('banner').textContent=d.dataKind==='sample'?'SAMPLE DATA — Fictional preview. No live tenant data is shown.':'TENANT EXPORT — Supplied metadata, not a live connection. Provenance has not been authenticated.';
$('dataset').textContent=`${d.name} · Snapshot ${d.capturedAt} · ${d.complete?'Declared complete agent inventory':'Partial agent inventory'} · ${d.agents.length} agents`;
for(const [id,items] of Object.entries({agent:d.agents.map(a=>[a.packageId,a.name||a.packageId]),platform:[...new Set(d.agents.map(a=>a.platform).filter(Boolean))].map(v=>[v,v]),type:[...new Set(d.agents.flatMap(a=>(a.sources||[]).map(s=>s.type.value)).filter(Boolean))].map(v=>[v,v]),label:[...d.labels.map(l=>[l.id,l.name]),['unknown','Unknown'],['notApplicable','Not applicable']]})){$(id).replaceChildren();option($(id),'','All');for(const [v,t]of items)option($(id),v,t);}
$('search').value='';$('external').value='';renderMetrics();render();$('governance-search').value='';renderGovernance();}
function renderMetrics(){const m=M.metrics(data),count=(n,partial)=>partial?(n?'At least '+n:'Unknown'):String(n);const flag=x=>[count(x.count,x.unknown>0||x.partial),`${x.unknown} agents unresolved${x.partial?' · inventory partial':''}`];
const cards=[['Discovered sites / containers',m.discovered===null?'Not available':String(m.discovered),evidence(data.discoveredContainers)],['Connected sites / containers',count(m.connected,m.connectionsUnknown),'Distinct configured container IDs'],['Agents with mixed labels',...flag(m.mixed)],['Agents with multiple containers',...flag(m.multiple)],['Agents with external sources',...flag(m.external)]];
$('metrics').replaceChildren(...cards.map(([title,n,note])=>{const e=el('article',undefined,'metric');e.append(el('p',title),el('strong',n),el('small',note));return e;}));}
function filters(){return Object.fromEntries(['search','agent','platform','type','label','external'].map(k=>[k,$(k).value]));}
function sortValue(r){if(sort.key==='agent')return r.a.name;if(sort.key==='name')return r.s.name.value;if(sort.key==='label'){const id=r.s.containerLabel.value;return id===null?null:data.labels.find(l=>l.id===id).rank;}return r.s.external.value;}
function render(){const f=filters(),rows=M.filtered(data,f);rows.sort((a,b)=>{const x=sortValue(a),y=sortValue(b);if(x===null||x===undefined)return y===null||y===undefined?0:1;if(y===null||y===undefined)return -1;return (typeof x==='string'?x.localeCompare(y):Number(x)-Number(y))*sort.direction;});
$('result-count').textContent=`${rows.length} source relationships`; $('empty').hidden=rows.length!==0;
$('rows').replaceChildren(...rows.map(({a,s})=>{const tr=el('tr'),ac=el('td'),button=el('button',a.name||a.packageId,'agent-link');button.onclick=()=>{selected=a.packageId;renderAgents(rows,f);renderDetail();};ac.append(button,el('small',value(a.platform)),el('small','Owner: '+value(a.owners)));tr.append(ac);
const cell=(txt,sub)=>{const c=el('td',txt);if(sub)c.append(el('small',sub));tr.append(c);};cell(value(s.name.value),evidence(s.name));cell(value(s.type.value),value(s.location.value));cell(s.container.value?.kind==='notApplicable'?'Not applicable':label(s.containerLabel.value),evidence(s.containerLabel));cell(s.contentLabels.value===null?'Not available':s.contentLabels.value.map(label).join(', ')||'No labels in supplied evidence',evidence(s.contentLabels));cell(state(s.external.value),evidence(s.external));cell(s.runtimeRetrieved.value===true?'Observed retrieval':s.runtimeRetrieved.value===false?'Not observed in supplied evidence':'Unknown',evidence(s.runtimeRetrieved));return tr;}));
for(const b of document.querySelectorAll('[data-sort]'))b.parentElement.setAttribute('aria-sort',sort.key===b.dataset.sort?(sort.direction===1?'ascending':'descending'):'none');renderAgents(rows,f);renderDetail();}
function renderAgents(rows,f){const visible=new Set(rows.map(r=>r.a.packageId));for(const a of data.agents){if((a.sources===null||a.sources.length===0)&&!f.type&&!f.label&&!f.external&&(!f.agent||f.agent===a.packageId)&&(!f.platform||f.platform===a.platform)&&(!f.search||[a.name,a.packageId,...a.owners||[]].join(' ').toLowerCase().includes(f.search.toLowerCase())))visible.add(a.packageId);}
const agents=data.agents.filter(a=>visible.has(a.packageId));if(!visible.has(selected))selected=agents[0]?.packageId;
$('agents').replaceChildren(...agents.map(a=>{const s=M.summarize(a,data),card=el('article',undefined,'agent-card'+(selected===a.packageId?' selected':'')),b=el('button',a.name||a.packageId,'agent-link');b.onclick=()=>{selected=a.packageId;renderAgents(rows,f);renderDetail();};card.append(b,el('p',`${value(a.platform)} · Owner: ${value(a.owners)}\nHighest known container label: ${s.highest||'Unknown / not rankable'}${s.unknownLabels?' · '+s.unknownLabels+' unknown labels':''}`));const flags=el('div',undefined,'flags');for(const [k,t]of [['mixed','Mixed sensitivity'],['multiple','Multiple containers'],['external','External source']])flags.append(el('span',`${t}: ${state(s[k])}`,'pill'+(s[k]===true?' warn':'')));card.append(flags,el('p',a.sources===null?'Configured-source inventory unavailable':`${a.sources.length} configured sources · ${a.sourcesComplete?'complete source inventory':'partial source inventory'}`));return card;}));if(!agents.length)$('agents').append(el('p','No agents match these filters.'));}
function renderDetail(){const host=$('detail');host.replaceChildren();const a=data.agents.find(a=>a.packageId===selected);if(!a){host.append(el('h2','Select an agent'),el('p','No agent is selected.'));return;}const s=M.summarize(a,data);host.append(el('p','AGENT DETAIL','eyebrow'),el('h2',a.name||a.packageId),el('p',`${a.packageId} · ${a.evidence.source} · ${a.evidence.checkedAt||'Timestamp unavailable'}`));const reasons=[`Highest known container sensitivity: ${s.highest||'Unknown — no known, fully ranked label set'}. Unknown labels are excluded, not ranked low.`,s.mixed===true?`Mixed sensitivity: known container labels differ (${s.labels.map(label).join(', ')}).`:`Mixed sensitivity: ${s.mixed===false?'known labels do not differ':'not determinable with incomplete or unknown labels'}.`,s.multiple===true?`Multiple containers: ${s.containers.length} distinct IDs (${s.containers.join(', ')}).`:`Multiple containers: ${s.multiple===false?'no more than one configured container':'container mapping or source inventory incomplete'}.`,s.external===true?`External source present: ${(a.sources||[]).filter(x=>x.external.value===true).map(x=>x.name.value||x.id).join(', ')}.`:`External source: ${s.external===false?'all configured sources are explicitly internal':'classification or inventory incomplete'}.`,`${s.unknownLabels} configured sources have unknown container labels. ${a.sourcesComplete?'':'Additional unlisted sources may exist.'}`];const ul=el('ul');for(const r of reasons)ul.append(el('li',r));host.append(ul);
const review=el('section',undefined,'review');review.append(el('h3','Review / suggested next steps'));const actions=[];if(s.mixed)actions.push('Confirm that combining differently labeled containers is intended; review the configured scope with the owner. Mixed labels alone do not prove a policy violation.');if(s.multiple)actions.push('Confirm each container is necessary and review access boundaries for the intended users.');if(s.external)actions.push('Review external-source ownership, trust and approved usage. Do not infer exposure of internal data from a configured external source.');if(s.unknownLabels||!a.sourcesComplete)actions.push('Obtain missing container classification and a complete source inventory from an authorized metadata export.');if(!a.owners?.length)actions.push('Assign or verify an accountable agent owner through the normal administrative process.');actions.push('Validate retrieval using metadata-only runtime evidence. A configured source is not proof it was read.');for(const action of actions)review.append(el('p',action));review.append(el('small','Suggested review only. This dashboard makes no changes.'));host.append(review);
for(const source of a.sources||[]){const details=el('details',undefined,'evidence');details.append(el('summary',(source.name.value||source.id)+' — evidence'));const dl=el('dl');for(const f of M.fields){let v=source[f].value;if(f==='containerLabel')v=v===null?'Unknown':label(v);if(f==='contentLabels')v=v===null?'Not available':v.map(label);if(f==='runtimeRetrieved')v=v===true?'Observed retrieval':v===false?'Not observed in supplied evidence':'Unknown';dl.append(el('dt',f));const dd=el('dd',value(v));dd.append(el('small',evidence(source[f])));dl.append(dd);}details.append(dl);host.append(details);}}
for(const id of ['search','agent','platform','type','label','external'])$(id).addEventListener('input',render);
$('clear').onclick=()=>{for(const id of ['search','agent','platform','type','label','external'])$(id).value='';render();};
for(const b of document.querySelectorAll('[data-sort]'))b.onclick=()=>{sort={key:b.dataset.sort,direction:sort.key===b.dataset.sort?-sort.direction:1};render();};
$('sample').onclick=()=>{importVersion++;load(window.KNOWLEDGE_SAMPLE);};
let importVersion=0;$('upload').onchange=async e=>{const file=e.target.files[0],version=++importVersion;if(!file)return;try{if(file.size>5*1024*1024)throw new Error('File exceeds 5 MB limit');const parsed=JSON.parse(await file.text());if(version!==importVersion)return;load(parsed);}catch(err){$('error').textContent='Import rejected. '+err.message+' Previous dataset remains loaded.';$('error').hidden=false;}finally{e.target.value='';}};
load(window.KNOWLEDGE_SAMPLE);

function renderGovernance(){
 const groups=window.KnowledgeGovernance.group(data),query=$('governance-search').value.toLowerCase();
 const missing=data.agents.filter(a=>a.sources===null||!a.sourcesComplete).length;
 $('governance-coverage').textContent=`${groups.length} configured data locations · ${missing} agents with incomplete source inventory · Permissions and DLP coverage not collected`;
 const host=$('governance');host.replaceChildren();
 for(const g of groups){
  if(query&&!g.entries.map(({a,s})=>[a.name,s.name.value,s.location.value].join(' ')).join(' ').toLowerCase().includes(query))continue;
  const card=el('details',undefined,'evidence');card.append(el('summary',`${g.location||'Unresolved location'} — ${g.agents.length} connected agents`));
  card.append(el('p','Connected agents: '+g.agents.map(a=>a.name||a.packageId).join(', ')));
  card.append(el('p','Accountable agent owners (not verified data owners): '+[...new Set(g.agents.flatMap(a=>a.owners||[]))].join(', ')));
  const containerLabels=[...new Set(g.entries.map(r=>r.s.containerLabel.value).filter(v=>v!==null))];
  card.append(el('p','Known container labels: '+(containerLabels.map(label).join(', ')||'Unknown')+(containerLabels.length>1?' — differing observations require review':'')));
  const review=el('section',undefined,'review');review.append(el('h3','Review queue'));
  for(const finding of g.findings)review.append(el('p',finding));
  review.append(el('p','Suggested sequence: resolve exact site/library/file IDs → confirm data owner and intended users → obtain file-label and sharing evidence → review applicable DLP scope and exceptions → prepare separately approved changes → verify results.'));
  review.append(el('small','Review only. Unknown labels do not mean unlabeled. Unknown DLP coverage does not mean unprotected. Mixed labels alone do not prove a violation.'));
  card.append(review);
  for(const {a,s} of g.entries){const detail=el('details');detail.append(el('summary',(a.name||a.packageId)+' / '+(s.name.value||s.id)));const dl=el('dl');
   for(const [title,field,display] of [
    ['Configured location','location',value(s.location.value)],['Container identity','container',value(s.container.value)],
    ['Container label','containerLabel',label(s.containerLabel.value)],['Content label evidence','contentLabels',s.contentLabels.value===null?'Not available':s.contentLabels.value.map(label).join(', ')||'No labels in supplied evidence'],
    ['Access context (not effective permissions)','accessContext',value(s.accessContext.value)],['External classification','external',state(s.external.value)],
    ['Runtime retrieval','runtimeRetrieved',s.runtimeRetrieved.value===true?'Observed in supplied evidence':s.runtimeRetrieved.value===false?'Not observed in supplied evidence':'Unknown'],['Metadata check','lastCheck',value(s.lastCheck.value)]]){
     dl.append(el('dt',title));const dd=el('dd',display);dd.append(el('small',evidence(s[field])));dl.append(dd);
   }detail.append(dl);card.append(detail);
  }
  card.append(el('p','Effective permissions / sharing / applicable DLP policy: Not available — not collected; no evidence timestamp.'));
  host.append(card);
 }
 if(!host.children.length)host.append(el('p','No configured data locations match. Missing source inventory is not evidence of no exposure.'));
}
$('governance-search').addEventListener('input',renderGovernance);
