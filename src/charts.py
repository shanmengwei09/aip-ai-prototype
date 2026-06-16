"""Small chart helpers used by the Streamlit dashboard."""

import plotly.express as px


CHART_TEMPLATE = "plotly_white"
COLOUR_SEQUENCE = ["#1F77B4", "#2CA02C", "#FF7F0E", "#9467BD", "#D62728", "#17BECF"]


def currency(value):
    """Format values as GBP millions for dashboard metrics."""
    try:
        return f"GBP {value / 1_000_000:.1f}m"
    except TypeError:
        return "GBP 0.0m"


def bar_chart(dataframe, x, y, title, colour=None):
    fig = px.bar(
        dataframe,
        x=x,
        y=y,
        color=colour,
        title=title,
        template=CHART_TEMPLATE,
        color_discrete_sequence=COLOUR_SEQUENCE,
    )
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=10))
    return fig


def line_chart(dataframe, x, y, title, colour=None):
    fig = px.line(
        dataframe,
        x=x,
        y=y,
        color=colour,
        markers=True,
        title=title,
        template=CHART_TEMPLATE,
        color_discrete_sequence=COLOUR_SEQUENCE,
    )
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=10))
    return fig


def pie_chart(dataframe, names, values, title):
    fig = px.pie(
        dataframe,
        names=names,
        values=values,
        title=title,
        template=CHART_TEMPLATE,
        color_discrete_sequence=COLOUR_SEQUENCE,
    )
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=10))
    return fig
