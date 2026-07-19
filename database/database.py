import sqlite3
from pathlib import Path

DB_PATH = Path("database/predictions.db")
def add_machine(
    machine_code,
    machine_name,
    machine_type,
    department,
    location,
    installation_date
):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""

            INSERT INTO machines(

                machine_code,
                machine_name,
                machine_type,
                department,
                location,
                installation_date

            )

            VALUES(?,?,?,?,?,?)

        """, (

            machine_code,
            machine_name,
            machine_type,
            department,
            location,
            installation_date

        ))

        conn.commit()

        return True

    except sqlite3.IntegrityError:

        return False

    finally:

        conn.close()
def get_all_machines():

    conn=get_connection()

    cursor=conn.cursor()

    cursor.execute("""

        SELECT *

        FROM machines

        ORDER BY id DESC

    """)

    data=cursor.fetchall()

    conn.close()

    return data
def update_machine_status(machine_code, status):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

        UPDATE machines

        SET current_status = ?

        WHERE machine_code = ?

    """, (

        status,
        machine_code

    ))

    conn.commit()

    conn.close()
def create_machine_table():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
CREATE TABLE IF NOT EXISTS machines (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    machine_code TEXT UNIQUE NOT NULL,

    machine_name TEXT NOT NULL,

    machine_type TEXT NOT NULL,

    department TEXT NOT NULL,

    location TEXT NOT NULL,

    installation_date TEXT,

    current_status TEXT DEFAULT 'Healthy',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

)
""")

    conn.commit()
    conn.close()


def get_connection():
    """
    Create a connection to the SQLite database.
    """
    DB_PATH.parent.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH)


def create_table():
    """
    Create prediction_history table if it does not exist.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
CREATE TABLE IF NOT EXISTS prediction_history(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    machine_code TEXT,

    machine_type TEXT,

    air_temperature REAL,

    process_temperature REAL,

    rotational_speed INTEGER,

    torque REAL,

    tool_wear INTEGER,

    prediction TEXT,

    health_status TEXT,

    failure_probability REAL,

    confidence TEXT,

    model_used TEXT,

    prediction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP

);
""")

    conn.commit()
    conn.close()
    create_machine_table()


def save_prediction(
    
    machine_code,
    machine_type,
    air_temperature,
    process_temperature,
    rotational_speed,
    torque,
    tool_wear,
    prediction,
    health_status,
    failure_probability,
    confidence,
    model_used,
):
    """
    Save a prediction into SQLite.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO prediction_history(

            machine_code,
            machine_type,
            air_temperature,
            process_temperature,
            rotational_speed,
            torque,
            tool_wear,
            prediction,
            health_status,
            failure_probability,
            confidence,
            model_used

        )
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
    """, (

        machine_code,
        machine_type,
        air_temperature,
        process_temperature,
        rotational_speed,
        torque,
        tool_wear,
        prediction,
        health_status,
        failure_probability,
        confidence,
        model_used,

    ))

    conn.commit()
    conn.close()


def get_all_predictions():
    """
    Retrieve all prediction history.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM prediction_history
        ORDER BY prediction_time DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows


def get_dashboard_stats():
    """
    Return dashboard statistics.
    """

    conn = get_connection()
    cursor = conn.cursor()

    # Total Predictions
    cursor.execute("SELECT COUNT(*) FROM prediction_history")
    total = cursor.fetchone()[0]

    # Healthy Machines
    cursor.execute("""
        SELECT COUNT(*)
        FROM prediction_history
        WHERE health_status LIKE '%Healthy%'
    """)
    healthy = cursor.fetchone()[0]

    # Warning Machines
    cursor.execute("""
        SELECT COUNT(*)
        FROM prediction_history
        WHERE health_status LIKE '%Warning%'
    """)
    warning = cursor.fetchone()[0]

    # Critical Machines
    cursor.execute("""
        SELECT COUNT(*)
        FROM prediction_history
        WHERE health_status LIKE '%Critical%'
    """)
    critical = cursor.fetchone()[0]

    conn.close()

    return {
        "total": total,
        "healthy": healthy,
        "warning": warning,
        "critical": critical,
    }
def delete_machine(machine_id):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

        DELETE FROM machines

        WHERE id=?

    """,(machine_id,))

    conn.commit()

    conn.close()
def get_machine(machine_code):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

        SELECT *

        FROM machines

        WHERE machine_code = ?

    """, (machine_code,))

    machine = cursor.fetchone()

    conn.close()

    return machine


def get_machine_by_id(machine_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT *
        FROM machines
        WHERE id = ?
    """, (machine_id,))
    machine = cursor.fetchone()
    conn.close()
    return machine


def update_machine(
    machine_id,
    machine_code,
    machine_name,
    machine_type,
    department,
    location,
    installation_date
):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Cascade update prediction_history when machine_code changes
        cursor.execute("SELECT machine_code FROM machines WHERE id = ?", (machine_id,))
        row = cursor.fetchone()
        if row:
            old_code = row[0]
            if old_code != machine_code:
                cursor.execute("""
                    UPDATE prediction_history
                    SET machine_code = ?
                    WHERE machine_code = ?
                """, (machine_code, old_code))
        
        cursor.execute("""
            UPDATE machines
            SET machine_code = ?,
                machine_name = ?,
                machine_type = ?,
                department = ?,
                location = ?,
                installation_date = ?
            WHERE id = ?
        """, (
            machine_code,
            machine_name,
            machine_type,
            department,
            location,
            installation_date,
            machine_id
        ))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_predictions_by_machine(machine_code):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT *
        FROM prediction_history
        WHERE machine_code = ?
        ORDER BY prediction_time DESC
    """, (machine_code,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_predictions_with_machine_details():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, p.machine_code, p.machine_type, p.air_temperature, 
               p.process_temperature, p.rotational_speed, p.torque, 
               p.tool_wear, p.prediction, p.health_status, p.failure_probability, 
               p.confidence, p.model_used, p.prediction_time,
               m.machine_name, m.department, m.location
        FROM prediction_history p
        LEFT JOIN machines m ON p.machine_code = m.machine_code
        ORDER BY p.prediction_time DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_all_departments():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT department 
        FROM machines 
        WHERE department IS NOT NULL AND department != ''
    """)
    depts = [r[0] for r in cursor.fetchall()]
    conn.close()
    return depts


def initialize_database():

    create_table()

    create_machine_table()
    

if __name__ == "__main__":
    initialize_database()
    print("Database created successfully.")