from flask import Blueprint, render_template, request, jsonify

from ml.predict import PredictiveMaintenancePredictor

main = Blueprint("main", __name__)

predictor = PredictiveMaintenancePredictor()


@main.route("/")
def home():
    return render_template("index.html")


@main.route("/predict", methods=["POST"])
def predict():
    try:
        data = {
            "Type": request.form["Type"],
            "Air temperature [K]": float(request.form["air_temperature"]),
            "Process temperature [K]": float(request.form["process_temperature"]),
            "Rotational speed [rpm]": float(request.form["rotational_speed"]),
            "Torque [Nm]": float(request.form["torque"]),
            "Tool wear [min]": float(request.form["tool_wear"]),
        }

        result = predictor.predict(data)

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 400