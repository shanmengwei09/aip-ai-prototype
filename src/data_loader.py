"""Data loading and validation for the AIP AI prototype."""

from pathlib import Path

import pandas as pd

from src.validation import REQUIRED_COLUMNS, validate_dataset


DATASET_FILES = {
    "assets": "assets.csv",
    "condition": "condition.csv",
    "schemes": "schemes.csv",
    "risks": "risks.csv",
    "delivery": "delivery.csv",
    "costs": "costs.csv",
    "handback": "handback.csv",
}

NUMERIC_COLUMNS = {
    "assets": ["chainage_start", "chainage_end", "asset_age"],
    "condition": ["condition_score"],
    "schemes": ["proposed_year", "previous_proposed_year", "estimated_cost"],
    "risks": ["likelihood", "impact", "risk_score"],
    "costs": ["previous_cost", "current_cost", "cost_change"],
}


def _coerce_numeric_columns(dataframe, dataset_name):
    """Convert known numeric columns and keep invalid values as blank."""
    for column in NUMERIC_COLUMNS.get(dataset_name, []):
        if column in dataframe.columns:
            dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")
    return dataframe


def load_dataset(data_dir, dataset_name):
    """Load one CSV file and return dataframe plus validation errors."""
    file_name = DATASET_FILES[dataset_name]
    path = Path(data_dir) / file_name

    if not path.exists():
        return pd.DataFrame(columns=REQUIRED_COLUMNS[dataset_name]), [
            f"Missing file: {path}"
        ]

    try:
        dataframe = pd.read_csv(path)
    except Exception as exc:
        return pd.DataFrame(columns=REQUIRED_COLUMNS[dataset_name]), [
            f"Could not read {path}: {exc}"
        ]

    errors = validate_dataset(dataframe, dataset_name)
    dataframe = _coerce_numeric_columns(dataframe, dataset_name)
    return dataframe, errors


def load_all_data(data_dir):
    """Load all prototype datasets from a folder."""
    data = {}
    errors = []

    for dataset_name in DATASET_FILES:
        dataframe, dataset_errors = load_dataset(data_dir, dataset_name)
        data[dataset_name] = dataframe
        errors.extend(dataset_errors)

    return data, errors
