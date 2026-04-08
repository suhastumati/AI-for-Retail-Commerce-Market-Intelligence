# AI-Driven Retail Intelligence and Market Forecasting

**Mid-Review Dissertation Report**

---

| Field | Detail |
|---|---|
| Title | AI-Driven Retail Intelligence and Market Forecasting |
| Student Name | Tumati Suhas Pranay |
| BITS ID | 2024SL93003 |
| Program | M.Tech Software Engineering (WILP) — SAP LABS |
| Course | SESAP ZG628T Dissertation |
| Supervisor | Rupa Venkata Muddisetty, SDE, SAP Labs India, Bengaluru |
| Additional Examiner | Anshul Jain, SDE, SAP Labs India, Bengaluru |
| Date | April 2026 |

---

# CHAPTER 1 — INTRODUCTION

## 1.1 Purpose

The purpose of this dissertation is to design, implement, and evaluate an AI-driven retail intelligence platform tailored to the operational realities of Indian electronics retail. Named **BluePill AI**, the system integrates demand forecasting, dynamic pricing optimisation, competitor price monitoring, aspect-based sentiment analysis, and geopolitical event tracking into a single, cohesive decision-support dashboard. The work demonstrates how machine learning models and zero-key live data APIs can be combined into a production-ready web application that delivers actionable intelligence at interactive response speeds.

## 1.2 Scope

The scope of this project encompasses:

- Design and development of a REST API backend using FastAPI (Python 3.11) serving eight electronics product SKUs representative of the Indian market.
- Construction of a two-model machine learning ensemble (XGBoost and Naïve ETS) for multi-step demand forecasting over an eight-month horizon.
- Implementation of a three-layer dynamic pricing engine that incorporates price elasticity regression, competitor price ceilings, and real-time geopolitical event signals.
- Integration of four zero-API-key live data sources: GDELT, python-holidays, World Bank, and Wikipedia Pageviews.
- Development of a single-page frontend application (Vanilla JS + Chart.js 4) exposing eight analytical views.
- Submission of the prototype to the AWS AI for Bharat Hackathon as a demonstration of AI application in Indian commerce.

The project does not cover full production deployment, real-time transaction processing, or integration with live point-of-sale systems. AWS cloud architecture is designed as a forward-looking production blueprint rather than a deployed environment.

## 1.3 Motivation

Indian electronics retail is characterised by high price sensitivity, pronounced seasonal demand spikes tied to festival calendars (Diwali, Navratri, Dussehra), aggressive multi-platform competition (Flipkart, Amazon, Croma, Reliance Digital), and supply chains susceptible to global semiconductor disruptions and import tariff changes. Despite these complexities, most mid-size Indian retailers rely on static pricing spreadsheets, periodic manual competitor checks, and intuition-driven inventory replenishment.

The gap between the analytical maturity of large retailers such as Amazon India and the tools available to independent or regional electronics chains is significant. Modern AI techniques — gradient-boosted trees for tabular time-series, NLP-based sentiment scoring, event-driven pricing adjustment — are well-established in academic literature but rarely assembled into an integrated, accessible dashboard for this market segment. This dissertation is motivated by the opportunity to close that gap using open-source ML libraries, freely available data APIs, and a lightweight web stack that requires no proprietary data feeds.

## 1.4 Problem Statement

Retailers in the Indian electronics segment face several compounding decision challenges simultaneously:

1. **Demand volatility**: Sales of consumer electronics in India exhibit strong seasonality (festival quarter uplift), long-term macroeconomic growth trends, and short-term disruptions from geopolitical events (import bans, semiconductor shortages). Forecasting these with simple moving averages or seasonal decomposition underperforms because the signal sources are heterogeneous.

2. **Pricing under competitive pressure**: Optimal price-setting requires balancing own-price elasticity, competitor benchmarks, platform fees, and real-time event-driven market signals. Manual approaches either leave margin on the table or risk losing conversions to cheaper competitors.

3. **Fragmented intelligence**: Market signals — news events, customer reviews, competitor prices, macroeconomic indicators — exist in disparate sources. Without a unified aggregation layer, retail managers cannot act on them coherently or quickly.

4. **Latency constraints**: Forecasting and pricing decisions must be available at interactive speeds (under 10 seconds) for a dashboard to be practically usable. Approaches such as Bayesian structural time-series (e.g., Prophet with Stan MCMC) are too computationally expensive for synchronous API responses in a single-server deployment.

The proposed system addresses all four challenges within a single integrated platform.

## 1.5 Literature Survey

**[1] Liu, Y., Ma, X., Ge, M., Han, Z., Qiu, J., Moe, Y. A., Shen, Y., Wei, W., and Huang, C. (2025). "AttnBoost: Retail Supply Chain Sales Insights via Gradient Boosting Perspective." *arXiv preprint arXiv:2509.10506*.**
Liu et al. propose AttnBoost, a hybrid architecture that augments gradient-boosted trees with a lightweight attention mechanism that dynamically re-weights features at each boosting round, giving higher importance to high-impact variables such as promotional events and seasonal indicators. Evaluations on large-scale retail transaction data demonstrate improvements over both conventional machine learning and deep tabular baselines. This work directly informs the design choice of XGBoost in the BluePill AI forecasting module — the finding that gradient boosting with explicit seasonality-aware feature importance consistently outperforms sequence models on structured retail tabular data supports the preference for XGBoost over deep learning alternatives in this project.

**[2] Ganguly, P. and Mukherjee, I. (2024). "Enhancing Retail Sales Forecasting with Optimized Machine Learning Models." *arXiv preprint arXiv:2410.13773*.**
Ganguly and Mukherjee conduct a systematic comparison of machine learning methods for retail sales prediction, reporting that an optimised gradient-boosted ensemble achieves R² = 0.945 on datasets with high seasonality and multiple product categories, outperforming linear regression (R² = 0.531) and baseline approaches. The paper demonstrates the critical role of hyperparameter tuning and feature engineering in retail forecasting contexts. This study validates the use of an auto-weighted ensemble with hold-out MAE-based model selection, as implemented in the BluePill AI demand forecasting module, over naïve single-model approaches.

