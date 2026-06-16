"""Transparent scoring rules for asset need, scheme challenge and delivery risk."""

import pandas as pd


LINK_SCORE = {
    "yes": 1.0,
    "partial": 0.5,
    "unclear": 0.25,
    "no": 0.0,
}

EVIDENCE_POINTS = {
    "strong": 10,
    "moderate": 6,
    "weak": 2,
    "none": 0,
}


def _normalise(value):
    if pd.isna(value):
        return ""
    return str(value).strip().lower()


def _mapped(value, mapping, default=0):
    return mapping.get(_normalise(value), default)


def _band(value, bands):
    for threshold, label in bands:
        if value >= threshold:
            return label
    return bands[-1][1]


def _join_flags(row, flag_columns):
    labels = []
    for column, label in flag_columns.items():
        if bool(row.get(column, False)):
            labels.append(label)
    return "; ".join(labels)


def score_asset_need(assets, condition):
    """Create an explainable 0-100 asset need score."""
    scored = assets.merge(condition, on="asset_id", how="left")

    condition_score = pd.to_numeric(scored["condition_score"], errors="coerce").fillna(3)
    condition_points = ((6 - condition_score).clip(1, 5)) * 7

    trend_points = scored["condition_trend"].map(
        lambda value: _mapped(
            value,
            {
                "rapid deterioration": 20,
                "deteriorating": 14,
                "stable": 5,
                "improving": 0,
            },
        )
    )
    criticality_points = scored["criticality"].map(
        lambda value: _mapped(value, {"high": 20, "medium": 10, "low": 4})
    )
    age = pd.to_numeric(scored["asset_age"], errors="coerce").fillna(0)
    age_points = pd.cut(
        age,
        bins=[-1, 14, 29, 49, 999],
        labels=[2, 6, 10, 15],
    ).astype(int)
    confidence_points = scored["confidence_level"].map(
        lambda value: _mapped(value, {"low": 10, "medium": 4, "high": 0})
    )

    scored["asset_need_score"] = (
        condition_points
        + trend_points
        + criticality_points
        + age_points
        + confidence_points
    ).clip(0, 100)
    scored["asset_need_band"] = scored["asset_need_score"].map(
        lambda value: _band(value, [(70, "High"), (45, "Medium"), (0, "Low")])
    )
    return scored


def score_scheme_priority(schemes, risks):
    """Create a 0-100 priority score using links, evidence and quantified risk."""
    scored = schemes.copy()
    risk_by_scheme = (
        risks.groupby("linked_scheme_id", dropna=False)["risk_score"]
        .max()
        .rename("max_risk_score")
        .reset_index()
    )
    scored = scored.merge(
        risk_by_scheme,
        left_on="scheme_id",
        right_on="linked_scheme_id",
        how="left",
    )

    scored["scheme_priority_score"] = (
        scored["safety_link"].map(lambda value: _mapped(value, LINK_SCORE)) * 18
        + scored["condition_link"].map(lambda value: _mapped(value, LINK_SCORE)) * 18
        + scored["performance_link"].map(lambda value: _mapped(value, LINK_SCORE)) * 12
        + scored["handback_link"].map(lambda value: _mapped(value, LINK_SCORE)) * 18
        + scored["whole_life_cost_link"].map(lambda value: _mapped(value, LINK_SCORE)) * 10
        + scored["evidence_strength"].map(lambda value: _mapped(value, EVIDENCE_POINTS))
        + (pd.to_numeric(scored["max_risk_score"], errors="coerce").fillna(0).clip(0, 20) / 20 * 14)
    ).round(1)
    scored["scheme_priority_band"] = scored["scheme_priority_score"].map(
        lambda value: _band(value, [(70, "Critical"), (50, "High"), (30, "Medium"), (0, "Low")])
    )
    return scored.drop(columns=["linked_scheme_id"], errors="ignore")


