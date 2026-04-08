# BluePill AI – System Design Document

## 1. Design Overview
BluePill AI is designed as a modular, cloud-native decision intelligence platform built on managed AWS AI services.
The architecture emphasizes scalability, explainability, and responsible AI usage.

The system processes multiple structured and unstructured data sources in parallel and converges insights into a unified recommendation layer reviewed by humans.

---

## 2. High-Level Architecture
The platform follows a layered architecture:

1. Data Sources
2. Data Ingestion & Processing
3. AI & Analytics Layer
4. Orchestration Layer
5. Storage & Analytics
6. Presentation & Interaction
7. Security & Monitoring

---

## 3. Data Sources
- Retail sales and inventory systems → `data_sources/sales_data/raw/sales.csv`
- Festival and promotional calendars → `data_sources/festivals/raw/festivals.csv`
- Competitor pricing feeds → `data_sources/competitor_prices/raw/competitor_prices.csv`
- Customer reviews and ratings → `data_sources/customer_reviews/raw/reviews.csv`
- Weather and climate data → `data_sources/climate/raw/weather.csv`
- Geopolitical events → `data_sources/geopolitical/raw/events.csv`
- Real-time news (GDELT, NewsAPI) → External APIs (to be integrated)

---

## 4. Data Ingestion & Processing
- Amazon S3 acts as the centralized data lake.
- AWS Lambda handles event-driven ingestion.
- AWS Glue performs data transformation, normalization, and schema management.
- Structured and unstructured data are prepared for downstream AI processing.

---

## 5. AI & Analytics Layer

### 5.1 Demand Forecasting
- Amazon Forecast is used for time-series demand prediction.
- External regressors such as festivals and seasonality are incorporated.
- Forecast confidence bands are generated for decision transparency.

### 5.2 Pricing & Risk Modeling
- Amazon SageMaker hosts custom ML models for:
  - Price elasticity estimation
  - Pricing optimization
  - Risk scoring
- Models are retrained periodically based on accuracy feedback.

### 5.3 NLP & Sentiment Analysis
- ✅ **IMPLEMENTED** in `ai_processing_layer/sentiment_analysis/`
- 5-model ensemble: Multilingual BERT, GoEmotions, sarcasm detection, star-rating
- Aspect-Based Sentiment Analysis (ABSA) for product features
- Fraud/fake review detection (Random Forest + Gradient Boosting)
- Web scraping pipeline (Amazon, Flipkart, YouTube)
- Production enhancements: Bayesian cross-platform fusion, uncertainty quantification, drift monitoring, bias detection

### 5.4 Market Events & Risk Intelligence
- GDELT Project integration for geopolitical event tracking (250M+ events)
- NewsAPI aggregation for real-time news monitoring
- BERT-based event classification (recall, launch, regulation, supply chain)
- Demand impact quantification based on severity, reach, and recency

### 5.5 Generative AI & Reasoning
- Amazon Bedrock powers:
  - Event summarization from news
  - Cross-signal reasoning
  - AI Business Copilot interactions

---

## 6. Workflow Orchestration
- AWS Step Functions orchestrate parallel AI workflows.
- Forecasting, pricing, sentiment, risk, and compliance analyses run concurrently.
- Outputs are aggregated into a unified recommendation object.

---

## 7. Storage & Analytics
- Amazon Redshift stores aggregated analytics and historical insights.
- Amazon DynamoDB stores low-latency recommendation metadata and state.
- Data is retained to enable auditing and explainability.

---

## 8. Presentation & User Interaction
- Amazon QuickSight provides interactive dashboards for:
  - Forecasts
  - Pricing insights
  - Sentiment trends
- A web-based UI (React / AWS Amplify) enables user interaction.
- The AI Business Copilot offers conversational access to insights.

---

## 9. Human-in-the-Loop & Responsible AI
- All AI outputs are recommendations, not automated actions.
- Business users review, validate, and approve decisions.
- Explanations and source references are provided for trust.
- Full audit trails are maintained for compliance-related workflows.

---

## 10. Security & Monitoring
- AWS IAM enforces role-based access control.
- Amazon Cognito manages user authentication.
- Amazon CloudWatch monitors system health and performance.
- Sensitive data is protected according to cloud security best practices.

---

## 11. Scalability & Feasibility
- The system is built using fully managed AWS services.
- Components scale independently based on demand.
- Initial deployment focuses on pilot scope with phased expansion.

---

## 12. Design Rationale
This design ensures:
- Meaningful use of AI beyond rule-based logic
- Clear separation of concerns
- Production readiness within hackathon constraints
- Alignment with real-world retail and marketplace complexity