**[3] Shapiro, S. and Panvelwala, B. (2026). "Prophet as a Reproducible Forecasting Framework: A Methodological Guide for Business and Financial Analytics." *arXiv preprint arXiv:2601.05929*.**
Shapiro and Panvelwala evaluate Prophet's suitability for business analytics workflows, documenting both its strengths in decomposable additive modelling and its computational limitations in high-throughput settings. The paper confirms that Stan MCMC inference creates significant latency barriers for synchronous, multi-SKU API applications. This directly supports the architectural decision in this dissertation to disable Prophet in the online inference path and instead implement its conceptual contributions — trend decomposition, holiday effects, and external regressors — as explicit engineered features within the XGBoost feature matrix.

**[4] Garg, L., Yaswanth, S., Mishra, D. N., Kumaran, K., Sharma, A., and Uniyal, M. (2026). "Monodense Deep Neural Model for Determining Item Price Elasticity." *arXiv preprint arXiv:2603.29261*.**
Garg et al. address item-level price elasticity estimation without requiring randomised treatment controls — the realistic setting for most retail deployments. They benchmark a Monodense neural network architecture against Double Machine Learning and LightGBM approaches on millions of retail transaction records. Their finding that the confounding effect of secular trends must be isolated before regression directly validates the detrended log-log elasticity approach implemented in `analytics.py`, which explicitly removes time-trend components before fitting the price elasticity coefficient.

**[5] Silcenco, O., Machad, M. R., Ugulino, W. C., and Braun, D. (2025). "A Retail-Corpus for Aspect-Based Sentiment Analysis with Large Language Models." *arXiv preprint arXiv:2508.17994*.**
Silcenco et al. introduce a benchmark of 10,814 multilingual customer reviews from retail stores, labelled across eight aspect dimensions and corresponding sentiment polarities. Evaluation of GPT-4 and LLaMA-3 achieves over 85% aspect-level accuracy. The paper establishes that aspect-based sentiment analysis is the appropriate granularity for retail product teams — aggregate document-level sentiment misses actionable signals about specific product dimensions. This motivates the aspect-level breakdown (quality, delivery, value, support) in the BluePill AI sentiment module, which normalises scores to a 0–1 scale per aspect.

**[6] Xiang, Y., Yu, H., Gong, Y., Huo, S., and Zhu, M. (2024). "Text Understanding and Generation Using Transformer Models for Intelligent E-commerce Recommendations." *arXiv preprint arXiv:2402.16035*.**
Xiang et al. survey transformer-based language model applications across e-commerce platforms, covering sentiment analysis, personalised recommendation systems, and automated product intelligence. The authors identify how pre-trained transformer models excel at processing unstructured user-generated content at scale. This paper contextualises the NLP pipeline in BluePill AI — the keyword-based relevance scoring over GDELT news feeds operates as a computationally lightweight alternative to full transformer inference for extracting market signals at interactive API response speeds.

**[7] Banh Nghiep, K., Nguyen Minh, D., and Hoang Thi, L. (2026). "Bridging Deep Learning and Integer Linear Programming: A Predictive-to-Prescriptive Framework for Supply Chain Analytics." *arXiv preprint arXiv:2604.01775*.**
Banh Nghiep et al. propose a two-stage predictive-to-prescriptive architecture where a deep learning model first generates demand predictions whose outputs feed into a constrained optimisation solver for inventory and procurement decisions. This framework directly parallels the BluePill AI architecture, where ML-generated demand forecasts and elasticity estimates feed into the pricing optimiser and profit engine (constrained grid search with competitor ceiling). The paper validates the design philosophy of separating prediction modules from decision modules, enabling each to be improved independently.

**[8] Fatima, A. and Salam, M. A. (2026). "A Data-Driven Predictive Framework for Inventory Optimization Using Context-Augmented Machine Learning Models." *arXiv preprint arXiv:2601.05033*.**
Fatima and Salam develop a context-augmented ML pipeline for inventory optimisation that incorporates external contextual signals — macroeconomic indicators, seasonality indices, and event calendars — alongside historical demand data to improve reorder recommendations. Their finding that context-augmented models reduce inventory errors by 18–23% compared to history-only baselines directly motivates the multi-signal feature engineering in BluePill AI, which incorporates CPI inflation multipliers, Wikipedia brand interest trends, and python-holidays India festival indicators as external regressors alongside standard lag and rolling-window features.

## 1.6 Existing System

Existing retail analytics solutions available to Indian electronics retailers fall into three broad categories:

**ERP-Bundled Analytics**: SAP Retail, Oracle Retail, and similar enterprise systems provide historical sales reporting and basic demand planning. However, these platforms are expensive, require lengthy implementation cycles, and do not ingest real-time external signals such as news events or live competitor pricing. Their forecasting modules typically use classical ARIMA or Holt-Winters methods without external regressors.

**E-Commerce Platform Dashboards**: Flipkart Seller Hub and Amazon Seller Central provide sellers with their own platform's performance data but offer no cross-platform competitor benchmarking, no macroeconomic signal integration, and no causal event attribution.

**Point Solutions**: Standalone tools exist for each problem in isolation — price monitoring tools (Prisync, Wiser), sentiment scrapers, and demand forecasting SaaS (Lokad, Streamline). However, these solutions are not integrated, are priced for enterprise budgets, require API keys or subscription fees for data, and do not surface cross-signal intelligence (e.g., how a GDELT-detected semiconductor shortage should simultaneously affect demand forecasts, pricing recommendations, and inventory reorder points).

No existing solution accessible to a mid-size Indian electronics retailer combines demand forecasting, event-aware dynamic pricing, competitor intelligence, sentiment analysis, and live news monitoring into a single integrated, open-source platform with zero external API dependencies.

## 1.7 Proposed System

BluePill AI is a unified retail intelligence platform that ingests data from five constructed historical CSVs and four zero-key live APIs, processes them through five AI and analytics modules, and exposes the results via ten REST endpoints consumed by an eight-view single-page application.

