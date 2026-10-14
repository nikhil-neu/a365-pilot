const {chromium}=require('playwright');
const assert=require('node:assert/strict'),path=require('node:path');
(async()=>{const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',args:['--disable-background-networking']});try{
const page=await browser.newPage({viewport:{width:1440,height:1000}});const errors=[],network=[];page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url()))network.push(r.url());});
await page.goto('file://'+path.resolve('dashboards/knowledge-exposure/wireframe.html'));
assert.equal(await page.locator('#rows tr').count(),5);assert.match(await page.locator('#banner').innerText(),/SAMPLE DATA/);
await page.locator('#filter').selectOption('unknown');assert.equal(await page.locator('#rows tr').count(),3);
await page.locator('#filter').selectOption('all');await page.locator('#search').fill('supplier');assert.equal(await page.locator('#rows tr').count(),1);await page.locator('.review-button').click();assert.match(await page.locator('.review-output').innerText(),/No action submitted/);
const data=JSON.parse(JSON.stringify(require('../dashboards/knowledge-exposure/file-governance.sample.json')));data.dataKind='tenant-export';data.name='<img src=x onerror=alert(1)>';data.files=[];
await page.locator('#upload').setInputFiles({name:'fixture.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(data))});await page.waitForFunction(()=>document.querySelector('#kind').textContent==='TENANT EXPORT');assert.equal(await page.locator('#rows tr').count(),0);assert.equal(await page.locator('img').count(),0);
await page.locator('#upload').setInputFiles({name:'bad.json',mimeType:'application/json',buffer:Buffer.from('{}')});await page.waitForSelector('#error:not([hidden])');assert.equal(await page.locator('#kind').innerText(),'TENANT EXPORT');
const downloaded=page.waitForEvent('download');await page.locator('#export').click();assert.equal((await downloaded).suggestedFilename(),'agent-governance-review.txt');
await page.locator('#reset').click();assert.equal(await page.locator('#rows tr').count(),5);
await page.setViewportSize({width:390,height:844});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Mobile overflow');await page.screenshot({path:'/tmp/file-governance-mobile.png',fullPage:true});assert.deepEqual(errors,[]);assert.deepEqual(network,[]);console.log('PASS: browser import, rejection retention, empty tenant export, safe rendering, filters, review draft, download, reset, mobile and no HTTP calls');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
