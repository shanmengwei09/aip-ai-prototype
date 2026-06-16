"""Local question answering over the prototype CSV data lake.

This is deliberately deterministic. It simulates the retrieval and insight layer
that would later be replaced by Azure AI Search and Azure OpenAI.
"""

import re

import pandas as pd


STOP_WORDS = {
    "a",
    "about",
    "all",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "for",
    "from",
    "give",
    "has",
    "have",
    "how",
    "in",
    "is",
    "me",
    "of",
    "on",
    "or",
    "our",
    "show",
    "tell",
    "the",
    "to",
    "what",
    "where",
    "which",
    "with",
}

TOPIC_HINTS = {
    "handback": {"handback", "defer", "deferred", "deferral", "critical", "gap"},
    "challenge": {"challenge", "evidence", "weak", "justification", "driver", "unclear"},
    "delivery": {"delivery", "deliverability", "carryover", "access", "commercial", "design"},
    "affordability": {"affordability", "cost", "expensive", "increase", "pressure", "budget"},
    "condition": {"asset", "condition", "deteriorating", "inspection", "confidence", "criticality"},
    "change": {"change", "changed", "new", "removed", "deferred", "movement", "previous"},
    "risk": {"risk", "likelihood", "impact", "mitigation", "residual"},
}


def _tokens(text):
    words = re.findall(r"[a-z0-9]+", str(text).lower())
    return [word for word in words if word not in STOP_WORDS and len(word) > 1]


def _normalise(value):
    if pd.isna(value):
        return ""
    return str(value).strip().lower()


def _money(value):
    try:
        return f"GBP {float(value) / 1_000_000:.1f}m"
    except (TypeError, ValueError):
        return "GBP 0.0m"


def _detect_topic(question):
    question_tokens = set(_tokens(question))
    scores = {
        topic: len(question_tokens.intersection(hints))
        for topic, hints in TOPIC_HINTS.items()
    }
    best_topic = max(scores, key=scores.get)
    return best_topic if scores[best_topic] > 0 else "search"


def _extract_filters(question, schemes, assets):
    lowered = str(question).lower()
    filters = {}

    years = re.findall(r"\b20\d{2}\b", lowered)
    if years:
        filters["years"] = {int(year) for year in years}

    asset_classes = {
        str(value).lower(): value for value in schemes["asset_class"].dropna().unique()
    }
    matched_classes = {
        original
        for lowered_class, original in asset_classes.items()
        if lowered_class in lowered
    }
    if matched_classes:
        filters["asset_classes"] = matched_classes

    routes = {str(value).lower(): value for value in assets["route"].dropna().unique()}
    matched_routes = {
        original
        for lowered_route, original in routes.items()
        if lowered_route in lowered
    }
    if matched_routes:
        filters["routes"] = matched_routes

    ids = re.findall(r"\b[asr]\d{3}\b", lowered)
    if ids:
        filters["ids"] = {value.upper() for value in ids}

    return filters


def _apply_scheme_filters(dataframe, filters, assets):
    filtered = dataframe.copy()
    if "years" in filters and "proposed_year" in filtered.columns:
        filtered = filtered[filtered["proposed_year"].isin(filters["years"])]
    if "asset_classes" in filters and "asset_class" in filtered.columns:
        filtered = filtered[filtered["asset_class"].isin(filters["asset_classes"])]
    if "routes" in filters and "linked_asset_id" in filtered.columns:
        route_assets = assets[assets["route"].isin(filters["routes"])]["asset_id"]
        filtered = filtered[filtered["linked_asset_id"].isin(route_assets)]
    if "ids" in filters:
        id_values = filters["ids"]
        id_columns = [column for column in ["scheme_id", "linked_asset_id", "asset_id"] if column in filtered.columns]
        if id_columns:
            mask = False
            for column in id_columns:
                mask = mask | filtered[column].isin(id_values)
            filtered = filtered[mask]
    return filtered


def _source_rows(dataset, dataframe, id_column, title_column=None, limit=8):
    rows = []
    if dataframe.empty:
        return rows

    for _, row in dataframe.head(limit).iterrows():
        title = ""
        if title_column and title_column in row:
            title = str(row[title_column])
        summary_parts = []
        for column in dataframe.columns:
            value = row.get(column)
            if pd.notna(value) and str(value).strip():
                summary_parts.append(f"{column}: {value}")
            if len(summary_parts) >= 5:
                break
        rows.append(
            {
                "source": dataset,
                "record_id": row.get(id_column, ""),
                "title": title,
                "summary": "; ".join(summary_parts),
            }
        )
    return rows


