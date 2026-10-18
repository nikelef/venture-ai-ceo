import { createHash, createHmac, createCipheriv, randomBytes, timingSafeEqual } from 'node:crypto';

export const EXPERIMENT = 'agency-handoff-v1';
export const CONSENT = '2026-10-19-v1';
export const PRICE = 900;
export const FLAGS = { engaged:1, interaction:2, evaluation_complete:4, sample:8, report_download:16 };
export const ROLES = ['agency','merchant','catalog','other'];
export const SOURCES = ['direct','organic','guide','community','directory','other'];
export const sha = value => createHash('sha256').update(value).digest('hex');
const token = () => randomBytes(32).toString('base64url');
const same = (a,b) => typeof a === 'string' && typeof b === 'string' &&
  Buffer.byteLength(a) === Buffer.byteLength(b) && timingSafeEqual(Buffer.from(a),Buffer.from(b));
class Invalid extends Error { constructor(status, message) { super(message); this.status=status; } }
function keys(data, allowed) {
  if (!data || Array.isArray(data) || typeof data !== 'object' || Object.keys(data).some(k=>!allowed.includes(k)))
    throw new Invalid(400,'Unsupported fields. Do not send catalog or personal data outside the registration email field.');
}
function choice(value, values) {
  if (!values.includes(value)) throw new Invalid(400,'Choose one of the displayed options.');
  return value;
}
async function jsonBody(request) {
  if (request.headers.get('content-type')?.split(';')[0] !== 'application/json') throw new Invalid(415,'JSON required.');
  if (Number(request.headers.get('content-length')||0)>4096) throw new Invalid(413,'Request too large.');
  const reader = request.body?.getReader();
  if (!reader) throw new Invalid(400,'Missing request.');
  let timer;
  try {
    const read = async () => {
      const chunks=[]; let size=0;
      while (true) {
        const {done,value}=await reader.read(); if(done) break;
        size+=value.length; if(size>4096) throw new Invalid(413,'Request too large.');
        chunks.push(value);
      }
      try {return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(Buffer.concat(chunks)));}
      catch {throw new Invalid(400,'Invalid JSON.');}
    };
    return await Promise.race([read(), new Promise((_,reject)=>{
      timer=setTimeout(()=>{void reader.cancel();reject(new Invalid(408,'Request timeout.'));},3000);
    })]);
  } finally {clearTimeout(timer);void reader.cancel().catch(()=>{});}
}

