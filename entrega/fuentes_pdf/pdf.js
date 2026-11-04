const { chromium } = require('playwright');
(async () => { const b = await chromium.launch(); const p = await b.newPage();
 await p.goto('file://' + process.argv[2], {waitUntil: 'networkidle'});
 await p.pdf({ path: process.argv[3], format: 'A4', printBackground: true, displayHeaderFooter: true,
   headerTemplate: '<span></span>', footerTemplate: '<div style="font-size:8px;width:100%;text-align:center;color:#777">BoletaYa SAS · Grupo 5 · <span class="pageNumber"></span> / <span class="totalPages"></span></div>',
   margin: {top:'15mm', bottom:'16mm', left:'14mm', right:'14mm'} });
 await b.close(); })();