def build_search_results(question, data, limit=10):
    """Search all loaded datasets and return likely source rows."""
    question_tokens = set(_tokens(question))
    id_hints = set(re.findall(r"\b[asr]\d{3}\b", str(question).lower()))
    records = []

    dataset_ids = {
        "assets": "asset_id",
        "condition": "asset_id",
        "schemes": "scheme_id",
        "risks": "risk_id",
        "delivery": "scheme_id",
        "costs": "scheme_id",
        "handback": "asset_id",
    }
    dataset_titles = {
        "assets": "location",
        "schemes": "scheme_name",
        "risks": "risk_description",
        "delivery": "key_constraint",
        "costs": "cost_change_reason",
        "handback": "current_gap",
    }

    for dataset_name, dataframe in data.items():
        if dataset_name not in dataset_ids or dataframe.empty:
            continue
        id_column = dataset_ids[dataset_name]
        title_column = dataset_titles.get(dataset_name)
        for _, row in dataframe.iterrows():
            text = " ".join(str(value) for value in row.values if pd.notna(value)).lower()
            row_tokens = set(_tokens(text))
            token_score = len(question_tokens.intersection(row_tokens))
            row_id = str(row.get(id_column, "")).lower()
            id_score = 8 if row_id in id_hints else 0
            score = token_score + id_score
            if score <= 0:
                continue
            title = str(row.get(title_column, "")) if title_column else ""
            records.append(
                {
                    "score": score,
                    "source": dataset_name,
                    "record_id": row.get(id_column, ""),
                    "title": title,
                    "summary": text[:260],
                }
            )

    records = sorted(records, key=lambda item: item["score"], reverse=True)
    return records[:limit]


