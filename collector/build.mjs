import { build } from 'esbuild';
await build({entryPoints:['index.mjs'], bundle:true, platform:'node', target:'node24', format:'esm',
  banner:{js:"import{createRequire as ___cr}from'node:module';import{fileURLToPath as ___fu}from'node:url';import{dirname as ___dn}from'node:path';const require=___cr(import.meta.url);const __filename=___fu(import.meta.url);const __dirname=___dn(__filename);"},
  outfile:'dist/index.mjs'});