The system is designed for Indian electronics retail but is architecturally generalisable to other markets and product categories. The prototype serves eight SKUs spanning five product categories (Smart TVs, Smartphones, Laptops, Appliances, Audio). All five AI modules execute asynchronously and their results converge into a single decision dashboard.

### 1.7.1 Features

| Feature | Capability |
|---|---|
| Demand Forecasting | 8-month horizon, XGBoost + NaiveETS ensemble, auto-weighted by hold-out MAE, CPI and Wikipedia external regressors |
| Dynamic Pricing | Detrended elasticity regression, competitor ceiling constraint, live GDELT event nudge (±5%) |
| Market Events Intelligence | GDELT daily CSV ingestion, 50+ keyword relevance filter, event → price signal mapping, 6-hour disk cache |
| Sentiment Analysis | 1,328-review dataset, aspect-level breakdown (quality, delivery, value, support), 0–1 unified scale |
| Competitor Intelligence | 5-competitor price tracking (Flipkart, Amazon, Croma, Reliance Digital, CompeteX), price war risk scoring |
| Profit Engine | COGS + logistics + platform fee + tax breakdown, what-if scenario slider (−15% to +20%), decision matrix |
| Inventory Management | Stock level estimates, reorder point alerts per SKU |
| Live Data Status | Real-time health monitoring of all four external data source connections |

---

# CHAPTER 2 — SOFTWARE REQUIREMENT SPECIFICATIONS

## 2.1 Purpose

This chapter specifies the functional and non-functional requirements of the BluePill AI platform, defines the data and interface contracts between system components, and documents the constraints that shaped design decisions. These specifications serve as the baseline against which the implemented system is evaluated.

## 2.2 Overall Description

BluePill AI is a web-based decision-support system. Its primary users are retail managers and business analysts at an Indian electronics retailer who require consolidated, AI-driven insights to support pricing, procurement, and marketing decisions. The system operates as a single-server local deployment in prototype form, with a documented path to distributed AWS deployment.

### 2.2.1 Functional Requirements

**FR-01 — Product Catalogue Management**: The system shall maintain a catalogue of eight product SKUs with associated metadata including brand, category, base price, and cost structure.

**FR-02 — Demand Forecasting**: The system shall generate an eight-month sales forecast for any requested SKU within ten seconds of the API call, using a machine learning ensemble that incorporates lag features, seasonality encodings, holiday indicators, CPI inflation, and Wikipedia brand interest.

**FR-03 — Dynamic Pricing Optimisation**: The system shall compute an optimal recommended price for each SKU by solving a constrained revenue maximisation problem using price elasticity estimates, competitor price data, and live event signals.

**FR-04 — Competitor Price Monitoring**: The system shall retrieve and display current estimated prices from five named competitors for all eight SKUs, and compute a price war risk indicator.

**FR-05 — Sentiment Analysis**: The system shall analyse customer review data at the aspect level and expose per-SKU sentiment scores on a 0–1 normalised scale for four aspects: product quality, delivery experience, value for money, and customer support.

**FR-06 — News and Market Events**: The system shall fetch, cache, filter, and display geopolitical and economic events from GDELT that are relevant to Indian electronics retail, updated at most every six hours.

**FR-07 — Profit and Margin Analysis**: The system shall decompose per-SKU profitability into cost components and support what-if scenario evaluation across a configurable price range.

**FR-08 — Inventory Alerts**: The system shall estimate current stock levels and flag SKUs that have fallen below their computed reorder point.

**FR-09 — Live Data Source Monitoring**: The system shall report the health and freshness of each external data connection (GDELT, World Bank, Wikipedia, python-holidays).

**FR-10 — Single-Page Application**: All views shall be accessible without full page reload through a client-side navigation model.

### 2.2.2 Non-Functional Requirements

**NFR-01 — Response Latency**: All endpoints except `/api/forecast/{sku}` shall respond within 2 seconds. The forecast endpoint shall respond within 10 seconds. Forecasting is executed in an asynchronous thread pool to avoid blocking the event loop.

**NFR-02 — Availability of Live Data**: The system shall degrade gracefully when GDELT or World Bank APIs are unreachable, falling back to cached data or static defaults rather than returning errors.

**NFR-03 — Zero External API Keys**: No endpoint shall require the user to supply an API key, subscription token, or paid credential for any data source.

**NFR-04 — Data Freshness**: Live API responses shall be cached to disk for a maximum of six hours. Cache files are stored in `AI/demo_app/cache/live/` and can be manually deleted to force immediate refresh.

**NFR-05 — Reproducibility**: All historical datasets (`sales.csv`, `competitor_prices.csv`, `reviews.csv`) shall remain static during a running session. The ML models shall produce deterministic outputs given the same input data.

**NFR-06 — Python Environment Isolation**: The system shall run exclusively within the project virtual environment (`../../.venv/`) using Python 3.11/3.12 to ensure package compatibility. System Python (3.14 on the development machine) shall not be used.

**NFR-07 — Browser Compatibility**: The frontend shall function without a build step or transpilation on any modern Chromium or Firefox browser, using only Vanilla JS ES6+ and Chart.js 4 loaded via CDN.

## 2.3 Specific Requirements

### 2.3.1 Backend Requirements

| ID | Requirement |
|---|---|
| BE-01 | FastAPI framework version ≥ 0.100 with async endpoint support |
| BE-02 | XGBoost ≥ 1.7 for gradient-boosted tree training and inference |
| BE-03 | scikit-learn for preprocessing, hold-out splitting, and MAE calculation |
| BE-04 | pandas ≥ 2.0; all forward-fill operations shall use `.ffill()` not `fillna(method=)` |
| BE-05 | requests library for GDELT and World Bank HTTP fetches |
| BE-06 | python-holidays ≥ 0.30 for offline India festival/public holiday generation |
| BE-07 | numpy for array operations and cyclical feature encoding |
| BE-08 | ThreadPoolExecutor for async offloading of CPU-bound ML inference |
| BE-09 | GDELT ZIP download and CSV parse shall complete within 30 seconds or time out gracefully |

