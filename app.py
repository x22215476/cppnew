#importing necessary modules and libraries 
from flask import Flask, render_template, request, redirect, url_for, flash, session
import requests
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField
from wtforms.validators import DataRequired, Email, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from functools import wraps
import json
from customlibrary.discount import DiscountManager  

app = Flask(__name__) #creating an instance 

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///services.db' #configuring the SQLAlchemy database here

secret_key = secrets.token_urlsafe(16)  
app.secret_key = secret_key

db = SQLAlchemy(app)

APIGATEWAY_ENDPOINT = 'https://0vkc9xi655.execute-api.eu-west-1.amazonaws.com/x22215476' #connecting the APIgateway to the code
discount_manager = DiscountManager() #creating an instance for the customlibrary
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    mobile_number = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)

class ServiceForm(FlaskForm):
    name = StringField('Service Name', validators=[DataRequired()])
    description = TextAreaField('Service Description')

class SignupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    name = StringField('Full Name', validators=[DataRequired()])
    mobile_number = StringField('Mobile Number', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    product = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)

def is_authenticated(username, password):
    user = User.query.filter_by(username=username).first()
    return user and check_password_hash(user.password, password)
 
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()        
        if is_authenticated(username, password):
            session['username'] = username
            session['user_id'] = get_user_id_from_database()
            session['admin'] = user.is_admin
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')
 
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm(request.form)
    if request.method == 'POST' and form.validate():
        username = form.username.data
        email = form.email.data
        name = form.name.data
        mobile_number = form.mobile_number.data
        password = form.password.data
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
 
        new_user = User(username=username, email=email, name=name, mobile_number=mobile_number, password=hashed_password)

        try:
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect(url_for('home'))
        except IntegrityError as e:
            db.session.rollback()
            print(f"Error: {e}")
            return render_template('signup.html', form=form, error='Username/email already exists. Choose a different one.')
    return render_template('signup.html', form=form)
 
#@app.route('/logout')
#def logout():
 #   session.pop('username', None)
  #  return redirect(url_for('login'))
   # from flask import redirect, url_for

@app.route('/logout')
def logout():
    # Clear the user session
    session.pop('username', None)
    # Redirect to the home page or any other page
    return redirect('/')

 
def login_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if 'username' in session:
            return route_function(*args, **kwargs)
        else:
            return redirect(url_for('login'))
    return wrapper
 
def get_user_id_from_session():
    if 'user_id' in session:
        return session['user_id']
    else:
        return None

def get_user_id_from_database():
    if 'username' in session:
        username = session['username']
        # Query the database to get the user by username
        user = User.query.filter_by(username=username).first()
        # Check if the user is found
        if user:
            return user.id  
    return None

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/')
def home():
    return render_template('dashboard.html')
    

def get_service(service_name):
    service_payload = {
        'operation': 'get_service_details',
        'service_name': service_name
    }

    try:
        lambda_response = requests.post(APIGATEWAY_ENDPOINT, json=service_payload)
        if lambda_response.status_code == 200:
            service_details = lambda_response.json()  # getting the service details from lambda
            print('service detials:',service_details)
            return service_details
    except Exception as e:
        print('Error:', e)
        flash('Error fetching service details. Please try again later.', 'error')
        return service_details


@app.route('/service/flooring')
@login_required
def flooring_service():
    service_name = 'Flooring'
    response = get_service(service_name)

    service_details = json.loads(response['body'])
    
    print('service_details:',service_details)

    return render_template('flooring.html', data=service_details)
@app.route('/service/interior')
@login_required
def interior_service():
    service_name = 'Interior'

    response = get_service(service_name)

    service_details = json.loads(response['body'])
    
    print('service_details:',service_details)

    return render_template('Interior.html', data=service_details)

@app.route('/service/roofing')
@login_required
def roofing_service():
    service_name = 'Roofing'

    response = get_service(service_name)

    service_details = json.loads(response['body'])
    
    print('service_details:',service_details)

    return render_template('Roofing.html', data=service_details)

@app.route('/service/insulation')
@login_required
def insulation_service():
    service_name = 'Insulation'

    response = get_service(service_name)

    service_details = json.loads(response['body'])
    
    print('service_details:',service_details)

    return render_template('Insulation.html', data=service_details)

@app.route('/service/plumbing')
@login_required
def plumbing_service():
    service_name = 'Plumbing'

    response = get_service(service_name)

    service_details = json.loads(response['body'])
    
    print('service_details:',service_details)

    return render_template('Plumbing.html', data=service_details)

@app.route('/service/lawn')
@login_required
def lawn_service():
    service_name = 'Lawn'

    response = get_service(service_name)

    service_details = json.loads(response['body'])
    
    print('service_details:',service_details)

    return render_template('Lawn.html', data=service_details)

@app.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    service_name = request.form.get('service')
    cost = request.form.get('cost')
    print('request.form:', request.form)
    user_id = get_user_id_from_session()
    print('user_id:',user_id)

    if 'cart' not in session:
        session['cart'] = []

    session['cart'].append({'service_name': service_name, 'cost': cost})

    flash('Service added to the cart successfully!', 'success')
    return redirect(url_for('cart'))

@app.route('/cart')
@login_required
def cart():
    cart = session.get('cart', [])
    total_cart_price = 0
    print('cart:',cart)

    for item in cart:
        total_cart_price = total_cart_price + int(item['cost'])
    discounted_price = discount_manager.apply_discount(total_cart_price) #apply_discount is being called 

    return render_template('cart.html', cart=cart, total_cart_price=total_cart_price,discounted_price=discounted_price)

@app.route('/orders')
@login_required
def orders():
    order_list = Order.query.all()
    return render_template('orders.html', orders=order_list)

@app.route('/place_order', methods=['POST'])
@login_required
def place_order():
    print('Right Here')
    user_id = get_user_id_from_session()
    print('user_id:', user_id)
    cart = session.get('cart', [])

    
    # Creating a payload to send details to API
    order_payload = {
        'operation': 'add_order',
        'user_id': user_id,
        'cart': cart
    }
    try:
        response = requests.post(APIGATEWAY_ENDPOINT, json=order_payload)

        if response.status_code == 200:
            session.pop('cart', None)
            flash('Order placed successfully!', 'success')
            return redirect(url_for('orders'))
        else:
            flash('Error placing order. Please try again later.', 'error')
            return redirect(url_for('index'))

    except Exception as e:
        print('error:',e)
        flash(f'Error placing order: {str(e)}', 'error')
        return redirect(url_for('index'))

# logic to calculate the total price
def calculate_total_price(service, price_per_service):
    total_price = total_price + price_per_service 
    return total_price

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)