# TravelGo - Full-Stack Travel Booking Platform

A web-based travel booking platform built with Flask and AWS DynamoDB. TravelGo simplifies the process of reserving buses, trains, flights, and hotels through a unified interface.

## 🌟 Features

- **Multi-Mode Booking**: Book buses, trains, flights, and hotels in one place
- **User Authentication**: Secure registration and login system
- **Dynamic Seat Selection**: Choose seats in real-time with interactive UI
- **Booking Management**: View, track, and cancel bookings from personalized dashboard
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **AWS DynamoDB Integration**: Persistent data storage with AWS DynamoDB

## 📋 Project Structure

```
TravelGo/
├── app.py                      # Main Flask application
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
├── README.md                  # Project documentation
│
└── templates/                 # HTML Templates
    ├── index.html            # Landing page
    ├── register.html         # User registration
    ├── login.html            # User login
    ├── dashboard.html        # User dashboard
    ├── bus.html              # Bus booking
    ├── train.html            # Train booking
    ├── flight.html           # Flight booking
    ├── hotels.html           # Hotel booking
    ├── seat.html             # Seat selection
    ├── payment.html          # Payment confirmation
    └── ticket.html           # Booking confirmation ticket
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- AWS Account with DynamoDB access
- AWS CLI configured with credentials
- pip (Python package manager)

### Installation

1. **Clone the repository** (if using Git)
```bash
cd d:\AWS_PROJECT
```

2. **Create a virtual environment**
```bash
python -m venv venv
venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up DynamoDB Tables**

Create two tables in AWS Console or using AWS CLI:

```bash
# Users table
aws dynamodb create-table \
    --table-name travel-users \
    --attribute-definitions AttributeName=email,AttributeType=S \
    --key-schema AttributeName=email,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1

# Bookings table
aws dynamodb create-table \
    --table-name travel-bookings \
    --attribute-definitions AttributeName=booking_id,AttributeType=S AttributeName=email,AttributeType=S \
    --key-schema AttributeName=booking_id,KeyType=HASH AttributeName=email,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1
```

5. **Configure environment variables**
```bash
# Create a .env file in the project root with the following variables:
FLASK_SECRET_KEY=your-secret-key-here
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
USERS_TABLE=travel-users
BOOKINGS_TABLE=travel-bookings
FLASK_ENV=development
```

6. **Run the application**
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## 🔧 Configuration

### Environment Variables (.env file)

```bash
# Flask Configuration
FLASK_SECRET_KEY=your-secret-key-here
FLASK_DEBUG=False

# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key

# DynamoDB Table Names
USERS_TABLE=travel-users
BOOKINGS_TABLE=travel-bookings

# Application Settings
FLASK_ENV=production
```

## 📊 AWS Services Required

### 1. **DynamoDB Tables**
- `travel-users`: Stores user account information
  - Primary Key: `email`
  - Fields: name, password, logins

- `travel-bookings`: Stores all booking records
  - Partition Key: `booking_id`
  - Sort Key: `email`
  - Fields: type, transport_id, date, seat, price, payment_method, payment_reference, created_at

### 2. **AWS SNS**
- Topic: `TravelGoNotifications`
- Sends email confirmations for bookings
- Integrates with Flask backend for real-time notifications

### 3. **AWS EC2**
- Hosts the Flask application
- Recommended: t2.small or larger instance
- OS: Amazon Linux 2 or Ubuntu

## 🔐 Security Features

- Session-based authentication
- Secure password storage (implement hashing in production)
- CSRF protection via Flask sessions
- Environment-based configuration (no hardcoded secrets)
- HTTPOnly and Secure cookies
- SameSite cookie policy

## 📚 API Routes

### Authentication
- `GET /` - Home page
- `POST /register` - User registration
- `POST /login` - User login
- `GET /logout` - User logout

### Booking
- `GET /dashboard` - User dashboard
- `GET /bus` - Browse bus options
- `GET /train` - Browse train options
- `GET /flight` - Browse flight options
- `GET /hotels` - Browse hotel options
- `GET /seat/<transport_id>/<price>` - Seat selection page
- `POST /book` - Process booking
- `POST /payment` - Process payment & create booking record
- `POST /remove_booking` - Cancel booking

## 💳 Payment Flow

1. User selects seats/room
2. Confirms booking details
3. Proceeds to payment page
4. Selects payment method and enters reference
5. Booking is recorded in DynamoDB
6. Email confirmation sent via SNS
7. Ticket confirmation page displayed

## 🎨 UI/UX Features

- **Responsive Design**: Mobile-first approach
- **Modern Color Scheme**: Blue (#0047ab), Yellow (#ffcc00)
- **Smooth Animations**: Hover effects and transitions
- **Icon Integration**: FontAwesome icons throughout
- **Clear Navigation**: Intuitive flow from browsing to booking

## 🧪 Testing

To test the application locally:

1. **User Registration**
   - Go to `/register`
   - Enter name, email, password
   - Click Register

2. **User Login**
   - Go to `/login`
   - Enter registered email and password
   - Click Login

3. **Book a Trip**
   - From dashboard, select a transport mode (Bus/Train/Flight/Hotel)
   - Select seats
   - Review booking details
   - Complete payment with test reference

## 📱 Responsive Breakpoints

- **Desktop**: 1200px+
- **Tablet**: 768px to 1199px
- **Mobile**: Below 768px

## 🛠️ Troubleshooting

### AWS Connection Issues
- Verify AWS credentials in `.env` file
- Check IAM permissions for EC2 role
- Ensure DynamoDB tables exist
- Verify SNS topic ARN

### Database Issues
- Ensure DynamoDB table names match in `app.py`
- Create GSI `email-index` on Bookings table if using query
- Check AWS region matches configuration

### Session Issues
- Clear browser cookies
- Verify `FLASK_SECRET_KEY` is set
- Check session storage settings

## 📖 Production Deployment

### On AWS EC2

1. **Create and configure EC2 instance**
   ```bash
   sudo yum update -y
   sudo yum install python3 python3-pip -y
   ```

2. **Clone project and setup**
   ```bash
   git clone <repository-url>
   cd TravelGo
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure with Gunicorn**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

4. **Use Nginx as reverse proxy**
   - Configure Nginx to forward requests to Gunicorn
   - Enable SSL/TLS certificates

5. **Monitor with CloudWatch**
   - Set up CloudWatch logs
   - Create alarms for errors

## 📝 Code Standards

- Use meaningful variable names
- Add comments for complex logic
- Follow PEP 8 Python style guide
- Use Flask blueprints for scalability (future enhancement)
- Implement proper error handling

## 🚀 Future Enhancements

- [ ] Payment gateway integration (Stripe, Razorpay)
- [ ] Advanced search and filtering
- [ ] User ratings and reviews
- [ ] Loyalty program/reward points
- [ ] Mobile app (React Native)
- [ ] Real-time availability updates
- [ ] Multiple language support
- [ ] Admin dashboard

## 📞 Support

For issues or questions:
- Email: support@travelgo.com
- Phone: +1 (800) 123-4567
- Location: Houston, TX, USA

## 📄 License

This project is provided as-is for educational purposes.

## 🙏 Acknowledgments

- Built with Flask - Python web framework
- AWS Services - Cloud infrastructure
- FontAwesome - Icon library
- Bootstrap-inspired responsive design

---

**Version**: 1.0.0  
**Last Updated**: March 2026  
**Status**: Active Development
#   T r a v e l G o  
 #   T r a v e l G O _ A W S  
 #   T r a v e l G O _ A W S  
 #   T r a v e l G O _ A W S  
 