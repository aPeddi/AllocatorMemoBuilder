// Cross-language metric parity helper (used by test_regressions.py).
// Loads the built self-contained memo and calls the SAME fundMetrics the client (and the
// audit re-derivation) uses, on caller-supplied golden return series. The Python side
// then asserts these match metrics.py — so the JS and Python engines can never drift.
//   argv[2] = absolute path to exports/memo.html
//   argv[3] = JSON array of return-series (arrays of numbers)
// stdout  = {"rf": <A.rfUsed>, "results": [ fundMetrics(series), ... ]}
const { chromium } = require('playwright');
(async () => {
  const htmlPath = process.argv[2];
  const sets = JSON.parse(process.argv[3] || '[]');
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto('file://' + htmlPath);
  await p.waitForFunction(() => window.AMB && window.AMB.core && typeof window.AMB.core.fundMetrics === 'function', { timeout: 15000 });
  const results = await p.evaluate((s) => s.map((series) => window.AMB.core.fundMetrics(series)), sets);
  const rf = await p.evaluate(() => (window.AMB.rfUsed != null ? window.AMB.rfUsed : 0.02));
  console.log(JSON.stringify({ rf, results }));
  await b.close();
})().catch((e) => { console.error('ERR', (e && e.message) || e); process.exit(3); });
