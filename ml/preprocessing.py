"""
Preprocessing module for AI Predictive Maintenance.
Handles dataset loading, categorical encoding, stratified train/test split,
and feature scaling.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


def load_data(filepath: str) -> pd.DataFrame:
    """
    Loads raw CSV data from the specified filepath.

    Args:
        filepath (str): Path to the CSV file.

    Returns:
        pd.DataFrame: Loaded dataset.
    """
    return pd.read_csv(filepath)


def preprocess_data(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """
    Preprocesses the raw dataset:
    - Encodes the categorical 'Type' feature to numerical values.
    - Selects the core features relevant for predictive maintenance.
    - Returns features (X) and target (y).

    Args:
        df (pd.DataFrame): Raw dataset.

    Returns:
        tuple[pd.DataFrame, pd.Series]: Features (X) and target series (y).
    """
    df_clean = df.copy()

    # Map Type: L -> 0, M -> 1, H -> 2
    df_clean["Type_encoded"] = df_clean["Type"].map(
        {"L": 0, "M": 1, "H": 2}
    )

    # Engineered features
    df_clean["Temp_diff"] = df_clean["Process temperature [K]"] - df_clean["Air temperature [K]"]
    df_clean["Power_Watts"] = df_clean["Torque [Nm]"] * df_clean["Rotational speed [rpm]"] * 2 * np.pi / 60
    df_clean["Overstrain_factor"] = df_clean["Tool wear [min]"] * df_clean["Torque [Nm]"]
    df_clean["HDF_indicator"] = ((df_clean["Temp_diff"] < 8.6) & (df_clean["Rotational speed [rpm]"] < 1380)).astype(int)
    df_clean["PWF_indicator"] = ((df_clean["Power_Watts"] < 3500) | (df_clean["Power_Watts"] > 9000)).astype(int)

    features = [
        "Type_encoded",
        "Air temperature [K]",
        "Process temperature [K]",
        "Rotational speed [rpm]",
        "Torque [Nm]",
        "Tool wear [min]",
        "Temp_diff",
        "Power_Watts",
        "Overstrain_factor",
        "HDF_indicator",
        "PWF_indicator",
    ]

    target = "Machine failure"

    X = df_clean[features]
    y = df_clean[target]

    return X, y


def split_data(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: float = 0.2,
    random_state: int = 123,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Splits features and target into train and test sets using stratification.

    Args:
        X (pd.DataFrame): Features.
        y (pd.Series): Target.
        test_size (float): Test set proportion.
        random_state (int): Random seed.

    Returns:
        tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
            X_train, X_test, y_train, y_test
    """

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )

    return X_train, X_test, y_train, y_test


def scale_features(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, StandardScaler]:
    """
    Fits a StandardScaler on training data and transforms both training
    and testing feature sets.

    Args:
        X_train (pd.DataFrame): Training features.
        X_test (pd.DataFrame): Testing features.

    Returns:
        tuple[pd.DataFrame, pd.DataFrame, StandardScaler]:
            X_train_scaled, X_test_scaled, scaler
    """

    scaler = StandardScaler()

    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    X_train_scaled_df = pd.DataFrame(
        X_train_scaled,
        columns=X_train.columns,
        index=X_train.index,
    )

    X_test_scaled_df = pd.DataFrame(
        X_test_scaled,
        columns=X_test.columns,
        index=X_test.index,
    )

    return X_train_scaled_df, X_test_scaled_df, scaler
