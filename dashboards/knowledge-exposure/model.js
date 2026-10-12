/* Shared browser/test calculations. No tenant calls or content ingestion. */
(function(root){
'use strict';
const fields=['name','type','location','container','containerLabel','contentLabels','external','accessContext','lastCheck','runtimeRetrieved'];
function assert(ok,msg){if(!ok)throw new Error(msg);}
function keys(o,allowed){assert(o&&typeof o==='object'&&!Array.isArray(o),'Expected object');assert(Object.keys(o).every(k=>allowed.includes(k)),'Unexpected field; use the documented metadata-only format');}
function date(v){return typeof v==='string'&&/T.*(Z|[+-]\d\d:\d\d)$/.test(v)&&Number.isFinite(Date.parse(v));}
function observation(o){keys(o,['value','evidence']);assert('value'in o,'Observation missing value');keys(o.evidence,['source','checkedAt']);assert(typeof o.evidence.source==='string'&&o.evidence.source.length>0,'Evidence source required');assert(o.evidence.checkedAt===null||date(o.evidence.checkedAt),'Evidence timestamp must have timezone or be null');}
function text(v){return v===null||typeof v==='string';}
function validate(d){
keys(d,['schemaVersion','dataKind','name','capturedAt','complete','labels','discoveredContainers','agents']);
assert(d.schemaVersion===1&&['sample','tenant-export'].includes(d.dataKind),'Expected schemaVersion 1 and explicit dataKind');
assert(typeof d.name==='string'&&date(d.capturedAt)&&typeof d.complete==='boolean','Invalid dataset metadata');
assert(Array.isArray(d.labels)&&Array.isArray(d.agents),'Labels/agents must be arrays');
const labels=new Map();for(const l of d.labels){keys(l,['id','name','rank']);assert(typeof l.id==='string'&&l.id&&!labels.has(l.id)&&typeof l.name==='string','Invalid/duplicate label');assert(l.rank===null||(Number.isInteger(l.rank)&&l.rank>=0),'Label rank must be nonnegative integer or null');labels.set(l.id,l);}
observation(d.discoveredContainers);assert(d.discoveredContainers.value===null||(Array.isArray(d.discoveredContainers.value)&&d.discoveredContainers.value.every(x=>typeof x==='string'&&x)&&new Set(d.discoveredContainers.value).size===d.discoveredContainers.value.length),'Discovered containers must be unique IDs or null');
const ids=new Set();for(const a of d.agents){keys(a,['packageId','name','platform','owners','sourcesComplete','sources','evidence']);assert(typeof a.packageId==='string'&&a.packageId&&!ids.has(a.packageId),'Duplicate/invalid agent ID');ids.add(a.packageId);assert(text(a.name)&&text(a.platform)&&(a.owners===null||(Array.isArray(a.owners)&&a.owners.every(x=>typeof x==='string'))),'Invalid agent metadata');observation({value:null,evidence:a.evidence});assert(typeof a.sourcesComplete==='boolean'&&(a.sources===null||Array.isArray(a.sources)),'Invalid sources');assert(a.sources!==null||!a.sourcesComplete,'Unknown sources cannot be complete');
const sourceIds=new Set();for(const s of a.sources||[]){keys(s,['id',...fields]);assert(typeof s.id==='string'&&s.id&&!sourceIds.has(s.id),'Duplicate source ID within agent');sourceIds.add(s.id);for(const f of fields)observation(s[f]);
for(const f of ['name','type','location','containerLabel','accessContext'])assert(text(s[f].value),'Expected string or null: '+f);
for(const f of ['external','runtimeRetrieved'])assert(s[f].value===null||typeof s[f].value==='boolean','Expected boolean or null: '+f);
assert(s.lastCheck.value===null||date(s.lastCheck.value),'Invalid last check');
const c=s.container.value;if(c!==null){keys(c,['id','kind']);assert(['site','container','notApplicable'].includes(c.kind),'Invalid container kind');assert(c.kind==='notApplicable'?c.id===null:typeof c.id==='string'&&c.id,'Invalid container ID');}
assert(s.containerLabel.value===null||labels.has(s.containerLabel.value),'Unknown label ID');assert(c===null||c.kind!=='notApplicable'||s.containerLabel.value===null,'Non-container cannot have a container label');
assert(s.contentLabels.value===null||(Array.isArray(s.contentLabels.value)&&s.contentLabels.value.every(x=>labels.has(x))),'Invalid content labels');
if(s.location.value&&/^https?:/i.test(s.location.value)){const u=new URL(s.location.value);assert(!u.username&&!u.password&&!u.search&&!u.hash,'Redact credentials, query strings and fragments from source URLs before import');}
for(const f of fields)if(s[f].value!==null)assert(s[f].evidence.checkedAt!==null,'Known source values need evidence timestamps');
}}
return d;
}
function summarize(a,d){const ss=a.sources||[],labels=[...new Set(ss.map(s=>s.containerLabel.value).filter(x=>x!==null))], containers=[...new Set(ss.map(s=>s.container.value).filter(c=>c&&c.kind!=='notApplicable').map(c=>c.id))];
const unknownLabels=ss.filter(s=>(s.container.value===null||s.container.value.kind!=='notApplicable')&&s.containerLabel.value===null).length;
const complete=a.sources!==null&&a.sourcesComplete;
const ranked=labels.map(id=>d.labels.find(l=>l.id===id));
const highest=ranked.length&&ranked.every(l=>l.rank!==null)?ranked.filter(l=>l.rank===Math.max(...ranked.map(x=>x.rank))).map(l=>l.name).join(' / '):null;
return {labels,containers,unknownLabels,highest,mixed:labels.length>1?true:complete&&!unknownLabels?false:null,multiple:containers.length>1?true:complete&&!ss.some(s=>s.container.value===null)?false:null,external:ss.some(s=>s.external.value===true)?true:complete&&ss.every(s=>s.external.value===false)?false:null};}
function metrics(d){const summaries=d.agents.map(a=>summarize(a,d));const flag=k=>({count:summaries.filter(s=>s[k]===true).length,unknown:summaries.filter(s=>s[k]===null).length,partial:!d.complete});return {discovered:d.discoveredContainers.value===null?null:d.discoveredContainers.value.length,connected:new Set(summaries.flatMap(s=>s.containers)).size,connectionsUnknown:!d.complete||d.agents.some(a=>!a.sourcesComplete||a.sources===null||(a.sources||[]).some(s=>s.container.value===null)),mixed:flag('mixed'),multiple:flag('multiple'),external:flag('external')};}
function filtered(d,f){return d.agents.flatMap(a=>(a.sources||[]).map(s=>({a,s}))).filter(({a,s})=>{
const q=[a.name,a.packageId,a.platform,...a.owners||[],s.name.value,s.type.value,s.location.value].join(' ').toLowerCase();
return (!f.search||q.includes(f.search.toLowerCase()))&&(!f.agent||a.packageId===f.agent)&&(!f.platform||a.platform===f.platform)&&(!f.type||s.type.value===f.type)&&(!f.label||(f.label==='unknown'?(s.containerLabel.value===null&&s.container.value?.kind!=='notApplicable'):f.label==='notApplicable'?s.container.value?.kind==='notApplicable':s.containerLabel.value===f.label))&&(!f.external||(f.external==='unknown'?s.external.value===null:String(s.external.value)===f.external));});}
const api={validate,summarize,metrics,filtered,fields};root.KnowledgeModel=api;if(typeof module!=='undefined')module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