def score_challenge(schemes, delivery, costs, risks, condition):
    """Flag schemes that may need challenge before approval."""
    scored = schemes.copy()

    risk_by_scheme = (
        risks.groupby("linked_scheme_id", dropna=False)["risk_score"]
        .max()
        .rename("max_risk_score")
        .reset_index()
    )
    condition_lookup = condition[["asset_id", "confidence_level"]].rename(
        columns={"asset_id": "linked_asset_id", "confidence_level": "asset_data_confidence"}
    )

    scored = scored.merge(delivery, on="scheme_id", how="left")
    scored = scored.merge(costs, on="scheme_id", how="left")
    scored = scored.merge(
        risk_by_scheme,
        left_on="scheme_id",
        right_on="linked_scheme_id",
        how="left",
    )
    scored = scored.merge(condition_lookup, on="linked_asset_id", how="left")

    estimated_cost = pd.to_numeric(scored["estimated_cost"], errors="coerce").fillna(0)
    previous_cost = pd.to_numeric(scored["previous_cost"], errors="coerce")
    current_cost = pd.to_numeric(scored["current_cost"], errors="coerce")
    cost_change = pd.to_numeric(scored["cost_change"], errors="coerce").fillna(0)
    safe_previous_cost = previous_cost.mask(previous_cost == 0)
    cost_change_pct = ((current_cost - previous_cost) / safe_previous_cost).fillna(0)

    evidence = scored["evidence_strength"].map(_normalise)
    driver = scored["investment_driver"].fillna("").astype(str).str.strip()
    change_reason = scored["change_reason"].fillna("").astype(str).str.strip().str.lower()

    scored["flag_weak_evidence"] = evidence.isin(["weak", "none", ""])
    scored["flag_high_cost_low_evidence"] = (estimated_cost >= 1_500_000) & scored["flag_weak_evidence"]
    scored["flag_unclear_driver"] = driver.eq("") | driver.str.lower().isin(["tbc", "to be confirmed", "unclear"])
    scored["flag_unclear_handback"] = scored["handback_link"].map(_normalise).isin(["unclear"])
    scored["flag_condition_evidence_weak"] = (
        scored["condition_link"].map(_normalise).isin(["yes", "partial"])
        & (
            scored["flag_weak_evidence"]
            | scored["asset_data_confidence"].map(_normalise).isin(["low", ""])
        )
    )
    scored["flag_risk_not_quantified"] = pd.to_numeric(scored["max_risk_score"], errors="coerce").isna()
    scored["flag_low_delivery_confidence"] = scored["delivery_confidence"].map(_normalise).isin(["low"])
    scored["flag_material_cost_increase"] = (cost_change >= 250_000) | (cost_change_pct >= 0.2)

    if "previous_proposed_year" in scored.columns:
        previous_year = pd.to_numeric(scored["previous_proposed_year"], errors="coerce")
        proposed_year = pd.to_numeric(scored["proposed_year"], errors="coerce")
        year_changed = previous_year.notna() & proposed_year.notna() & previous_year.ne(proposed_year)
        unclear_reason = change_reason.eq("") | change_reason.isin(["tbc", "to be confirmed", "unclear"])
        scored["flag_year_changed_without_reason"] = year_changed & unclear_reason
    else:
        scored["flag_year_changed_without_reason"] = False

    # Starter challenge weights. Review these with asset leads before real use.
    weights = {
        "flag_high_cost_low_evidence": 25,
        "flag_unclear_driver": 20,
        "flag_unclear_handback": 15,
        "flag_condition_evidence_weak": 15,
        "flag_risk_not_quantified": 10,
        "flag_low_delivery_confidence": 20,
        "flag_material_cost_increase": 15,
        "flag_year_changed_without_reason": 15,
    }
    scored["challenge_score"] = sum(scored[column].astype(int) * weight for column, weight in weights.items())
    scored["challenge_score"] = scored["challenge_score"].clip(0, 100)
    scored["challenge_band"] = scored["challenge_score"].map(
        lambda value: _band(value, [(60, "High"), (30, "Medium"), (1, "Low"), (0, "None")])
    )

    flag_labels = {
        "flag_high_cost_low_evidence": "high cost with low evidence",
        "flag_unclear_driver": "unclear investment driver",
        "flag_unclear_handback": "unclear handback link",
        "flag_condition_evidence_weak": "weak condition evidence",
        "flag_risk_not_quantified": "risk not quantified",
        "flag_low_delivery_confidence": "low delivery confidence",
        "flag_material_cost_increase": "material cost increase",
        "flag_year_changed_without_reason": "year changed without clear reason",
    }
    scored["challenge_reasons"] = scored.apply(lambda row: _join_flags(row, flag_labels), axis=1)
    return scored.drop(columns=["linked_scheme_id"], errors="ignore")


def score_deliverability(delivery):
    """Create a 0-100 deliverability risk score."""
    scored = delivery.copy()
    scored["deliverability_risk_score"] = (
        scored["design_status"].map(
            lambda value: _mapped(
                value,
                {
                    "detailed design complete": 0,
                    "detailed design in progress": 8,
                    "outline design complete": 12,
                    "feasibility complete": 18,
                    "feasibility incomplete": 25,
                    "concept only": 25,
                    "not applicable": 0,
                },
                default=15,
            )
        )
        + scored["commercial_status"].map(
            lambda value: _mapped(
                value,
                {
                    "contract in place": 0,
                    "framework call-off ready": 5,
                    "route to market agreed": 8,
                    "commercial strategy agreed": 10,
                    "procurement not started": 25,
                    "not applicable": 0,
                },
                default=15,
            )
        )
        + scored["access_constraint"].map(lambda value: _mapped(value, {"high": 25, "moderate": 12, "low": 3}))
        + scored["delivery_confidence"].map(lambda value: _mapped(value, {"high": 0, "medium": 12, "low": 25}))
        + scored["carryover_risk"].map(lambda value: _mapped(value, {"high": 25, "medium": 12, "low": 3}))
    ).clip(0, 100)
    scored["deliverability_risk_band"] = scored["deliverability_risk_score"].map(
        lambda value: _band(value, [(70, "High"), (40, "Medium"), (0, "Low")])
    )
    return scored
