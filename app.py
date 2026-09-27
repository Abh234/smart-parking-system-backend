from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_mysqldb import MySQL
from flask import Response
import csv
import io
from datetime import datetime
import random
import string
from flask import request, jsonify

import os
from dotenv import load_dotenv

load_dotenv()

# ================= HELPERS =================
def get_table_columns(cur, table_name):
    cur.execute(f"SHOW COLUMNS FROM {table_name}")
    return [row[0] for row in cur.fetchall()]


def first_existing(columns, candidates):
    column_set = set(columns)
    for candidate in candidates:
        if candidate in column_set:
            return candidate
    return None

# ================= INIT =================
app = Flask(__name__)
allowed_origins = [
    origin.strip()
    for origin in os.environ.get('FRONTEND_ORIGIN', '*').split(',')
    if origin.strip()
]
CORS(app, resources={r"/api/*": {"origins": allowed_origins}})

# ================= MYSQL CONFIG =================
app.config['MYSQL_HOST'] = os.environ.get('DB_HOST', 'localhost')
app.config['MYSQL_USER'] = os.environ.get('DB_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.environ.get('DB_PASSWORD', '')
app.config['MYSQL_DB'] = os.environ.get('DB_NAME', 'parksmart')

mysql = MySQL(app)

# ================= HOME =================
@app.route('/')
def home():
    return "ParkSmart Backend Running"

# ================= TEST =================
@app.route('/test')
def test():
    return "API WORKING"

# ================= REGISTER =================
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()

    try:
        cur = mysql.connection.cursor()

        cur.execute("""
            INSERT INTO users(name, phone, email, password, role)
            VALUES (%s,%s,%s,%s,%s)
        """, (
            data['name'],
            data['phone'],
            data['email'],
            data['password'],
            data['role']
        ))

        mysql.connection.commit()
        cur.close()

        return jsonify({"success": True, "message": "User Registered"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ================= LOGIN =================
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()

    try:
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT email FROM users WHERE email=%s AND password=%s",
            (data['email'], data['password'])
        )
        user = cur.fetchone()
        cur.close()

        if user:
            return jsonify({
                "success": True,
                "email": user[0]   # ✅ USE EMAIL
            })
        else:
            return jsonify({
                "success": False,
                "message": "Invalid email or password"
            })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })
    



# ================= GET SLOTS =================
@app.route('/api/slots', methods=['GET'])
def get_slots():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT slot_id, slot_name, status, price FROM slots")
        data = cur.fetchall()
        cur.close()

        result = []
        for row in data:
            result.append({
                "slot_id": row[0],
                "slot_name": row[1],
                "status": row[2],
                "price": row[3]
            })

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)})