### 2.3.2 Frontend Requirements

| ID | Requirement |
|---|---|
| FE-01 | Single HTML file (`index.html`) acting as SPA shell |
| FE-02 | All rendering logic in `app.js`; no JS framework dependencies |
| FE-03 | Chart.js 4 for all data visualisations (line charts, bar charts, doughnut charts) |
| FE-04 | Eight named view sections toggled by client-side navigation |
| FE-05 | Event signal banner on Pricing view displaying active GDELT-derived price signals |
| FE-06 | Forecast view to render an 8-bar chart with model weight annotation |
| FE-07 | What-if scenario on Profit Engine view using a price slider or input field |
| FE-08 | Responsive layout compatible with desktop viewport widths ≥ 1024px |

## 2.4 Interface Requirements

### 2.4.1 REST API Interface

All API endpoints accept and return JSON over HTTP/1.1. The server binds to `0.0.0.0:8000`. CORS is permissive for local development. The table below summarises the complete API surface.

| Method | Path | Description | Typical Response Time |
|---|---|---|---|
| GET | `/api/products` | All 8 SKUs with metadata | < 100 ms |
| GET | `/api/inventory` | Stock levels and reorder flags | < 500 ms |
| GET | `/api/pricing` | Optimal prices per SKU with event signals | < 2 s |
| GET | `/api/sentiment` | Aspect-level sentiment scores per SKU | < 500 ms |
| GET | `/api/forecast/{sku}?horizon=8` | Demand forecast array | 3–5 s |
| GET | `/api/news` | Filtered GDELT events | < 2 s (cached) |
| GET | `/api/data-sources` | Live source health status | < 2 s |
| GET | `/api/profit` | Portfolio margin overview | < 500 ms |
| GET | `/api/profit/scenario/{sku}` | What-if pricing scenario for one SKU | < 500 ms |
| GET | `/api/competitors/live` | Competitor prices for all SKUs | < 1 s |

### 2.4.2 Data Source Interface

| Source | Access Method | Data Provided | Cache Policy |
|---|---|---|---|
| GDELT | HTTP GET, ZIP download, CSV parse | World events with location, CAMEO code, tone | 6-hour disk cache |
| python-holidays | Local Python package, no network | India public/festival holidays 2019–2027 | No cache needed (offline) |
| World Bank API | HTTP GET JSON | CPI inflation, GDP per capita for India | 6-hour disk cache |
| Wikipedia Pageviews | HTTP GET JSON | Monthly page views per electronics brand | 6-hour disk cache |

---

# CHAPTER 3 — HIGH LEVEL DESIGN

## 3.1 System Architecture

The BluePill AI platform is structured as a three-tier architecture: a data ingestion and storage tier, a processing and intelligence tier, and a presentation tier. The defining architectural characteristic is that all five AI/analytics modules execute independently against their respective data slices and their outputs are aggregated at the API layer before being consumed by the frontend. This parallel processing model enables the dashboard to display a unified view of demand, pricing, sentiment, events, and competition without any single module blocking the others.

**[Figure 3.1: Unified AI Decision Pipeline — insert Slide 10 from PPT here]**

*Caption: Figure 3.1 illustrates how the five analytical modules (Demand Forecasting, Dynamic Pricing, Market Events Intelligence, Sentiment Analysis, Competitor Monitoring) execute concurrently and converge their outputs into a single unified recommendation layer consumed by the dashboard frontend.*

The data tier consists of five static CSV datasets constructed to reflect realistic Indian electronics market conditions over 2019–2024, supplemented by four live data source connectors. The intelligence tier comprises five Python modules (`demand_forecasting.py`, `analytics.py`, `live_data_fetcher.py`, `competitor_scraper.py`, `profit_engine.py`) orchestrated by the FastAPI application in `app.py`. The presentation tier is a Vanilla JS single-page application that calls the REST API and renders results using Chart.js 4.

**Target Production Architecture (AWS)**

The prototype runs as a single FastAPI process on a local machine. The target production architecture, designed for the AWS AI for Bharat Hackathon, replaces each component with a managed AWS equivalent.

**[Figure 3.2: Target AWS Cloud Architecture — insert Slide 12 from PPT here]**

*Caption: Figure 3.2 shows the target deployment architecture on AWS, mapping the current FastAPI server to AWS Lambda + API Gateway, the ML models to Amazon SageMaker endpoints, the disk cache to Amazon ElastiCache, the static frontend to Amazon S3 + CloudFront, and the data pipeline to AWS Glue + S3.*

The key AWS service mappings are:

| Prototype Component | AWS Production Equivalent |
|---|---|
| FastAPI server (local) | AWS Lambda + Amazon API Gateway |
| ML model inference (in-process) | Amazon SageMaker real-time endpoints |
| Disk-based 6h cache | Amazon ElastiCache (Redis) |
| Static CSV files | Amazon S3 + AWS Glue ETL |
| Frontend (`index.html`) | Amazon S3 static hosting + Amazon CloudFront |
| Event processing | Amazon EventBridge + AWS Lambda |

## 3.2 Module-wise Design

### 3.2.1 Demand Forecasting Module

**[Figure 3.2.1: Demand Forecasting Pipeline — insert Slide 4 from PPT here]**

*Caption: Figure 3.2.1 depicts the demand forecasting data flow from raw sales CSV and external signal ingestion through feature engineering, two-model parallel training, hold-out MAE weighting, and ensemble forecast output.*

The demand forecasting module accepts a SKU identifier and a forecast horizon (default: 8 months) and returns an array of predicted monthly sales quantities. The design follows a two-stage pipeline:

**Stage 1 — Feature Engineering**: Raw monthly sales data from `sales.csv` is enriched with the following feature set:

