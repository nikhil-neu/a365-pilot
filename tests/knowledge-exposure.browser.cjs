// Optional integration test: requires Playwright and a Chrome/Chromium executable.
const {chromium}=require('playwright');
const assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',args:['--disable-background-networking','--disable-component-update','--no-first-run']});
 try{
 const page=await browser.newPage({viewport:{width:1440,height:1100}}),errors=[],network=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url()))network.push(r.url());});
 await page.goto('file://'+path.resolve(__dirname,'../dashboards/knowledge-exposure/index.html'));
 await page.waitForSelector('#rows tr');assert.equal(await page.locator('#rows tr').count(),5);assert.match(await page.locator('#banner').innerText(),/SAMPLE DATA/);
 assert.equal(await page.locator('#agents .agent-card').count(),4);
 await page.locator('#external').selectOption('true');assert.equal(await page.locator('#rows tr').count(),1);assert.match(await page.locator('#detail').innerText(),/Market reference/);
 await page.locator('#clear').click();await page.locator('#search').fill('demo hr');assert.equal(await page.locator('#rows tr').count(),2);
 await page.locator('[data-sort="name"]').click();assert.equal(await page.locator('[data-sort="name"]').evaluate(e=>e.parentElement.getAttribute('aria-sort')),'descending');
 await page.locator('#clear').click();await page.locator('#agent').selectOption('sample-support');assert.equal(await page.locator('#rows tr').count(),0);assert.match(await page.locator('#agents').innerText(),/inventory unavailable/);
 await page.locator('#sample').click();await page.locator('#detail details').first().locator('summary').click();assert.match(await page.locator('#detail').innerText(),/Synthetic runtime metadata/);
 const fixture=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../dashboards/knowledge-exposure/sample.json')));
 fixture.dataKind='tenant-export';fixture.name='<img src=x onerror=alert(1)>';fixture.complete=true;fixture.agents=[];fixture.discoveredContainers.value=null;
 await page.locator('#upload').setInputFiles({name:'export.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(fixture))});
 await page.waitForFunction(()=>document.querySelector('#banner').textContent.startsWith('TENANT EXPORT'));
 assert.equal(await page.locator('img').count(),0);assert.match(await page.locator('#metrics').innerText(),/Not available/);assert.equal(await page.locator('#rows tr').count(),0);
 await page.locator('#upload').setInputFiles({name:'bad.json',mimeType:'application/json',buffer:Buffer.from('{"token":"not-allowed"}')});
 await page.waitForSelector('#error:not([hidden])');assert.match(await page.locator('#banner').innerText(),/TENANT EXPORT/);
 await page.locator('#sample').click();assert.equal(await page.locator('#rows tr').count(),5);
 await page.screenshot({path:'/tmp/a365-knowledge-desktop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));await page.screenshot({path:'/tmp/a365-knowledge-mobile.png',fullPage:true});
 assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),'Mobile page overflow');
 await page.screenshot({path:'/tmp/a365-knowledge-mobile-top.png'});await page.locator('#detail').scrollIntoViewIfNeeded();await page.screenshot({path:'/tmp/a365-knowledge-mobile-detail.png'});
 assert.deepEqual(errors,[]);assert.deepEqual(network,[]);
 console.log('PASS: file:// render, filters, sort, unavailable agents, evidence detail, import, XSS-safe text, rejected import, reset, mobile width and zero HTTP requests');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
