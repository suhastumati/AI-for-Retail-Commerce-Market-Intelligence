/* ═══════════════════════════════════════════════════════════════
   BluePill AI — Retail Intelligence Dashboard  (app.js)
   Pure vanilla ES6+  ·  Chart.js 4
   ═══════════════════════════════════════════════════════════════ */

const API = '';
const VIEWS = ['dashboard', 'pricing', 'inventory', 'sentiment', 'competitors', 'forecast', 'news', 'profit'];
const TITLES = {
  dashboard:   'Executive Dashboard',
  pricing:     'Pricing Optimization',
  inventory:   'Inventory Management',
  sentiment:   'Sentiment Analytics',
  competitors: 'Competitor Intelligence',
  forecast:    'Demand Forecast',
  news:        'News & Geopolitical Events',
  profit:      'Profit Margin Engine',
};

// Chart colour palette
const C = {
  blue:  'rgba(0,102,204,', green: 'rgba(16,185,129,',
  amber: 'rgba(245,158,11,', red:   'rgba(239,68,68,',
  gray:  'rgba(107,114,128,', purple:'rgba(139,92,246,',
};
const fill  = (c, a=0.15) => c + a + ')';
const solid = (c) => c + '1)';

// ── utility ──────────────────────────────────────────────────
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);
const fmt = (n) => {
  if (n === undefined || n === null) return '—';
  if (n >= 1e7) return '₹' + (n / 1e7).toFixed(2) + ' Cr';
  if (n >= 1e5) return '₹' + (n / 1e5).toFixed(2) + ' L';
  if (n >= 1e3) return '₹' + n.toLocaleString('en-IN');
  return n.toLocaleString('en-IN');
};
const pct = (v) => (v > 0 ? '+' : '') + v.toFixed(1) + '%';
const stars = (r) => '★'.repeat(Math.round(r)) + '☆'.repeat(5 - Math.round(r));

// Chart.js defaults
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.legend.labels.padding = 16;
const charts = {};

// ── navigation ───────────────────────────────────────────────
function navigate(view) {
  $$('.view').forEach(v => v.classList.remove('active'));
  $$('.nav-item').forEach(n => n.classList.remove('active'));
  $(`#view-${view}`).classList.add('active');
  $(`.nav-item[data-view="${view}"]`).classList.add('active');
  $('#pageTitle').textContent = TITLES[view] || view;
  // sidebar close on mobile
  $('#sidebar').classList.remove('open');
  // load data
  loadView(view);
}

$$('.nav-item').forEach(el => {
  el.addEventListener('click', () => navigate(el.dataset.view));
});
$('#sidebar-toggle').addEventListener('click', () => {
  $('#sidebar').classList.toggle('open');
});

// ── data cache ───────────────────────────────────────────────
const cache = {};
async function api(path) {
  if (cache[path]) return cache[path];
  const res = await fetch(API + path);
  const data = await res.json();
  cache[path] = data;
  return data;
}

// ── view loader ──────────────────────────────────────────────
async function loadView(view) {
  try {
    if (view === 'dashboard')   await renderDashboard();
    if (view === 'pricing')     await renderPricing();
    if (view === 'inventory')   await renderInventory();
    if (view === 'sentiment')   await renderSentiment();
    if (view === 'competitors') await renderCompetitors();
    if (view === 'forecast')    await renderForecast();
    if (view === 'news')        await renderNews();
    if (view === 'profit')      await renderProfit();
  } catch (e) {
    console.error('Load error:', e);
  }
}

// ══════════════════════════════════════════════════════════════
// 1. DASHBOARD
// ══════════════════════════════════════════════════════════════
async function renderDashboard() {
  const d = await api('/api/dashboard');

  // ── KPIs ──
  const k = d.kpis;
  const kpiHtml = `
    <div class="kpi-card">
      <span class="kpi-label">Total Revenue</span>
      <span class="kpi-value">${fmt(k.total_revenue?.value)}</span>
      <span class="kpi-change ${k.total_revenue?.change > 0 ? 'up' : 'down'}">${pct(k.total_revenue?.change || 0)} ${k.total_revenue?.period || ''}</span>
    </div>
    <div class="kpi-card green">
      <span class="kpi-label">Avg Margin</span>
      <span class="kpi-value">${(k.avg_margin?.value || 0).toFixed(1)}%</span>
      <span class="kpi-change ${k.avg_margin?.change > 0 ? 'up' : 'down'}">${k.avg_margin?.change > 0 ? '+' : ''}${(k.avg_margin?.change || 0).toFixed(1)}pp</span>
    </div>
    <div class="kpi-card amber">
      <span class="kpi-label">Total Units Sold</span>
      <span class="kpi-value">${(k.total_units?.value || 0).toLocaleString('en-IN')}</span>
      <span class="kpi-change neutral">Monthly: ${k.total_units?.latest_monthly || 0}</span>
    </div>
    <div class="kpi-card ${k.avg_sentiment?.value > 0.6 ? 'green' : k.avg_sentiment?.value < 0.4 ? 'red' : ''}">
      <span class="kpi-label">Avg Sentiment</span>
      <span class="kpi-value">${(k.avg_sentiment?.value || 0).toFixed(3)}</span>
      <span class="kpi-change neutral">across all SKUs</span>
    </div>
  `;
  $('#kpiRow').innerHTML = kpiHtml;

  // ── Revenue chart ──
  const t = d.trend;
  makeChart('revChart', {
    type: 'line',
    data: {
      labels: t.dates,
      datasets: [
        { label: 'Revenue (₹)', data: t.revenue, borderColor: solid(C.blue), backgroundColor: fill(C.blue), fill: true, tension: .3, yAxisID: 'y' },
        { label: 'Margin %',    data: t.margin,  borderColor: solid(C.green), backgroundColor: fill(C.green,0), tension: .3, yAxisID: 'y1' },
      ],
    },
    options: { scales: {
      y:  { position: 'left',  title: { display: true, text: 'Revenue ₹' } },
      y1: { position: 'right', title: { display: true, text: 'Margin %' }, grid: { drawOnChartArea: false } },
    }},
  });

  // ── Units chart ──
  makeChart('unitsChart', {
    type: 'bar',
    data: {
      labels: t.dates,
      datasets: [{ label: 'Units', data: t.units, backgroundColor: fill(C.blue, 0.6), borderRadius: 4 }],
    },
    options: { scales: { y: { title: { display: true, text: 'Units Sold' } } } },
  });

  // ── Alerts ──
  const alerts = d.alerts || [];
  $('#alertBadge').textContent = alerts.length;
  $('#alertsList').innerHTML = alerts.length === 0
    ? '<div class="empty-state">No active alerts</div>'
    : alerts.slice(0, 8).map(a => `
      <div class="alert-item ${a.severity}">
        <span class="alert-sev ${a.severity}">${a.severity}</span>
        <div class="alert-body">
          <div class="alert-msg">${a.product} — ${a.message}</div>
          <div class="alert-action">↳ ${a.action}</div>
        </div>
      </div>`).join('');

  // ── Products table ──
  const tbody = $('#productsTable tbody');
  tbody.innerHTML = d.products.map(p => {
    const sentClr = p.avg_sentiment > 0.6 ? 'green' : p.avg_sentiment < 0.4 ? 'red' : 'amber';
    return `<tr>
      <td><code>${p.sku}</code></td>
      <td><strong>${p.product}</strong><br><small style="color:var(--text-secondary)">${p.brand}</small></td>
      <td>${p.category}</td>
      <td>${p.current_price ? fmt(p.current_price) : '—'}</td>
      <td>${p.has_sales ? p.avg_margin.toFixed(1) + '%' : '—'}</td>
      <td><span class="review-stars">${stars(p.avg_rating)}</span> ${p.avg_rating.toFixed(1)}</td>
      <td><span class="tag tag-${sentClr}">${p.avg_sentiment.toFixed(3)}</span></td>
      <td>${p.review_count}</td>
      <td>${p.has_sales ? '<span class="tag tag-green">Sales</span>' : ''} ${p.has_competitor ? '<span class="tag tag-blue">Comp</span>' : ''}</td>
    </tr>`;
  }).join('');
}

