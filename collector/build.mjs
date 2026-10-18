import { build } from 'esbuild';
await build({entryPoints:['index.mjs'], bundle:true, platform:'node', target:'node24', format:'esm',
  banner:{js:"import{createRequire as ___cr}from'node:module';const require=___cr(import.meta.url);"},
  outfile:'dist/index.mjs'});