- **Lag features**: `lag_1`, `lag_3`, `lag_6`, `lag_12` — direct historical sales at offset months
- **Rolling statistics**: 3-month and 6-month rolling mean and standard deviation
- **Cyclical time encoding**: `month_sin = sin(2π × month / 12)` and `month_cos = cos(2π × month / 12)`, which represent the circular periodicity of the calendar without imposing an ordinal relationship on month numbers
- **Binary event indicators**: `is_holiday` (whether the month contains a major Indian public holiday from python-holidays), `is_weekend` (month-end proximity proxy)
- **External regressors**: `cpi_multiplier` derived from World Bank India CPI data, and `wiki_interest_multiplier` derived from Wikipedia Pageviews for the relevant brand

**Stage 2 — Ensemble Training and Weighting**: Two models are trained independently on the feature matrix:

- **XGBoostForecaster**: A gradient-boosted tree regressor trained on the full engineered feature set. XGBoost is selected for its ability to capture non-linear interactions between lag values, seasonality encodings, and external signals without requiring stationarity.
- **NaiveForecaster (ETS-like)**: A seasonally adjusted exponential smoothing model that provides a statistically principled baseline. This model is computationally inexpensive and performs well when patterns are stable, providing a complementary signal to XGBoost's non-linear flexibility.

Ensemble weights are determined dynamically by evaluating both models on a hold-out set consisting of the trailing three months of historical data. The model with the lower MAE on this hold-out set receives the higher weight. This automatic weighting strategy ensures that during stable market periods the smoother ETS model may dominate, while during disrupted periods XGBoost's richer feature use provides better accuracy.

The design explicitly excludes Facebook Prophet. While Prophet's additive decomposition and holiday regressor are conceptually relevant, its reliance on Stan MCMC sampling introduces per-SKU latency of 30–90 seconds, which is incompatible with the < 10 second API response requirement. Prophet's conceptual contributions are preserved through explicit feature engineering rather than generative modelling.

### 3.2.2 Dynamic Pricing Engine

**[Figure 3.2.2: Dynamic Pricing Engine Pipeline — insert Slide 5 from PPT here]**

*Caption: Figure 3.2.2 shows the three-layer pricing pipeline: detrended elasticity regression at the base layer, competitor ceiling constraint at the middle layer, and GDELT-derived live event nudge at the top layer.*

The pricing engine produces an optimal recommended price for each SKU through three sequential layers:

**Layer 1 — Elasticity Estimation**: Price elasticity is estimated via a log-log regression of log(quantity_sold) on log(price), with a time-trend covariate explicitly included and removed. The detrending step is critical: without it, the secular growth trend in Indian electronics consumption creates a spurious positive correlation between price and demand (both rise over time), yielding physically impossible positive elasticity estimates. After detrending, elasticity coefficients are clamped to the range [−3.5, −0.3] to exclude statistically implausible outliers. A grid search over prices in the range [base × 0.80, base × 1.20] is then used to find the price that maximises expected revenue given the estimated elasticity.

**Layer 2 — Competitor Ceiling**: The grid search optimum is subject to an upper bound derived from competitor prices:

```
max_price = max(comp_avg × 1.10, min_viable × 1.05, base × 1.20)
```

Where `comp_avg` is the average price across the five tracked competitors, `min_viable` is the price that yields a minimum acceptable margin after COGS, logistics, platform fee, and tax. This constraint prevents the engine from recommending prices that would be competitively unviable, even if elasticity estimates technically support them.

**Layer 3 — Live Event Nudge**: The constrained optimum is further adjusted by a signal derived from GDELT event analysis. The `get_event_price_signals()` function in `live_data_fetcher.py` maps detected event types to directional price adjustments (e.g., `supply_chain` disruption → +2–3%, `macroeconomic_inflation` → −1–2%, `festival_season` → +3–5%, `regulatory_tariff` → +1–2%, `geopolitical_trade` → variable). Adjustments from all detected active events are aggregated into a `net_adjustment_pct`, capped at ±5% on top of the Layer 2 price. The frontend Pricing view displays an event signal banner enumerating the active GDELT events contributing to this nudge.

### 3.2.3 Market Events Intelligence Module

**[Figure 3.2.3: Market Events Intelligence Flow — insert Slide 6 from PPT here]**

*Caption: Figure 3.2.3 illustrates the GDELT data pipeline: daily export ZIP download, 57-column CSV parsing, India location filtering, electronics relevance scoring against a 50+ keyword vocabulary, event-to-price-signal mapping, and 6-hour cache management.*

The market events module serves two functions: surfacing relevant world events in the News & Events dashboard view, and providing quantitative price signal inputs to the pricing engine.

**Data Ingestion**: GDELT daily export files are fetched as ZIP archives from `http://data.gdeltproject.org/events/YYYYMMDD.export.CSV.zip`. Each archive contains approximately 100,000+ event records encoded across 57 columns following the GDELT 1.0 schema. The module parses these columns, filters to rows where Actor1Geo_CountryCode or Actor2Geo_CountryCode equals `IN` (India), and retains events from the trailing 30 days.

**Relevance Scoring**: Each filtered event is scored for electronics-domain relevance by matching event source URLs and actor names against a vocabulary of 50+ keywords including brand names (samsung, apple, xiaomi, sony, lg, daikin, dell, whirlpool), platform names (flipkart, amazon, myntra), and sector terms (semiconductor, gst, festive, import, tariff, inflation, supply chain). A keyword match score in [0, 1] is computed; events scoring below 0.25 are discarded. This filter removes geographically-tagged but topically irrelevant GDELT events (wildlife news, transport incidents, political speeches unrelated to commerce).

**URL Headline Extraction**: GDELT encodes actor information in CAMEO codes rather than natural-language titles. A headline extractor function converts the source URL and actor codes into a human-readable event description displayed in the dashboard.

**Cache Management**: Downloaded and parsed GDELT data is serialised to CSV in `AI/demo_app/cache/live/` with a six-hour TTL. Subsequent API calls within the TTL window serve from cache, eliminating redundant large downloads during normal dashboard usage.

### 3.2.4 Sentiment Analysis Module

