const fs=require('fs');const src=fs.readFileSync('scripts/web_markup_assertions.mjs','utf8');
for (const id of ['html-example-010','html-example-054']) {
  const i=src.indexOf(`HTML_CASES.set('${id}'`);const e=src.indexOf('\n});',i);
  console.log('='.repeat(15),id);console.log(src.slice(i,e));
}
