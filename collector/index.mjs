import pg from 'pg';
import { attachDatabasePool } from '@neon/functions';
import { createHandler } from './core.mjs';
import { postgresStore } from './store.mjs';
const database=new URL(process.env.VALIDATION_DATABASE_URL||'invalid:');
if(database.protocol!=='postgresql:' || database.username!=='venture_collector' || !database.hostname.endsWith('.neon.tech') || database.searchParams.get('sslmode')!=='verify-full')
  throw new Error('A verified, least-privilege collector database connection is required.');
const pool=new pg.Pool({connectionString:database.href,
  max:2,idleTimeoutMillis:10000,connectionTimeoutMillis:5000,statement_timeout:5000});
attachDatabasePool(pool);
const handle=createHandler(postgresStore(pool),{
  origin:'https://venture-ai-ceo-evaluator.onrender.com',
  contactKey:process.env.CONTACT_ENCRYPTION_KEY,readKey:process.env.VALIDATION_READ_KEY,
  qaKey:process.env.VALIDATION_QA_KEY,stopped:process.env.VALIDATION_STOPPED!=='false'});
export default {fetch:handle};
