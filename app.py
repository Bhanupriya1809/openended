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
# Using sensible defaults and environment variables
app.config['MAIL_USERNAME'] = os.getenv("EMAIL_USER", "namma.relentless@gmail.com")
app.config['MAIL_PASSWORD'] = os.getenv("EMAIL_PASS", "olcv pton pqqp yqvn") 
mail = Mail(app)

# ---------------- DATABASE CONNECTION ---------
def get_db_connection():
    # Using environment variables for secure and flexible deployment
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "host.docker.internal"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "root@123"),
        database=os.getenv("DB_NAME", "health_reminder"),
        port=os.getenv("DB_PORT", "3306")
    )

# ---------------- SEND EMAIL -------------------
def send_email_alert(med):
    try:
        msg = Message(
            subject=f"⏰ Medicine Reminder: {med['name']}",
            sender=app.config['MAIL_USERNAME'],
            recipients=[os.getenv("EMAIL_TO", "amoghmn2004@gmail.com")] # Target email recipient
        )
        # Format the email body cleanly
        msg.body = f"""
This is your medicine reminder:

Name: {med['name']}
Dosage: {med['dosage']}
Time: {med['reminder_time']}
Notes: {med['notes']}
        """

        # Must be run within an application context for Flask-Mail
        with app.app_context():
            mail.send(msg)
        print(f"Email sent successfully for {med['name']}!")
    except Exception as e:
        print(f"Email error for {med['name']}:", e)

# ---------------- REMINDER CHECKER (Every 1 min) --------------
def check_reminders():
    """
    Background job to check for due reminders and send emails.
    Uses a 5-minute lookback window to prevent missed reminders due to clock drift.
    """
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking reminders for email...")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 🚨 FIX: Widen the check window to 5 minutes (300 seconds)
    # Checks for any medicine due within the last 5 minutes.
    cursor.execute("""
        SELECT * FROM medicines
        WHERE reminder_time <= NOW()
        AND reminder_time >= NOW() - INTERVAL 5 MINUTE
    """)

    due_meds = cursor.fetchall()
    cursor.close()
    conn.close()

    for med in due_meds:
        # Note: In a real system, you would mark this as "sent" to avoid duplicates.
        # For simplicity, we just send the email every time it enters the 5-minute window.
        print(f"Triggering email for: {med['name']}")
        send_email_alert(med)

# ---------------- SCHEDULER ---------------------
scheduler = BackgroundScheduler()
# Run the check every 1 minute
scheduler.add_job(check_reminders, trigger="interval", minutes=1)
scheduler.start()

# ---------------- ROUTES ------------------------
@app.route("/")
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM medicines ORDER BY reminder_time")
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

    # Assuming you have an 'add_medicine.html' template
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

# ---------------- POPUP CHECK API (New Improved) -------------------
@app.route("/check_due_popup")
def check_due_popup():
    """
    API endpoint called by the browser client via AJAX/fetch.
    Returns JSON of due medicines to trigger client-side pop-ups.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 🚨 FIX: Widen the safe window from 60 seconds to 5 minutes (300 SECOND)
    # This is the crucial change for preventing missed browser pop-ups.
    cursor.execute("""
        SELECT * FROM medicines
        WHERE reminder_time <= NOW()
        AND reminder_time >= NOW() - INTERVAL 300 SECOND
    """)

    meds = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(meds) # Must return JSON for the frontend to process

# ---------------- RUN APP -------------------------
if __name__ == "__main__":
    # Ensure the scheduler runs when the main thread starts
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False) # use_reloader=False prevents duplicate scheduler jobs