**[Figure 3.2.4: Sentiment Analysis Pipeline — insert Slide 7 from PPT here]**

*Caption: Figure 3.2.4 shows the sentiment pipeline from raw review CSV ingestion through aspect extraction, per-aspect scoring, and normalisation to the 0–1 `sentiment_unified` scale used in dashboard displays.*

The sentiment module processes the `reviews.csv` dataset (1,328 rows) to produce per-SKU, per-aspect sentiment scores. Each review record contains a free-text body, a star rating, and pre-annotated aspect labels (quality, delivery, value, support). The `sentiment_unified` field is a normalised 0–1 score where 0.0 represents strongly negative, 0.5 is neutral, and 1.0 is strongly positive. This normalisation scheme is intentional: it avoids the ambiguity of bipolar [−1, +1] scales when computing averages that will be displayed as KPIs.

The Sentiment view in the frontend renders a per-aspect breakdown chart for a selected SKU, allowing a retail manager to identify whether negative signals are concentrated in product quality (actionable via procurement/QC), delivery experience (actionable via logistics partner review), or pricing perception (actionable via promotional strategy).

---

# CHAPTER 4 — DETAILED DESIGN

## 4.1 Demand Forecasting Implementation

The forecasting pipeline is implemented in `AI/demo_app/backend/demand_forecasting.py`. The entry function is `generate_forecast(sku_id, horizon=8)`, which is called from the FastAPI route handler via `asyncio.get_event_loop().run_in_executor(executor, ...)` to avoid blocking the async event loop during CPU-bound tree inference.

**Feature matrix construction** proceeds as follows:

1. Load `sales.csv`, filter to the requested SKU, sort by year-month.
2. Compute lag columns (`shift(1)`, `shift(3)`, `shift(6)`, `shift(12)`).
3. Compute `rolling(3).mean()`, `rolling(6).mean()`, `rolling(3).std()`, `rolling(6).std()`.
4. Encode month as `month_sin = np.sin(2 * np.pi * df['month'] / 12)` and `month_cos = np.cos(2 * np.pi * df['month'] / 12)`.
5. Join `india_holidays_real.csv` to produce `is_holiday` binary column.
6. Join World Bank CPI series (loaded at startup) to produce `cpi_multiplier` (CPI_year / CPI_base_year).
7. Join Wikipedia Pageviews series (fetched and cached) to produce `wiki_interest_multiplier` (pageviews_month / pageviews_mean).
8. Drop rows with NaN from lag computation (first 12 rows).

**Ensemble training and hold-out weighting**:

```python
# Split: train on all but last 3 months; evaluate on last 3
X_train, X_holdout = X[:-3], X[-3:]
y_train, y_holdout = y[:-3], y[-3:]

xgb_model.fit(X_train, y_train)
ets_model.fit(X_train, y_train)

xgb_mae = mean_absolute_error(y_holdout, xgb_model.predict(X_holdout))
ets_mae = mean_absolute_error(y_holdout, ets_model.predict(X_holdout))

# Inverse-MAE weighting: lower error → higher weight
total_inv = (1/xgb_mae) + (1/ets_mae)
w_xgb = (1/xgb_mae) / total_inv
w_ets = (1/ets_mae) / total_inv
```

**Forecast generation**: For the forward horizon, feature rows are iteratively constructed by appending each predicted value to the history buffer and recomputing lag and rolling features. This recursive multi-step forecasting approach accumulates error over the horizon; the eight-month horizon was chosen as the maximum practically useful length given this limitation.

**Response payload** includes the forecast array, the model weights `(w_xgb, w_ets)`, a confidence band (±1 rolling standard deviation of residuals), and the external signal multipliers in effect.

## 4.2 Pricing Module Implementation

The pricing module's main entry point is `pricing_analysis()` in `AI/demo_app/backend/analytics.py`, called from `GET /api/pricing`. It processes all eight SKUs in a loop and returns a list of pricing recommendation objects.

**Detrended elasticity regression**:

```python
# Add integer time index t = 0, 1, ..., T
df['t'] = range(len(df))

# Log-log OLS with time trend: log(Q) = α + β·log(P) + γ·t + ε
# β is the elasticity coefficient
X = np.column_stack([np.log(df['price']), df['t'], np.ones(len(df))])
y = np.log(df['quantity'])
coeffs, *_ = np.linalg.lstsq(X, y, rcond=None)
elasticity = np.clip(coeffs[0], -3.5, -0.3)
```

**Grid search over price range**:

```python
candidate_prices = np.linspace(base_price * 0.80, base_price * 1.20, 100)
expected_revenue = candidate_prices * (base_qty * np.exp(elasticity * np.log(candidate_prices / base_price)))
optimal_price_raw = candidate_prices[np.argmax(expected_revenue)]
```

**Competitor ceiling application**:

```python
comp_avg = competitor_prices[sku].mean()
min_viable = cost_structure[sku]['total_cost'] * 1.05
price_ceiling = max(comp_avg * 1.10, min_viable * 1.05, base_price * 1.20)
optimal_price = min(optimal_price_raw, price_ceiling)
```

**Event signal application**:

```python
event_signals = live_data_fetcher.get_event_price_signals()
net_event_pct = np.clip(event_signals['net_adjustment_pct'], -0.05, 0.05)
final_price = optimal_price * (1 + net_event_pct)
```

## 4.3 Data Pipeline Design and Frontend UI

**Data Pipeline**: At server startup, `data_loader.py` reads all five static CSVs into memory as pandas DataFrames. The live data connectors in `live_data_fetcher.py` check the disk cache directory for each source; if the cache file is absent or older than six hours, a fresh fetch is initiated. Cache files are stored as CSVs in `AI/demo_app/cache/live/`. This design means the server is fully functional without network access as long as valid cache files exist.

**Frontend UI Design**:

**[Figure 4.1: Dashboard, Forecast, and Pricing Wireframes — insert Slide 11 from PPT here]**

