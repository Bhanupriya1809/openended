from flask import Flask, render_template, request, redirect
import mysql.connector
import os

app = Flask(__name__)

def get_db_connection():
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "host.docker.internal"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "root@123"),
        database=os.getenv("DB_NAME", "health_reminder"),
        port=os.getenv("DB_PORT", "3306")
    )
    return conn

@app.route("/")
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM medicines ORDER BY reminder_time;")
    medicines = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("index.html", medicines=medicines)

@app.route("/add", methods=["GET", "POST"])
def add_medicine():
    if request.method == "POST":
        name = request.form["name"]
        dosage = request.form["dosage"]
        reminder_time = request.form["reminder_time"]
        notes = request.form["notes"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO medicines (name, dosage, reminder_time, notes) VALUES (%s, %s, %s, %s)",
            (name, dosage, reminder_time, notes),
        )
        conn.commit()
        cursor.close()
        conn.close()
        return redirect("/")

    return render_template("add_medicine.html")

@app.route("/delete/<int:med_id>")
def delete_medicine(med_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM medicines WHERE id = %s", (med_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect("/")

if __name__ == "__main__":
    # FIX: must bind to 0.0.0.0 inside Docker
    app.run(host="0.0.0.0", port=5000, debug=True)
