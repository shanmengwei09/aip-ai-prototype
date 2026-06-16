# AI in Asset Investment Planning Prototype

This repository is a practical starter prototype for AI in Asset Investment Planning (AIP) in a highways asset management context. It uses mock data only and is intended to help develop thinking around AMFP / AAMP, 5AMP and 30AMP planning.

The prototype provides:

- A simple CSV-based data model.
- Fictional sample datasets for assets, condition, schemes, risks, delivery, handback and costs.
- An Ask AIP Data workspace where users can ask questions against the mock data lake.
- A Streamlit dashboard with portfolio, asset need, scheme challenge, handback, deliverability and change views.
- Transparent scoring logic for asset need, scheme priority, challenge and deliverability risk.
- Data templates for inventory and scheme evidence capture.
- Documentation for future development and a Microsoft-based RAG proof of concept.

## How To Run

Install Python 3.10 or later, then run the following from this folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

The app will open in a browser, usually at:

```text
http://localhost:8501
```

The sidebar lets you point the app at a different CSV data folder. By default it reads:

```text
data/sample/
```

## Repository Structure

```text
aip-ai-prototype/
  app.py
  requirements.txt
  README.md
  data/
    sample/
      assets.csv
      schemes.csv
      condition.csv
      risks.csv
      delivery.csv
      handback.csv
      costs.csv
    templates/
      data_inventory_template.csv
      scheme_evidence_template.csv
  src/
    data_loader.py
    scoring.py
    validation.py
    charts.py
  docs/
    data_model.md
    dashboard_design.md
    rag_microsoft_design.md
    implementation_plan.md
```

## What Each File Does

`app.py` is the Streamlit dashboard. It loads data, applies scoring and renders the six dashboard views.

`src/data_loader.py` reads CSV files, applies basic numeric conversion and reports missing files.

`src/qa_engine.py` provides the local question answering layer. It searches the mock CSV data lake, applies the scoring outputs and returns cited source rows. This is a prototype stand-in for a future Azure AI Search and Azure OpenAI pattern.

`src/validation.py` defines the required columns for each dataset and reports missing columns.

`src/scoring.py` contains the transparent scoring rules. These are deliberately simple and editable.

`src/charts.py` contains small Plotly chart helpers.

`data/sample/*.csv` contains fictional test data. Replace this with real, approved data when ready.

`data/templates/*.csv` contains starter templates for dataset inventory and scheme evidence tracking.

`docs/data_model.md` explains the dataset structure and relationships.

`docs/dashboard_design.md` explains the dashboard views and intended questions.

`docs/rag_microsoft_design.md` explains a future Microsoft RAG / AI query approach.

`docs/implementation_plan.md` gives phased next steps.

## What To Replace With Real Data

The analyst should replace the files in `data/sample/` with extracts from approved sources, keeping the same column names where possible:

- `assets.csv`: asset inventory and location data.
- `condition.csv`: latest condition and inspection evidence.
- `schemes.csv`: AMFP / AAMP / 5AMP scheme list.
- `risks.csv`: asset and scheme risks.
- `delivery.csv`: design, commercial, access and carryover information.
- `costs.csv`: previous and current scheme cost position.
- `handback.csv`: handback requirements, gaps and consequences.

If column names differ, update `src/validation.py` and the relevant dashboard logic in `app.py`.

## Scoring Assumptions

The scoring is not a black-box model. It is a transparent rule set that should be reviewed by asset leads.

Main assumptions:

- Condition score uses 1 as poor and 5 as good.
- High asset criticality increases asset need.
- Deteriorating condition increases asset need.
- Low confidence data increases need because the planning position is less certain.
- Scheme priority is higher where there are clear safety, condition, performance, handback, whole-life cost and risk links.
- Challenge score increases where evidence is weak, costs are high, handback is unclear, delivery confidence is low or costs have materially increased.
- Material cost increase is currently defined as at least GBP 250,000 or at least 20 percent.
- High cost with low evidence is currently defined as at least GBP 1.5m and weak or no evidence.

These thresholds are starter assumptions only.

## Ask AIP Data Assumptions

The question answering feature is a local prototype, not a live AI service.

It currently:

- Treats the CSV folder as a mock data lake.
- Detects broad question topics such as handback, challenge, delivery, affordability, condition, change and risk.
- Searches source rows using keywords, IDs, years, asset classes and routes.
- Generates deterministic insight text from the loaded data and scoring outputs.
- Cites the source rows it used.

The production version should replace this local logic with governed retrieval from Azure AI Search and grounded answer generation using Azure OpenAI.

## Limitations

- The data is fictional and should not be used for real investment decisions.
- The dashboard does not connect to live systems.
- There is no user authentication or permissions model.
- The Ask AIP Data feature is deterministic local logic, not a generative model.
- The scoring does not replace engineering judgement, asset lead review or governance decisions.
- The Microsoft RAG design is a future-state design, not an implemented RAG service.

## Suggested Next Step

Run a short working session with asset leads and the data analyst to confirm the minimum fields, scoring thresholds and source ownership. Then replace the mock CSVs with a controlled extract from current AMFP / AAMP / 5AMP working data.
