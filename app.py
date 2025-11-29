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
    """Sends email and marks the medicine as sent in the database."""
    success = False
    try:
        msg = Message(
            subject=f"⏰ Medicine Reminder: {med['name']}",
            sender=app.config['MAIL_USERNAME'],
            recipients=[os.getenv("EMAIL_TO", "amoghmn2004@gmail04.com")] # Target email recipient
        )
        msg.body = f"""
This is your medicine reminder:

Name: {med['name']}
Dosage: {med['dosage']}
Time: {med['reminder_time']}
Notes: {med['notes']}
        """

        with app.app_context():
            mail.send(msg)
        print(f"Email sent successfully for {med['name']}!")
        success = True
    except Exception as e:
        print(f"Email error for {med['name']}: {e}")
        print("!!! TROUBLESHOOTING: Please check your Gmail App Password and network connection. !!!")

    # 💡 TRANSACTIONAL FIX: Update DB only if email sending was attempted/successful
    if success:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # Mark the reminder as sent to prevent re-sending. (Requires the new DB column!)
            cursor.execute(
                "UPDATE medicines SET reminder_sent = 1 WHERE id = %s", 
                (med['id'],)
            )
            conn.commit()
            cursor.close()
            conn.close()
            print(f"Medicine ID {med['id']} marked as sent.")
        except Exception as db_e:
            # This exception likely means the 'reminder_sent' column is missing!
            print(f"Database error marking medicine as sent. DID YOU RUN THE SQL COMMAND? Error: {db_e}")

# ---------------- REMINDER CHECKER (Every 1 min) --------------
def check_reminders():
    """
    Background job to check for due reminders and send emails.
    Only checks for items where reminder_sent is 0 (not sent yet).
    """
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking reminders for email...")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 🚨 FIX: Only select reminders that haven't been sent (reminder_sent = 0)
    cursor.execute("""
        SELECT * FROM medicines
        WHERE reminder_time <= NOW()
        AND reminder_time >= NOW() - INTERVAL 5 MINUTE
        AND reminder_sent = 0 
    """)

    due_meds = cursor.fetchall()
    cursor.close()
    conn.close()

    for med in due_meds:
        print(f"Triggering email for: {med['name']} (ID: {med['id']})")
        # send_email_alert handles the database update after sending
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

# 💡 NEW ROUTE: Simple test to verify email configuration works
@app.route("/test-email")
def test_email():
    test_med = {
        'id': 0, # Dummy ID for testing only
        'name': 'Test Pill', 
        'dosage': '5mg', 
        'reminder_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
        'notes': 'This is a test email sent manually.'
    }
    # NOTE: This test email will confirm connectivity but will fail to update the DB since ID 0 doesn't exist.
    send_email_alert(test_med)
    return "Attempted to send test email. Check your application console for success/error messages, and check your inbox."


@app.route("/add", methods=["GET", "POST"])
def add_medicine():
    if request.method == "POST":
        name = request.form["name"]
        dosage = request.form["dosage"]
        reminder_time = request.form["reminder_time"]
        notes = request.form["notes"]

        conn = get_db_connection()
        cursor = conn.cursor()
        # Insert with new column default (must exist in DB)
        cursor.execute(
            "INSERT INTO medicines (name, dosage, reminder_time, notes, reminder_sent) VALUES (%s, %s, %s, %s, 0)",
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

    # 🚨 FIX: Only show pop-ups for reminders that have NOT been sent yet (reminder_sent = 0)
    cursor.execute("""
        SELECT * FROM medicines
        WHERE reminder_time <= NOW()
        AND reminder_time >= NOW() - INTERVAL 300 SECOND
        AND reminder_sent = 0
    """)

    meds = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify(meds) # Must return JSON for the frontend to process

# ---------------- RUN APP -------------------------
if __name__ == "__main__":
    # Ensure the scheduler runs when the main thread starts
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False) # use_reloader=False prevents duplicate scheduler jobs