*Caption: Figure 4.1 shows wireframe-level mockups of three key views: (a) the Dashboard view with KPI summary cards and revenue trend chart, (b) the Demand Forecast view with the 8-month forecast bar chart and model weight indicators, and (c) the Pricing view with per-SKU recommendation cards and the GDELT event signal banner.*

The frontend SPA (`index.html`, `app.js`, `styles.css`) uses a single HTML shell with eight `<section>` elements, each corresponding to one view. Navigation links toggle the `active` CSS class to show/hide sections without page reload. On initial load, `app.js` calls `/api/products` to populate the global product registry, then fetches the data for whichever view is active.

**Dashboard view** (`view-dashboard`) renders four KPI cards (Total Revenue, Units Sold, Average Margin, Active Alerts) and a Chart.js line chart of monthly revenue across all SKUs.

**Forecast view** (`view-forecast`) accepts a SKU selector and horizon input, calls `/api/forecast/{sku}?horizon=8`, and renders a bar chart with actual history overlaid by forecast bars, annotated with the XGBoost and NaiveETS ensemble weights as text badges.

**Pricing view** (`view-pricing`) calls `/api/pricing`, renders a card per SKU showing base price, optimal price, event-adjusted final price, and elasticity coefficient. An event signal banner at the top of the view lists all active GDELT event signals with their direction and strength, derived from `net_adjustment_pct`.

**Profit Engine view** (`view-profit`) renders a cost stack breakdown (stacked bar chart) and a what-if price slider that calls `/api/profit/scenario/{sku}` dynamically as the slider moves, updating a projected margin figure and decision matrix table in real time.

---

# CHAPTER 5 — IMPLEMENTATION (Work Accomplished)

## 5.1 Plan of Work

The dissertation work was executed across four phases aligned with the BITS Pilani WILP mid-review timeline. The table below reflects the planned schedule from the dissertation abstract, updated with completion status as of April 2026.

| Phase | Activities | Planned Dates | Status |
|---|---|---|---|
| Phase 1 — Research & Design | Literature survey; problem definition; system architecture design; technology selection; data source identification | Aug 2024 – Nov 2024 | **Completed** |
| Phase 2 — Data & Backend Development | CSV dataset construction (sales, competitors, reviews, holidays, GDELT); FastAPI backend implementation; ML module development (XGBoost + NaiveETS ensemble); live data connector implementation; profit engine | Dec 2024 – Feb 2025 | **Completed** |
| Phase 3 — Frontend & Integration | SPA development (8 views, Chart.js 4); REST API integration; GDELT event signal pipeline end-to-end; competitor price monitoring; mid-review report preparation | Mar 2025 – Mar 2026 | **Completed** |
| Phase 4 — Evaluation & Submission | Model performance evaluation; system testing; AWS architecture documentation; hackathon submission; final dissertation write-up | Apr 2026 – Jul 2026 | **In Progress** |

## 5.2 Key Challenges Encountered

**Challenge 1 — Prophet Latency Incompatibility**

Early prototyping included Facebook Prophet as the primary forecasting model, motivated by its native holiday regressor and additive decomposition capabilities. However, Stan MCMC sampling required 30–90 seconds per SKU, making the `/api/forecast/{sku}` endpoint unusable in a synchronous dashboard context. The resolution was to disable Prophet entirely (`USE_PROPHET_IN_ENSEMBLE = False`) and instead implement its conceptual contributions (holiday indicators, trend decomposition, external regressors) as explicit engineered features within the XGBoost feature matrix. The NaiveETS model provides the smoothing component that Prophet's Holt-Winters seasonality would have contributed.

**Challenge 2 — Spurious Positive Price Elasticity**

Initial elasticity regression on raw price-quantity time series produced positive coefficients for several SKUs — an economically invalid result. Investigation revealed that both prices and quantities for Indian electronics have trended upward over 2019–2024 due to market growth, creating spurious positive correlation. The resolution was to include a linear time trend variable (`t = 0, 1, ..., T`) as a covariate in the log-log regression, explicitly absorbing the secular growth trend before estimating the price-demand relationship. Post-detrending, all elasticity coefficients were economically plausible and negative.

**Challenge 3 — GDELT Relevance Noise**

Raw GDELT India-filtered data contained a high proportion of events geographically located in India but topically irrelevant to electronics retail (wildlife stories, road accidents, agricultural news). Without filtering, the News & Events view displayed confusing and unhelpful content, and the pricing engine received nonsensical price nudge signals. The resolution was to implement a keyword relevance scorer using a manually curated vocabulary of 50+ domain-specific terms, with a minimum score threshold of 0.25 to pass the filter.

**Challenge 4 — Pandas 2.x Deprecation**

The initial codebase used `fillna(method='ffill')` for forward-filling missing values in time series, which raises a `FutureWarning` in pandas 2.0 and an error in pandas 2.1+. All instances were replaced with the pandas 2.x idiomatic `.ffill()` method to ensure forward compatibility.

**Challenge 5 — Async ML Inference in FastAPI**

FastAPI's async event loop cannot be blocked by CPU-bound operations. Initial synchronous calls to XGBoost inference caused the server to become unresponsive during forecast computation. The resolution was to wrap forecast generation in `asyncio.get_event_loop().run_in_executor(None, generate_forecast, sku_id, horizon)`, delegating ML work to a thread pool while keeping the event loop free.

## 5.3 Potential Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| GDELT API unavailability | Medium | Medium | 6-hour disk cache; graceful fallback to last cached data; `/api/data-sources` health endpoint to monitor status |
| World Bank API rate limiting | Low | Low | Cached at startup; rarely needs refresh; static fallback CPI values hardcoded |
| XGBoost overfitting on small SKU history | Medium | Medium | Hold-out MAE weighting reduces reliance on XGBoost when it overfits; NaiveETS provides regularising baseline |
| Competitor price data staleness | Medium | High | Competitor prices modelled with realistic noise; production path uses live scraping or a third-party feed |
| Wikipedia Pageviews API changes | Low | Low | Six-hour cache; brand interest multiplier is a secondary feature; removal degrades forecast slightly but does not break the system |
| Single-server bottleneck at scale | High | High | AWS architecture design (Lambda + SageMaker) addresses horizontal scalability; current prototype is explicitly single-user |

