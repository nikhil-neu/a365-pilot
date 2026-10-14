'use strict';
const M=window.FileGovernance;
let dataset=M.validate(window.FILE_GOVERNANCE_SAMPLE),files=dataset.files.map(M.view);
const $=id=>document.getElementById(id);
const node=(tag,text,cls)=>{const e=document.createElement(tag);e.textContent=text;if(cls)e.className=cls;return e;};
const statuses={finding:'Review required',unknown:'Needs evidence',clear:'No finding established'};
let selected=files[0]?.id;
function detail(f){const host=$('detail');host.replaceChildren();if(!f){host.append(node('h2','No matching file'));return;}
 host.append(node('span',statuses[f.status],'badge '+f.status),node('h2',f.name),node('p',f.location||'Location unavailable','path'),node('h3','Configured source relationships'));
 const chips=node('div','','chips');f.agents.forEach(a=>chips.append(node('span',a,'chip')));host.append(chips,node('p','Agents are configured for the containing source. This does not prove access to, or retrieval of, every file.','footnote'));
 host.append(node('h3','Protection evidence'));
 const grid=node('div','','evidence-grid');
 for(const key of M.fields){
 const o=f.observations[key];
 const cell=node('div','');cell.append(node('span',key),node('strong',f[key]),node('small',o.evidence.source+' · '+o.evidence.checkedAt+' · '+o.state));grid.append(cell);
 }host.append(grid);
 const card=node('div','','review-card');card.append(node('strong','Why this file needs review'),node('p',f.reason));host.append(card,node('h3','Suggested remediation'));
 const steps=node('ol','','steps');f.steps.forEach(s=>steps.append(node('li',s)));host.append(steps);
 const button=node('button','Prepare review summary','review-button');const output=node('div','','review-output');output.setAttribute('aria-live','polite');button.onclick=()=>{output.replaceChildren(node('strong','Draft review · '+dataset.dataKind),node('p',f.name+' — owner: '+f.owner),node('p',f.steps.join(' ')),node('p','No action submitted. Recollect live evidence, confirm scope and obtain separate approval before changing labels, permissions or DLP.'));};host.append(button,output);
 const evidence=node('details','');evidence.append(node('summary','Coverage and limitations'),node('p','Exported observations are supplied evidence, not independently verified. No file content, prompts or responses are collected. Policy inclusion does not prove a rule match or effective enforcement. External sharing is not itself proof of unauthorized disclosure. Unknown classification is never treated as unlabeled.'));host.append(evidence);
}
function render(){
 $('locations').textContent=files.length;
 $('agents').textContent=new Set(dataset.files.flatMap(f=>f.agents.map(a=>a.id))).size;
 $('findings').textContent=files.filter(f=>f.status==='finding').length;
 $('unknown').textContent=files.filter(f=>f.unknown.length).length;
 $('coverage').textContent=['label','sharing','dlp'].map(k=>k+': '+files.filter(f=>f.observations[k].state==='known').length+'/'+files.length+' observed').join(' · ')+' · Inventory completeness (exporter declaration): '+dataset.complete;
 $('kind').textContent=dataset.dataKind==='sample'?'SAMPLE DATA':'TENANT EXPORT';
 $('dataset').textContent=dataset.name;
 $('identity').textContent=dataset.tenantId+' / '+dataset.environment;
 $('banner').textContent=(dataset.dataKind==='sample'?'SAMPLE DATA — all evidence is fictional. ':'TENANT EXPORT — supplied evidence; provenance has not been independently verified. ')+ 'Snapshot: '+dataset.capturedAt+'. No live connection or changes. No tenant-wide completeness inferred.';
const q=$('search').value.toLowerCase(),filter=$('filter').value;
 const visible=files.filter(f=>(filter==='all'||(filter==='unknown'?f.unknown.length>0:f.status===filter))&&[f.name,f.site,...f.agents].join(' ').toLowerCase().includes(q));
 if(!visible.some(f=>f.id===selected))selected=visible[0]?.id;
 $('rows').replaceChildren();for(const f of visible){const row=node('tr','',f.id===selected?'selected':'');const cell=node('td',''),b=node('button',f.name);b.setAttribute('aria-pressed',String(f.id===selected));b.onclick=()=>{selected=f.id;render();};cell.append(b,node('small',f.site),node('small',f.agents.length+' connected agent(s)'));row.append(cell,node('td',f.label==='Labeled'?f.labelName:f.label),node('td',f.sharing),node('td',f.dlp));const status=node('td','');status.append(node('span',statuses[f.status],'badge '+f.status));row.append(status);$('rows').append(row);}
 $('count').textContent=visible.length+' files';$('empty').hidden=visible.length!==0;detail(visible.find(f=>f.id===selected));
}
$('search').addEventListener('input',render);$('filter').addEventListener('change',render);render();

function load(d){M.validate(d);dataset=d;files=d.files.map(M.view);selected=files[0]?.id;$('search').value='';$('filter').value='all';$('error').hidden=true;render();}
let importVersion=0;
$('upload').addEventListener('change',async e=>{const ticket=++importVersion;try{const f=e.target.files[0];if(!f)return;if(f.size>5*1024*1024)throw new Error('File exceeds 5 MB');const text=await f.text();if(ticket!==importVersion)return;load(JSON.parse(text));}catch(err){if(ticket!==importVersion)return;$('error').textContent='Import rejected: '+err.message+'. Previous dataset retained.';$('error').hidden=false;}finally{e.target.value='';}});
$('reset').onclick=()=>{importVersion++;load(window.FILE_GOVERNANCE_SAMPLE);};
function download(name,text,type){const u=URL.createObjectURL(new Blob([text],{type}));const a=document.createElement('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);}
$('export').onclick=()=>download('agent-governance-review.txt',M.report(dataset),'text/plain');
$('template').onclick=()=>download('file-governance.sample.json',JSON.stringify(window.FILE_GOVERNANCE_SAMPLE,null,2),'application/json');
