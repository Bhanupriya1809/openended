from flask import Flask, render_template, request, redirect, jsonify
import mysql.connector
import os
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from flask_mail import Mail, Message

app = Flask(__name__)

# ---------------- EMAIL CONFIG -----------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("EMAIL_USER", "mbhanubhavi47@gmail.com")
app.config['MAIL_PASSWORD'] = os.getenv("EMAIL_PASS", "qmnh ytzz tsuq jknk")
mail = Mail(app)

# ---------------- DATABASE CONNECTION ---------
def get_db_connection():
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "host.docker.internal"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "root@123"),
        database=os.getenv("DB_NAME", "health_reminder"),
        port=os.getenv("DB_PORT", "3306")
    )
    return conn

# --------------- SEND EMAIL -------------------
def send_email_alert(med):
    try:
        msg = Message(
            subject=f"⏰ Medicine Reminder: {med['name']}",
            sender=app.config['MAIL_USERNAME'],
            recipients=[os.getenv("EMAIL_TO", "amoghmn2004@gmail.com")]
        )
        msg.body = f"""
        Reminder for medicine:
        Name: {med['name']}
        Dosage: {med['dosage']}
        Time: {med['reminder_time']}
        Notes: {med['notes']}
        """

        mail.send(msg)
        print("Email sent!")
    except Exception as e:
        print("Email error:", e)

# ---------------- REMINDER CHECKER --------------
def check_reminders():
    print("Checking reminders...")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM medicines
        WHERE TIMESTAMPDIFF(MINUTE, reminder_time, NOW()) = 0
    """)
    due_meds = cursor.fetchall()

    cursor.close()
    conn.close()

    for med in due_meds:
        print("Reminder triggered:", med['name'])
        send_email_alert(med)

# ---------------- SCHEDULER ---------------------
scheduler = BackgroundScheduler()
scheduler.add_job(check_reminders, trigger="interval", minutes=1)
scheduler.start()

# ---------------- ROUTES ------------------------
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

# -------- Browser popup API (JS polls every 30 sec) ------
@app.route("/check_due_popup")
def check_due_popup():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM medicines
        WHERE TIMESTAMPDIFF(MINUTE, reminder_time, NOW()) = 0
    """)
    due = cursor.fetchall()

    cursor.close()
    conn.close()
    return jsonify(due)

@app.route("/check_due_popup")
def check_due_popup():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM medicines
        WHERE reminder_time <= NOW()
        AND reminder_time >= NOW() - INTERVAL 20 SECOND
    """)

    meds = cursor.fetchall()
    cursor.close()
    conn.close()

    return meds


# ---------------- RUN APP -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