# ================= BOOK SLOT =================
# ================= BOOK SLOT =================
@app.route('/api/book', methods=['POST'])
def book_slot():
    data = request.get_json()

    try:
        cur = mysql.connection.cursor()

        required_fields = [
            'email', 'slot_id', 'date',
            'start_time', 'end_time',
            'vehicle_type', 'vehicle_number'
        ]

        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    "success": False,
                    "message": f"{field} is required"
                })

        cur.execute("SELECT id FROM users WHERE email=%s", (data['email'],))
        user = cur.fetchone()

        if not user:
            cur.close()
            return jsonify({
                "success": False,
                "message": "User not found"
            })

        user_id = user[0]

        cur.execute("SELECT status FROM slots WHERE slot_id=%s", (data['slot_id'],))
        slot = cur.fetchone()

        if not slot:
            cur.close()
            return jsonify({
                "success": False,
                "message": "Slot not found"
            })

        if slot[0] == 'booked':
            cur.close()
            return jsonify({
                "success": False,
                "message": "Slot already booked"
            })

        cur.execute("""
            INSERT INTO bookings(
                user_id,
                slot_id,
                vehicle_type,
                vehicle_number,
                booking_date,
                start_time,
                end_time,
                status
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            user_id,
            data['slot_id'],
            data['vehicle_type'],
            data['vehicle_number'],
            data['date'],
            data['start_time'],
            data['end_time'],
            'booked'
        ))

        cur.execute(
            "UPDATE slots SET status='booked' WHERE slot_id=%s",
            (data['slot_id'],)
        )

        mysql.connection.commit()
        cur.close()

        return jsonify({
            "success": True,
            "message": "Slot booked successfully"
        })

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            "success": False,
            "error": str(e)
        })


# ================= MY BOOKINGS =================
@app.route('/api/my-bookings', methods=['GET'])
def my_bookings():
    try:
        email = request.args.get("email")

        if not email:
            return jsonify({"success": False, "message": "Email required"})

        cur = mysql.connection.cursor()

        cur.execute("SELECT id FROM users WHERE email=%s", (email,))
        user = cur.fetchone()

        if not user:
            cur.close()
            return jsonify({"success": False, "message": "User not found"})

        user_id = user[0]

        cur.execute("""
            SELECT 
                b.booking_id,
                s.slot_name,
                b.vehicle_type,
                b.vehicle_number,
                b.booking_date,
                b.start_time,
                b.end_time,
                b.status
            FROM bookings b
            JOIN slots s ON b.slot_id = s.slot_id
            WHERE b.user_id=%s
            ORDER BY b.booking_id DESC
        """, (user_id,))

        rows = cur.fetchall()
        cur.close()

        bookings = []
        for row in rows:
            bookings.append({
                "booking_id": row[0],
                "slot_name": row[1],
                "vehicle_type": row[2],
                "vehicle_number": row[3],
                "booking_date": str(row[4]),
                "start_time": str(row[5]),
                "end_time": str(row[6]),
                "status": row[7]
            })

        return jsonify({
            "success": True,
            "bookings": bookings
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })


@app.route('/api/user-dashboard', methods=['GET'])
def user_dashboard():
    try:
        email = request.args.get("email")

        if not email:
            return jsonify({
                "success": False,
                "message": "Email required"
            })

        cur = mysql.connection.cursor()

        user_columns = get_table_columns(cur, "users")
        wallet_column = first_existing(user_columns, [
            "wallet_balance",
            "wallet",
            "balance",
            "wallet_amount",
            "amount"
        ])

        if wallet_column:
            cur.execute(
                f"SELECT id, COALESCE({wallet_column}, 0) FROM users WHERE email=%s LIMIT 1",
                (email,)
            )
        else:
            cur.execute(
                "SELECT id, 0 FROM users WHERE email=%s LIMIT 1",
                (email,)
            )

        user = cur.fetchone()

        if not user:
            cur.close()
            return jsonify({
                "success": False,
                "message": "User not found"
            })

        user_id = user[0]
        wallet_balance = float(user[1] or 0)

        cur.execute("""
            SELECT COUNT(*)
            FROM bookings
            WHERE user_id=%s
        """, (user_id,))
        total_bookings = cur.fetchone()[0] or 0

        cur.execute("""
            SELECT COUNT(*)
            FROM bookings
            WHERE user_id=%s AND status='booked'
        """, (user_id,))
        active_parking = cur.fetchone()[0] or 0

        cur.execute("""
            SELECT COALESCE(SUM(p.amount), 0)
            FROM bookings b
            LEFT JOIN payments p ON p.booking_id = b.booking_id
            WHERE b.user_id=%s
        """, (user_id,))
        total_spent = float(cur.fetchone()[0] or 0)

        cur.execute("""
            SELECT
                b.booking_id,
                s.slot_name,
                b.vehicle_number,
                b.booking_date,
                b.start_time,
                b.end_time,
                b.status,
                COALESCE(p.amount, 0) AS amount
            FROM bookings b
            JOIN slots s ON b.slot_id = s.slot_id
            LEFT JOIN payments p ON p.booking_id = b.booking_id
            WHERE b.user_id=%s
            ORDER BY b.booking_id DESC
            LIMIT 5
        """, (user_id,))

        rows = cur.fetchall()
        cur.close()

        recent_bookings = []
        for row in rows:
            recent_bookings.append({
                "booking_id": row[0],
                "slot_name": row[1],
                "vehicle_number": row[2],
                "booking_date": str(row[3]),
                "start_time": str(row[4]),
                "end_time": str(row[5]),
                "booking_status": row[6],
                "amount": float(row[7] or 0)
            })

        return jsonify({
            "success": True,
            "email": email,
            "total_bookings": int(total_bookings),
            "active_parking": int(active_parking),
            "wallet_balance": wallet_balance,
            "recent_spent": total_spent,
            "recent_bookings": recent_bookings
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })



# ================= CANCEL BOOKING =================
@app.route('/api/cancel/<int:booking_id>', methods=['DELETE'])
def cancel_booking(booking_id):
    try:
        email = request.args.get("email")

        if not email:
            return jsonify({"success": False, "message": "Email required"})

        cur = mysql.connection.cursor()

        cur.execute("""
            SELECT b.slot_id, b.status, u.email
            FROM bookings b
            JOIN users u ON b.user_id = u.id
            WHERE b.booking_id = %s
        """, (booking_id,))

        row = cur.fetchone()

        if not row:
            cur.close()
            return jsonify({"success": False, "message": "Booking not found"})

        slot_id, status, user_email = row

        if email != user_email:
            cur.close()
            return jsonify({"success": False, "message": "Unauthorized"})

        if status == "cancelled":
            cur.close()
            return jsonify({"success": False, "message": "Already cancelled"})

        cur.execute(
            "UPDATE bookings SET status='cancelled' WHERE booking_id=%s",
            (booking_id,)
        )

        cur.execute(
            "UPDATE slots SET status='available' WHERE slot_id=%s",
            (slot_id,)
        )

        mysql.connection.commit()
        cur.close()

        return jsonify({"success": True, "message": "Booking cancelled successfully"})

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({"success": False, "message": str(e)})

# ================= VEHICLES =================
@app.route('/api/vehicles/<int:user_id>', methods=['GET'])
def get_vehicles(user_id):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT vehicle_id, vehicle_number, vehicle_type 
        FROM vehicles 
        WHERE user_id=%s
    """, (user_id,))
    data = cur.fetchall()
    cur.close()

    result = []
    for row in data:
        result.append({
            "vehicle_id": row[0],
            "vehicle_number": row[1],
            "vehicle_type": row[2]
        })

    return jsonify(result)

