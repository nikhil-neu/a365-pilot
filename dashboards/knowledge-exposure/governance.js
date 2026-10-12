/* Data-first projection of the existing metadata-only snapshot. No inferred permissions. */
(function(root){
'use strict';
function group(data){
 const groups=new Map();
 for(const a of data.agents)for(const s of a.sources||[]){
  const c=s.container.value,location=s.location.value;
  const key=location?JSON.stringify(['location',location]):c?.id?JSON.stringify(['container',c.kind,c.id]):JSON.stringify(['unresolved',a.packageId,s.id]);
  if(!groups.has(key))groups.set(key,{location:location||c?.id||null,entries:[],agents:[],findings:[]});
  const g=groups.get(key);g.entries.push({a,s});if(!g.agents.some(x=>x.packageId===a.packageId))g.agents.push(a);
 }
 for(const g of groups.values()){
  const ss=g.entries.map(r=>r.s);
  if(ss.some(s=>!s.container.value))g.findings.push('Container mapping unresolved: obtain authoritative identifiers before proposing site-scoped changes.');
  if(ss.some(s=>s.containerLabel.value===null&&s.container.value?.kind!=='notApplicable'))g.findings.push('Container classification unknown: obtain label evidence from the authoritative service.');
  if(ss.some(s=>s.contentLabels.value===null))g.findings.push('File classification unavailable: inspect content-label metadata; a site label does not label its files.');
  if(ss.some(s=>s.external.value===true))g.findings.push('External source recorded: confirm ownership and permitted use; this does not demonstrate internal data leakage.');
  if(g.agents.length>1)g.findings.push('Shared dependency: review the impact on all connected agents before changing this data source.');
  g.findings.push('Access and DLP require review: effective permissions, sharing and policy coverage are not present in this snapshot format.');
 }
 return [...groups.values()];
}
root.KnowledgeGovernance={group};if(typeof module!=='undefined')module.exports={group};
})(typeof globalThis!=='undefined'?globalThis:this);
