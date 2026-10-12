'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.resolve(__dirname,'..'),M=require('../dashboards/knowledge-exposure/model.js');
const fixture=JSON.parse(fs.readFileSync(path.join(root,'dashboards/knowledge-exposure/sample.json')));
const copy=()=>JSON.parse(JSON.stringify(fixture));
M.validate(fixture);
const context={window:{}};vm.runInNewContext(fs.readFileSync(path.join(root,'dashboards/knowledge-exposure/sample.js'),'utf8'),context);assert.equal(JSON.stringify(context.window.KNOWLEDGE_SAMPLE),JSON.stringify(fixture));
assert.equal(M.metrics(fixture).discovered,5);assert.equal(M.metrics(fixture).connected,4);assert.equal(M.metrics(fixture).mixed.count,1);assert.equal(M.metrics(fixture).external.count,1);
const people=M.summarize(fixture.agents[0],fixture);assert.equal(people.highest,'Internal');assert.equal(people.mixed,true);assert.equal(people.multiple,true);assert.equal(people.external,false);
assert.equal(M.summarize(fixture.agents[2],fixture).mixed,null);assert.equal(M.summarize(fixture.agents[3],fixture).external,null);
let d=copy();d.labels.find(l=>l.id==='internal').rank=null;assert.equal(M.summarize(d.agents[0],d).highest,null);
d=copy();d.agents[0].sources[1].container.value.id='site-people';assert.equal(M.summarize(d.agents[0],d).multiple,false);
d=copy();d.agents[0].sources[1].containerLabel.value=null;assert.equal(M.summarize(d.agents[0],d).mixed,null);assert.equal(M.summarize(d.agents[0],d).unknownLabels,1);
d=copy();d.complete=true;d.agents=[];d.discoveredContainers.value=null;assert.equal(M.metrics(d).mixed.count,0);assert.equal(M.metrics(d).mixed.partial,false);assert.equal(M.metrics(d).discovered,null);
assert.equal(M.filtered(fixture,{external:'true'}).length,1);assert.equal(M.filtered(fixture,{search:'demo hr'}).length,2);assert.equal(M.filtered(fixture,{agent:'sample-people',label:'public'}).length,1);
for(const change of [d=>d.agents.push(d.agents[0]),d=>d.agents[0].sources[0].external.value='true',d=>d.agents[0].sources[0].runtimeRetrieved.evidence.checkedAt=null,d=>d.agents[0].sources[0].containerLabel.value='invented',d=>d.agents[0].sources[0].location.value='https://example.invalid/?token=secret',d=>d.prompt='forbidden',d=>d.agents[3].sourcesComplete=true]){d=copy();change(d);assert.throws(()=>M.validate(d));}
console.log('PASS: sample consistency, counts, unknowns, label order, distinct containers, filters and invalid metadata rejection');

{
const governance = require('../dashboards/knowledge-exposure/governance.js');
const fixture = require('../dashboards/knowledge-exposure/sample.json');
const grouped = governance.group(fixture);
require('node:assert/strict').equal(grouped.reduce((n,g)=>n+g.entries.length,0),fixture.agents.reduce((n,a)=>n+(a.sources||[]).length,0));
const unknown = JSON.parse(JSON.stringify(fixture));
for(const a of unknown.agents)for(const s of a.sources||[]){s.location.value=null;s.container.value=null;}
require('node:assert/strict').equal(governance.group(unknown).length,unknown.agents.reduce((n,a)=>n+(a.sources||[]).length,0));
console.log('PASS: governance preserves relationships and keeps unresolved locations separate');

}
