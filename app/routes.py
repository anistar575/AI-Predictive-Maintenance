
import traceback
from functools import wraps
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, abort, g
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
    get_all_departments,
    add_maintenance_schedule,
    get_maintenance_schedules,
    complete_maintenance_schedule,
    delete_maintenance_schedule,
    get_user_by_username
)

from ml.predict import PredictiveMaintenancePredictor

main = Blueprint("main", __name__)

predictor = PredictiveMaintenancePredictor()


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("role") != "Admin":
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


@main.before_request
def check_login():
    if request.endpoint == "main.login_route" or (request.path and request.path.startswith("/static")):
        return
    if "user_id" not in session:
        return redirect(url_for("main.login_route"))


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
@admin_required
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
@admin_required
def delete_machine_route(id):

    delete_machine(id)

    return redirect("/machines")


@main.route("/edit-machine/<int:id>", methods=["GET", "POST"])
@admin_required
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

    # Generate rule-based maintenance recommendation
    recommendation = {
        "status": "info",
        "title": "No Telemetry Data Available",
        "action": "Run equipment diagnostics from the dashboard to collect telemetry data."
    }

    if latest_prediction:
        failure_prob = latest_prediction[9]
        tool_wear = latest_prediction[6]
        torque = latest_prediction[5]
        air_temp = latest_prediction[2]
        proc_temp = latest_prediction[3]
        temp_diff = proc_temp - air_temp

        if failure_prob > 0.70:
            recommendation = {
                "status": "critical",
                "title": "URGENT INSPECTION REQUIRED",
                "action": "The ML model predicts a critical failure risk. Immediately halt machine operation. Inspect tool cutters for wear/breakage, examine mechanical bearings, and check electrical load parameters for torque spikes."
            }
        elif failure_prob > 0.30:
            recommendation = {
                "status": "warning",
                "title": "PLAN PREVENTATIVE MAINTENANCE",
                "action": "A warning risk level has been identified. Schedule maintenance within the next 24 operating hours."
            }
            if tool_wear > 180:
                recommendation["action"] += " High tool wear detected; plan cutter bit replacement."
            if temp_diff > 8.5:
                recommendation["action"] += " High process temperature difference detected; check cooling fans and heat sink dissipation."
        else:
            recommendation = {
                "status": "healthy",
                "title": "HEALTH STATUS OPTIMAL",
                "action": "Machine is running within normal limits. Continue standard operating logs. Next routine check recommended on schedule."
            }
            if tool_wear > 150:
                recommendation["action"] = "Machine health is overall optimal, but Tool Wear is reaching preventative limits. Plan tool replacement during the next shift change."

    # Serialize chronological prediction log for Chart.js (oldest first)
    import json
    chronological_predictions = []
    for row in reversed(predictions):
        chronological_predictions.append({
            "date": str(row[12])[:16], # YYYY-MM-DD HH:MM
            "failure_prob": row[9],
            "tool_wear": row[6],
            "status": row[8]
        })
    chronological_json = json.dumps(chronological_predictions)

    return render_template(
        "machine_details.html",
        machine=machine,
        predictions=predictions,
        latest_prediction=latest_prediction,
        recommendation=recommendation,
        chronological_json=chronological_json
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


@main.route("/maintenance")
def maintenance_route():
    schedules = get_maintenance_schedules()
    machines = get_all_machines()
    
    # Split schedules into pending and completed:
    pending = [s for s in schedules if s[5] == 0]
    completed = [s for s in schedules if s[5] == 1]
    
    return render_template(
        "maintenance.html",
        pending=pending,
        completed=completed,
        machines=machines
    )


@main.route("/maintenance/add", methods=["POST"])
@admin_required
def add_maintenance_route():
    machine_code = request.form.get("machine_code")
    task_name = request.form.get("task_name")
    scheduled_date = request.form.get("scheduled_date")
    urgency = request.form.get("urgency")
    
    if machine_code and task_name and scheduled_date and urgency:
        add_maintenance_schedule(machine_code, task_name, scheduled_date, urgency)
        
    return redirect("/maintenance")


@main.route("/maintenance/complete/<int:schedule_id>", methods=["POST"])
@admin_required
def complete_maintenance_route(schedule_id):
    complete_maintenance_schedule(schedule_id)
    return redirect("/maintenance")


@main.route("/maintenance/delete/<int:schedule_id>", methods=["POST"])
@admin_required
def delete_maintenance_route(schedule_id):
    delete_maintenance_schedule(schedule_id)
    return redirect("/maintenance")


@main.route("/login", methods=["GET", "POST"])
def login_route():
    if "user_id" in session:
        return redirect(url_for("main.home"))
        
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        user = get_user_by_username(username)
        if user:
            from werkzeug.security import check_password_hash
            if check_password_hash(user[2], password):
                session["user_id"] = user[0]
                session["username"] = user[1]
                session["role"] = user[3]
                return redirect(url_for("main.home"))
                
        error = "Invalid username or password."
        
    return render_template("login.html", error=error)


@main.route("/logout")
def logout_route():
    session.clear()
    return redirect(url_for("main.login_route"))