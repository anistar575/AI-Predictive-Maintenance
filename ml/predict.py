import os
import joblib
import pandas as pd
import numpy as np
from typing import Union

TYPE_MAPPING = {
    "L": 0,
    "M": 1,
    "H": 2,
}


class PredictiveMaintenancePredictor:
    def __init__(self, model_filepath: str | None = None):
        """
        Load the trained model and preprocessing objects.
        """
        if model_filepath is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)

            model_filepath = os.path.join(
                project_root,
                "saved_models",
                "best_model.joblib",
            )

        if not os.path.exists(model_filepath):
            raise FileNotFoundError(
                f"Model file not found:\n{model_filepath}\n"
                "Please train the model first."
            )

        print(f"\nLoading model from:\n{model_filepath}")

        model_data = joblib.load(model_filepath)

        self.model = model_data["model"]
        self.scaler = model_data["scaler"]
        self.features = model_data["features"]
        self.model_name = model_data["model_name"]

        print(f"Loaded model: {self.model_name}")

    def preprocess_input(self, input_data: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare and validate input data before prediction.
        """
        df = input_data.copy()

        # Validate machine type
        if "Type" in df.columns and "Type_encoded" not in df.columns:
            invalid = df.loc[
                ~df["Type"].isin(TYPE_MAPPING.keys()),
                "Type",
            ]

            if not invalid.empty:
                raise ValueError(
                    f"Invalid machine type(s): {list(invalid)}. "
                    "Allowed values are: L, M, H."
                )

            df["Type_encoded"] = df["Type"].map(TYPE_MAPPING)

        if "Type_encoded" in df.columns:
            df["Type_encoded"] = (
                pd.to_numeric(df["Type_encoded"], errors="raise")
                .astype(int)
            )

        # Validate numeric features and check ranges
        range_checks = {
            "Air temperature [K]": (200.0, 400.0),
            "Process temperature [K]": (200.0, 400.0),
            "Rotational speed [rpm]": (0.0, 10000.0),
            "Torque [Nm]": (0.0, 500.0),
            "Tool wear [min]": (0.0, 1000.0),
        }

        for feature, (min_val, max_val) in range_checks.items():
            if feature not in df.columns:
                # If named differently in dictionary (e.g. lowercase without brackets)
                # app/routes.py maps them directly using proper names, so they should be present.
                raise ValueError(f"Missing required parameter: {feature}")

            try:
                df[feature] = pd.to_numeric(df[feature], errors="raise").astype(float)
            except Exception:
                raise ValueError(f"'{feature}' must contain numeric values.")

            # Validate boundaries
            val = df[feature].iloc[0]
            if not (min_val <= val <= max_val):
                raise ValueError(
                    f"Value for '{feature}' ({val}) is out of operational limits "
                    f"[{min_val}, {max_val}]."
                )

        # Create engineered features (identical to preprocessing during training)
        df["Temp_diff"] = df["Process temperature [K]"] - df["Air temperature [K]"]
        df["Power_Watts"] = df["Torque [Nm]"] * df["Rotational speed [rpm]"] * 2 * np.pi / 60
        df["Overstrain_factor"] = df["Tool wear [min]"] * df["Torque [Nm]"]
        df["HDF_indicator"] = ((df["Temp_diff"] < 8.6) & (df["Rotational speed [rpm]"] < 1380)).astype(int)
        df["PWF_indicator"] = ((df["Power_Watts"] < 3500) | (df["Power_Watts"] > 9000)).astype(int)

        # Check required features for model
        missing = [
            feature
            for feature in self.features
            if feature not in df.columns
        ]

        if missing:
            raise ValueError(
                f"Missing required features for model: {missing}"
            )

        X = df[self.features]

        if self.scaler is not None:
            X = pd.DataFrame(
                self.scaler.transform(X),
                columns=self.features,
                index=df.index,
            )

        return X

    @staticmethod
    def get_health_status(failure_probability: float) -> str:
        """
        Convert failure probability into industrial health levels.
        """
        if failure_probability <= 0.30:
            return "🟢 Healthy"
        elif failure_probability <= 0.70:
            return "🟡 Warning"
        
        return "🔴 Critical"

    @staticmethod
    def get_risk_level(failure_probability: float) -> str:
        """
        Convert failure probability into a risk level string.
        """
        if failure_probability <= 0.30:
            return "Low"
        elif failure_probability <= 0.70:
            return "Medium"
        
        return "High"

    def predict(
        self,
        input_data: Union[dict, list, pd.DataFrame],
    ) -> dict:
        if isinstance(input_data, dict):
            df = pd.DataFrame([input_data])
        elif isinstance(input_data, list):
            df = pd.DataFrame(input_data)
        elif isinstance(input_data, pd.DataFrame):
            df = input_data.copy()
        else:
            raise TypeError(
                "Input must be a DataFrame, dict or list of dictionaries."
            )

        X = self.preprocess_input(df)

        predictions = self.model.predict(X)
        probabilities = self.model.predict_proba(X)

        results = []

        for prediction, probability in zip(
            predictions,
            probabilities,
        ):
            healthy_probability = float(probability[0])
            failure_probability = float(probability[1])

            confidence = max(
                healthy_probability,
                failure_probability,
            )

            results.append(
                {
                    "Prediction": int(prediction),
                    "Prediction Label": "Failure" if prediction == 1 else "Healthy",
                    "Health Status": self.get_health_status(failure_probability),
                    "Risk Level": self.get_risk_level(failure_probability),
                    "Healthy Probability": round(healthy_probability, 4),
                    "Failure Probability": round(failure_probability, 4),
                    "Confidence": f"{confidence*100:.2f}%"
                }
            )

        return {
            "Model Used": self.model_name,
            "Results": results,
        }


def main():
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    predictor = PredictiveMaintenancePredictor()

    samples = [
        {
            "Type": "M",
            "Air temperature [K]": 298.1,
            "Process temperature [K]": 308.6,
            "Rotational speed [rpm]": 1551,
            "Torque [Nm]": 42.8,
            "Tool wear [min]": 0,
        },
        {
            "Type": "L",
            "Air temperature [K]": 302.5,
            "Process temperature [K]": 311.0,
            "Rotational speed [rpm]": 1200,
            "Torque [Nm]": 75.0,
            "Tool wear [min]": 210,
        },
    ]

    output = predictor.predict(samples)

    print("\n" + "=" * 50)
    print("PREDICTION RESULTS")
    print("=" * 50)
    print(f"\nModel Used: {output['Model Used']}")
    
    for i, result in enumerate(output["Results"], start=1):
        print(f"\nSample {i}")
        print("-" * 35)
        print(
            f"Prediction           : "
            f"{'Failure' if result['Prediction'] else 'Healthy'}"
        )
        print(
            f"Health Status        : {result['Health Status']}"
        )
        print(
            f"Risk Level           : {result['Risk Level']}"
        )
        print(
            f"Healthy Probability  : "
            f"{result['Healthy Probability']:.2%}"
        )
        print(
            f"Failure Probability  : "
            f"{result['Failure Probability']:.2%}"
        )
        print(
            f"Confidence           : {result['Confidence']}"
        )


if __name__ == "__main__":
    main()
