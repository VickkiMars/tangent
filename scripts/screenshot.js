const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  const page = await browser.newPage();
  
  await page.setViewport({ width: 1400, height: 900, deviceScaleFactor: 2 });
  
  console.log('Navigating to http://localhost:5173/marketing');
  await page.goto('http://localhost:5173/marketing', { waitUntil: 'networkidle0' });
  
  // Wait to ensure ReactFlow finishes layouting the nodes
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  const path = '/home/kami/.gemini/antigravity/brain/0744af8e-9291-4ca4-9456-e14b7c2be707/tangent_graph_ui.png';
  await page.screenshot({ path });
  console.log('Saved screenshot to', path);
  
  await browser.close();
})();