def answer_question(question, data, asset_needs, scheme_priority, challenge, delivery_scored):
    """Answer a question using loaded datasets and transparent rules."""
    question = str(question or "").strip()
    if not question:
        return {
            "topic": "intro",
            "answer": "Ask a question about schemes, assets, handback, evidence, delivery, affordability, change or risk.",
            "insights": [
                "Example: Which schemes have weak evidence and high cost?",
                "Example: What is critical for handback in 2027?",
                "Example: Which schemes are at risk of carryover?",
            ],
            "sources": [],
        }

    topic = _detect_topic(question)
    filters = _extract_filters(question, data["schemes"], data["assets"])
    schemes = data["schemes"]
    assets = data["assets"]

    if topic == "handback":
        handback_assets = data["handback"].merge(assets, on="asset_id", how="left")
        scheme_view = schemes[schemes["handback_link"].map(_normalise).isin(["yes", "partial", "unclear"])]
        scheme_view = _apply_scheme_filters(scheme_view, filters, assets)
        high_risk = handback_assets[handback_assets["handback_risk_level"].map(_normalise).eq("high")]
        answer = (
            f"I found {len(scheme_view)} schemes with a handback link and "
            f"{len(high_risk)} high handback risk assets in the current data."
        )
        insights = [
            f"Critical handback schemes total {_money(scheme_view[scheme_view['handback_link'].map(_normalise).eq('yes')]['estimated_cost'].sum())}.",
            "Treat unclear handback links as a review queue because they can hide future liability.",
            "High handback risk items should cite both the scheme row and the handback gap row before approval.",
        ]
        sources = _source_rows("schemes", scheme_view.sort_values("estimated_cost", ascending=False), "scheme_id", "scheme_name")
        sources += _source_rows("handback", high_risk, "asset_id", "current_gap")

    elif topic == "challenge":
        view = _apply_scheme_filters(challenge, filters, assets)
        view = view[view["challenge_score"].gt(0)].sort_values(["challenge_score", "estimated_cost"], ascending=[False, False])
        weak = int(view.get("flag_weak_evidence", pd.Series(dtype=bool)).sum())
        high_cost_low_evidence = int(view.get("flag_high_cost_low_evidence", pd.Series(dtype=bool)).sum())
        answer = (
            f"I found {len(view)} schemes with at least one challenge flag. "
            f"{weak} have weak or no evidence and {high_cost_low_evidence} are high cost with low evidence."
        )
        insights = [
            "The highest challenge scores should be reviewed before approval rather than treated as automatic rejects.",
            "Weak evidence combined with material cost growth is the strongest signal for scheme challenge.",
            "Unclear investment drivers should be closed before the scheme is used in a formal planning position.",
        ]
        sources = _source_rows("schemes_with_challenge_scores", view, "scheme_id", "scheme_name")

    elif topic == "delivery":
        delivery_view = schemes.merge(delivery_scored, on="scheme_id", how="left")
        delivery_view = _apply_scheme_filters(delivery_view, filters, assets)
        risky = delivery_view[
            delivery_view["carryover_risk"].map(_normalise).eq("high")
            | delivery_view["delivery_confidence"].map(_normalise).eq("low")
            | delivery_view["deliverability_risk_band"].eq("High")
        ].sort_values("deliverability_risk_score", ascending=False)
        answer = (
            f"I found {len(risky)} schemes with high carryover risk, low delivery confidence "
            "or a high deliverability risk score."
        )
        insights = [
            "Design maturity, procurement status and access constraints are the main drivers of carryover risk in this prototype.",
            "Schemes with both high access constraint and low confidence should be treated as delivery challenge items.",
            "A delivery risk score does not mean the scheme is low value; it means the plan may need mitigation or reprogramming.",
        ]
        sources = _source_rows("delivery_with_scores", risky, "scheme_id", "scheme_name")

    elif topic == "affordability":
        cost_view = schemes.merge(data["costs"], on="scheme_id", how="left")
        cost_view = _apply_scheme_filters(cost_view, filters, assets)
        pressure = cost_view[cost_view["affordability_pressure"].map(_normalise).eq("high")]
        material = cost_view[
            pd.to_numeric(cost_view["cost_change"], errors="coerce").fillna(0).abs().ge(250_000)
        ]
        answer = (
            f"I found {len(pressure)} high affordability pressure schemes and "
            f"{len(material)} schemes with cost movement of at least GBP 250,000."
        )
        insights = [
            f"High affordability pressure schemes total {_money(pressure['estimated_cost'].sum())}.",
            "Cost movement should be assessed alongside evidence strength, not in isolation.",
            "New urgent works can create pressure even when previous cost was zero, so they need a separate explanation.",
        ]
        sources = _source_rows("costs", pressure.sort_values("estimated_cost", ascending=False), "scheme_id", "scheme_name")
        sources += _source_rows("material_cost_changes", material.sort_values("cost_change", ascending=False), "scheme_id", "scheme_name")

    elif topic == "condition":
        asset_view = asset_needs.copy()
        if "asset_classes" in filters:
            asset_view = asset_view[asset_view["asset_class"].isin(filters["asset_classes"])]
        if "routes" in filters:
            asset_view = asset_view[asset_view["route"].isin(filters["routes"])]
        high_need = asset_view[
            asset_view["asset_need_band"].eq("High")
            | asset_view["condition_trend"].map(_normalise).isin(["deteriorating", "rapid deterioration"])
            | asset_view["confidence_level"].map(_normalise).eq("low")
        ].sort_values("asset_need_score", ascending=False)
        answer = (
            f"I found {len(high_need)} assets with high need, deterioration, or low confidence condition evidence."
        )
        insights = [
            "Low confidence evidence should create a data improvement action as well as an investment planning action.",
            "Rapid deterioration on high-criticality assets is the clearest signal for escalation.",
            "Old assets are not automatically high priority unless condition, trend or criticality supports that position.",
        ]
        sources = _source_rows("asset_need_scores", high_need, "asset_id", "location")

    elif topic == "change":
        change_view = schemes.merge(data["costs"], on="scheme_id", how="left")
        change_view = _apply_scheme_filters(change_view, filters, assets)
        current = change_view["current_status"].map(_normalise)
        previous = change_view["previous_plan_status"].map(_normalise)
        movement = change_view[
            current.isin(["new", "deferred", "removed"])
            | previous.isin(["new", "not in previous plan"])
            | pd.to_numeric(change_view["cost_change"], errors="coerce").fillna(0).abs().ge(250_000)
        ]
        answer = (
            f"I found {len(movement)} schemes with material movement, including "
            f"{current.eq('deferred').sum()} deferred and {current.eq('removed').sum()} removed schemes."
        )
        insights = [
            "Plan movement should be reviewed with both status change and cost movement visible.",
            "Deferred committed schemes need clear reasons because they can affect affordability and handback confidence.",
            "Removed schemes should keep a traceable challenge reason for audit.",
        ]
        sources = _source_rows("scheme_plan_movement", movement.sort_values("cost_change", ascending=False), "scheme_id", "scheme_name")

    elif topic == "risk":
        risk_view = data["risks"].copy()
        if "ids" in filters:
            ids = filters["ids"]
            risk_view = risk_view[
                risk_view["risk_id"].isin(ids)
                | risk_view["linked_asset_id"].isin(ids)
                | risk_view["linked_scheme_id"].isin(ids)
            ]
        high_risk = risk_view[pd.to_numeric(risk_view["risk_score"], errors="coerce").fillna(0).ge(12)]
        answer = f"I found {len(high_risk)} quantified risks with a score of 12 or above."
        insights = [
            "Risks without a quantified score should be challenged because they weaken prioritisation.",
            "Residual risk should be checked where the scheme is deferred or under review.",
            "High risk is most useful when linked to both an asset and a scheme.",
        ]
        sources = _source_rows("risks", high_risk.sort_values("risk_score", ascending=False), "risk_id", "risk_description")

    else:
        results = build_search_results(question, data)
        answer = (
            f"I searched the mock data lake and found {len(results)} potentially relevant source rows. "
            "The strongest matches are shown below."
        )
        insights = [
            "This is keyword and ID based retrieval in the prototype.",
            "The production version should use Azure AI Search for retrieval and Azure OpenAI for grounded answer generation.",
            "Every generated answer should cite source rows or approved documents.",
        ]
        sources = results

    if not sources:
        sources = build_search_results(question, data)

    return {
        "topic": topic,
        "answer": answer,
        "insights": insights,
        "sources": sources[:12],
    }