# ================= Admin  =================

# ================= ADMIN REGISTER =================
@app.route('/api/admin/register', methods=['POST'])
def admin_register():
    try:
        data = request.get_json()

        name = data.get("name")
        phone = data.get("phone")
        email = data.get("email")
        password = data.get("password")

        if not name or not phone or not email or not password:
            return jsonify({"success": False, "message": "All fields required"})

        # ✅ USE mysql (NOT db)
        cur = mysql.connection.cursor()

        # CHECK EXIST
        cur.execute("SELECT * FROM admins WHERE email=%s", (email,))
        if cur.fetchone():
            cur.close()
            return jsonify({"success": False, "message": "Admin already exists"})

        # INSERT
        cur.execute("""
            INSERT INTO admins (name, phone, email, password)
            VALUES (%s, %s, %s, %s)
        """, (name, phone, email, password))

        mysql.connection.commit()
        cur.close()

        return jsonify({"success": True, "message": "Admin registered successfully"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ================= ADMIN LOGIN =================
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    try:
        data = request.get_json()

        email = data.get("email")
        password = data.get("password")

        # ✅ USE mysql
        cur = mysql.connection.cursor()

        cur.execute("""
            SELECT id, name, email FROM admins
            WHERE email=%s AND password=%s
        """, (email, password))

        admin = cur.fetchone()
        cur.close()

        if admin:
            return jsonify({
                "success": True,
                "admin": {
                    "id": admin[0],
                    "name": admin[1],
                    "email": admin[2]
                }
            })
        else:
            return jsonify({
                "success": False,
                "message": "Invalid credentials"
            })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ================= Dashboard  admin API =================
@app.route("/api/dashboard", methods=["GET"])
def dashboard():
    try:
        cur = mysql.connection.cursor()

        cur.execute("SELECT COUNT(*) FROM users")
        total_users = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM slots")
        total_slots = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM bookings WHERE status='booked'")
        booked_slots = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM bookings WHERE status='cancelled'")
        cancelled_bookings = cur.fetchone()[0]

        cur.execute("SELECT SUM(amount) FROM payments WHERE status='paid'")
        total_revenue = cur.fetchone()[0] or 0

        available_slots = total_slots - booked_slots

        cur.close()

        return jsonify({
            "success": True,
            "total_users": total_users,
            "total_slots": total_slots,
            "booked_slots": booked_slots,
            "available_slots": available_slots,
            "cancelled_bookings": cancelled_bookings,
            "total_revenue": float(total_revenue)
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

    
# ================= admin  =================


@app.route('/api/admin/users', methods=['GET'])
def admin_users():
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT id, name, email, phone, role
            FROM users
            ORDER BY id DESC
        """)
        rows = cur.fetchall()
        cur.close()

        users = []
        for row in rows:
            users.append({
                "id": row[0],
                "name": row[1],
                "email": row[2],
                "phone": row[3],
                "role": row[4]
            })

        return jsonify({
            "success": True,
            "users": users
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })



##############################hist####################
@app.route('/api/history', methods=['GET'])
def booking_history():
    try:
        email = request.args.get("email")

        if not email:
            return jsonify({
                "success": False,
                "message": "Email required"
            })

        cur = mysql.connection.cursor()

        cur.execute("SELECT id FROM users WHERE email=%s", (email,))
        user = cur.fetchone()

        if not user:
            cur.close()
            return jsonify({
                "success": False,
                "message": "User not found"
            })

        user_id = user[0]

        cur.execute("""
            SELECT
                b.booking_id,
                s.slot_name,
                b.vehicle_type,
                b.vehicle_number,
                b.booking_date,
                b.start_time,
                b.end_time,
                b.status,
                p.razorpay_payment_id,
                p.order_id,
                p.amount,
                p.currency,
                p.status,
                p.payment_method
            FROM bookings b
            JOIN slots s ON b.slot_id = s.slot_id
            LEFT JOIN payments p ON p.booking_id = b.booking_id
            WHERE b.user_id=%s
            ORDER BY b.booking_id DESC
        """, (user_id,))

        rows = cur.fetchall()
        cur.close()

        history = []
        for row in rows:
            history.append({
                "booking_id": row[0],
                "slot_name": row[1],
                "vehicle_type": row[2],
                "vehicle_number": row[3],
                "booking_date": str(row[4]),
                "start_time": str(row[5]),
                "end_time": str(row[6]),
                "booking_status": row[7],
                "payment_id": row[8],
                "order_id": row[9],
                "amount": float(row[10] or 0),
                "currency": row[11] or "INR",
                "payment_status": row[12] or "pending",
                "payment_method": row[13] or "manual"
            })

        return jsonify({
            "success": True,
            "history": history
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })
#########################slots######################

@app.route('/api/admin/slots', methods=['GET'])
def admin_get_slots():
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT slot_id, parking_id, slot_name, status, price
            FROM slots
            ORDER BY slot_id ASC
        """)
        rows = cur.fetchall()
        cur.close()

        slots = []
        for row in rows:
            slots.append({
                "slot_id": row[0],
                "parking_id": row[1],
                "slot_name": row[2],
                "status": row[3],
                "price": float(row[4])
            })

        return jsonify({
            "success": True,
            "slots": slots
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })


    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/admin/slots', methods=['GET', 'POST'])
def admin_slots():
    if request.method == 'GET':
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                SELECT slot_id, parking_id, slot_name, status, price
                FROM slots
                ORDER BY slot_id ASC
            """)
            rows = cur.fetchall()
            cur.close()

            slots = []
            for row in rows:
                slots.append({
                    "slot_id": row[0],
                    "parking_id": row[1],
                    "slot_name": row[2],
                    "status": row[3],
                    "price": float(row[4])
                })

            return jsonify({
                "success": True,
                "slots": slots
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            })

    elif request.method == 'POST':
        try:
            data = request.get_json()

            parking_id = data.get("parking_id")
            slot_name = data.get("slot_name")
            price = data.get("price")
            status = data.get("status", "available")

            if not parking_id or not slot_name or not price:
                return jsonify({
                    "success": False,
                    "message": "parking_id, slot_name and price are required"
                })

            cur = mysql.connection.cursor()

            cur.execute(
                "SELECT slot_id FROM slots WHERE parking_id=%s AND slot_name=%s",
                (parking_id, slot_name)
            )
            existing = cur.fetchone()

            if existing:
                cur.close()
                return jsonify({
                    "success": False,
                    "message": "Slot already exists for this parking"
                })

            cur.execute("""
                INSERT INTO slots (parking_id, slot_name, status, price)
                VALUES (%s, %s, %s, %s)
            """, (parking_id, slot_name, status, price))

            mysql.connection.commit()
            cur.close()

            return jsonify({
                "success": True,
                "message": "Slot added successfully"
            })

        except Exception as e:
            mysql.connection.rollback()
            return jsonify({
                "success": False,
                "error": str(e)
            })
###############################################Payment ###########

@app.route("/api/admin/payments", methods=["GET"])
def admin_payments():
    try:
        cur = mysql.connection.cursor()

        cur.execute("""
            SELECT
                payment_id,
                order_id,
                user_id,
                booking_id,
                slot_id,
                amount,
                currency,
                status,
                payment_method,
                created_at
            FROM payments
            ORDER BY payment_id DESC
        """)
        rows = cur.fetchall()

        payments = []
        total_revenue = 0
        successful_payments = 0
        method_counts = {}

        for row in rows:
            amount = float(row[5] or 0)
            status = row[7] or "pending"
            method = row[8] or "unknown"

            payments.append({
                "payment_id": row[0],
                "order_id": row[1],
                "user_id": row[2],
                "booking_id": row[3],
                "slot_id": row[4],
                "amount": amount,
                "currency": row[6] or "INR",
                "status": status,
                "payment_method": method,
                "created_at": str(row[9]) if row[9] else None
            })

            if str(status).lower() == "paid":
                successful_payments += 1
                total_revenue += amount

            method_counts[method] = method_counts.get(method, 0) + 1

        top_method = "-"
        if method_counts:
            top_method = max(method_counts, key=method_counts.get)

        cur.close()

        return jsonify({
            "success": True,
            "summary": {
                "total_revenue": total_revenue,
                "successful_payments": successful_payments,
                "total_payments": len(payments),
                "top_method": top_method
            },
            "payments": payments
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })
########################################

@app.route('/api/admin/bookings', methods=['GET'])
def admin_bookings():
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT
                booking_id,
                user_id,
                slot_id,
                vehicle_type,
                vehicle_number,
                booking_date,
                start_time,
                end_time,
                status,
                created_at
            FROM bookings
            ORDER BY booking_id DESC
        """)
        rows = cur.fetchall()
        cur.close()

        bookings = []
        for row in rows:
            bookings.append({
                "booking_id": row[0],
                "user_id": row[1],
                "slot_id": row[2],
                "vehicle_type": row[3],
                "vehicle_number": row[4],
                "booking_date": str(row[5]),
                "start_time": str(row[6]),
                "end_time": str(row[7]),
                "status": row[8],
                "created_at": str(row[9])
            })

        return jsonify({
            "success": True,
            "bookings": bookings
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })



def get_month_year_filters():
    month = request.args.get("month")
    year = request.args.get("year")
    return month, year


def build_date_filter(column_name):
    month, year = get_month_year_filters()
    conditions = []
    params = []

    if month:
        conditions.append(f"MONTH({column_name}) = %s")
        params.append(month)

    if year:
        conditions.append(f"YEAR({column_name}) = %s")
        params.append(year)

    where_clause = ""
    if conditions:
        where_clause = " WHERE " + " AND ".join(conditions)

    return where_clause, params


@app.route('/api/admin/reports', methods=['GET'])
def admin_reports():
    try:
        cur = mysql.connection.cursor()

        cur.execute("SELECT COUNT(*) FROM users")
        total_users = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM slots")
        total_slots = cur.fetchone()[0]

        bookings_where, bookings_params = build_date_filter("booking_date")
        cur.execute(f"SELECT COUNT(*) FROM bookings{bookings_where}", tuple(bookings_params))
        total_bookings = cur.fetchone()[0]

        cancelled_sql = f"SELECT COUNT(*) FROM bookings{bookings_where}"
        if bookings_where:
            cancelled_sql += " AND status='cancelled'"
        else:
            cancelled_sql += " WHERE status='cancelled'"
        cur.execute(cancelled_sql, tuple(bookings_params))
        cancelled_bookings = cur.fetchone()[0]

        try:
            payments_where, payments_params = build_date_filter("created_at")
            cur.execute(f"SELECT COUNT(*) FROM payments{payments_where}", tuple(payments_params))
            total_payments = cur.fetchone()[0]

            cur.execute(f"SELECT SUM(amount) FROM payments{payments_where}", tuple(payments_params))
            total_revenue = float(cur.fetchone()[0] or 0)
        except Exception:
            total_payments = 0
            total_revenue = 0.0

        cur.close()

        return jsonify({
            "success": True,
            "report": {
                "total_users": total_users,
                "total_slots": total_slots,
                "total_bookings": total_bookings,
                "cancelled_bookings": cancelled_bookings,
                "total_payments": total_payments,
                "total_revenue": total_revenue
            }
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })


@app.route('/api/admin/reports/export/<report_type>', methods=['GET'])
def export_report(report_type):
    try:
        cur = mysql.connection.cursor()
        output = io.StringIO()
        writer = csv.writer(output)

        if report_type == "users":
            cur.execute("SELECT id, name, email, phone, role FROM users ORDER BY id DESC")
            writer.writerow(["id", "name", "email", "phone", "role"])
            for row in cur.fetchall():
                writer.writerow(row)

        elif report_type == "slots":
            cur.execute("SELECT slot_id, parking_id, slot_name, status, price FROM slots ORDER BY slot_id DESC")
            writer.writerow(["slot_id", "parking_id", "slot_name", "status", "price"])
            for row in cur.fetchall():
                writer.writerow(row)

        elif report_type == "bookings":
            where_clause, params = build_date_filter("booking_date")
            cur.execute(f"""
                SELECT booking_id, user_id, slot_id, vehicle_type, vehicle_number,
                       booking_date, start_time, end_time, status, created_at
                FROM bookings
                {where_clause}
                ORDER BY booking_id DESC
            """, tuple(params))
            writer.writerow([
                "booking_id", "user_id", "slot_id", "vehicle_type", "vehicle_number",
                "booking_date", "start_time", "end_time", "status", "created_at"
            ])
            for row in cur.fetchall():
                writer.writerow(row)

        elif report_type == "payments":
            where_clause, params = build_date_filter("created_at")
            cur.execute(f"SELECT * FROM payments{where_clause}", tuple(params))
            rows = cur.fetchall()
            headers = [desc[0] for desc in cur.description]
            writer.writerow(headers)
            for row in rows:
                writer.writerow(row)

        else:
            cur.close()
            return jsonify({"success": False, "message": "Invalid report type"})

        cur.close()

        csv_data = output.getvalue()
        output.close()

        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={report_type}_report.csv"}
        )

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })


