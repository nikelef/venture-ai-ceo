import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createDecipheriv } from 'node:crypto';
import vm from 'node:vm';
import {createHandler, CONSENT, sha} from '../collector/core.mjs';
const origin='https://venture-ai-ceo-evaluator.onrender.com';
function fixture(stopped=false) {
  const sessions=new Map(),leads=new Map();let now=1792357200000;
  const config={origin,contactKey:Buffer.alloc(32,7).toString('base64'),readKey:'test-only-read-key',qaKey:'test-only-qa-key',stopped};
  const store={
    async admit(s){sessions.set(s.id,s);},async session(id){return sessions.get(id);},
    async event(id,flag){sessions.get(id).flags|=flag;},
    async interest(row){if(leads.has(row.email_hash))return false;leads.set(row.email_hash,row);return true;},
    async withdraw(receipt){for(const [k,v] of leads)if(v.receipt_hash===receipt)leads.delete(k);},
    async forget(id){sessions.delete(id);},async purge(cutoff){for(const [k,v] of sessions)if(v.created_at<cutoff)sessions.delete(k);},
    async summary(){return {sessions:sessions.size,registrations:leads.size};}
  };
  const handle=createHandler(store,config,()=>now);
  const call=(path,data,token,headers={})=>handle(new Request('https://collector.example'+path,{
    method:data===undefined?'GET':'POST',headers:{origin,'content-type':'application/json','user-agent':'Mozilla/5.0',
      ...(token?{authorization:`Bearer ${token}`} : {}),...headers},...(data===undefined?{}:{body:JSON.stringify(data)})}));
  const begin=async(measurement=true,headers={})=>{
    const r=await call('/session',{consent:CONSENT,measurement,role:'agency',source:'guide',website:'',automated:false},null,headers);
    assert.equal(r.status,201);return (await r.json()).token;
  };
  const interest={email:'pilot@example.invalid',role:'agency',platform:'shopify',timing:'30days',problem:'handoff',pilot:true,willingness:'yes',price_cents:900,currency:'EUR',consent:CONSENT,website:''};
  return {call,begin,sessions,leads,interest,config,advance:ms=>{now+=ms;},store};
}
test('collector fails closed without encryption and access secrets',()=>{
  assert.throws(()=>createHandler({},{}),/secrets/);
});
test('explicit consent, allowed origin, honeypot and bot checks protect admission',async()=>{
  const f=fixture();
  const body={consent:CONSENT,measurement:true,role:'agency',source:'direct',website:'',automated:false};
  for(const change of [{consent:false},{website:'spam'},{automated:true},{role:'ceo'},{csv:'private-catalog'}])
    assert.equal((await f.call('/session',{...body,...change})).status,400);
  assert.equal((await f.call('/session',body,null,{origin:'https://other.invalid'})).status,403);
  assert.equal((await f.call('/session',body,null,{'user-agent':'Googlebot'})).status,403);
  assert.equal(f.sessions.size,0);
  const first=await f.begin();assert.equal(f.sessions.get(sha(first)).consent_version,CONSENT);
  f.advance(30*86400000+1);await f.begin();assert.equal(f.sessions.size,1);
});
test('bounded JSON rejects excess data and requests without valid authentication',async()=>{
  const f=fixture();
  assert.equal((await f.call('/event',{event:'interaction'})).status,401);
  assert.equal((await f.call('/session',{x:'a'.repeat(5000)})).status,413);
  assert.equal((await f.call('/upload',{csv:'value'})).status,404);
  assert.equal((await f.call('/checkout',{})).status,404);
  assert.equal((await f.call('/summary')).status,401);
  assert.equal((await f.call('/session',{},null,{'content-type':'text/plain'})).status,415);
});
test('real evaluation is separate from a sample, needs engagement, and flags are idempotent',async()=>{
  const f=fixture(), token=await f.begin();
  assert.equal((await f.call('/event',{event:'engaged'},token)).status,400);
  assert.equal((await f.call('/event',{event:'evaluation_complete'},token)).status,400);
  f.advance(11000);
  for(const event of ['engaged','interaction','sample','sample']) assert.equal((await f.call('/event',{event},token)).status,200);
  assert.equal(f.sessions.get(sha(token)).flags,11);
  assert.equal((await f.call('/event',{event:'evaluation_complete'},token)).status,200);
  assert.equal(f.sessions.get(sha(token)).flags,15);
  assert.equal((await f.call('/event',{event:'interaction',report:{price:10}},token)).status,400);
  const noMetrics=await f.begin(false);
  assert.equal((await f.call('/event',{event:'interaction'},noMetrics)).status,403);
});
test('registration requires its own affirmative consent and exact displayed price',async()=>{
  const f=fixture(),token=await f.begin(false);f.advance(2500);
  for(const change of [{consent:false},{willingness:''},{price_cents:100},{currency:'USD'},{email:'bad'},{name:'extra'}, {pilot:'yes'}])
    assert.equal((await f.call('/interest',{...f.interest,...change},token)).status,400);
  assert.equal(f.leads.size,0);
  const r=await f.call('/interest',f.interest,token),body=await r.json();
  assert.equal(r.status,201);assert.equal(body.paid_order,false);assert.equal(body.email_verified,false);
  const row=[...f.leads.values()][0];assert.equal(row.independently_verified,undefined);
  assert.ok(!JSON.stringify(row).includes(f.interest.email));assert.equal(row.receipt_hash,sha(body.receipt));
  const encrypted=Buffer.from(row.encrypted_contact,'base64');
  const decipher=createDecipheriv('aes-256-gcm',Buffer.from(f.config.contactKey,'base64'),encrypted.subarray(0,12));
  decipher.setAuthTag(encrypted.subarray(12,28));
  assert.equal(Buffer.concat([decipher.update(encrypted.subarray(28)),decipher.final()]).toString(),f.interest.email);
  assert.equal((await f.call('/interest',f.interest,token)).status,400);
});
test('private receipt deletes only its matching registration; session and registration withdrawal are separate',async()=>{
  const f=fixture(),one=await f.begin(),two=await f.begin();f.advance(2500);
  const first=await (await f.call('/interest',f.interest,one)).json();
  const second=await (await f.call('/interest',{...f.interest,email:'second@example.invalid'},two)).json();
  assert.equal(f.leads.size,2);
  assert.equal((await f.call('/withdraw',{receipt:'x'.repeat(43)})).status,200);assert.equal(f.leads.size,2);
  await f.call('/withdraw',{receipt:first.receipt});assert.equal(f.leads.size,1);
  assert.ok([...f.leads.values()].some(x=>x.receipt_hash===sha(second.receipt)));
  await f.call('/forget',{},one);assert.equal(f.sessions.size,1);assert.equal(f.leads.size,1);
});
test('shutdown blocks public enrollment, QA stays marked synthetic, and privacy withdrawal remains usable',async()=>{
  const f=fixture(true);
  assert.equal((await f.call('/session',{consent:CONSENT})).status,503);
  const token=await f.begin(true,{'x-validation-qa':f.config.qaKey});
  assert.equal(f.sessions.get(sha(token)).test,true);
  assert.equal((await f.call('/forget',{},token)).status,200);
  assert.equal((await f.call('/withdraw',{receipt:'x'.repeat(43)})).status,200);
});
test('session expiry, safe failures and summary authorization fail closed',async()=>{
  const f=fixture(),token=await f.begin();f.advance(4*3600000+1);
  assert.equal((await f.call('/event',{event:'interaction'},token)).status,401);
  assert.equal((await f.call('/forget',{},token)).status,200);
  assert.equal(f.sessions.size,0);
  const summary=await f.call('/summary',undefined,f.config.readKey);assert.equal(summary.status,200);
  f.store.admit=async()=>{throw new Error('private secret and email must not appear');};
  const response=await f.call('/session',{consent:CONSENT,measurement:true,role:'agency',source:'direct',website:'',automated:false});
  assert.equal(response.status,503);assert.ok(!(await response.text()).includes('private secret'));
});
test('runtime diagnostics require the separate QA key and cannot expose records',async()=>{
  const f=fixture(true);let called=0;
  const status=await (await f.call('/status')).json();assert.equal(status.application,'venture-validation');assert.equal(status.collection_enabled,false);
  f.store.securityStatus=async()=>{called++;return {role:'venture_collector',privileged:false,tls:true,tls_authorized:true};};
  assert.equal((await f.call('/diagnostics')).status,401);
  assert.equal((await f.call('/diagnostics',undefined,f.config.readKey)).status,401);
  assert.equal(called,0);
  const r=await f.call('/diagnostics',undefined,null,{'x-validation-qa':f.config.qaKey});
  assert.equal(r.status,200);assert.equal((await r.json()).tls_authorized,true);assert.equal(called,1);
});
test('SQL metrics exclude QA and cannot self-confirm independence; no catalog or payment tables',()=>{
  const store=readFileSync(new URL('../collector/store.mjs',import.meta.url),'utf8');
  const schema=readFileSync(new URL('../collector/schema.sql',import.meta.url),'utf8');
  assert.equal((store.match(/WHERE NOT test/g)||[]).length,3);
  assert.match(store,/independently_verified AND willingness='yes'/);
  assert.match(schema,/independently_verified boolean NOT NULL DEFAULT false/);
  assert.ok(!/CREATE TABLE[^;]*(?:payment|catalog_content)/i.test(schema));
});
function browserFixture() {
  const elements=new Map(),events=[];
  function element(id){if(!elements.has(id))elements.set(id,{value:'',checked:false,disabled:false,hidden:true,files:[],listeners:{},
    addEventListener(name,fn){this.listeners[name]=fn;},replaceChildren(){},append(){}});return elements.get(id);}
  const context={document:{getElementById:element,createElement:()=>({})},window:{dispatchEvent:e=>events.push(e.detail)},
    CustomEvent:class{constructor(type,args){this.type=type;this.detail=args.detail;}},TextDecoder,
    CatalogPreflight:{LIMITS:{bytes:2000000},CsvError:Error,analyzeCsv:()=>({data_records:2,errors:0,warnings:0,issues:[]})}};
  vm.runInNewContext(readFileSync(new URL('../web/app.js',import.meta.url),'utf8'),context);
  return {element,events};
}
test('browser sample never counts as a real evaluation, even when the real-catalog box was previously checked',async()=>{
  const f=browserFixture();f.element('real-catalog').checked=true;
  f.element('sample').listeners.click();f.element('profile').listeners.change();
  assert.ok(f.events.includes('sample'));assert.ok(!f.events.includes('evaluation_complete'));
  f.element('csv-file').files=[{size:20,arrayBuffer:async()=>new TextEncoder().encode('real,csv').buffer}];
  await f.element('csv-file').listeners.change();assert.ok(f.events.includes('evaluation_complete'));
});
test('public offer separates free functionality, proposed price and non-binding intent',()=>{
  const html=readFileSync(new URL('../web/index.html',import.meta.url),'utf8');
  assert.match(html,/Paid purchasing is not currently available/);
  assert.match(html,/Yes, I would pay €9/);assert.match(html,/Expression of interest/);
  assert.ok(!/<input[^>]+id="interest-consent"[^>]+\bchecked/.test(html));
  assert.ok(!/<option[^>]+value="yes"[^>]+selected/.test(html));
  assert.ok(!html.includes('name="robots" content="noindex'));
});
test('page load and scripted clicks cannot start optional collection; pause disables the form',async()=>{
  for(const enabled of [false,true]) {
    const items=new Map();let calls=0;
    const el=id=>{if(!items.has(id))items.set(id,{disabled:false,hidden:true,value:'agency',checked:false,textContent:'',elements:[{disabled:false}],listeners:{},addEventListener(n,f){this.listeners[n]=f;}});return items.get(id);};
    const context={window:{VentureExperiment:{enabled,endpoint:'https://example.invalid',consent:CONSENT},addEventListener(){}},
      document:{getElementById:el,addEventListener(){},visibilityState:'visible'},fetch(){calls++;throw new Error('Unexpected collection');},
      setInterval(){},setTimeout(){},URLSearchParams,URL,AbortSignal,location:{search:'',hostname:'example.invalid'},navigator:{webdriver:false}};
    vm.runInNewContext(readFileSync(new URL('../web/demand.js',import.meta.url),'utf8'),context);
    assert.equal(calls,0);
    if(!enabled) {assert.equal(el('interest-submit').disabled,true);assert.equal(el('interest-form').elements[0].disabled,true);}
    else {await el('measurement-yes').listeners.click({isTrusted:false});assert.equal(calls,0);}
  }
});
