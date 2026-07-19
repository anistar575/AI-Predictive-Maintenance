
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
    if request.endpoint in ("main.login_route", "main.debug_webhook_listener") or (request.path and request.path.startswith("/static")):
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
            result["Health Status"]
        )
        
        # Trigger webhook alert on warning or critical issues
        if "Warning" in result["Health Status"] or "Critical" in result["Health Status"]:
            from datetime import datetime
            trigger_webhook_alert({
                "machine_code": request.form["machine_code"],
                "status": result["Health Status"],
                "failure_probability": float(result["Failure Probability"]),
                "prediction_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "advisory": f"Tool wear: {data['Tool wear [min]']} min. Temp offset: {round(data['Process temperature [K]'] - data['Air temperature [K]'], 2)} K."
            })

        return jsonify(prediction)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400


def trigger_webhook_alert(data):
    import requests
    import threading
    webhook_url = "http://127.0.0.1:5000/debug/webhook-listener"
    
    def send_post():
        try:
            requests.post(webhook_url, json=data, timeout=2)
        except Exception as e:
            print("Webhook dispatch error:", e)
            
    threading.Thread(target=send_post).start()


@main.route("/debug/webhook-listener", methods=["POST"])
def debug_webhook_listener():
    data = request.get_json()
    import json
    with open("C:/Users/Admin/.gemini/antigravity/brain/36731fe5-10b6-47c8-a0b6-7307e7aff08a/scratch/webhook_alerts.json", "a") as f:
        f.write(json.dumps(data) + "\n")
    return jsonify({"status": "received"}), 200


@main.app_context_processor
def inject_notifications():
    notifications = []
    
    # 1. Fetch latest 5 Warning/Critical predictions
    all_preds = get_predictions_with_machine_details()
    warn_crit_preds = [p for p in all_preds if 'Warning' in p[9] or 'Critical' in p[9]]
    # Sort by prediction time descending
    warn_crit_preds.sort(key=lambda x: x[12], reverse=True)
    for p in warn_crit_preds[:5]:
        notifications.append({
            "type": "alert",
            "severity": "critical" if "Critical" in p[9] else "warning",
            "title": f"{p[9].upper()}: {p[14]} ({p[1]})",
            "message": f"Failure prob. {round(p[10]*100, 1)}%. Speed: {p[5]} RPM, Wear: {p[6]} min.",
            "time": p[12][11:16] # HH:MM
        })
        
    # 2. Fetch pending maintenance tasks
    all_tasks = get_maintenance_schedules()
    pending_tasks = [t for t in all_tasks if t[5] == 0]
    # Sort by scheduled date descending
    pending_tasks.sort(key=lambda x: x[3], reverse=True)
    for t in pending_tasks[:5]:
        notifications.append({
            "type": "maintenance",
            "severity": "info",
            "title": f"MAINTENANCE DUE: {t[1]}",
            "message": f"Task: {t[2]} scheduled for {t[3]} (Urgency: {t[4]}).",
            "time": t[3]
        })
        
    return dict(
        system_notifications=notifications,
        unread_notifications_count=len(notifications)
    )


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
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        
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


@main.route("/reports")
def reports_route():
    machines = get_all_machines()
    departments = get_all_departments()
    # Fetch first 10 diagnostics as a preview
    preview_data = get_predictions_with_machine_details()[:10]
    
    return render_template(
        "reports.html",
        machines=machines,
        departments=departments,
        preview_data=preview_data
    )


