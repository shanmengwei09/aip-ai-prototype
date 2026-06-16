from pathlib import Path

import pandas as pd
import streamlit as st

from src.charts import bar_chart, currency, pie_chart
from src.data_loader import load_all_data
from src.llm_answer import generate_grounded_answer
from src.qa_engine import answer_question
from src.scoring import (
    score_asset_need,
    score_challenge,
    score_deliverability,
    score_scheme_priority,
)


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = BASE_DIR / "data" / "sample"


@st.cache_data
def load_dashboard_data(data_dir):
    return load_all_data(data_dir)


def filter_by_sidebar(schemes):
    asset_classes = sorted(schemes["asset_class"].dropna().unique())
    years = sorted(int(year) for year in schemes["proposed_year"].dropna().unique())

    selected_classes = st.sidebar.multiselect("Asset classes", asset_classes, default=asset_classes)
    selected_years = st.sidebar.multiselect("Proposed years", years, default=years)

    filtered = schemes[
        schemes["asset_class"].isin(selected_classes)
        & schemes["proposed_year"].isin(selected_years)
    ]
    return filtered, selected_classes


def display_table(dataframe, columns, height=360):
    existing_columns = [column for column in columns if column in dataframe.columns]
    st.dataframe(dataframe[existing_columns], use_container_width=True, height=height)


def set_example_question(question):
    st.session_state["aip_question"] = question


def get_openai_settings():
    try:
        api_key = st.secrets.get("OPENAI_API_KEY")
        model = st.secrets.get("OPENAI_MODEL", "gpt-5.5")
    except Exception:
        api_key = None
        model = "gpt-5.5"
    return api_key, model


def ask_aip_data_view(data, asset_needs, scheme_priority, challenge, delivery_scored):
    st.subheader("Ask AIP Data")
    st.caption("Prototype question answering over the mock AIP data lake. Answers cite the source rows used.")

    examples = [
        "Which schemes have weak evidence and high cost?",
        "What is critical for handback in 2027?",
        "Which schemes are at risk of carryover?",
        "Where are the affordability pressures?",
    ]

    example_cols = st.columns(len(examples))
    for index, example in enumerate(examples):
        example_cols[index].button(
            example,
            use_container_width=True,
            on_click=set_example_question,
            args=(example,),
        )

    question = st.text_area(
        "Question",
        key="aip_question",
        height=90,
        placeholder="Ask about schemes, assets, handback, evidence, delivery, cost, change or risk.",
    )

    answer = answer_question(question, data, asset_needs, scheme_priority, challenge, delivery_scored)
    api_key, model = get_openai_settings()
    llm_answer = None
    if api_key and question:
        with st.spinner("Generating grounded AI answer from cited source rows..."):
            llm_answer = generate_grounded_answer(
                question=question,
                draft_answer=answer["answer"],
                insights=answer["insights"],
                sources=answer["sources"],
                api_key=api_key,
                model=model,
            )

    displayed_answer = llm_answer if llm_answer else answer

    if api_key:
        if llm_answer and "error" not in llm_answer:
            st.success(f"OpenAI grounded answer mode is active using {llm_answer.get('model', model)}.")
        elif llm_answer and "error" in llm_answer:
            st.warning(llm_answer["error"])
        else:
            st.info("OpenAI answer mode is configured. Ask a question to use it.")
    else:
        st.info("Local prototype mode is active. Add OPENAI_API_KEY in Streamlit secrets to enable smarter grounded answers.")

    st.markdown("**Answer**")
    st.info(displayed_answer["answer"])

    insight_cols = st.columns(3)
    for index, insight in enumerate(displayed_answer["insights"][:3]):
        with insight_cols[index]:
            st.markdown(f"**Insight {index + 1}**")
            st.write(insight)

    sources = pd.DataFrame(answer["sources"])
    st.markdown("**Cited source rows**")
    if sources.empty:
        st.warning("No matching source rows were found in the loaded data.")
    else:
        st.dataframe(sources, use_container_width=True, height=320)

    with st.expander("How this prototype answers questions"):
        st.write(
            "The current version uses local CSV files as a mock data lake, searches across the loaded datasets, "
            "applies transparent scoring rules, and returns cited source rows. A production version should replace "
            "this local logic with Azure AI Search for retrieval and Azure OpenAI for grounded answer generation."
        )


