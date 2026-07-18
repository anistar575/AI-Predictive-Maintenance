from flask import redirect
from database.database import (
    add_machine,
    get_all_machines
)
from database.database import (
    save_prediction,
    get_all_predictions,
    get_dashboard_stats
)
from flask import Blueprint, render_template, request, jsonify

from ml.predict import PredictiveMaintenancePredictor

main = Blueprint("main", __name__)

predictor = PredictiveMaintenancePredictor()


@main.route("/")
def home():

    stats = get_dashboard_stats()
    predictions = get_all_predictions()

    return render_template(
        "index.html",
        stats=stats,
        predictions=predictions[:5]
    )


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

        prediction = predictor.predict(data)

        result = prediction["Results"][0]

        save_prediction(
            machine_type=data["Type"],
            air_temperature=float(data["Air temperature [K]"]),
            process_temperature=float(data["Process temperature [K]"]),
            rotational_speed=int(data["Rotational speed [rpm]"]),
            torque=float(data["Torque [Nm]"]),
            tool_wear=int(data["Tool wear [min]"]),
            prediction="Failure" if result["Prediction"] == 1 else "Healthy",
            health_status=result["Health Status"],
            failure_probability=result["Failure Probability"],
            confidence=result["Confidence"],
            model_used=prediction["Model Used"],
        )

        return jsonify(prediction)

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@main.route("/history")
def history():

    predictions = get_all_predictions()

    return render_template(
        "history.html",
        predictions=predictions
    )
@main.route("/machines")
def machines():

    machines = get_all_machines()

    return render_template(
        "machines.html",
        machines=machines
    )
@main.route("/add-machine", methods=["POST"])
def add_machine_route():

    add_machine(

        machine_code=request.form["machine_code"],

        machine_name=request.form["machine_name"],

        machine_type=request.form["machine_type"],

        department=request.form["department"],

        location=request.form["location"],

        installation_date=request.form["installation_date"]

    )

    return redirect("/machines")