@main.route("/reports/download")
def download_report_route():
    import io
    import csv
    from flask import Response
    
    report_type = request.args.get("type", "predictions")
    machine_code = request.args.get("machine_code", "all")
    department = request.args.get("department", "all")
    status = request.args.get("status", "all")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    if report_type == "predictions":
        rows = get_predictions_with_machine_details()
        filtered = []
        for r in rows:
            if machine_code != "all" and r[1] != machine_code: continue
            if department != "all" and r[15] != department: continue
            if status != "all" and status.lower() not in r[9].lower(): continue
            if start_date and r[13][:10] < start_date: continue
            if end_date and r[13][:10] > end_date: continue
            filtered.append(r)
            
        writer.writerow(["ID", "Machine Code", "Machine Type", "Air Temp (K)", "Process Temp (K)", 
                         "Rotational Speed (RPM)", "Torque (Nm)", "Tool Wear (min)", "Prediction", 
                         "Health Status", "Failure Probability", "Confidence", "Model Used", 
                         "Prediction Time", "Machine Name", "Department", "Location"])
        for r in filtered:
            writer.writerow(r)
            
        filename = f"diagnostics_report_{start_date or 'all'}_to_{end_date or 'all'}.csv"
        
    elif report_type == "machines":
        rows = get_all_machines()
        filtered = []
        for r in rows:
            if machine_code != "all" and r[1] != machine_code: continue
            if department != "all" and r[4] != department: continue
            if status != "all" and status.lower() not in r[7].lower(): continue
            filtered.append(r)
            
        writer.writerow(["ID", "Machine Code", "Machine Name", "Machine Type", "Department", 
                         "Location", "Installation Date", "Health Status", "Registered At"])
        for r in filtered:
            writer.writerow(r)
            
        filename = "machines_registry_report.csv"
        
    else: # maintenance schedules
        rows = get_maintenance_schedules()
        # Build department lookup map
        dept_map = {m[1]: m[4] for m in get_all_machines()}
        filtered = []
        for r in rows:
            if machine_code != "all" and r[1] != machine_code: continue
            m_dept = dept_map.get(r[1], "Unassigned")
            if department != "all" and m_dept != department: continue
            if status == "Healthy" and r[5] != 1: continue
            if status in ("Warning", "Critical") and r[5] == 1: continue
            if start_date and r[3] < start_date: continue
            if end_date and r[3] > end_date: continue
            filtered.append(r)
            
        writer.writerow(["Schedule ID", "Machine Code", "Task Name", "Scheduled Date", "Urgency", "Completed Status", "Machine Name"])
        for r in filtered:
            writer.writerow([
                r[0], r[1], r[2], r[3], r[4],
                "Complete" if r[5] == 1 else "Pending",
                r[6]
            ])
            
        filename = "maintenance_schedules_report.csv"
        
    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response


@main.route("/reports/print")
def print_report_route():
    report_type = request.args.get("type", "predictions")
    machine_code = request.args.get("machine_code", "all")
    department = request.args.get("department", "all")
    status = request.args.get("status", "all")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    
    headers = []
    rows = []
    
    if report_type == "predictions":
        headers = ["ID", "Machine Code", "Machine Name", "Department", "Health Status", "Failure Prob.", "Confidence", "Date/Time"]
        all_rows = get_predictions_with_machine_details()
        for r in all_rows:
            if machine_code != "all" and r[1] != machine_code: continue
            if department != "all" and r[15] != department: continue
            if status != "all" and status.lower() not in r[9].lower(): continue
            if start_date and r[13][:10] < start_date: continue
            if end_date and r[13][:10] > end_date: continue
            rows.append([
                r[0], r[1], r[14], r[15], r[9], f"{round(r[10]*100, 2)}%", r[11], r[13]
            ])
        title = "Diagnostics Telemetry History Report"
        
    elif report_type == "machines":
        headers = ["Code", "Machine Name", "Type", "Department", "Location", "Installation Date", "Health Status"]
        all_rows = get_all_machines()
        for r in all_rows:
            if machine_code != "all" and r[1] != machine_code: continue
            if department != "all" and r[4] != department: continue
            if status != "all" and status.lower() not in r[7].lower(): continue
            rows.append([
                r[1], r[2], r[3], r[4], r[5], r[6] if r[6] else "--", r[7]
            ])
        title = "Registered Machinery Asset Report"
        
    else: # maintenance
        headers = ["Task ID", "Machine", "Task Name", "Scheduled Date", "Urgency", "Status"]
        all_rows = get_maintenance_schedules()
        dept_map = {m[1]: m[4] for m in get_all_machines()}
        for r in all_rows:
            if machine_code != "all" and r[1] != machine_code: continue
            m_dept = dept_map.get(r[1], "Unassigned")
            if department != "all" and m_dept != department: continue
            if status == "Healthy" and r[5] != 1: continue
            if status in ("Warning", "Critical") and r[5] == 1: continue
            if start_date and r[3] < start_date: continue
            if end_date and r[3] > end_date: continue
            rows.append([
                r[0], f"{r[1]} - {r[6]}", r[2], r[3], r[4], "Completed" if r[5] == 1 else "Pending"
            ])
        title = "Maintenance Tasks Schedule Report"
        
    return render_template(
        "print_report.html",
        title=title,
        headers=headers,
        rows=rows,
        filters={
            "Type": report_type.upper(),
            "Machine Code": machine_code,
            "Department": department,
            "Status": status,
            "Date Range": f"{start_date or 'Start'} to {end_date or 'End'}"
        }
    )