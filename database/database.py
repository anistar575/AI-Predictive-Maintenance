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


def save_prediction(
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
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (

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
        WHERE health_status LIKE '%Moderate%'
    """)
    warning = cursor.fetchone()[0]

    # Critical Machines
    cursor.execute("""
        SELECT COUNT(*)
        FROM prediction_history
        WHERE health_status LIKE '%High%'
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
    def delete_machine(machine_id):
        conn = get_connection()

        cursor = conn.cursor()

    cursor.execute("""

        DELETE FROM machines

        WHERE id = ?

    """, (machine_id,))

    conn.commit()

    conn.close()
def initialize_database():

    create_table()

    create_machine_table()
    

if __name__ == "__main__":
    initialize_database()
    print("Database created successfully.")