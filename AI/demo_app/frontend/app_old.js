const resultEl = document.getElementById("result");
const driversEl = document.getElementById("drivers");
const risksEl = document.getElementById("risks");
const summaryEl = document.getElementById("summary");

async function loadRecommendation() {
  const sku = document.getElementById("sku").value;
  const region = document.getElementById("region").value;

  resultEl.textContent = "Loading…";
  driversEl.innerHTML = "";
  risksEl.innerHTML = "";
  summaryEl.textContent = "";

  const response = await fetch(`/api/recommendation?sku=${encodeURIComponent(sku)}&region=${encodeURIComponent(region)}`);
  const data = await response.json();

  if (data.error) {
    resultEl.textContent = data.error;
    return;
  }

  resultEl.innerHTML = `
    <strong>${data.product}</strong> (${data.brand})<br/>
    Current price: ₹${data.current_price.toLocaleString()}<br/>
    Recommended price: <strong>₹${data.recommended_price.toLocaleString()}</strong><br/>
    Recommended discount: ${data.recommended_discount_pct.toFixed(1)}%<br/>
    Expected monthly demand: ${data.expected_monthly_demand}<br/>
    Expected monthly profit: ₹${data.expected_monthly_profit.toLocaleString()}<br/>
    Confidence: ${(data.confidence * 100).toFixed(0)}%<br/>
    Sentiment score: ${(data.sentiment_score * 100).toFixed(0)}%
  `;

  data.drivers.forEach((driver) => {
    const li = document.createElement("li");
    li.textContent = driver;
    driversEl.appendChild(li);
  });

  data.risks.forEach((risk) => {
    const li = document.createElement("li");
    li.textContent = risk;
    risksEl.appendChild(li);
  });

  summaryEl.textContent = data.market_summary;
}

const runBtn = document.getElementById("run");
runBtn.addEventListener("click", loadRecommendation);

loadRecommendation();