def portfolio_overview(schemes, costs):
    st.subheader("Portfolio Overview")

    total_investment = schemes["estimated_cost"].sum()
    committed = schemes[schemes["current_status"].str.lower().eq("committed")]
    uncommitted = schemes[~schemes["current_status"].str.lower().eq("committed")]

    metric_cols = st.columns(4)
    metric_cols[0].metric("Total investment", currency(total_investment))
    metric_cols[1].metric("Schemes", f"{len(schemes):,}")
    metric_cols[2].metric("Committed", f"{len(committed):,}")
    metric_cols[3].metric("Uncommitted", f"{len(uncommitted):,}")

    investment_by_class = (
        schemes.groupby("asset_class", as_index=False)["estimated_cost"]
        .sum()
        .sort_values("estimated_cost", ascending=False)
    )
    investment_by_year = (
        schemes.groupby("proposed_year", as_index=False)["estimated_cost"]
        .sum()
        .sort_values("proposed_year")
    )

    chart_cols = st.columns(2)
    chart_cols[0].plotly_chart(
        bar_chart(investment_by_class, "asset_class", "estimated_cost", "Investment by asset class"),
        use_container_width=True,
    )
    chart_cols[1].plotly_chart(
        bar_chart(investment_by_year, "proposed_year", "estimated_cost", "Investment by proposed year"),
        use_container_width=True,
    )

    status_summary = schemes.assign(
        commitment=schemes["current_status"].where(
            schemes["current_status"].str.lower().eq("committed"),
            "Uncommitted",
        )
    )
    status_summary = status_summary.groupby("commitment", as_index=False)["scheme_id"].count()
    status_summary = status_summary.rename(columns={"scheme_id": "scheme_count"})

    pressure = schemes.merge(costs, on="scheme_id", how="left")
    pressure = pressure.sort_values(["affordability_pressure", "estimated_cost"], ascending=[True, False])
    high_pressure = pressure[pressure["affordability_pressure"].str.lower().eq("high")]

    chart_cols = st.columns(2)
    chart_cols[0].plotly_chart(
        pie_chart(status_summary, "commitment", "scheme_count", "Committed vs uncommitted"),
        use_container_width=True,
    )
    with chart_cols[1]:
        st.markdown("**Top affordability pressures**")
        display_table(
            high_pressure,
            ["scheme_id", "scheme_name", "asset_class", "estimated_cost", "cost_change", "cost_change_reason"],
            height=260,
        )


def asset_need_view(asset_needs, selected_classes):
    st.subheader("Asset Need View")
    filtered = asset_needs[asset_needs["asset_class"].isin(selected_classes)]

    condition_summary = (
        filtered.groupby("asset_class", as_index=False)["condition_score"]
        .mean()
        .sort_values("condition_score")
    )
    age_summary = (
        filtered.groupby("asset_class", as_index=False)["asset_age"]
        .mean()
        .sort_values("asset_age", ascending=False)
    )
    trend_summary = filtered.groupby("condition_trend", as_index=False)["asset_id"].count()
    trend_summary = trend_summary.rename(columns={"asset_id": "asset_count"})

    chart_cols = st.columns(3)
    chart_cols[0].plotly_chart(
        bar_chart(condition_summary, "asset_class", "condition_score", "Average condition score"),
        use_container_width=True,
    )
    chart_cols[1].plotly_chart(
        bar_chart(age_summary, "asset_class", "asset_age", "Average asset age"),
        use_container_width=True,
    )
    chart_cols[2].plotly_chart(
        bar_chart(trend_summary, "condition_trend", "asset_count", "Condition trend"),
        use_container_width=True,
    )

    table_cols = st.columns(2)
    with table_cols[0]:
        st.markdown("**High-criticality and high-need assets**")
        high_need = filtered[
            filtered["criticality"].str.lower().eq("high")
            | filtered["asset_need_band"].eq("High")
        ].sort_values("asset_need_score", ascending=False)
        display_table(
            high_need,
            ["asset_id", "asset_class", "route", "location", "criticality", "condition_score", "asset_need_score", "asset_need_band"],
        )

    with table_cols[1]:
        st.markdown("**Low confidence condition data**")
        low_confidence = filtered[filtered["confidence_level"].str.lower().eq("low")]
        display_table(
            low_confidence,
            ["asset_id", "asset_class", "route", "location", "condition_score", "evidence_source", "confidence_level"],
        )


