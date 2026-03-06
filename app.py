import os
import uuid
import datetime
from decimal import Decimal
from flask import Flask, render_template, request, redirect, session, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# SECURITY: Use environment variables for secrets
app.secret_key = app.config['SECRET_KEY']

# ---------------- MONGODB CONNECTION ----------------
MONGODB_URI = app.config['MONGODB_URI']
MONGODB_DB = app.config['MONGODB_DB']

client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB]
users_collection = db['users']
bookings_collection = db['bookings']

# Create indexes for better query performance
users_collection.create_index("email", unique=True)
bookings_collection.create_index("email")

# ---------------- STATIC DATA ----------------
bus_data = [
    {"id": "B1", "name": "Super Luxury Bus", "source": "Hyderabad", "dest": "Bangalore", "price": 800},
    {"id": "B2", "name": "Express Bus", "source": "Chennai", "dest": "Hyderabad", "price": 700},
    {"id": "B3", "name": "Premium Coach", "source": "Bangalore", "dest": "Chennai", "price": 750},
    {"id": "B4", "name": "Comfort Travels", "source": "Delhi", "dest": "Agra", "price": 600},
    {"id": "B5", "name": "Night Cruiser", "source": "Mumbai", "dest": "Pune", "price": 550},
    {"id": "B6", "name": "Mega Bus", "source": "Kolkata", "dest": "Delhi", "price": 1200},
    {"id": "B7", "name": "Deluxe Express", "source": "Hyderabad", "dest": "Chennai", "price": 650},
    {"id": "B8", "name": "City Link", "source": "Bangalore", "dest": "Hyderabad", "price": 850},
    {"id": "B9", "name": "Royal Coach", "source": "Mumbai", "dest": "Bangalore", "price": 1100},
    {"id": "B10", "name": "Swift Travels", "source": "Delhi", "dest": "Jaipur", "price": 500}
]

train_data = [
    {"id": "T1", "name": "Rajdhani Express", "source": "Hyderabad", "dest": "Delhi", "price": 1500},
    {"id": "T2", "name": "Shatabdi Express", "source": "Chennai", "dest": "Bangalore", "price": 900},
    {"id": "T3", "name": "Deccan Queen", "source": "Mumbai", "dest": "Pune", "price": 800},
    {"id": "T4", "name": "Konkan Railway", "source": "Mumbai", "dest": "Goa", "price": 950},
    {"id": "T5", "name": "Golden Chariot", "source": "Bangalore", "dest": "Mysore", "price": 700},
    {"id": "T6", "name": "Howrah Express", "source": "Kolkata", "dest": "Delhi", "price": 1800},
    {"id": "T7", "name": "Duranto Express", "source": "Hyderabad", "dest": "Bangalore", "price": 1100},
    {"id": "T8", "name": "Chennai Express", "source": "Chennai", "dest": "Delhi", "price": 1600},
    {"id": "T9", "name": "Garib Rath", "source": "Delhi", "dest": "Indore", "price": 1200},
    {"id": "T10", "name": "Samta Express", "source": "Jaipur", "dest": "Agra", "price": 450}
]

flight_data = [
    {"id": "F1", "name": "Indigo 6E203", "source": "Hyderabad", "dest": "Dubai", "price": 8500},
    {"id": "F2", "name": "Air India AI102", "source": "Delhi", "dest": "Singapore", "price": 9500},
    {"id": "F3", "name": "SpiceJet SG101", "source": "Mumbai", "dest": "Bangkok", "price": 7800},
    {"id": "F4", "name": "GoAir G8201", "source": "Bangalore", "dest": "Kuala Lumpur", "price": 8200},
    {"id": "F5", "name": "Vistara UK101", "source": "Chennai", "dest": "London", "price": 15000},
    {"id": "F6", "name": "Air India AI501", "source": "Hyderabad", "dest": "Mumbai", "price": 4500},
    {"id": "F7", "name": "Indigo 6E501", "source": "Bangalore", "dest": "Delhi", "price": 5000},
    {"id": "F8", "name": "GoAir G8401", "source": "Chennai", "dest": "Hyderabad", "price": 4200},
    {"id": "F9", "name": "SpiceJet SG301", "source": "Kolkata", "dest": "Mumbai", "price": 6800},
    {"id": "F10", "name": "Air India AI701", "source": "Delhi", "dest": "Jaipur", "price": 3500}
]

