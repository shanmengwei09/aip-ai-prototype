# Dashboard Design

The dashboard is intended to support practical asset investment planning conversations. It is not a final production Power BI design.

## Intended Users

- Asset leads
- Investment planners
- Programme and delivery teams
- Data analysts
- Handback and governance reviewers

## Design Principles

- Use approved and traceable data.
- Keep scoring transparent and editable.
- Highlight issues that need review, not automated decisions.
- Show change from the previous planning position.
- Make evidence weakness visible early.
- Keep the first prototype simple enough to maintain in CSV and Python.

## Primary Query Workspace

### Ask AIP Data

This is now the main user experience. It is intended to feel closer to an AI assistant over an approved AIP data lake than a traditional dashboard.

Questions answered:

- Which schemes have weak evidence and high cost?
- What is critical for handback in 2027?
- Which schemes are at risk of carryover?
- Where are the affordability pressures?
- What has changed from the previous planning position?

Main outputs:

- Plain English answer
- Generated insights
- Cited source rows
- Topic-specific retrieval across schemes, assets, risks, delivery, costs and handback data

Prototype limitation:

- The current version uses local deterministic query logic over CSVs. It does not call a live language model.

Future direction:

- Replace the local query logic with Azure AI Search over approved data lake sources and Azure OpenAI grounded answer generation.

## Supporting Evidence Views

### 1. Portfolio Overview

Questions answered:

- What is the total investment value?
- How many schemes are in the filtered portfolio?
- Where is investment concentrated by asset class and year?
- How much is committed versus uncommitted?
- Which schemes create the greatest affordability pressure?

Main outputs:

- Total investment metric
- Scheme count
- Committed and uncommitted counts
- Investment by asset class
- Investment by proposed year
- Top affordability pressure table

### 2. Asset Need View

Questions answered:

- Which asset classes have poor condition?
- Which assets are old, high criticality or deteriorating?
- Where is condition data weak or low confidence?
- Which assets may need further evidence before planning decisions?

Main outputs:

- Average condition by asset class
- Average asset age by asset class
- Condition trend profile
- High-criticality and high-need asset table
- Low confidence data table

### 3. Scheme Challenge View

Questions answered:

- Which schemes have weak evidence?
- Which schemes are high cost but weakly justified?
- Which schemes have unclear investment drivers?
- Which schemes have unclear handback links?
- Which schemes need challenge before approval?

Main outputs:

- High challenge count
- Weak evidence count
- High cost and low evidence count
- Unclear handback count
- Challenge band chart
- Scheme challenge table with reasons

### 4. Handback View

Questions answered:

- Which assets have handback relevance?
- What handback gaps are open?
- Which schemes are critical to handback?
- What is the consequence of deferring schemes?
- Which items carry high handback risk?

Main outputs:

- Handback asset count
- High handback risk count
- Linked scheme count
- Critical handback scheme count
- Handback risk chart
- Gap and consequence table
- Linked scheme table

### 5. Deliverability View

Questions answered:

- Which schemes are at risk of carryover?
- Which schemes have low delivery confidence?
- Which schemes have access constraints?
- Where are design or commercial readiness issues?
- What are the key delivery constraints?

Main outputs:

- High carryover risk count
- Low confidence count
- High access constraint count
- High delivery risk count
- Carryover risk chart
- Deliverability risk chart
- Key constraint table

### 6. Change View

Questions answered:

- What is new compared with the previous plan?
- What has been deferred or removed?
- Which schemes have material cost changes?
- How has the position moved from the previous AMFP / AAMP / 5AMP view?

Main outputs:

- New scheme count
- Deferred scheme count
- Removed scheme count
- Material cost change count
- Previous status to current status chart
- Movement and material change table

## Filters

The prototype has two sidebar filters:

- Asset class
- Proposed year

These filters apply to scheme-led dashboard views. Asset need remains filtered by selected asset class.

## Future Enhancements

Useful next dashboard features:

- Scenario filters for affordability options.
- Side-by-side comparison of AAMP, 5AMP and 30AMP positions.
- Evidence document links for each scheme.
- Exportable challenge list.
- RAG answer panel that only uses approved source material.
- Power BI version once fields and measures are stable.