// ══════════════════════════════════════════════════════════════
// 2. PRICING
// ══════════════════════════════════════════════════════════════
let pricingData = [];
async function renderPricing() {
  pricingData = await api('/api/pricing');

  // summary KPIs
  const up = pricingData.filter(p => p.change_pct > 0).length;
  const down = pricingData.filter(p => p.change_pct < 0).length;
  const avgLift = pricingData.length > 0
    ? pricingData.reduce((s, p) => s + p.profit_change_pct, 0) / pricingData.length : 0;

  // Global event signal (from first product — shared across all)
  const globalSignal = pricingData[0]?.event_price_signal || {};
  const sigDir = globalSignal.direction || 'hold';
  const sigAdj = globalSignal.adjustment_pct || 0;
  const sigColor = sigDir === 'raise' ? 'var(--success)' : sigDir === 'lower' ? 'var(--danger)' : 'var(--text-secondary)';
  const sigArrow = sigDir === 'raise' ? '↑' : sigDir === 'lower' ? '↓' : '→';

  $('#pricingKpis').innerHTML = `
    <div class="kpi-card green"><span class="kpi-label">Price Increase</span><span class="kpi-value">${up}</span><span class="kpi-change neutral">products</span></div>
    <div class="kpi-card red"><span class="kpi-label">Price Decrease</span><span class="kpi-value">${down}</span><span class="kpi-change neutral">products</span></div>
    <div class="kpi-card"><span class="kpi-label">Avg Profit Lift</span><span class="kpi-value">${avgLift.toFixed(1)}%</span><span class="kpi-change neutral">from optimization</span></div>
    <div class="kpi-card amber"><span class="kpi-label">Live Event Signal</span>
      <span class="kpi-value" style="color:${sigColor}">${sigArrow} ${sigAdj > 0 ? '+' : ''}${sigAdj.toFixed(1)}%</span>
      <span class="kpi-change neutral">${sigDir.toUpperCase()} — market driven</span>
    </div>
  `;

  // Event signal banner (if there are meaningful signals)
  const topSigs = globalSignal.top_signals || [];
  if (topSigs.length > 0 && Math.abs(sigAdj) > 0.5) {
    const bannerColor = sigDir === 'raise' ? '#d1fae5' : sigDir === 'lower' ? '#fee2e2' : '#f3f4f6';
    const bannerBorder = sigDir === 'raise' ? 'var(--success)' : sigDir === 'lower' ? 'var(--danger)' : 'var(--border)';
    document.getElementById('pricingEventBanner').innerHTML = `
      <div style="background:${bannerColor};border-left:4px solid ${bannerBorder};border-radius:8px;padding:12px 16px;margin-bottom:16px">
        <div style="font-weight:700;font-size:.9rem;margin-bottom:6px">
          📰 Live Market Signal: ${globalSignal.summary || ''}
        </div>
        <div style="display:flex;flex-wrap:wrap;gap:8px">
          ${topSigs.map(s => {
            const a = s.adjustment_pct;
            const c = a > 0 ? 'var(--success)' : 'var(--danger)';
            const url = s.url ? `<a href="${s.url}" target="_blank" rel="noopener" style="color:var(--accent);margin-left:4px">↗</a>` : '';
            return `<div style="background:white;border-radius:6px;padding:6px 10px;font-size:.78rem;border:1px solid var(--border);max-width:320px">
              <span style="font-weight:600">${s.title.slice(0,60)}${s.title.length>60?'…':''}</span>${url}<br>
              <span style="color:var(--text-secondary)">${s.reason.slice(0,80)}</span>
              <span style="color:${c};font-weight:700;margin-left:6px">${a>0?'+':''}${a.toFixed(1)}%</span>
            </div>`;
          }).join('')}
        </div>
      </div>`;
    document.getElementById('pricingEventBanner').style.display = 'block';
  } else {
    document.getElementById('pricingEventBanner').style.display = 'none';
  }

  // pricing cards
  $('#pricingCards').innerHTML = pricingData.map((p, i) => {
    const arrow = p.change_pct > 0 ? '↑' : p.change_pct < 0 ? '↓' : '→';
    const clr = p.change_pct > 0 ? 'green' : p.change_pct < 0 ? 'red' : 'amber';
    const evSig = p.event_price_signal || {};
    const evDir = evSig.direction || 'hold';
    const evBadge = evDir !== 'hold'
      ? `<span class="tag tag-${evDir === 'raise' ? 'green' : 'red'}" title="${evSig.summary || ''}">📰 ${evDir}</span>`
      : '';
    return `<div class="pricing-card" onclick="showSensitivity(${i})">
      <div><div class="pc-name">${p.product}</div><div class="pc-sku">${p.sku} · ${p.brand || ''}</div></div>
      <div><small>Current</small><br><strong>${fmt(p.current_price)}</strong></div>
      <div><small>Optimal (Event-Adjusted)</small><br><strong style="color:var(--${clr === 'green' ? 'success' : clr === 'red' ? 'danger' : 'warning'})">${fmt(p.recommended_price)}</strong></div>
      <div><span class="tag tag-${clr}">${arrow} ${pct(p.change_pct)}</span></div>
      <div>${evBadge} <span class="tag tag-green">+${pct(p.profit_change_pct)} profit</span></div>
    </div>`;
  }).join('') || '<div class="empty-state">No pricing data — only SKUs with sales history can be optimized</div>';
}