hotel_data = [
    {"id": "H1", "name": "Grand Palace", "city": "Chennai", "type": "Luxury", "price": 4000},
    {"id": "H2", "name": "Budget Inn", "city": "Hyderabad", "type": "Budget", "price": 1500},
    {"id": "H3", "name": "The Oberoi", "city": "Mumbai", "type": "Luxury", "price": 6000},
    {"id": "H4", "name": "Taj Mahal View", "city": "Agra", "type": "5-Star", "price": 8000},
    {"id": "H5", "name": "Goa Sands Resort", "city": "Goa", "type": "Resort", "price": 3500},
    {"id": "H6", "name": "The Imperial", "city": "Delhi", "type": "Luxury", "price": 5500},
    {"id": "H7", "name": "Bangalore Hilton", "city": "Bangalore", "type": "4-Star", "price": 3200},
    {"id": "H8", "name": "Jaipur Palace", "city": "Jaipur", "type": "Heritage", "price": 2800},
    {"id": "H9", "name": "Kolkata Grand", "city": "Kolkata", "type": "4-Star", "price": 2500},
    {"id": "H10", "name": "Mysore Heritage", "city": "Mysore", "type": "Heritage", "price": 1800}
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
        try:
            users_collection.insert_one({
                'email': request.form['email'],
                'name': request.form['name'],
                'password': request.form['password'],
                'logins': 0,
                'created_at': datetime.datetime.utcnow()
            })
            return redirect('/login')
        except Exception as e:
            return render_template("register.html", error=str(e))
    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            user = users_collection.find_one({'email': request.form['email']})
            if user and user['password'] == request.form['password']:
                session['user'] = user['email']
                session['name'] = user['name']
                users_collection.update_one(
                    {'email': user['email']},
                    {'$inc': {'logins': 1}}
                )
                return redirect('/dashboard')
            return render_template("login.html", error="Invalid Credentials")
        except Exception as e:
            return render_template("login.html", error=str(e))
    return render_template("login.html")

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    
    try:
        bookings = list(bookings_collection.find({'email': session['user']}))
        # Convert ObjectId to string for JSON serialization
        for booking in bookings:
            booking['_id'] = str(booking['_id'])
            booking['booking_id'] = booking.get('booking_id', str(booking['_id']))
    except Exception as e:
        print(f"Query Error: {e}")
        bookings = []
    
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
    booking_data['price'] = float(booking_data['price'])
    booking_data['created_at'] = datetime.datetime.utcnow()

    bookings_collection.insert_one(booking_data)

    final_booking = booking_data.copy()
    session.pop('booking_flow', None)
    return render_template("ticket.html", booking=final_booking)

@app.route('/remove_booking', methods=['POST'])
def remove_booking():
    if 'user' not in session:
        return redirect('/login')
    
    booking_id = request.form.get('booking_id')
    
    # Delete booking from MongoDB
    try:
        bookings_collection.delete_one({'booking_id': booking_id})
    except Exception as e:
        print(f"Delete Error: {e}")
    
    return redirect('/dashboard')

# -------- SEARCH FUNCTIONALITY --------

@app.route('/search_bus', methods=['GET', 'POST'])
def search_bus():
    query_source = request.args.get('source', '').strip().lower()
    query_dest = request.args.get('dest', '').strip().lower()
    
    results = []
    if query_source or query_dest:
        results = [
            b for b in bus_data 
            if (not query_source or query_source in b['source'].lower()) and
               (not query_dest or query_dest in b['dest'].lower())
        ]
    
    return render_template("bus.html", buses=results, search_performed=bool(query_source or query_dest), all_buses=bus_data)

@app.route('/search_train', methods=['GET', 'POST'])
def search_train():
    query_source = request.args.get('source', '').strip().lower()
    query_dest = request.args.get('dest', '').strip().lower()
    
    results = []
    if query_source or query_dest:
        results = [
            t for t in train_data 
            if (not query_source or query_source in t['source'].lower()) and
               (not query_dest or query_dest in t['dest'].lower())
        ]
    
    return render_template("train.html", trains=results, search_performed=bool(query_source or query_dest), all_trains=train_data)

@app.route('/search_flight', methods=['GET', 'POST'])
def search_flight():
    query_source = request.args.get('source', '').strip().lower()
    query_dest = request.args.get('dest', '').strip().lower()
    
    results = []
    if query_source or query_dest:
        results = [
            f for f in flight_data 
            if (not query_source or query_source in f['source'].lower()) and
               (not query_dest or query_dest in f['dest'].lower())
        ]
    
    return render_template("flight.html", flights=results, search_performed=bool(query_source or query_dest), all_flights=flight_data)

@app.route('/search_hotel', methods=['GET', 'POST'])
def search_hotel():
    query_city = request.args.get('city', '').strip().lower()
    query_type = request.args.get('type', '').strip().lower()
    
    results = []
    if query_city or query_type:
        results = [
            h for h in hotel_data 
            if (not query_city or query_city in h['city'].lower()) and
               (not query_type or query_type in h['type'].lower())
        ]
    
    return render_template("hotels.html", hotels=results, search_performed=bool(query_city or query_type), all_hotels=hotel_data)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    # Running on 0.0.0.0 for EC2 access, but debug is OFF for safety
    app.run(host='0.0.0.0', port=5000, debug=False)
