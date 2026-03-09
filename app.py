import os
import uuid
import datetime
from decimal import Decimal
from flask import Flask, render_template, request, redirect, session, jsonify
import boto3
from boto3.dynamodb.conditions import Key

app = Flask(__name__)

# Flask Secret Key
app.secret_key = "your-secret-key-change-in-production"

# ---------------- AWS CONFIGURATION ----------------
AWS_REGION = "us-east-1"
USERS_TABLE = "travel-Users"
BOOKINGS_TABLE = "Bookings"
SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:336449003024:TravelGoNotifications"

# Initialize AWS Services
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
sns = boto3.client('sns', region_name=AWS_REGION)

users_table = dynamodb.Table(USERS_TABLE)
bookings_table = dynamodb.Table(BOOKINGS_TABLE)

# ---------------- STATIC DATA ----------------
bus_data = [
    {"id": "B1", "name": "Super Luxury Bus", "source": "Hyderabad", "dest": "Bangalore", "price": 800},
    {"id": "B2", "name": "Express Bus", "source": "Chennai", "dest": "Hyderabad", "price": 700}
]
train_data = [
    {"id": "T1", "name": "Rajdhani Express", "source": "Hyderabad", "dest": "Delhi", "price": 1500},
    {"id": "T2", "name": "Shatabdi Express", "source": "Chennai", "dest": "Bangalore", "price": 900}
]
flight_data = [
    {"id": "F1", "name": "Indigo 6E203", "source": "Hyderabad", "dest": "Dubai", "price": 8500},
    {"id": "F2", "name": "Air India AI102", "source": "Delhi", "dest": "Singapore", "price": 9500}
]
hotel_data = [
    {"id": "H1", "name": "Grand Palace", "city": "Chennai", "type": "Luxury", "price": 4000},
    {"id": "H2", "name": "Budget Inn", "city": "Hyderabad", "type": "Budget", "price": 1500}
]

# ---------------- HELPER FUNCTIONS ----------------

def get_transport_info(t_id):
    """Identifies the service type and details based on the ID."""
    all_services = [bus_data, train_data, flight_data]
    types = ['Bus', 'Train', 'Flight']
    
    for idx, service_list in enumerate(all_services):
        for item in service_list:
            if item['id'] == t_id:
                return {
                    'type': types[idx],
                    'source': item['source'],
                    'destination': item['dest'],
                    'details': f"{item['name']} ({item['source']} - {item['dest']})"
                }
    
    for h in hotel_data:
        if h['id'] == t_id:
            return {
                'type': 'Hotel',
                'source': h['city'],
                'destination': h['city'],
                'details': f"{h['name']} in {h['city']} ({h['type']})"
            }
            
    return {'type': 'General', 'source': 'Unknown', 'destination': 'Unknown', 'details': 'Transport Details'}

# ---------------- ROUTES ----------------

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        users_table.put_item(
            Item={
                'email': request.form['email'],
                'name': request.form['name'],
                'password': request.form['password'],
                'logins': 0
            }
        )
        return redirect('/login')
    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            response = users_table.get_item(Key={'email': request.form['email']})
            user = response.get('Item')
            if user and user['password'] == request.form['password']:
                session['user'] = user['email']
                session['name'] = user['name']
                return redirect('/dashboard')
            return render_template("login.html", error="Invalid Credentials")
        except Exception as e:
            return render_template("login.html", error=str(e))
    return render_template("login.html")

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    
    # IMPROVED: Using Query with GSI instead of Scan
    # Requires a GSI named 'email-index' on the Bookings table
    try:
        response = bookings_table.query(
            IndexName='email-index',
            KeyConditionExpression=Key('email').eq(session['user'])
        )
        bookings = response.get('Items', [])
    except Exception as e:
        print(f"Query Error: {e}. Falling back to scan (Not recommended for prod)")
        response = bookings_table.scan(FilterExpression=Key('email').eq(session['user']))
        bookings = response.get('Items', [])
    
    return render_template("dashboard.html", name=session.get('name', 'User'), bookings=bookings)

@app.route('/bus')
def bus(): return render_template("bus.html", buses=bus_data)

@app.route('/train')
def train(): return render_template("train.html", trains=train_data)

@app.route('/flight')
def flight(): return render_template("flight.html", flights=flight_data)

@app.route('/hotels')
def hotels(): return render_template("hotels.html", hotels=hotel_data)

@app.route('/seat/<transport_id>/<price>')
def seat(transport_id, price):
    if 'user' not in session: return redirect('/login')
    return render_template("seat.html", id=transport_id, price=price)

@app.route('/book', methods=['POST'])
def book():
    if 'user' not in session: return redirect('/login')
    t_id = request.form['transport_id']
    seats = request.form.get('seat')
    price = request.form['price']
    info = get_transport_info(t_id)
    
    session['booking_flow'] = {
        'transport_id': t_id,
        'type': info['type'],
        'source': info['source'],
        'destination': info['destination'],
        'details': info['details'],
        'seat': seats,
        'price': price,
        'date': str(datetime.date.today())
    }
    return render_template("payment.html", booking=session['booking_flow'])

@app.route('/payment', methods=['POST'])
def payment():
    if 'user' not in session or 'booking_flow' not in session:
        return redirect('/dashboard')

    booking_data = session['booking_flow']
    booking_id = str(uuid.uuid4())[:8]
    booking_data['booking_id'] = booking_id
    booking_data['email'] = session['user']
    booking_data['payment_method'] = request.form.get('method')
    booking_data['payment_reference'] = request.form.get('reference')
    booking_data['price'] = Decimal(str(booking_data['price']))

    bookings_table.put_item(Item=booking_data)

    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="TravelGo Booking Confirmed",
            Message=f"Booking ID: {booking_id}\nType: {booking_data['type']}\nDetails: {booking_data['details']}\nSeats: {booking_data['seat']}\nTotal Paid: Rs. {booking_data['price']}"
        )
    except Exception as e:
        print(f"SNS Error: {e}")

    final_booking = booking_data.copy()
    session.pop('booking_flow', None)
    return render_template("ticket.html", booking=final_booking)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    # Running on 0.0.0.0 for EC2 access, but debug is OFF for safety
    app.run(host='0.0.0.0', port=5000, debug=False)
