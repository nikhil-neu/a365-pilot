'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const M=require('../dashboards/knowledge-exposure/file-governance-model.js');
const sample=require('../dashboards/knowledge-exposure/file-governance.sample.json');
const clone=()=>JSON.parse(JSON.stringify(sample));
M.validate(sample);assert.equal(M.assess(sample.files[2]).status,'unknown');assert.equal(M.assess(sample.files[2]).findings.length,0);
assert(M.assess(sample.files[0]).findings.some(s=>s.includes('no label')));
assert(M.assess(sample.files[4]).unknown.includes('dlp'));
for(const mutate of [d=>d.token='secret',d=>d.files.push(d.files[0]),d=>d.files[0].observations.label.evidence.checkedAt=null,d=>d.files[0].observations.label.value='invalid',d=>d.files[0].observations.sharing.state='unknown',d=>d.files[0].location='https://example.com/?token=abc',d=>d.files[0].agents[0].relationship='retrieved',d=>d.files[0].observations.labelName.value='conflicting']){const d=clone();mutate(d);assert.throws(()=>M.validate(d));}
const empty=clone();empty.dataKind='tenant-export';empty.files=[];M.validate(empty);assert.match(M.report(empty),/TENANT EXPORT/);assert.doesNotMatch(M.report(empty),/SAMPLE DATA/);
assert.match(M.report(sample),/SAMPLE DATA/);assert.match(M.report(sample),/Fictional label observation/);
const context={window:{}};vm.runInNewContext(fs.readFileSync('dashboards/knowledge-exposure/file-governance.sample.js','utf8'),context);assert.equal(JSON.stringify(context.window.FILE_GOVERNANCE_SAMPLE),JSON.stringify(sample));
console.log('PASS: evidence validation, unknown handling, findings, empty exports, metadata restrictions and sample consistency');
