import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
# --- FIX: Added generate_password_hash ---
from werkzeug.security import check_password_hash, generate_password_hash
import database as db
import security_utils

app = Flask(__name__)
# Load the secret key from .env for session management
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY")

# === User Authentication Routes ===

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        user = db.get_user(username)

        # Note: user['password_hash'] works because our db cursor uses dictionary=True
        if user and check_password_hash(user['password_hash'], password):
            # Password is correct, now generate and store OTP for MFA
            otp = security_utils.generate_otp()
            session['mfa_otp'] = otp
            session['mfa_username'] = username
            print(f"(For demo) MFA OTP for {username}: {otp}")
            flash(f"An OTP has been sent (check console).", "info")
            return redirect(url_for('mfa_verify'))
        else:
            flash("Invalid username or password.", "danger")
    
    return render_template("login.html")

#
# --- NEW CODE: Signup Route ---
#
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Check if passwords match
        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('signup'))
        
        # Hash the password
        password_hash = generate_password_hash(password)
        
        # Try to create the user
        if db.create_user(username, password_hash):
            flash("Account created successfully! Please log in.", "success")
            return redirect(url_for('login'))
        else:
            # This message handles duplicate usernames or other DB errors
            flash("Username already exists. Please choose another.", "danger")
            return redirect(url_for('signup'))

    # Show the signup page for a GET request
    return render_template("signup.html")

@app.route("/mfa", methods=["GET", "POST"])
def mfa_verify():
    if 'mfa_username' not in session:
        return redirect(url_for('login'))

    if request.method == "POST":
        entered_otp = request.form['otp']
        if entered_otp == session.get('mfa_otp'):
            # MFA success! Log the user in.
            session['logged_in'] = True
            session['username'] = session['mfa_username']
            session.pop('mfa_otp', None)
            session.pop('mfa_username', None)
            return redirect(url_for('payment_form'))
        else:
            flash("Invalid OTP.", "danger")
            
    return render_template("mfa_page.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

# === Payment Processing Routes ===

@app.route("/", methods=["GET"])
def payment_form():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template("index.html")

@app.route("/pay", methods=["POST"])
def process_payment():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    # Step 1: Get data from form
    card_number = request.form['card_number']
    amount = float(request.form['amount'])
    region = request.form['region']

    # Step 2: Run security checks
    security_utils.antivirus_scan("web_transaction")
    risk_score = security_utils.risk_analysis(amount, region)
    print(f"Transaction risk score: {risk_score}")

    # Store transaction details in session to use after 3DS
    session['payment_data'] = {
        "card": card_number,
        "amount": amount,
        "region": region,
        "risk": risk_score
    }

    # Step 3: Check for 3D Secure
    if security_utils.requires_3ds_challenge(risk_score):
        # Risk is high, require 3DS
        otp_3ds = "123456" # Hardcoded OTP from your original script
        session['3ds_otp'] = otp_3ds
        print(f"(For demo) 3D Secure OTP: {otp_3ds}")
        flash("High-risk transaction. Please complete 3D Secure verification.", "warning")
        return redirect(url_for('verify_3ds'))
    else:
        # Risk is low, process directly
        return redirect(url_for('complete_payment'))

@app.route("/verify-3ds", methods=["GET", "POST"])
def verify_3ds():
    if not session.get('logged_in') or '3ds_otp' not in session:
        return redirect(url_for('payment_form'))

    if request.method == "POST":
        entered_otp = request.form['otp']
        if entered_otp == session.get('3ds_otp'):
            # 3DS passed
            session.pop('3ds_otp', None)
            return redirect(url_for('complete_payment'))
        else:
            # 3DS failed
            flash("3D Secure authentication failed.", "danger")
            # Log the failed attempt
            data = session.get('payment_data', {})
            db.save_transaction(
                session['username'],
                data.get('card', 'N/A'),
                data.get('amount', 0),
                data.get('region', 'N/A'),
                data.get('risk', 0),
                "failed_3ds"
            )
            session.pop('payment_data', None)
            return redirect(url_for('payment_failed'))
            
    return render_template("verify_3ds.html")

@app.route("/complete-payment")
def complete_payment():
    if not session.get('logged_in') or 'payment_data' not in session:
        return redirect(url_for('login'))

    data = session.get('payment_data')
    
    # Log successful payment
    db.save_transaction(
        session['username'],
        data['card'],
        data['amount'],
        data['region'],
        data['risk'],
        "success"
    )
    
    # Clean up session
    session.pop('payment_data', None)
    
    return redirect(url_for('payment_success'))

@app.route("/success")
def payment_success():
    return render_template("success.html")

@app.route("/failed")
def payment_failed():
    return render_template("failed.html")


if __name__ == "__main__":
    # --- FIX: Removed the os.path.exists check for 'users.db' ---
    # We no longer use SQLite, so we don't need to check for the file.
    # The database.py script is now run manually once to init MySQL.
    app.run(debug=True)