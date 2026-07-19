
import traceback
from flask import redirect
from database.database import (
    save_prediction,
    get_all_predictions,
    add_machine,
    get_all_machines,
    delete_machine,
    get_machine,
    update_machine_status,
    get_dashboard_stats,
    get_machine_by_id,
    update_machine,
    get_predictions_by_machine,
    get_predictions_with_machine_details,
    get_all_departments
)
from flask import Blueprint, render_template, request, jsonify

from ml.predict import PredictiveMaintenancePredictor

main = Blueprint("main", __name__)

predictor = PredictiveMaintenancePredictor()


@main.route("/")
def home():

    stats = get_dashboard_stats()
    predictions = get_all_predictions()
    machines = get_all_machines()

    return render_template(
        "index.html",
        stats=stats,
        predictions=predictions[:5],
        machines=machines
    )


@main.route("/predict", methods=["POST"])
def predict():
    try:

        machine = get_machine(request.form["machine_code"])
        print("Selected Machine:", repr(machine).encode('ascii', 'backslashreplace').decode('ascii'))

        data = {
            "Type": machine[3],   # Machine Type (H/M/L)

            "Air temperature [K]": float(request.form["air_temperature"]),

            "Process temperature [K]": float(request.form["process_temperature"]),

            "Rotational speed [rpm]": float(request.form["rotational_speed"]),

            "Torque [Nm]": float(request.form["torque"]),

            "Tool wear [min]": float(request.form["tool_wear"]),
        }

        prediction = predictor.predict(data)

        result = prediction["Results"][0]

        save_prediction(
            machine_code=request.form["machine_code"],
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
        update_machine_status(
    request.form["machine_code"],
    result["Health Status"])

        return jsonify(prediction)

        

    except Exception as e:
        traceback.print_exc()
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
@main.route("/delete-machine/<int:id>")
def delete_machine_route(id):

    delete_machine(id)

    return redirect("/machines")


@main.route("/edit-machine/<int:id>", methods=["GET", "POST"])
def edit_machine_route(id):
    machine = get_machine_by_id(id)
    if not machine:
        return "Machine not found", 404

    if request.method == "POST":
        machine_code = request.form["machine_code"]
        machine_name = request.form["machine_name"]
        machine_type = request.form["machine_type"]
        department = request.form["department"]
        location = request.form["location"]
        installation_date = request.form["installation_date"]

        success = update_machine(
            machine_id=id,
            machine_code=machine_code,
            machine_name=machine_name,
            machine_type=machine_type,
            department=department,
            location=location,
            installation_date=installation_date
        )
        if success:
            return redirect("/machines")
        else:
            return render_template(
                "edit_machine.html",
                machine=machine,
                error="Error: Machine Code must be unique. Another machine may already use this code."
            )

    return render_template("edit_machine.html", machine=machine)


@main.route("/machine/<string:machine_code>")
def machine_details_route(machine_code):
    machine = get_machine(machine_code)
    if not machine:
        return "Machine not found", 404

    predictions = get_predictions_by_machine(machine_code)
    latest_prediction = predictions[0] if predictions else None


    return render_template(
        "machine_details.html",
        machine=machine,
        predictions=predictions,
        latest_prediction=latest_prediction
    )


@main.route("/analytics")
def analytics_route():
    import json
    predictions = get_predictions_with_machine_details()
    machines = get_all_machines()
    departments = get_all_departments()

    # Let's fix the serialization to use the correct indices!
    serialized_predictions = []
    for row in predictions:
        serialized_predictions.append({
            "id": row[0],
            "machine_code": row[1],
            "machine_type": row[2],
            "air_temp": row[3],
            "process_temp": row[4],
            "rotational_speed": row[5],
            "torque": row[6],
            "tool_wear": row[7],
            "prediction": row[8],
            "health_status": row[9],
            "failure_probability": row[10],
            "confidence": row[11],
            "model_used": row[12],
            "prediction_time": row[13],
            "machine_name": row[14] if row[14] else "Unknown",
            "department": row[15] if row[15] else "Unassigned",
            "location": row[16] if row[16] else "Unknown"
        })

    predictions_json = json.dumps(serialized_predictions)

    return render_template(
        "analytics.html",
        predictions_json=predictions_json,
        machines=machines,
        departments=departments
    )