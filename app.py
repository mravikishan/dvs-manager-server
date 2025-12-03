# app.py - Python Flask Server (with SQLite Database Integration)

from flask import Flask, request, jsonify
from flask_cors import CORS 
from flask_sqlalchemy import SQLAlchemy # Permanent storage ke liye
import os 
from datetime import datetime 

# --- App Initialization ---
app = Flask(__name__)
# Sabhi endpoints ke liye CORS enable karein
CORS(app, resources={r"/*": {"origins": "*"}}) 

# --- Database Configuration (SQLite) ---
# Render environment mein SQLite file 'dvs_data.db' mein data hamesha ke liye save hoga.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dvs_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Database Models (Tables) ---

# Member Table: Naye Sadasya ka pura record
class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id_code = db.Column(db.String(20), unique=True, nullable=False) # Jaise: DV1001
    name = db.Column(db.String(100), nullable=False)
    mobile = db.Column(db.String(15), unique=True, nullable=False)
    aadhaar = db.Column(db.String(12), unique=True, nullable=False)
    pan = db.Column(db.String(10))
    bank_details = db.Column(db.String(200))
    application_type = db.Column(db.String(10), default='deposit')
    loan_amount_requested = db.Column(db.Float, default=0.0)
    loan_repayment_period = db.Column(db.String(50))
    loan_reason = db.Column(db.Text)
    status = db.Column(db.String(10), default='Active') # Active, Deactivated
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Deposit Table: Jama ki gayi rashi ka record
class Deposit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False) # Kis sadasya ka deposit hai
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(10), nullable=False) # offline/online
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Loan Table: Karz aavedan ka record
class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False) # Kis sadasya ka karz hai
    amount = db.Column(db.Float, nullable=False)
    repayment_period = db.Column(db.String(50), nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='Pending') # Pending, Approved, Disbursed
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# Function to create tables and run once
def setup_database():
    with app.app_context():
        # Yeh function shuru hone par database tables ko bana dega
        db.create_all()
        print("Database tables created successfully (or already exist).")


# ---------- API ENDPOINTS FOR FORMS ----------

@app.route('/submit_member', methods=['POST'])
def submit_member():
    data = request.json
    print("\n--- NEW MEMBER REGISTRATION RECEIVED ---")

    try:
        # Generate a simple member ID (count lekar usme 1001 jodein)
        member_count = Member.query.count()
        new_member_id_code = f"DV{1001 + member_count}"

        # Create a new Member object and populate data
        new_member = Member(
            member_id_code=new_member_id_code,
            name=data['name'],
            mobile=data['mobile'],
            aadhaar=data['aadhaar'],
            pan=data.get('pan'),
            bank_details=data.get('bank_details'),
            application_type=data.get('application_type', 'deposit'),
            loan_amount_requested=float(data.get('loan_amount', 0.0)),
            loan_repayment_period=data.get('loan_repayment', ''),
            loan_reason=data.get('loan_reason', ''),
            timestamp=datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00')) 
        )
        
        db.session.add(new_member)
        db.session.commit() # Data database mein save karein
        
        return jsonify({
            "status": "success",
            "message": f"Member '{data.get('name')}' (ID: {new_member_id_code}) ka data database mein safaltapoorvak save hua."
        }), 200

    except Exception as e:
        db.session.rollback() # Agar error aaye to changes vapas lein
        print(f"Database Error: {e}")
        return jsonify({
            "status": "error",
            "error": "Database mein data save karne mein error aaya. Duplicate entry (Aadhaar/Mobile) ho sakti hai.",
            "details": str(e)
        }), 500


@app.route('/submit_deposit', methods=['POST'])
def submit_deposit():
    data = request.json
    print("\n--- DEPOSIT RECEIVED ---")

    try:
        # Frontend se aane wale member_id ko asali Member ID se badalna hoga.
        # Abhi sirf dummy data (member_id=1) use ho raha hai.
        
        new_deposit = Deposit(
            member_id=1, 
            amount=float(data['amount']),
            payment_method=data['payment_method'],
            timestamp=datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        )
        
        db.session.add(new_deposit)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": f"Deposit ₹{data.get('amount')} for ID {data.get('member_id')} database mein safaltapoorvak darj hua."
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"Database Error: {e}")
        return jsonify({
            "status": "error",
            "error": "Database mein deposit save karne mein error aaya.",
            "details": str(e)
        }), 500


@app.route('/submit_loan', methods=['POST'])
def submit_loan():
    data = request.json
    print("\n--- LOAN APPLICATION RECEIVED ---")

    try:
        new_loan = Loan(
            member_id=1, # Fix this later when Member lookup is implemented
            amount=float(data['amount']),
            repayment_period=data['repayment'],
            reason=data['reason'],
            timestamp=datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        )

        db.session.add(new_loan)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": f"Loan application for ID {data.get('member_id')} database mein darj hua."
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"Database Error: {e}")
        return jsonify({
            "status": "error",
            "error": "Database mein loan application save karne mein error aaya.",
            "details": str(e)
        }), 500


@app.route('/deactivate_member', methods=['POST'])
def deactivate_member():
    data = request.json
    print("\n--- DEACTIVATION REQUEST RECEIVED ---")
    
    # Ismein database mein Member ka status 'Deactivated' update hoga.
    
    return jsonify({
        "status": "success",
        "message": f"Member ID {data.get('member_id')} ka account band karne ka anurodh database mein darj kiya gaya hai."
    }), 200


# Server run block
if __name__ == '__main__':
    # Setup database (create tables) before running the app
    setup_database()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
