"""Column requirements and validation helpers for prototype datasets."""

REQUIRED_COLUMNS = {
    "assets": [
        "asset_id",
        "asset_class",
        "location",
        "route",
        "chainage_start",
        "chainage_end",
        "asset_age",
        "criticality",
        "handback_relevance",
    ],
    "condition": [
        "asset_id",
        "condition_score",
        "condition_trend",
        "latest_inspection_date",
        "evidence_source",
        "confidence_level",
    ],
    "schemes": [
        "scheme_id",
        "scheme_name",
        "asset_class",
        "linked_asset_id",
        "intervention_type",
        "proposed_year",
        "estimated_cost",
        "investment_driver",
        "safety_link",
        "condition_link",
        "performance_link",
        "handback_link",
        "whole_life_cost_link",
        "evidence_strength",
        "current_status",
        "previous_plan_status",
        "change_reason",
    ],
    "risks": [
        "risk_id",
        "linked_asset_id",
        "linked_scheme_id",
        "risk_description",
        "likelihood",
        "impact",
        "risk_score",
        "mitigation",
        "residual_risk",
    ],
    "delivery": [
        "scheme_id",
        "design_status",
        "commercial_status",
        "access_constraint",
        "delivery_confidence",
        "carryover_risk",
        "key_constraint",
    ],
    "costs": [
        "scheme_id",
        "previous_cost",
        "current_cost",
        "cost_change",
        "cost_change_reason",
        "affordability_pressure",
    ],
    "handback": [
        "asset_id",
        "handback_requirement",
        "current_gap",
        "proposed_intervention",
        "handback_risk_level",
        "consequence_if_deferred",
    ],
}

OPTIONAL_COLUMNS = {
    "schemes": ["previous_proposed_year"],
}


def missing_columns(dataframe, dataset_name):
    """Return required columns that are absent from a dataframe."""
    required = REQUIRED_COLUMNS.get(dataset_name, [])
    return [column for column in required if column not in dataframe.columns]


def validate_dataset(dataframe, dataset_name):
    """Return a list of human-readable validation errors for one dataset."""
    missing = missing_columns(dataframe, dataset_name)
    if not missing:
        return []
    joined = ", ".join(missing)
    return [f"{dataset_name}.csv is missing required column(s): {joined}"]
