import { EXPERIMENT } from './core.mjs';
export function postgresStore(pool) {
  const query=(sql,args=[])=>pool.query(sql,args);
  async function locked(work) {
    const client=await pool.connect();
    try {await client.query('BEGIN');await client.query('SELECT pg_advisory_xact_lock(19271019)');
      const result=await work(client);await client.query('COMMIT');return result;
    } catch(error) {await client.query('ROLLBACK');throw error;} finally {client.release();}
  }
  const capacity=()=>{const e=new Error('Capacity');e.code='CAPACITY';throw e;};
  return {
    async admit(row) {return locked(async c=>{
      const day=new Date(row.created_at).toISOString().slice(0,10);
      const counts=await c.query('SELECT count(*)::int AS n FROM validation_sessions');
      const daily=await c.query('SELECT admissions FROM validation_limits WHERE day=$1',[day]);
      if(counts.rows[0].n>=5000 || (daily.rows[0]?.admissions||0)>=500) capacity();
      await c.query('INSERT INTO validation_limits(day,admissions) VALUES($1,1) ON CONFLICT(day) DO UPDATE SET admissions=validation_limits.admissions+1',[day]);
      await c.query('INSERT INTO validation_sessions(id,created_at,source,role,measurement,test,flags) VALUES($1,$2,$3,$4,$5,$6,0)',
        [row.id,row.created_at,row.source,row.role,row.measurement,row.test]);
    });},
    async session(id) {return (await query('SELECT * FROM validation_sessions WHERE id=$1',[id])).rows[0];},
    async event(id,flag) {await query('UPDATE validation_sessions SET flags=flags|$2 WHERE id=$1 AND flags&$2=0',[id,flag]);},
    async interest(row) {return locked(async c=>{
      if((await c.query('SELECT count(*)::int AS n FROM validation_interest')).rows[0].n>=500) capacity();
      const fields=Object.keys(row), values=Object.values(row);
      return (await c.query(`INSERT INTO validation_interest(${fields.join(',')}) VALUES(${fields.map((_,i)=>`$${i+1}`).join(',')}) ON CONFLICT(email_hash) DO NOTHING`,values)).rowCount===1;
    });},
    async forget(id) {await query('DELETE FROM validation_sessions WHERE id=$1',[id]);},
    async withdraw(receipt) {await query('DELETE FROM validation_interest WHERE receipt_hash=$1',[receipt]);},
    async purge(cutoff) {await locked(async c=>{
      await c.query('DELETE FROM validation_sessions WHERE created_at<$1',[cutoff]);
      await c.query('DELETE FROM validation_interest WHERE created_at<$1',[cutoff]);
      await c.query('DELETE FROM validation_limits WHERE day<$1',[new Date(cutoff).toISOString().slice(0,10)]);
    });},
    async summary() {
      const visits=(await query(`SELECT count(*) FILTER(WHERE flags&1=1)::int AS engaged_sessions,
        count(*) FILTER(WHERE flags&3=3 AND role<>'other')::int AS candidate_relevant_sessions,
        count(*) FILTER(WHERE flags&2=2)::int AS product_interactions,
        count(*) FILTER(WHERE flags&7=7 AND role<>'other')::int AS completed_evaluations,
        count(*) FILTER(WHERE flags&8=8)::int AS sample_sessions
        FROM validation_sessions WHERE NOT test AND measurement`)).rows[0];
      const leads=(await query(`SELECT count(*)::int AS registrations,
        count(*) FILTER(WHERE pilot)::int AS pilot_requests,
        count(*) FILTER(WHERE pilot AND role<>'other' AND platform='shopify' AND timing='30days')::int AS qualified_pilots_unverified,
        count(*) FILTER(WHERE willingness='yes' AND role<>'other' AND platform='shopify' AND timing='30days')::int AS willing_to_pay_unverified,
        count(*) FILTER(WHERE independently_verified AND willingness='yes' AND role<>'other' AND platform='shopify' AND timing='30days')::int AS independently_verified_willing_to_pay
        FROM validation_interest WHERE NOT test`)).rows[0];
      const sources=(await query(`SELECT source,count(*)::int AS sessions FROM validation_sessions
        WHERE NOT test AND measurement AND flags&3=3 AND role<>'other' GROUP BY source`)).rows;
      return {experiment:EXPERIMENT,window_days:30,price_cents:900,currency:'EUR',...visits,...leads,
        acquisition_sources:sources,verified_relevant_people:null,
        decision:leads.independently_verified_willing_to_pay>=3?'review_evidence':'distribution_unresolved',
        caveat:'Consented sessions are not verified unique people. Registrations and stated intent remain unverified until reviewed. No payments are available.'};
    }
  };
}
