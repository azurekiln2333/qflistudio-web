const fs = require('fs');
const src = fs.readFileSync('scripts/web_markup_assertions.mjs','utf8');
for (const id of ['html-example-018','html-example-030','html-example-031','html-example-035','html-example-060','html-example-065','html-example-069','html-example-076']) {
  const i = src.indexOf(`HTML_CASES.set('${id}'`);
  const end = src.indexOf('\n});', i);
  console.log('='.repeat(20), id);
  console.log(src.slice(i, end));
}