export function createHandler(store, config, clock=()=>Date.now()) {
  if (!config.contactKey || Buffer.from(config.contactKey,'base64').length!==32 || !config.readKey || !config.qaKey)
    throw new Error('Collector secrets must be configured.');
  const encrypt = email => {
    const iv=randomBytes(12), cipher=createCipheriv('aes-256-gcm',Buffer.from(config.contactKey,'base64'),iv);
    const data=Buffer.concat([cipher.update(email,'utf8'),cipher.final()]);
    return Buffer.concat([iv,cipher.getAuthTag(),data]).toString('base64');
  };
  return async function handle(request) {
    const origin=request.headers.get('origin');
    const headers={'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store',
      'X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Vary':'Origin'};
    if(origin===config.origin) {
      headers['Access-Control-Allow-Origin']=origin;
      headers['Access-Control-Allow-Headers']='content-type,authorization';
      headers['Access-Control-Allow-Methods']='POST,OPTIONS';
    }
    const reply=(data,status=200)=>new Response(JSON.stringify(data),{status,headers});
    const path=new URL(request.url).pathname;
    try {
      if(path==='/healthz' && request.method==='GET') return reply({application:'venture-validation',experiment:EXPERIMENT,collection_enabled:!config.stopped,payments_enabled:false,uploads_enabled:false});
      if(path==='/summary' && request.method==='GET') {
        if(!same(request.headers.get('authorization'),`Bearer ${config.readKey}`)) throw new Invalid(401,'Unauthorized.');
        await store.purge(clock()-30*86400000);
        return reply({...await store.summary(),collection_enabled:!config.stopped});
      }
      if(!['/session','/event','/interest','/withdraw','/forget'].includes(path)) throw new Invalid(404,'Not found.');
      if(origin!==config.origin) throw new Invalid(403,'Origin not allowed.');
      if(request.method==='OPTIONS') return new Response(null,{status:204,headers});
      if(request.method!=='POST') throw new Invalid(405,'POST required.');
      if(config.stopped && !['/withdraw','/forget'].includes(path) && !same(request.headers.get('x-validation-qa'),config.qaKey))
        throw new Invalid(503,'Registration and optional measurement are paused. The free checker remains available.');
      if(!['/withdraw','/forget'].includes(path) && /bot|crawl|spider|headless|curl|python|wget|preview/i.test(request.headers.get('user-agent')||''))
        throw new Invalid(403,'Automated traffic is not enrolled in the customer experiment.');
      const data=await jsonBody(request), now=clock();
      if(path==='/session') {
        keys(data,['consent','measurement','role','source','website','automated']);
        if(data.consent!==CONSENT || typeof data.measurement!=='boolean' || data.website!=='' || data.automated!==false)
          throw new Invalid(400,'Affirmative consent and a person using the page are required.');
        choice(data.role,ROLES);choice(data.source,SOURCES);
        const raw=token(), id=sha(raw), test=same(request.headers.get('x-validation-qa'),config.qaKey);
        await store.admit({id,created_at:now,source:data.source,role:data.role,measurement:data.measurement,test,flags:0});
        return reply({token:raw,expires_in:14400,experiment:EXPERIMENT},201);
      }
      if(path==='/withdraw') {
        keys(data,['receipt']);
        if(!/^[A-Za-z0-9_-]{43}$/.test(data.receipt||'')) throw new Invalid(400,'Use your private registration receipt.');
        await store.withdraw(sha(data.receipt));
        return reply({withdrawn:true}); // Same response whether the receipt existed or not.
      }
      const raw=request.headers.get('authorization')?.replace(/^Bearer /,'')||'';
      if(!/^[A-Za-z0-9_-]{43}$/.test(raw)) throw new Invalid(401,'A consented session is required.');
      const id=sha(raw), session=await store.session(id);
      if(!session || now-session.created_at>4*3600000) throw new Invalid(401,'Session expired. Please consent again.');
      if(path==='/forget') {keys(data,[]);await store.forget(id);return reply({forgotten:true});}
      if(path==='/event') {
        keys(data,['event']);choice(data.event,Object.keys(FLAGS));
        if(!session.measurement) throw new Invalid(403,'Measurement consent required.');
        if(data.event==='engaged' && now-session.created_at<10000) throw new Invalid(400,'Keep the page active before counting a visit.');
        if(['evaluation_complete','report_download'].includes(data.event) && (session.flags&3)!==3)
          throw new Invalid(400,'An engaged product interaction is required first.');
        await store.event(id,FLAGS[data.event]);return reply({recorded:true});
      }
      keys(data,['email','role','platform','timing','problem','pilot','willingness','price_cents','currency','consent','website']);
      if(data.consent!==CONSENT || data.website!=='' || data.price_cents!==PRICE || data.currency!=='EUR' || typeof data.pilot!=='boolean')
        throw new Invalid(400,'Review the price and registration consent.');
      choice(data.role,ROLES);choice(data.platform,['shopify','other']);
      choice(data.timing,['30days','later','none']);choice(data.problem,['structure','variants','prices','handoff','other']);
      choice(data.willingness,['yes','no','unsure']);
      const email=typeof data.email==='string'?data.email.trim().toLowerCase():'';
      if(email.length>254 || !/^[^\s<>@]+@[^\s<>@]+\.[A-Za-z]{2,63}$/.test(email) || now-session.created_at<2000)
        throw new Invalid(400,'Check the work email and try again after a few seconds.');
      const receipt=token();
      const saved=await store.interest({email_hash:createHmac('sha256',Buffer.from(config.contactKey,'base64')).update(email).digest('hex'),
        encrypted_contact:encrypt(email),receipt_hash:sha(receipt),created_at:now,source:session.source,
        role:data.role,platform:data.platform,timing:data.timing,problem:data.problem,pilot:data.pilot,willingness:data.willingness,
        price_cents:PRICE,currency:'EUR',consent_version:CONSENT,test:session.test});
      if(!saved) throw new Invalid(400,'Registration could not be added. Check the fields; an existing registration needs its original receipt.');
      return reply({registered:true,receipt,pilot_requested:data.pilot,paid_order:false,email_verified:false},201);
    } catch(error) {
      if(error instanceof Invalid) return reply({error:error.message},error.status);
      if(error?.code==='CAPACITY') {headers['Retry-After']='3600';return reply({error:'Experiment capacity reached. Please try another day.'},429);}
      // Do not log errors, query arguments, request headers, catalog data or contact data.
      return reply({error:'Evidence collector unavailable. Your CSV is still processed only on your device. Please try later.'},503);
    }
  };
}
