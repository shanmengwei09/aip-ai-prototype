# Implementation Plan

## Phase 1 - Data Inventory And Prototype

Objectives:

- Confirm available datasets.
- Agree minimum required fields.
- Create dashboard prototype.
- Test with asset leads.

Activities:

- Complete `data/templates/data_inventory_template.csv`.
- Identify owners for asset, condition, scheme, risk, delivery, cost and handback data.
- Confirm which fields are already available and which fields need manual enrichment.
- Replace mock data with a small approved extract.
- Review dashboard outputs with asset leads.
- Capture missing fields, unclear definitions and duplicate sources.

Outputs:

- Agreed minimum data model.
- Working prototype dashboard using approved sample extracts.
- Initial list of data quality issues.

## Phase 2 - Data Quality And Governance

Objectives:

- Improve data quality.
- Agree ownership.
- Define update frequency.
- Introduce confidence scoring.
- Create handback tagging.

Activities:

- Define controlled values for fields such as evidence strength, criticality and confidence level.
- Agree data owners and update frequency.
- Add validation checks for unique IDs and broken links.
- Define confidence scoring rules.
- Confirm how handback relevance should be tagged.
- Establish a controlled source folder for extracts.

Outputs:

- Data ownership matrix.
- Data quality rules.
- Confidence scoring approach.
- Handback tagging rules.

## Phase 3 - Investment Challenge And Scenario Planning

Objectives:

- Add prioritisation logic.
- Add challenge flags.
- Add affordability scenarios.
- Compare AAMP / 5AMP movements.

Activities:

- Review scoring thresholds with asset leads.
- Add scenario fields for preferred, minimum and deferred investment cases.
- Add affordability bands and fiscal year limits.
- Create outputs for challenge meetings.
- Track movements from previous to current planning position.
- Add export of challenge lists.

Outputs:

- Agreed challenge logic.
- Scenario planning dashboard.
- Change log view for planning movements.

## Phase 4 - Microsoft RAG Proof Of Concept

Objectives:

- Identify approved documents.
- Create controlled source library.
- Test AI querying.
- Validate source citation.
- Test user permissions.

Activities:

- Choose one asset class or route for the pilot.
- Create a SharePoint source library with approved files only.
- Add metadata for version, owner, approval status and asset class.
- Index the source library with Azure AI Search.
- Use Azure OpenAI or Copilot Studio for controlled question answering.
- Test known-answer questions.
- Confirm that unsupported questions are refused.
- Validate that users only see sources they are permitted to access.

Outputs:

- Controlled RAG proof of concept.
- Test results and failure examples.
- Recommendation on whether to scale.

## Phase 5 - Productionisation

Objectives:

- Integrate with approved systems.
- Automate refreshes.
- Introduce governance workflow.
- Define ownership and support model.

Activities:

- Move reporting to Power BI or another approved platform if required.
- Automate data refreshes from approved sources.
- Create governance workflow for source approval.
- Define support ownership.
- Add monitoring and audit logging.
- Confirm retention and archive approach.
- Document operational controls.

Outputs:

- Production roadmap.
- Support model.
- Governance process.
- Approved system integration plan.

## Immediate Next Actions

1. Agree the minimum viable data fields.
2. Confirm scoring thresholds for high cost, material cost change, weak evidence and low delivery confidence.
3. Replace mock CSVs with a small controlled extract.
4. Run the dashboard with asset leads.
5. Decide whether the Microsoft RAG proof of concept should start with one asset class, one route or one planning cycle.