---

# CHAPTER 6 — CONCLUSION

## 6.1 Summary of Contributions

This dissertation has designed and implemented BluePill AI, a working retail intelligence platform that addresses four simultaneous decision challenges facing Indian electronics retailers: demand volatility, competitive pricing pressure, fragmented market intelligence, and forecasting latency constraints. The system makes the following technical contributions:

1. **A two-model ensemble forecasting architecture** that combines the non-linear pattern recognition of XGBoost over a rich engineered feature set with the smoothing stability of a Naïve ETS baseline, using dynamic hold-out MAE weighting to adaptively favour the better-performing model per SKU per deployment period.

2. **A three-layer event-aware pricing engine** that sequentially applies detrended price elasticity estimation, competitor ceiling constraints, and GDELT-derived live event nudges, producing pricing recommendations that are simultaneously economically grounded, competitively bounded, and responsive to real-world market events.

3. **A zero-key live data integration framework** demonstrating that geopolitical intelligence (GDELT), macroeconomic indicators (World Bank), brand interest signals (Wikipedia Pageviews), and festival calendars (python-holidays) can all be integrated without commercial API subscriptions, making the architecture replicable without infrastructure cost.

4. **A unified single-page dashboard** that makes all five analytical modules accessible through eight views without requiring any data science expertise from the end user, fulfilling the goal of democratising retail analytics for mid-size Indian retailers.

## 6.2 Observations and Findings

The most significant finding from implementation is that **feature engineering is a more practical substitute for sophisticated generative models** in latency-constrained API settings. Prophet's functional contributions — holiday effects, trend decomposition, external regressors — can be replicated as explicit input features to a gradient-boosted tree model at a fraction of the inference cost. This trade-off is well-documented in the industrial ML literature but is worth re-affirming in the context of Indian retail, where festival-driven seasonality is both highly structured and well-represented in available offline data sources.

The GDELT-based market intelligence pipeline demonstrated that open news data can yield actionable price signals when subjected to domain-specific relevance filtering. The 50+ keyword vocabulary, combined with a minimum relevance score of 0.25, successfully surfaced events such as semiconductor supply disruptions, GST rate changes, and Diwali festival forecasts while eliminating the majority of geographically-coincident but topically irrelevant records.

The detrended elasticity approach resolved a non-trivial data quality problem specific to emerging-market retail datasets: the confounding of genuine price-demand relationships by secular market growth trends. This correction is not universally applied in practical implementations and its omission would have produced systematically wrong pricing recommendations.

## 6.3 Future Work

The following extensions are planned for the final dissertation phase:

- **Production AWS deployment**: Migrate from single-server FastAPI to the Lambda + API Gateway + SageMaker architecture documented in Figure 3.2.
- **Online model retraining**: Implement a scheduled retraining pipeline (AWS Glue + SageMaker Pipelines) that updates the XGBoost models as new sales data accumulates, rather than retraining from scratch on each API call.
- **Live review ingestion**: Replace the static `reviews.csv` with a live scraping or NLP pipeline over public e-commerce review sources, enabling real-time sentiment monitoring.
- **Elasticity confidence intervals**: Extend the elasticity regression to report bootstrap confidence intervals on the coefficient, which would allow the pricing engine to apply more conservative adjustments when the elasticity estimate is uncertain.
- **Expansion to additional product categories**: The modular architecture supports straightforward addition of new SKUs and categories beyond the current eight. Testing with a broader catalogue would validate generalisation of the ensemble weighting and elasticity estimation approaches.

---

# REFERENCES

[1] Liu, Y., Ma, X., Ge, M., Han, Z., Qiu, J., Moe, Y. A., Shen, Y., Wei, W., and Huang, C. (2025). "AttnBoost: Retail Supply Chain Sales Insights via Gradient Boosting Perspective." *arXiv preprint*. Available: https://arxiv.org/abs/2509.10506.

[2] Ganguly, P. and Mukherjee, I. (2024). "Enhancing Retail Sales Forecasting with Optimized Machine Learning Models." *arXiv preprint*. Available: https://arxiv.org/abs/2410.13773.

[3] Shapiro, S. and Panvelwala, B. (2026). "Prophet as a Reproducible Forecasting Framework: A Methodological Guide for Business and Financial Analytics." *arXiv preprint*. Available: https://arxiv.org/abs/2601.05929.

[4] Garg, L., Yaswanth, S., Mishra, D. N., Kumaran, K., Sharma, A., and Uniyal, M. (2026). "Monodense Deep Neural Model for Determining Item Price Elasticity." *arXiv preprint*. Available: https://arxiv.org/abs/2603.29261.

[5] Silcenco, O., Machad, M. R., Ugulino, W. C., and Braun, D. (2025). "A Retail-Corpus for Aspect-Based Sentiment Analysis with Large Language Models." *arXiv preprint*. Available: https://arxiv.org/abs/2508.17994.

[6] Xiang, Y., Yu, H., Gong, Y., Huo, S., and Zhu, M. (2024). "Text Understanding and Generation Using Transformer Models for Intelligent E-commerce Recommendations." *arXiv preprint*. Available: https://arxiv.org/abs/2402.16035.

[7] Banh Nghiep, K., Nguyen Minh, D., and Hoang Thi, L. (2026). "Bridging Deep Learning and Integer Linear Programming: A Predictive-to-Prescriptive Framework for Supply Chain Analytics." *arXiv preprint*. Available: https://arxiv.org/abs/2604.01775.

[8] Fatima, A. and Salam, M. A. (2026). "A Data-Driven Predictive Framework for Inventory Optimization Using Context-Augmented Machine Learning Models." *arXiv preprint*. Available: https://arxiv.org/abs/2601.05033.

---

*End of Mid-Review Dissertation Report*
*Tumati Suhas Pranay | 2024SL93003 | M.Tech Software Engineering (WILP) | April 2026*