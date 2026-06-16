# Data Model

The prototype uses a small CSV-based model. It is designed to be easy to inspect, edit and replace with real extracts later.

## Core Relationships

```text
assets.asset_id
  -> condition.asset_id
  -> handback.asset_id
  -> schemes.linked_asset_id
  -> risks.linked_asset_id

schemes.scheme_id
  -> risks.linked_scheme_id
  -> delivery.scheme_id
  -> costs.scheme_id
```

## Dataset Summary

### Asset Inventory

File: `data/sample/assets.csv`

Purpose: one row per asset or asset grouping used for investment planning.

Required fields:

- `asset_id`
- `asset_class`
- `location`
- `route`
- `chainage_start`
- `chainage_end`
- `asset_age`
- `criticality`
- `handback_relevance`

### Condition Data

File: `data/sample/condition.csv`

Purpose: latest condition view and confidence in the supporting evidence.

Required fields:

- `asset_id`
- `condition_score`
- `condition_trend`
- `latest_inspection_date`
- `evidence_source`
- `confidence_level`

Assumption: `condition_score` is 1 to 5, where 1 is poor and 5 is good.

### Scheme Data

File: `data/sample/schemes.csv`

Purpose: current investment planning schemes and their evidence links.

Required fields:

- `scheme_id`
- `scheme_name`
- `asset_class`
- `linked_asset_id`
- `intervention_type`
- `proposed_year`
- `estimated_cost`
- `investment_driver`
- `safety_link`
- `condition_link`
- `performance_link`
- `handback_link`
- `whole_life_cost_link`
- `evidence_strength`
- `current_status`
- `previous_plan_status`
- `change_reason`

Optional field used in this prototype:

- `previous_proposed_year`

This optional field enables transparent testing of whether the proposed year has moved without a clear reason.

### Risk Data

File: `data/sample/risks.csv`

Purpose: asset and scheme risks linked to investment need.

Required fields:

- `risk_id`
- `linked_asset_id`
- `linked_scheme_id`
- `risk_description`
- `likelihood`
- `impact`
- `risk_score`
- `mitigation`
- `residual_risk`

Assumption: `risk_score` is normally likelihood multiplied by impact, but the prototype accepts a blank value where risk is not quantified.

### Delivery Data

File: `data/sample/delivery.csv`

Purpose: delivery readiness, constraints and carryover risk.

Required fields:

- `scheme_id`
- `design_status`
- `commercial_status`
- `access_constraint`
- `delivery_confidence`
- `carryover_risk`
- `key_constraint`

### Cost Data

File: `data/sample/costs.csv`

Purpose: previous and current cost position.

Required fields:

- `scheme_id`
- `previous_cost`
- `current_cost`
- `cost_change`
- `cost_change_reason`
- `affordability_pressure`

### Handback Data

File: `data/sample/handback.csv`

Purpose: handback requirements, gaps and consequences.

Required fields:

- `asset_id`
- `handback_requirement`
- `current_gap`
- `proposed_intervention`
- `handback_risk_level`
- `consequence_if_deferred`

## Controlled Values

The prototype currently expects simple text categories.

Suggested values:

- Criticality: `High`, `Medium`, `Low`
- Handback relevance: `High`, `Medium`, `Low`
- Condition trend: `Improving`, `Stable`, `Deteriorating`, `Rapid deterioration`
- Confidence level: `High`, `Medium`, `Low`
- Link fields: `Yes`, `Partial`, `Unclear`, `No`
- Evidence strength: `Strong`, `Moderate`, `Weak`, `None`
- Affordability pressure: `High`, `Medium`, `Low`
- Carryover risk: `High`, `Medium`, `Low`

## Data Quality Checks

The current validation checks are intentionally basic:

- Required CSV files must exist.
- Required columns must exist.
- Known numeric columns are converted to numbers where possible.

Recommended next checks:

- Unique `asset_id` in `assets.csv`.
- Unique `scheme_id` in `schemes.csv`.
- All scheme `linked_asset_id` values must exist in `assets.csv`.
- All cost and delivery `scheme_id` values must exist in `schemes.csv`.
- Controlled values should be validated against agreed lists.
- Date fields should be valid dates and current enough for planning use.
