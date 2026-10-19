"use strict";
(() => {
  const config=window.VentureExperiment, byId=id=>document.getElementById(id);
  const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
  if(!config.enabled) {
    byId('measurement-yes').disabled=true;byId('interest-submit').disabled=true;
    const message='Optional measurement and registration are paused pending collector deployment and security checks. The free checker works normally. Contact: ceoagentai@proton.me.';
    byId('measurement-status').textContent=message;byId('interest-status').textContent=message;
    for(const field of byId('interest-form').elements) field.disabled=true;
    return;
  }
  byId('measurement-yes').disabled=false;byId('interest-submit').disabled=false;
  for(const field of byId('interest-form').elements) field.disabled=false;
  let session=null, measuring=false, generation=0, queue=Promise.resolve(), engaged=false, receipt='';
  let trusted=false, activeSeconds=0;
  const source=()=>{
    const tag=new URLSearchParams(location.search).get('source');
    if(['guide','community','directory'].includes(tag)) return tag;
    try {
      const host=new URL(document.referrer).hostname;
      if(/(^|\.)(google\.[a-z.]+|bing\.com|duckduckgo\.com|search\.yahoo\.com)$/.test(host)) return 'organic';
      if(host===location.hostname) return 'guide';
      return 'other';
    } catch {return 'direct';}
  };
  const request=async(path,data,bearer)=>{
    if(!config?.endpoint) throw new Error('Registration is not available yet. The free checker still works.');
    const response=await fetch(config.endpoint+path,{method:'POST',credentials:'omit',referrerPolicy:'no-referrer',
      headers:{'Content-Type':'application/json',...(bearer?{Authorization:`Bearer ${bearer}`}:{})},
      body:JSON.stringify(data),signal:AbortSignal.timeout(15000)});
    let body;try{body=await response.json();}catch{throw new Error('The collector did not confirm a saved form. Please try later.');}
    if(!response.ok) throw new Error(body.error||'Request not confirmed. Please try later.');
    return body;
  };
  const begin=async(measurement,role)=>{
    const body=await request('/session',{consent:config.consent,measurement,role,source:source(),website:'',automated:!!navigator.webdriver});
    return {token:body.token,started:Date.now()};
  };
  document.addEventListener('pointerdown',e=>{if(e.isTrusted)trusted=true;},{passive:true});
  document.addEventListener('keydown',e=>{if(e.isTrusted)trusted=true;});
  setInterval(()=>{if(document.visibilityState==='visible' && trusted) activeSeconds++;},1000);
  async function waitEngaged(epoch) {
    while(measuring && generation===epoch && (!trusted || activeSeconds<10 || Date.now()-session.started<10500)) await pause(300);
    if(!measuring || generation!==epoch) return false;
    if(!engaged) {await request('/event',{event:'engaged'},session.token);engaged=true;}
    return true;
  }
  function track(event) {
    if(!measuring || !session || !trusted || document.visibilityState!=='visible') return;
    const epoch=generation;
    queue=queue.catch(()=>{}).then(async()=>{
      if(await waitEngaged(epoch)) await request('/event',{event},session.token);
    }).catch(()=>{byId('measurement-status').textContent='Some optional measurement could not be saved. It is not counted as confirmed.';});
  }
  byId('measurement-yes').addEventListener('click',async e=>{
    if(!e.isTrusted || measuring) return;
    const role=byId('visitor-role').value;
    if(!role) {byId('measurement-status').textContent='Choose a role, or continue without measurement.';return;}
    const epoch=++generation;
    byId('measurement-yes').disabled=true;
    try {
      const created=await begin(true,role);
      if(generation!==epoch) {await request('/forget',{},created.token);return;}
      session=created;measuring=true;engaged=false;
      byId('measurement-forget').hidden=false;
      byId('measurement-status').textContent='Optional measurement is on for this page session. You can stop and delete it below.';
      track('engaged');
    } catch(error) {byId('measurement-status').textContent=error.message;byId('measurement-yes').disabled=false;}
  });
  async function stop() {
    const old=session; generation++;measuring=false;session=null;engaged=false;
    byId('measurement-status').textContent='Optional measurement is off.';
    if(old) {
      try {await queue;await request('/forget',{},old.token);byId('measurement-status').textContent='Optional measurement is off and this session was deleted.';}
      catch {byId('measurement-status').textContent='Measurement stopped. Deletion could not be confirmed; retry while this page is open.';session=old;}
    }
    byId('measurement-forget').hidden=!session;byId('measurement-yes').disabled=false;
  }
  byId('measurement-no').addEventListener('click',stop);byId('measurement-forget').addEventListener('click',stop);
  window.addEventListener('catalog-action',e=>{
    // Only a fixed event name crosses this boundary; never accept file/report content.
    if(['interaction','evaluation_complete','sample','report_download'].includes(e.detail)) track(e.detail);
  });
  byId('interest-form').addEventListener('submit',async e=>{
    e.preventDefault();if(!e.isTrusted || !byId('interest-consent').checked) return;
    const status=byId('interest-status'), button=byId('interest-submit');button.disabled=true;
    status.textContent='Submitting your voluntary interest…';
    let registrationSession=null;
    try {
      registrationSession=session||await begin(false,byId('interest-role').value);
      await pause(Math.max(0,2200-(Date.now()-registrationSession.started)));
      const body=await request('/interest',{
        email:byId('work-email').value,role:byId('interest-role').value,platform:byId('interest-platform').value,
        timing:byId('interest-timing').value,problem:byId('interest-problem').value,pilot:byId('interest-pilot').checked,
        willingness:byId('interest-willingness').value,price_cents:config.price_cents,currency:'EUR',
        consent:config.consent,website:byId('interest-website').value
      },registrationSession.token);
      if(body.registered!==true || !body.receipt) throw new Error('Saved registration was not confirmed.');
      receipt=body.receipt;byId('receipt').textContent=receipt;byId('receipt-panel').hidden=false;
      byId('work-email').value='';byId('interest-consent').checked=false;
      status.textContent='Your expression of interest was saved. No purchase was made. Save your private deletion receipt below.';
    } catch(error) {status.textContent=error.message;}
    finally {
      if(registrationSession && registrationSession!==session) await request('/forget',{},registrationSession.token).catch(()=>{});
      button.disabled=false;
    }
  });
  byId('receipt-download').addEventListener('click',()=>{
    if(!receipt)return;
    const text=`Catalog Preflight voluntary registration\nPrivate deletion receipt: ${receipt}\nWithdraw at https://venture-ai-ceo-evaluator.onrender.com/#pilot-title\nThis is not an order. No payment was made.\n`;
    const url=URL.createObjectURL(new Blob([text],{type:'text/plain'}));
    const link=document.createElement('a');link.href=url;link.download='catalog-preflight-private-receipt.txt';link.click();
    setTimeout(()=>URL.revokeObjectURL(url),1000);
  });
  byId('withdraw').addEventListener('click',async()=>{
    try {await request('/withdraw',{receipt:byId('withdraw-receipt').value.trim()});byId('withdraw-status').textContent='Any registration matching this receipt has been deleted.';byId('withdraw-receipt').value='';}
    catch(error) {byId('withdraw-status').textContent=error.message;}
  });
})();