def scheme_challenge_view(challenge, scheme_priority):
    st.subheader("Scheme Challenge View")
    challenge = challenge.merge(
        scheme_priority[["scheme_id", "scheme_priority_score", "scheme_priority_band"]],
        on="scheme_id",
        how="left",
    )

    metric_cols = st.columns(4)
    metric_cols[0].metric("High challenge", f"{len(challenge[challenge['challenge_band'].eq('High')]):,}")
    metric_cols[1].metric("Weak evidence", f"{challenge['flag_weak_evidence'].sum():,}")
    metric_cols[2].metric("High cost and low evidence", f"{challenge['flag_high_cost_low_evidence'].sum():,}")
    metric_cols[3].metric("Unclear handback", f"{challenge['flag_unclear_handback'].sum():,}")

    chart_data = challenge.groupby("challenge_band", as_index=False)["scheme_id"].count()
    chart_data = chart_data.rename(columns={"scheme_id": "scheme_count"})
    st.plotly_chart(
        bar_chart(chart_data, "challenge_band", "scheme_count", "Challenge bands"),
        use_container_width=True,
    )

    st.markdown("**Schemes requiring further challenge before approval**")
    display_table(
        challenge.sort_values(["challenge_score", "estimated_cost"], ascending=[False, False]),
        [
            "scheme_id",
            "scheme_name",
            "asset_class",
            "estimated_cost",
            "evidence_strength",
            "delivery_confidence",
            "challenge_score",
            "challenge_band",
            "challenge_reasons",
        ],
        height=430,
    )


def handback_view(assets, schemes, handback):
    st.subheader("Handback View")
    handback_assets = handback.merge(assets, on="asset_id", how="left")
    handback_schemes = schemes[schemes["handback_link"].str.lower().isin(["yes", "partial", "unclear"])]

    metric_cols = st.columns(4)
    metric_cols[0].metric("Handback assets", f"{len(handback_assets):,}")
    metric_cols[1].metric("High handback risk", f"{len(handback_assets[handback_assets['handback_risk_level'].str.lower().eq('high')]):,}")
    metric_cols[2].metric("Linked schemes", f"{len(handback_schemes):,}")
    metric_cols[3].metric("Critical schemes", f"{len(handback_schemes[handback_schemes['handback_link'].str.lower().eq('yes')]):,}")

    risk_summary = handback_assets.groupby("handback_risk_level", as_index=False)["asset_id"].count()
    risk_summary = risk_summary.rename(columns={"asset_id": "asset_count"})
    st.plotly_chart(
        bar_chart(risk_summary, "handback_risk_level", "asset_count", "Handback risk level"),
        use_container_width=True,
    )

    table_cols = st.columns(2)
    with table_cols[0]:
        st.markdown("**Handback gaps and consequences**")
        display_table(
            handback_assets.sort_values("handback_risk_level"),
            [
                "asset_id",
                "asset_class",
                "route",
                "current_gap",
                "handback_risk_level",
                "consequence_if_deferred",
            ],
            height=420,
        )
    with table_cols[1]:
        st.markdown("**Schemes linked to handback**")
        display_table(
            handback_schemes.sort_values(["handback_link", "estimated_cost"], ascending=[True, False]),
            ["scheme_id", "scheme_name", "linked_asset_id", "asset_class", "estimated_cost", "handback_link", "current_status"],
            height=420,
        )


def deliverability_view(schemes, delivery_scored):
    st.subheader("Deliverability View")
    deliverability = schemes.merge(delivery_scored, on="scheme_id", how="left")

    metric_cols = st.columns(4)
    metric_cols[0].metric("High carryover risk", f"{len(deliverability[deliverability['carryover_risk'].str.lower().eq('high')]):,}")
    metric_cols[1].metric("Low confidence", f"{len(deliverability[deliverability['delivery_confidence'].str.lower().eq('low')]):,}")
    metric_cols[2].metric("High access constraint", f"{len(deliverability[deliverability['access_constraint'].str.lower().eq('high')]):,}")
    metric_cols[3].metric("High delivery risk", f"{len(deliverability[deliverability['deliverability_risk_band'].eq('High')]):,}")

    chart_cols = st.columns(2)
    carryover = deliverability.groupby("carryover_risk", as_index=False)["scheme_id"].count().rename(columns={"scheme_id": "scheme_count"})
    delivery_band = deliverability.groupby("deliverability_risk_band", as_index=False)["scheme_id"].count().rename(columns={"scheme_id": "scheme_count"})
    chart_cols[0].plotly_chart(bar_chart(carryover, "carryover_risk", "scheme_count", "Carryover risk"), use_container_width=True)
    chart_cols[1].plotly_chart(bar_chart(delivery_band, "deliverability_risk_band", "scheme_count", "Deliverability risk band"), use_container_width=True)

    st.markdown("**Key delivery constraints**")
    display_table(
        deliverability.sort_values("deliverability_risk_score", ascending=False),
        [
            "scheme_id",
            "scheme_name",
            "proposed_year",
            "design_status",
            "commercial_status",
            "access_constraint",
            "delivery_confidence",
            "carryover_risk",
            "deliverability_risk_score",
            "key_constraint",
        ],
        height=430,
    )