########################################################


from datetime import datetime
import random
import string
from flask import request, jsonify

def generate_upi_reference():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"PHN{timestamp}{suffix}"


@app.route('/api/payment/phonepe/confirm', methods=['POST'])
def confirm_phonepe_manual_payment():
    data = request.get_json() or {}
    cur = None

    try:
        required_fields = [
            'email', 'slot_id', 'date', 'start_time', 'end_time',
            'vehicle_type', 'vehicle_number', 'hours', 'payer_name'
        ]

        for field in required_fields:
            if field not in data or not str(data[field]).strip():
                return jsonify({
                    "success": False,
                    "message": f"{field} is required"
                })

        payment_method = data.get("payment_method", "phonepe_manual")

        cur = mysql.connection.cursor()

        cur.execute("SELECT id FROM users WHERE email=%s", (data['email'],))
        user = cur.fetchone()
        if not user:
            cur.close()
            return jsonify({
                "success": False,
                "message": "User not found"
            })

        user_id = user[0]

        cur.execute("SELECT slot_name, status, price FROM slots WHERE slot_id=%s", (data['slot_id'],))
        slot = cur.fetchone()
        if not slot:
            cur.close()
            return jsonify({
                "success": False,
                "message": "Slot not found"
            })

        slot_name, slot_status, slot_price = slot

        if slot_status == 'booked':
            cur.close()
            return jsonify({
                "success": False,
                "message": "Selected slot is already booked"
            })

        cur.execute("""
            INSERT INTO bookings(
                user_id, slot_id, vehicle_type, vehicle_number,
                booking_date, start_time, end_time, status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            data['slot_id'],
            data['vehicle_type'],
            data['vehicle_number'],
            data['date'],
            data['start_time'],
            data['end_time'],
            'booked'
        ))

        booking_id = cur.lastrowid

        base_amount = float(slot_price) * int(data['hours'])
        platform_fee = 20.0
        gst = round((base_amount + platform_fee) * 0.18, 2)
        amount = round(base_amount + platform_fee + gst, 2)

        generated_utr = generate_upi_reference()

        cur.execute("""
            INSERT INTO payments(
                user_id, booking_id, slot_id,
                amount, currency, status,
                payment_method, order_id, razorpay_payment_id, razorpay_signature
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            booking_id,
            data['slot_id'],
            amount,
            'INR',
            'paid',
            payment_method,
            f"UPI-MANUAL-{booking_id}",
            generated_utr,
            data['payer_name']
        ))

        cur.execute(
            "UPDATE slots SET status='booked' WHERE slot_id=%s",
            (data['slot_id'],)
        )

        mysql.connection.commit()
        cur.close()

        return jsonify({
            "success": True,
            "booking_id": booking_id,
            "slot_name": slot_name,
            "amount_paid": amount,
            "payment_method": payment_method,
            "upi_reference": generated_utr
        })

    except Exception as e:
        if cur is not None:
            mysql.connection.rollback()
            cur.close()
        return jsonify({
            "success": False,
            "error": str(e)
        })


@app.route('/api/payment/status/<int:booking_id>', methods=['GET'])
def payment_status(booking_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT
                b.booking_id,
                s.slot_name,
                p.razorpay_payment_id,
                p.amount,
                p.status,
                p.payment_method,
                p.order_id,
                p.created_at
            FROM bookings b
            JOIN slots s ON b.slot_id = s.slot_id
            LEFT JOIN payments p ON p.booking_id = b.booking_id
            WHERE b.booking_id=%s
            LIMIT 1
        """, (booking_id,))

        row = cur.fetchone()
        cur.close()

        if not row:
            return jsonify({
                "success": False,
                "message": "Booking not found"
            })

        return jsonify({
            "success": True,
            "booking_id": row[0],
            "slot_name": row[1],
            "payment": {
                "payment_id": row[2],
                "amount": float(row[3] or 0),
                "status": row[4] or "paid",
                "payment_method": row[5] or "phonepe_manual",
                "order_id": row[6],
                "created_at": str(row[7]) if row[7] else None
            }
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })




# ================= RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", debug=False, port=port)
