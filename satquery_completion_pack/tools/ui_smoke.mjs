import { chromium } from 'playwright';
import fs from 'fs'; import path from 'path';
const root=process.argv[2]; if(!root) throw new Error('Pass project root');
const out=path.join(root,'docs','evidence'); fs.mkdirSync(out,{recursive:true});
const browser=await chromium.launch({headless:true}); const page=await browser.newPage({viewport:{width:1440,height:900}}); const errors=[];
page.on('console',m=>{if(m.type()==='error') errors.push('console: '+m.text())}); page.on('pageerror',e=>errors.push('pageerror: '+e.message));
await page.goto('http://127.0.0.1:8080',{waitUntil:'networkidle',timeout:60000}); const title=await page.title(); const buttons=await page.locator('button').count(); await page.screenshot({path:path.join(out,'ui_desktop.png'),fullPage:true});
const labels=['Single image','Optical + SAR','Before / After']; const clicks={};
for(const text of labels){ const loc=page.getByRole('button',{name:text,exact:false}); clicks[text]=await loc.count(); if(clicks[text]){await loc.first().click(); await page.waitForTimeout(300);} }
await page.setViewportSize({width:390,height:844}); await page.reload({waitUntil:'networkidle'}); await page.screenshot({path:path.join(out,'ui_mobile.png'),fullPage:true}); const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth+2);
const report={title,button_count:buttons,mode_button_matches:clicks,console_or_page_errors:errors,mobile_horizontal_overflow:overflow,pass:errors.length===0&&!overflow&&buttons>0}; fs.writeFileSync(path.join(out,'UI_SMOKE.json'),JSON.stringify(report,null,2)); console.log(JSON.stringify(report,null,2)); await browser.close(); if(!report.pass) process.exit(2);