def change_view(schemes, costs):
    st.subheader("Change View")
    changes = schemes.merge(costs, on="scheme_id", how="left")
    previous_status = changes["previous_plan_status"].str.lower()
    current_status = changes["current_status"].str.lower()

    new_schemes = changes[previous_status.isin(["new", "not in previous plan"]) | current_status.eq("new")]
    deferred_schemes = changes[current_status.eq("deferred")]
    removed_schemes = changes[current_status.eq("removed")]
    previous_cost = pd.to_numeric(changes["previous_cost"], errors="coerce")
    current_cost = pd.to_numeric(changes["current_cost"], errors="coerce")
    safe_previous_cost = previous_cost.mask(previous_cost == 0)
    cost_change_percentage = ((current_cost - previous_cost) / safe_previous_cost).fillna(0)
    material_cost = changes[
        (pd.to_numeric(changes["cost_change"], errors="coerce").fillna(0).abs() >= 250_000)
        | cost_change_percentage.abs().ge(0.2)
    ]

    metric_cols = st.columns(4)
    metric_cols[0].metric("New schemes", f"{len(new_schemes):,}")
    metric_cols[1].metric("Deferred schemes", f"{len(deferred_schemes):,}")
    metric_cols[2].metric("Removed schemes", f"{len(removed_schemes):,}")
    metric_cols[3].metric("Material cost changes", f"{len(material_cost):,}")

    status_movement = (
        changes.groupby(["previous_plan_status", "current_status"], as_index=False)["scheme_id"]
        .count()
        .rename(columns={"scheme_id": "scheme_count"})
    )
    st.plotly_chart(
        bar_chart(status_movement, "previous_plan_status", "scheme_count", "Movement from previous plan", "current_status"),
        use_container_width=True,
    )

    st.markdown("**Movement and material changes**")
    display_table(
        changes.sort_values(["current_status", "cost_change"], ascending=[True, False]),
        [
            "scheme_id",
            "scheme_name",
            "previous_plan_status",
            "current_status",
            "previous_proposed_year",
            "proposed_year",
            "previous_cost",
            "current_cost",
            "cost_change",
            "cost_change_reason",
            "change_reason",
        ],
        height=430,
    )


def main():
    st.set_page_config(
        page_title="AIP AI Prototype",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.title("AI in Asset Investment Planning Prototype")
    st.caption("Mock AMFP / AAMP / 5AMP dashboard using CSV inputs and transparent scoring.")

    st.sidebar.header("Data")
    data_dir = Path(st.sidebar.text_input("CSV data folder", str(DEFAULT_DATA_DIR)))
    data, errors = load_dashboard_data(str(data_dir))

    if errors:
        st.error("Some required data could not be loaded.")
        for error in errors:
            st.write(f"- {error}")
        st.stop()

    schemes, selected_classes = filter_by_sidebar(data["schemes"])
    selected_scheme_ids = set(schemes["scheme_id"])

    assets = data["assets"]
    condition = data["condition"]
    costs = data["costs"][data["costs"]["scheme_id"].isin(selected_scheme_ids)]
    risks = data["risks"][data["risks"]["linked_scheme_id"].isin(selected_scheme_ids)]
    delivery = data["delivery"][data["delivery"]["scheme_id"].isin(selected_scheme_ids)]
    handback = data["handback"]

    asset_needs = score_asset_need(assets, condition)
    scheme_priority = score_scheme_priority(schemes, risks)
    challenge = score_challenge(schemes, delivery, costs, risks, condition)
    delivery_scored = score_deliverability(delivery)

    tabs = st.tabs(
        [
            "Ask AIP Data",
            "Portfolio Overview",
            "Asset Need",
            "Scheme Challenge",
            "Handback",
            "Deliverability",
            "Change",
        ]
    )

    with tabs[0]:
        ask_aip_data_view(data, asset_needs, scheme_priority, challenge, delivery_scored)
    with tabs[1]:
        portfolio_overview(schemes, costs)
    with tabs[2]:
        asset_need_view(asset_needs, selected_classes)
    with tabs[3]:
        scheme_challenge_view(challenge, scheme_priority)
    with tabs[4]:
        handback_view(assets, schemes, handback)
    with tabs[5]:
        deliverability_view(schemes, delivery_scored)
    with tabs[6]:
        change_view(schemes, costs)


if __name__ == "__main__":
    main()