function showSensitivity(idx) {
  const p = pricingData[idx];
  if (!p) return;
  const card = $('#sensitivityCard');
  card.style.display = 'block';
  $('#sensProduct').textContent = `${p.product} (${p.sku})`;

  // table
  const tb = $('#sensTable tbody');
  tb.innerHTML = p.sensitivity.map(s => {
    const hl = s.label ? ' style="font-weight:600;background:var(--blue-50)"' : '';
    return `<tr${hl}>
      <td>${fmt(s.price)}</td><td>${s.demand}</td><td>${fmt(s.revenue)}</td><td>${fmt(s.profit)}</td><td>${s.label}</td>
    </tr>`;
  }).join('');

  // risk checks + rationale + event signals
  const evSig = p.event_price_signal || {};
  const evHtml = evSig.top_signals?.length ? `
    <h4 style="margin:12px 0 8px;font-size:.85rem">📰 Live Event Drivers</h4>
    <div style="display:flex;flex-direction:column;gap:6px">
      ${(evSig.top_signals || []).map(s => {
        const a = s.adjustment_pct;
        const c = a > 0 ? 'var(--success)' : 'var(--danger)';
        const link = s.url ? `<a href="${s.url}" target="_blank" rel="noopener" style="color:var(--accent)"> ↗ ${s.source}</a>` : `<span style="color:var(--text-secondary)"> ${s.source}</span>`;
        return `<div style="font-size:.78rem;padding:6px 8px;background:var(--surface);border-radius:4px;border-left:3px solid ${c}">
          <strong>${s.title.slice(0,70)}${s.title.length>70?'…':''}</strong>${link}<br>
          <span style="color:var(--text-secondary)">${s.reason}</span>
          <span style="color:${c};font-weight:700;float:right">${a>0?'+':''}${a.toFixed(1)}% on price</span>
        </div>`;
      }).join('')}
    </div>` : '';

  $('#riskChecks').innerHTML = '<h4 style="margin-bottom:8px;font-size:.85rem">Risk Checks</h4>' +
    p.risk_checks.map(r => `<div class="risk-item"><span class="risk-icon">${r.pass ? '✅' : '⚠️'}</span> ${r.check}</div>`).join('') +
    '<h4 style="margin:12px 0 8px;font-size:.85rem">Optimization Rationale</h4>' +
    '<ul style="padding-left:16px;font-size:.82rem;color:var(--text-secondary)">' +
    p.rationale.map(r => `<li style="margin-bottom:4px">${r}</li>`).join('') + '</ul>' +
    evHtml;

  // chart
  makeChart('sensChart', {
    type: 'bar',
    data: {
      labels: p.sensitivity.map(s => fmt(s.price)),
      datasets: [
        { label: 'Revenue', data: p.sensitivity.map(s => s.revenue), backgroundColor: fill(C.blue, 0.5), yAxisID: 'y' },
        { label: 'Profit',  data: p.sensitivity.map(s => s.profit),  backgroundColor: fill(C.green, 0.5), yAxisID: 'y' },
      ],
    },
    options: { plugins: { title: { display: true, text: 'Revenue & Profit at Each Price Point' } } },
  });

  card.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ══════════════════════════════════════════════════════════════
// 3. INVENTORY
// ══════════════════════════════════════════════════════════════
async function renderInventory() {
  const inv = await api('/api/inventory');

  // KPIs
  const critical = inv.filter(i => i.urgency === 'critical').length;
  const optimal  = inv.filter(i => i.urgency === 'optimal').length;
  const totalCost = inv.reduce((s, i) => s + i.order_cost, 0);

  $('#invKpis').innerHTML = `
    <div class="kpi-card red"><span class="kpi-label">Critical Stock</span><span class="kpi-value">${critical}</span><span class="kpi-change neutral">products need reorder</span></div>
    <div class="kpi-card green"><span class="kpi-label">Optimal Stock</span><span class="kpi-value">${optimal}</span><span class="kpi-change neutral">within target</span></div>
    <div class="kpi-card"><span class="kpi-label">Total Order Cost</span><span class="kpi-value">${fmt(totalCost)}</span><span class="kpi-change neutral">pending POs</span></div>
    <div class="kpi-card amber"><span class="kpi-label">Products Tracked</span><span class="kpi-value">${inv.length}</span><span class="kpi-change neutral">with sales data</span></div>
  `;

  // Table
  const tb = $('#invTable tbody');
  tb.innerHTML = inv.map(i => {
    const urgTag = { critical: 'red', warning: 'amber', optimal: 'green', overstock: 'blue' }[i.urgency] || 'gray';
    return `<tr>
      <td><code>${i.sku}</code></td><td>${i.product}</td>
      <td>${i.current_stock}</td><td>${i.daily_demand}</td>
      <td><strong>${i.dio.toFixed(0)}</strong></td>
      <td>${i.reorder_point}</td><td>${i.eoq}</td>
      <td>${i.stockout_prob.toFixed(1)}%</td>
      <td><span class="tag tag-${urgTag}">${i.urgency}</span></td>
      <td>${i.order_qty || '—'}</td>
      <td>${i.order_cost ? fmt(i.order_cost) : '—'}</td>
    </tr>`;
  }).join('');

  // DIO chart
  makeChart('dioChart', {
    type: 'bar',
    data: {
      labels: inv.map(i => i.product),
      datasets: [
        { label: 'Days of Inventory', data: inv.map(i => i.dio), backgroundColor: inv.map(i => i.urgency === 'critical' ? solid(C.red) : i.urgency === 'warning' ? solid(C.amber) : solid(C.green)), borderRadius: 6 },
      ],
    },
    options: {
      indexAxis: 'y',
      plugins: { annotation: {} },
      scales: { x: { title: { display: true, text: 'Days' } } },
    },
  });

  // PO list
  const pos = inv.filter(i => i.order_qty > 0);
  $('#poList').innerHTML = pos.length === 0
    ? '<div class="empty-state">No purchase orders needed</div>'
    : '<div style="font-weight:600;margin-bottom:8px;font-size:.82rem;display:grid;grid-template-columns:2fr 1fr 1fr;gap:8px"><span>Product</span><span>Order Qty</span><span>Est. Cost</span></div>' +
      pos.map(i => `<div class="po-item"><span>${i.product}</span><span>${i.order_qty} units</span><span>${fmt(i.order_cost)}</span></div>`).join('');
}

// ══════════════════════════════════════════════════════════════
// 4. SENTIMENT
// ══════════════════════════════════════════════════════════════
let sentimentData = null;
async function renderSentiment() {
  sentimentData = await api('/api/sentiment');
  const sd = sentimentData;

  const skuEntries = Object.values(sd.per_sku || {});

  // KPIs
  const avgSent = sd.overall_avg || 0;
  const totalReviews = skuEntries.reduce((s, e) => s + e.review_count, 0);
  const avgFraud = skuEntries.length > 0
    ? skuEntries.reduce((s, e) => s + (e.fraud_pct || 0), 0) / skuEntries.length : 0;

  const sentClr = avgSent > 0.6 ? 'green' : avgSent < 0.4 ? 'red' : 'amber';

  $('#sentKpis').innerHTML = `
    <div class="kpi-card ${sentClr}"><span class="kpi-label">Overall Sentiment</span><span class="kpi-value">${avgSent.toFixed(3)}</span><span class="kpi-change neutral">${skuEntries.length} products analyzed</span></div>
    <div class="kpi-card"><span class="kpi-label">Total Reviews</span><span class="kpi-value">${totalReviews.toLocaleString()}</span><span class="kpi-change neutral">across all SKUs</span></div>
    <div class="kpi-card ${avgFraud > 10 ? 'red' : 'green'}"><span class="kpi-label">Avg Fraud %</span><span class="kpi-value">${avgFraud.toFixed(1)}%</span><span class="kpi-change neutral">flagged reviews</span></div>
    <div class="kpi-card"><span class="kpi-label">Products</span><span class="kpi-value">${skuEntries.length}</span><span class="kpi-change neutral">with sentiment data</span></div>
  `;

  // Sentiment bar chart
  makeChart('sentBarChart', {
    type: 'bar',
    data: {
      labels: skuEntries.map(e => e.product),
      datasets: [{
        label: 'Sentiment Score',
        data: skuEntries.map(e => e.avg_sentiment),
        backgroundColor: skuEntries.map(e => e.avg_sentiment > 0.6 ? solid(C.green) : e.avg_sentiment < 0.4 ? solid(C.red) : solid(C.amber)),
        borderRadius: 6,
      }],
    },
    options: { indexAxis: 'y', scales: { x: { min: 0, max: 1, title: { display: true, text: 'Sentiment (0–1)' } } } },
  });

  // Emotion chart
  const emos = sd.overall_emotions || {};
  makeChart('emotionChart', {
    type: 'doughnut',
    data: {
      labels: Object.keys(emos),
      datasets: [{
        data: Object.values(emos),
        backgroundColor: [solid(C.blue), solid(C.green), solid(C.amber), solid(C.red), solid(C.purple), solid(C.gray),
          fill(C.blue,0.6), fill(C.green,0.6), fill(C.amber,0.6), fill(C.red,0.6)],
      }],
    },
    options: { plugins: { legend: { position: 'right' } } },
  });

  // SKU select
  const sel = $('#sentSkuSelect');
  sel.innerHTML = skuEntries.map(e => `<option value="${e.sku}">${e.product} (${e.sku})</option>`).join('');
  sel.onchange = () => renderSkuSentiment(sel.value);
  if (skuEntries.length > 0) renderSkuSentiment(skuEntries[0].sku);

  // Recent reviews
  const reviews = sd.recent_reviews || [];
  $('#reviewsFeed').innerHTML = reviews.map(r => `
    <div class="review-item">
      <div class="review-meta">
        <span class="review-stars">${stars(r.rating)}</span>
        <span>${r.product}</span>
        <span>${r.date}</span>
      </div>
      <div>${r.text}</div>
    </div>`).join('') || '<div class="empty-state">No reviews</div>';
}

function renderSkuSentiment(sku) {
  const sd = sentimentData;
  const entry = sd.per_sku[sku];
  if (!entry) return;

  const aspects = entry.aspects || [];
  let html = `
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin-bottom:16px">
      <div><small>Avg Sentiment</small><br><strong style="font-size:1.2rem">${entry.avg_sentiment.toFixed(3)}</strong></div>
      <div><small>Avg Rating</small><br><strong style="font-size:1.2rem">${entry.avg_rating.toFixed(2)} / 5</strong></div>
      <div><small>Reviews</small><br><strong style="font-size:1.2rem">${entry.review_count}</strong></div>
      <div><small>Fraud %</small><br><strong style="font-size:1.2rem">${entry.fraud_pct.toFixed(1)}%</strong></div>
      <div><small>Sarcasm %</small><br><strong style="font-size:1.2rem">${entry.sarcasm_pct.toFixed(1)}%</strong></div>
    </div>
    <h4 style="font-size:.85rem;margin-bottom:8px">Top Emotions</h4>
    <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px">
      ${Object.entries(entry.top_emotions || {}).map(([em, ct]) => `<span class="tag tag-blue">${em}: ${ct}</span>`).join('')}
    </div>
  `;
  $('#sentDetails').innerHTML = html;

  // aspect grid
  const maxM = Math.max(...aspects.map(a => a.mentions), 1);
  $('#aspectGrid').innerHTML = aspects.length === 0
    ? '<div class="empty-state">No aspects detected</div>'
    : aspects.map(a => {
      const pct = ((a.sentiment + 1) / 2 * 100).toFixed(0);
      const clr = a.sentiment > 0.2 ? 'var(--success)' : a.sentiment < -0.2 ? 'var(--danger)' : 'var(--warning)';
      return `<div class="aspect-row">
        <span style="font-weight:500;text-transform:capitalize">${a.aspect}</span>
        <div class="aspect-bar-track"><div class="aspect-bar-fill" style="width:${pct}%;background:${clr}"></div></div>
        <span style="font-weight:600;color:${clr}">${a.sentiment > 0 ? '+' : ''}${a.sentiment.toFixed(2)}</span>
        <span class="tag tag-gray">${a.mentions}</span>
      </div>`;
    }).join('');
}

// ══════════════════════════════════════════════════════════════
// 5. COMPETITORS
// ══════════════════════════════════════════════════════════════
let compData = null;
async function renderCompetitors() {
  compData = await api('/api/competitors');
  const products = compData.products || [];

  if (products.length === 0) {
    $('#compCards').innerHTML = '<div class="empty-state">No competitor data available</div>';
    return;
  }

  $('#compCards').innerHTML = products.map((p, i) => {
    const posClr = { Premium: 'amber', Discount: 'green', Parity: 'blue' }[p.position] || 'gray';
    return `<div class="comp-card" onclick="showCompTrend(${i})">
      <div class="comp-header">
        <div><strong>${p.product}</strong> <small style="color:var(--text-secondary)">${p.sku}</small></div>
        <span class="tag tag-${posClr}">${p.position} (${p.gap_pct > 0 ? '+' : ''}${p.gap_pct}%)</span>
      </div>
      <div class="comp-prices">
        <div class="comp-price-box"><span class="comp-price-label">Our Price</span><span class="comp-price-value" style="color:var(--primary)">${fmt(p.our_price)}</span></div>
        <div class="comp-price-box"><span class="comp-price-label">Comp. Avg</span><span class="comp-price-value">${fmt(p.competitor_avg)}</span></div>
        ${p.competitors.map(c => `
          <div class="comp-price-box"><span class="comp-price-label">${c.name}</span><span class="comp-price-value">${fmt(c.latest_price)}</span><small style="color:${c.trend_pct > 0 ? 'var(--danger)' : 'var(--success)'}">${pct(c.trend_pct)}</small></div>
        `).join('')}
      </div>
    </div>`;
  }).join('');

  // auto-show first
  if (products.length > 0) showCompTrend(0);

  // news
  const news = compData.news || [];
  $('#compNews').innerHTML = news.length === 0
    ? '<div class="empty-state">No market events</div>'
    : news.map(n => `<div class="news-item">
        <div style="display:flex;justify-content:space-between"><span class="news-date">${n.date}</span><span class="news-impact tag tag-${n.impact > 0.5 ? 'red' : 'amber'}">Impact: ${n.impact.toFixed(2)}</span></div>
        <div style="margin-top:4px">${n.summary}</div>
        <div class="tag tag-gray" style="margin-top:4px">${n.type}</div>
      </div>`).join('');
}

function showCompTrend(idx) {
  const p = compData.products[idx];
  if (!p) return;
  const card = $('#compTrendCard');
  card.style.display = 'block';
  $('#compTrendTitle').textContent = p.product;

  const datasets = [{
    label: 'Our Price',
    data: p.our_prices,
    borderColor: solid(C.blue),
    backgroundColor: fill(C.blue),
    fill: false, tension: .3,
  }];
  // Use our dates as primary labels
  const labels = p.our_dates.length > 0 ? p.our_dates : (p.competitors[0]?.dates || []);

  p.competitors.forEach((c, ci) => {
    const colors = [C.red, C.amber, C.green, C.purple];
    datasets.push({
      label: c.name,
      data: c.prices,
      borderColor: solid(colors[ci % colors.length]),
      backgroundColor: fill(colors[ci % colors.length], 0),
      fill: false, tension: .3,
    });
  });

  makeChart('compTrendChart', {
    type: 'line',
    data: { labels, datasets },
    options: { scales: { y: { title: { display: true, text: 'Price (₹)' } } } },
  });

  card.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ══════════════════════════════════════════════════════════════
// Chart helper
// ══════════════════════════════════════════════════════════════
function makeChart(id, config) {
  if (charts[id]) charts[id].destroy();
  const ctx = document.getElementById(id);
  if (!ctx) return;
  config.options = config.options || {};
  config.options.responsive = true;
  config.options.maintainAspectRatio = false;
  charts[id] = new Chart(ctx.getContext('2d'), config);
}

// ══════════════════════════════════════════════════════════════
// DEMAND FORECAST VIEW
// ══════════════════════════════════════════════════════════════
const _fcState = { data: null, allSkus: [] };

async function renderForecast() {
  // Populate SKU selector once
  if (_fcState.allSkus.length === 0) {
    const products = await api('/api/products');
    _fcState.allSkus = products.filter(p => p.has_sales).map(p => p);
    const sel = $('#fcSkuSelect');
    sel.innerHTML = _fcState.allSkus.map(p =>
      `<option value="${p.sku}">${p.product}</option>`
    ).join('');
  }

  // Attach run button listener (once)
  const btn = $('#fcRunBtn');
  if (!btn._fc_bound) {
    btn._fc_bound = true;
    btn.addEventListener('click', _runForecast);
  }

  // Auto-run for first SKU
  await _runForecast();
}

async function _runForecast() {
  const sku     = $('#fcSkuSelect').value;
  const horizon = $('#fcHorizonSelect').value;
  if (!sku) return;

  $('#fcLoading').style.display = 'block';

  // Invalidate cache for this endpoint so fresh data is fetched
  const path = `/api/forecast/${sku}?horizon=${horizon}`;
  delete cache[path];

  let fc;
  try {
    fc = await api(path);
  } catch(e) {
    $('#fcLoading').style.display = 'none';
    return;
  }
  $('#fcLoading').style.display = 'none';
  _fcState.data = fc;

  // KPIs
  const kpiEl = $('#fcKpis');
  const stockoutClass = fc.stockout_risk ? 'danger' : 'success';
  kpiEl.innerHTML = `
    <div class="kpi-card">
      <div class="kpi-label">Total Forecast (${horizon}mo)</div>
      <div class="kpi-value">${(fc.total_forecast_units||0).toLocaleString()} units</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Current Stock (est.)</div>
      <div class="kpi-value">${(fc.current_stock||0).toLocaleString()} units</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Stockout Risk</div>
      <div class="kpi-value kpi-${stockoutClass}">${fc.stockout_risk ? '⚠ Yes' : '✓ Safe'}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Recommended Order</div>
      <div class="kpi-value">${(fc.recommended_order_qty||0).toLocaleString()} units</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Forecast Accuracy (MAPE)</div>
      <div class="kpi-value">${fc.mape_estimate||'—'}%</div>
    </div>
  `;

  // Main chart — historical + forecast with CI band
  const histDates = fc.historical_dates || [];
  const histUnits = fc.historical_units || [];
  const fcDates   = fc.forecast_dates   || [];
  const fcUnits   = fc.forecast_units   || [];
  const lower     = fc.lower_bound      || [];
  const upper     = fc.upper_bound      || [];

  const allLabels = [...histDates, ...fcDates];
  const histSeries = [...histUnits, ...Array(fcDates.length).fill(null)];
  const fcSeries   = [...Array(histDates.length).fill(null), ...fcUnits];
  const lowerSeries = [...Array(histDates.length).fill(null), ...lower];
  const upperSeries = [...Array(histDates.length).fill(null), ...upper];

  makeChart('fcChart', {
    type: 'line',
    data: {
      labels: allLabels,
      datasets: [
        {
          label: 'Historical Demand',
          data: histSeries,
          borderColor: solid(C.blue), backgroundColor: fill(C.blue),
          borderWidth: 2, pointRadius: 3, tension: 0.3,
        },
        {
          label: 'Forecast (Point)',
          data: fcSeries,
          borderColor: solid(C.green), backgroundColor: 'transparent',
          borderWidth: 2.5, borderDash: [6, 3], pointRadius: 4,
          tension: 0.3,
        },
        {
          label: 'Upper Bound (95%)',
          data: upperSeries,
          borderColor: fill(C.green, 0.3), backgroundColor: fill(C.green, 0.1),
          borderWidth: 1, fill: '+1', tension: 0.3, pointRadius: 0,
        },
        {
          label: 'Lower Bound (95%)',
          data: lowerSeries,
          borderColor: fill(C.green, 0.3), backgroundColor: fill(C.green, 0.1),
          borderWidth: 1, fill: false, tension: 0.3, pointRadius: 0,
        },
      ],
    },
    options: {
      interaction: { mode: 'index', intersect: false },
      plugins: { legend: { position: 'top' } },
      scales: { y: { title: { display: true, text: 'Units Sold' } } },
    },
  });

  // Forecast table
  const tbody = $('#fcTable tbody');
  tbody.innerHTML = fcDates.map((d, i) => `
    <tr>
      <td>${d}</td>
      <td><strong>${(fcUnits[i]||0).toLocaleString()}</strong></td>
      <td>${(lower[i]||0).toLocaleString()}</td>
      <td>${(upper[i]||0).toLocaleString()}</td>
    </tr>
  `).join('');

  // Drivers
  const driversEl = $('#fcDrivers');
  const drivers = fc.drivers || [];
  if (!drivers.length) {
    driversEl.innerHTML = '<p style="color:var(--text-secondary)">Not enough data to identify drivers.</p>';
  } else {
    driversEl.innerHTML = drivers.map(d => `
      <div class="driver-card ${d.direction === '+' ? 'positive' : 'negative'}">
        <div class="driver-icon">${d.direction === '+' ? '📈' : '📉'}</div>
        <div class="driver-info">
          <strong>${d.driver}</strong>
          <small>${d.description}</small>
        </div>
        <div class="driver-pct ${d.direction === '+' ? 'text-green' : 'text-red'}">
          ${d.direction}${d.impact_pct}%
        </div>
      </div>
    `).join('');
  }

  // Order recommendation
  const orderEl = $('#fcOrderBody');
  orderEl.innerHTML = `
    <div class="order-box">
      <div class="order-stat">
        <div class="val">${(fc.total_forecast_units||0).toLocaleString()}</div>
        <div class="lbl">Total Forecast Demand</div>
      </div>
      <div class="order-stat">
        <div class="val">${(fc.current_stock||0).toLocaleString()}</div>
        <div class="lbl">Current Stock</div>
      </div>
      <div class="order-stat">
        <div class="val">${(fc.recommended_order_qty||0).toLocaleString()}</div>
        <div class="lbl">Recommended Order Qty</div>
      </div>
      <div class="order-stat">
        <div class="val">${fc.estimated_order_cost ? fmt(fc.estimated_order_cost) : '—'}</div>
        <div class="lbl">Estimated Order Cost</div>
      </div>
      <div class="order-stat">
        <div class="val">
          <span class="stockout-badge ${fc.stockout_risk ? 'risk' : 'safe'}">
            ${fc.stockout_risk ? '⚠ Stockout Risk' : '✓ Sufficient Stock'}
          </span>
        </div>
        <div class="lbl">Inventory Status</div>
      </div>
    </div>
  `;

  // Model weights doughnut
  const weights = fc.model_weights || { prophet: 0.33, xgboost: 0.33, naive: 0.34 };
  makeChart('fcWeightsChart', {
    type: 'doughnut',
    data: {
      labels: ['Prophet', 'XGBoost', 'Naive/ETS'],
      datasets: [{
        data: [weights.prophet, weights.xgboost, weights.naive],
        backgroundColor: [solid(C.blue), solid(C.green), solid(C.amber)],
        borderWidth: 2,
      }],
    },
    options: {
      plugins: { legend: { position: 'right' },
        tooltip: { callbacks: { label: (c) => ` ${c.label}: ${(c.raw * 100).toFixed(1)}%` } }
      },
    },
  });
}

// ══════════════════════════════════════════════════════════════
// NEWS & EVENTS VIEW
// ══════════════════════════════════════════════════════════════
const EVENT_ICONS = {
  supply_chain: '🚢', regulatory: '🏛️', geopolitical: '🌍',
  competitor_launch: '🚀', product_recall: '⚠️', positive_media: '✨',
  negative_media: '📉', macroeconomic: '💵', unknown: '📰',
};
const EVENT_LABELS = {
  supply_chain: 'Supply Chain', regulatory: 'Regulatory',
  geopolitical: 'Geopolitical', competitor_launch: 'Competitor Launch',
  product_recall: 'Product Recall', positive_media: 'Positive Media',
  negative_media: 'Negative Media', macroeconomic: 'Macroeconomic',
  unknown: 'Other',
};

async function renderNews() {
  const data = await api('/api/news');
  const events = data.events || [];
  const summary = data.summary || {};
  const sources = data.data_sources || [];

  // Count electronics-relevant events (relevance_score >= 0.25 means already filtered)

  // KPIs
  $('#newsKpis').innerHTML = `
    <div class="kpi-card">
      <div class="kpi-label">Electronics-Relevant</div>
      <div class="kpi-value kpi-success">${events.length}</div>
      <div style="font-size:.72rem;color:var(--text-secondary)">of ${summary.total_events || events.length} filtered</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">High Impact Events</div>
      <div class="kpi-value kpi-danger">${summary.high_impact_count || 0}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Net Positive Impact</div>
      <div class="kpi-value kpi-success">+${summary.net_positive_impact_pct || 0}%</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Net Negative Impact</div>
      <div class="kpi-value kpi-danger">${summary.net_negative_impact_pct || 0}%</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Live Sources</div>
      <div class="kpi-value">${sources.length}</div>
      <div style="font-size:.72rem;color:var(--success)">✓ No API key needed</div>
    </div>
  `;

  // Events by type chart
  const byType = summary.by_type || {};
  const typeLabels = Object.keys(byType).map(k => EVENT_LABELS[k] || k);
  const typeData   = Object.values(byType);
  const typeColors = Object.keys(byType).map((_, i) => {
    const cols = [C.blue, C.red, C.green, C.amber, C.purple, C.gray];
    return solid(cols[i % cols.length]);
  });

  makeChart('newsTypeChart', {
    type: 'doughnut',
    data: { labels: typeLabels, datasets: [{ data: typeData, backgroundColor: typeColors, borderWidth: 2 }] },
    options: { plugins: { legend: { position: 'right' } } },
  });

  // Impact distribution histogram (bucketed)
  const impacts = events.map(e => parseFloat(e.demand_change_pct || 0));
  const buckets = [[-50,-20],[-20,-10],[-10,-5],[-5,0],[0,5],[5,10],[10,20],[20,50]];
  const bucketLabels = buckets.map(([a,b]) => `${a}% to ${b}%`);
  const bucketCounts = buckets.map(([a,b]) => impacts.filter(v => v >= a && v < b).length);
  const bucketColors = buckets.map(([a]) => a < 0 ? solid(C.red) : solid(C.green));

  makeChart('newsImpactChart', {
    type: 'bar',
    data: { labels: bucketLabels, datasets: [{ label: 'Events', data: bucketCounts, backgroundColor: bucketColors }] },
    options: { scales: { y: { title: { display: true, text: '# Events' }, beginAtZero: true } },
                plugins: { legend: { display: false } } },
  });

  // Filter + render feed
  const filterSel = $('#newsFilterSelect');
  const renderFeed = (filterType) => {
    const filtered = filterType === 'all' ? events : events.filter(e => e.event_type === filterType);
    const feedEl = $('#newsFeed');
    if (!filtered.length) {
      feedEl.innerHTML = '<p style="color:var(--text-secondary);padding:16px">No events found for this filter.</p>';
      return;
    }
    feedEl.innerHTML = filtered.slice(0, 30).map(ev => {
      const chg = parseFloat(ev.demand_change_pct || 0);
      const dir = chg > 0 ? 'pos' : (chg < 0 ? 'neg' : 'neutral');
      const impactStr = chg !== 0 ? `${chg > 0 ? '+' : ''}${chg.toFixed(1)}% demand` : 'Neutral';
      const hasUrl = ev.url && ev.url.startsWith('http');
      const titleHtml = hasUrl
        ? `<a class="ev-title-link" href="${ev.url}" target="_blank" rel="noopener noreferrer">${ev.title || 'Unknown event'} ↗</a>`
        : `<span class="ev-title">${ev.title || 'Unknown event'}</span>`;
      const mentions = ev.mentions ? ` · ${ev.mentions} mentions` : '';
      // Relevance badge
      const rel = ev.relevance_score || 0;
      const relBadge = rel >= 0.7
        ? `<span style="background:#d1fae5;color:#065f46;font-size:.68rem;padding:1px 5px;border-radius:3px;font-weight:600">🎯 High Relevance</span> `
        : rel >= 0.4
        ? `<span style="background:#fef3c7;color:#92400e;font-size:.68rem;padding:1px 5px;border-radius:3px;font-weight:600">📌 Relevant</span> `
        : '';
      // Price signal badge
      const psBadge = ev.price_signal && ev.price_signal !== 'hold'
        ? `<span style="background:${ev.price_signal === 'raise' ? '#d1fae5' : '#fee2e2'};color:${ev.price_signal === 'raise' ? '#065f46' : '#991b1b'};font-size:.68rem;padding:1px 5px;border-radius:3px;font-weight:600">💰 ${ev.price_signal === 'raise' ? '↑ Price up' : '↓ Price down'}</span>`
        : '';
      return `
        <div class="event-card ${ev.event_type || 'unknown'}">
          <div class="event-icon">${EVENT_ICONS[ev.event_type] || '📰'}</div>
          <div class="event-body">
            <div class="ev-title-wrap">${relBadge}${psBadge}${psBadge ? ' ' : ''}${titleHtml}</div>
            <div class="ev-meta">
              <span>${EVENT_LABELS[ev.event_type] || 'Other'}</span> ·
              <span>${ev.published_at || ev.date || '—'}</span> ·
              <span>${ev.source || 'GDELT'}</span>
              ${mentions}
              ${ev.duration_days ? ` · ~${ev.duration_days}d impact` : ''}
            </div>
          </div>
          <div class="event-impact ${dir}">${impactStr}</div>
        </div>
      `;
    }).join('');
  };

  filterSel.addEventListener('change', () => renderFeed(filterSel.value));
  renderFeed('all');

  // Data sources status — dynamic from /api/data-sources
  try {
    const dsData = await api('/api/data-sources');
    const dsMap = dsData.sources || {};
    const LIVE_SOURCES = [
      { key: 'gdelt',     name: 'GDELT Direct CSV',    desc: 'Global events, India-filtered, updates every 15 min — no API key' },
      { key: 'holidays',  name: 'python-holidays',     desc: 'India public holidays 2019–2027 — offline, no API key' },
      { key: 'worldbank', name: 'World Bank API',       desc: 'India CPI inflation & GDP — free, no API key' },
      { key: 'wikipedia', name: 'Wikipedia Pageviews', desc: 'Electronics brand interest trends — free Wikimedia API' },
    ];
    const statusPills = LIVE_SOURCES.map(s => {
      const info = dsMap[s.key] || {};
      const active = info.status === 'active' || info.rows > 0;
      const rows = info.rows ? ` · ${info.rows} rows` : '';
      const updated = info.last_updated ? ` · ${info.last_updated}` : '';
      return `<span class="source-pill ${active ? 'active' : 'inactive'}" title="${s.desc}${rows}${updated}">
        ${active ? '✓' : '○'} ${s.name}${active && info.rows ? ` <small>(${info.rows})</small>` : ''}
      </span>`;
    }).join('');
    $('#newsSourceStatus').innerHTML = `
      <div class="source-pills">${statusPills}</div>
      <div class="api-config-note" style="color:var(--success)">
        ✅ All sources are free &amp; open — <strong>no API keys required</strong>.
        GDELT live data refreshes every 6 hours.
      </div>
    `;
  } catch (_) {
    $('#newsSourceStatus').innerHTML = `
      <div class="source-pills">
        <span class="source-pill active">✓ GDELT Direct CSV</span>
        <span class="source-pill active">✓ python-holidays</span>
        <span class="source-pill active">✓ World Bank API</span>
        <span class="source-pill active">✓ Wikipedia Pageviews</span>
      </div>
      <div class="api-config-note" style="color:var(--success)">
        ✅ All sources are free &amp; open — no API keys required.
      </div>
    `;
  }
}

// ══════════════════════════════════════════════════════════════
// PROFIT ENGINE VIEW
// ══════════════════════════════════════════════════════════════
async function renderProfit() {
  const data = await api('/api/profit');
  const bySkus = data.by_sku || [];

  // KPIs
  $('#profitKpis').innerHTML = `
    <div class="kpi-card">
      <div class="kpi-label">Portfolio Margin</div>
      <div class="kpi-value">${data.portfolio_margin_pct || 0}%</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Total Revenue</div>
      <div class="kpi-value">${fmt(data.total_period_revenue || 0)}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Total Profit</div>
      <div class="kpi-value kpi-success">${fmt(data.total_period_profit || 0)}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Below Threshold</div>
      <div class="kpi-value kpi-${(data.below_threshold_count||0) > 0 ? 'danger' : 'success'}">
        ${data.below_threshold_count || 0} SKUs
      </div>
    </div>
  `;

  // Margin bar chart
  const labels = bySkus.map(s => s.product.split(' ').slice(0,2).join(' '));
  const margins = bySkus.map(s => s.margin_pct);
  const barColors = margins.map(m => m >= 25 ? solid(C.green) : m >= 15 ? solid(C.blue) : solid(C.red));

  makeChart('profitBarChart', {
    type: 'bar',
    data: {
      labels,
      datasets: [
        { label: 'Net Margin %', data: margins, backgroundColor: barColors, borderRadius: 6 },
        { label: 'Threshold (20%)', data: Array(labels.length).fill(20),
          type: 'line', borderColor: solid(C.amber), borderDash: [4,4],
          borderWidth: 2, pointRadius: 0, fill: false },
      ],
    },
    options: {
      scales: { y: { title: { display: true, text: 'Net Margin (%)' }, beginAtZero: true } },
      plugins: { legend: { position: 'top' } },
    },
  });

  // Margin table
  const tbody = $('#profitTable tbody');
  tbody.innerHTML = bySkus.map(s => {
    const statusClass = s.margin_status || 'healthy';
    return `<tr>
      <td>${s.product}</td>
      <td>${fmt(s.price)}</td>
      <td>${fmt(s.cogs)}</td>
      <td>${fmt(s.total_cost_per_unit || (s.price - s.net_margin_per_unit))}</td>
      <td><strong>${fmt(s.net_margin_per_unit)}</strong></td>
      <td><strong>${s.margin_pct}%</strong></td>
      <td><span class="margin-status ${statusClass}">${statusClass.replace('_',' ')}</span></td>
      <td>${fmt(s.min_viable_price)}</td>
    </tr>`;
  }).join('');

  // Populate SKU selector for scenarios
  const profitSel = $('#profitSkuSelect');
  const hasSalesSkus = bySkus.filter(s => s.period_revenue > 0);
  profitSel.innerHTML = hasSalesSkus.map(s =>
    `<option value="${s.sku}">${s.product}</option>`
  ).join('');

  // Scenario button
  const scenBtn = $('#profitScenarioBtn');
  if (!scenBtn._profit_bound) {
    scenBtn._profit_bound = true;
    scenBtn.addEventListener('click', _runProfitScenario);
  }

  // Opportunities
  const opps = data.improvement_opportunities || [];
  const oppsEl = $('#profitOpportunities');
  if (!opps.length) {
    oppsEl.innerHTML = '<p style="color:var(--text-secondary);padding:16px">All products within target margin range. 🎉</p>';
  } else {
    oppsEl.innerHTML = opps.map(o => `
      <div class="opportunity-card">
        <div class="opp-icon">💡</div>
        <div class="opp-info">
          <strong>${o.product}</strong>
          <small>${o.issue} — ${o.suggestion}</small>
        </div>
        <div class="opp-gain">+${fmt(o.potential_gain)}/mo</div>
      </div>
    `).join('');
  }
}

async function _runProfitScenario() {
  const sku = $('#profitSkuSelect').value;
  if (!sku) return;

  const loading = $('#profitScenarioLoading');
  const content = $('#profitScenarioContent');
  loading.style.display = 'block';
  content.style.display = 'none';

  const path = `/api/profit/scenario/${sku}`;
  delete cache[path];

  let sc;
  try {
    sc = await api(path);
  } catch(e) {
    loading.style.display = 'none';
    return;
  }
  loading.style.display = 'none';
  content.style.display = 'block';

  // Decision matrix
  const dm = sc.decision_matrix_cell || {};
  $('#decisionMatrix').innerHTML = `
    <div class="decision-matrix-wrap">
      <div class="dm-cell">
        <div class="dm-action">${dm.action || '—'}</div>
        <div class="dm-rationale">${dm.rationale || ''}</div>
        <div class="dm-tags">
          <span class="dm-tag">Sentiment: ${dm.sentiment_tier || '—'}</span>
          <span class="dm-tag">Inventory: ${dm.inventory_tier || '—'}</span>
          <span class="dm-tag">vs Market: ${dm.competitor_tier || '—'}</span>
        </div>
      </div>
      <div class="dm-cell">
        <div class="dm-action" style="font-size:.9rem;color:var(--gray-700)">Pricing Parameters</div>
        <div class="dm-rationale">
          Current: ${fmt(sc.base_price)} →
          Recommended: <strong style="color:var(--primary)">${fmt(sc.recommended_price)}</strong>
          (${sc.price_change_pct > 0 ? '+' : ''}${sc.price_change_pct}%)<br>
          Sentiment mod: ${sc.sentiment_modifier} ·
          Inventory mod: ${sc.inventory_modifier}<br>
          Floor: ${fmt(sc.min_viable_price)} · Ceiling: ${fmt(sc.competitor_ceiling)}
        </div>
      </div>
    </div>
  `;

  // Scenario chart
  const scenarios = sc.scenarios || [];
  const labels    = scenarios.map(s => `₹${(s.price/1000).toFixed(1)}K`);
  const profits   = scenarios.map(s => s.total_profit);
  const margins   = scenarios.map(s => s.margin_pct);
  const bgColors  = scenarios.map(s =>
    s.label.includes('Recommended') ? solid(C.green) :
    s.label === 'Current' ? solid(C.blue) : fill(C.gray, 0.6)
  );

  makeChart('profitScenChart', {
    type: 'bar',
    data: {
      labels,
      datasets: [
        { label: 'Total Profit (₹)', data: profits, backgroundColor: bgColors, yAxisID: 'y', borderRadius: 4 },
        { label: 'Margin %', data: margins, type: 'line', borderColor: solid(C.amber),
          borderWidth: 2, pointRadius: 3, yAxisID: 'y2', fill: false, tension: .3 },
      ],
    },
    options: {
      scales: {
        y:  { title: { display: true, text: 'Total Profit (₹)' }, position: 'left' },
        y2: { title: { display: true, text: 'Margin (%)' }, position: 'right', grid: { drawOnChartArea: false } },
      },
      plugins: { legend: { position: 'top' } },
    },
  });

  // Scenario table
  const scenTbody = $('#profitScenTable tbody');
  scenTbody.innerHTML = scenarios.map(s => `
    <tr class="${s.label.includes('Recommended') ? 'row-highlight-green' : s.label === 'Current' ? 'row-highlight-blue' : ''}">
      <td>${fmt(s.price)} ${s.label ? `<span style="font-size:.7rem;color:var(--primary)">${s.label}</span>` : ''}</td>
      <td>${s.demand}</td>
      <td>${s.margin_pct}%</td>
      <td><strong>${fmt(s.total_profit)}</strong></td>
      <td style="font-size:.75rem">${s.viable ? '✓' : '✗'}</td>
    </tr>
  `).join('');

  // Rationale
  const rationale = sc.rationale || [];
  $('#profitRationale').innerHTML = rationale.map(r =>
    `<div class="driver-card"><div class="driver-icon">•</div><div class="driver-info"><small>${r}</small></div></div>`
  ).join('');
}

// ══════════════════════════════════════════════════════════════
// Boot
// ══════════════════════════════════════════════════════════════
navigate('dashboard');
