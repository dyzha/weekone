from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, date
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    birthday = db.Column(db.Date, nullable=False)
    address = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(100), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@property
def age(self):
    if not self.birthday:
        return 0
    today = date.today()
    age = today.year - self.birthday.year
    if (today.month, today.day) < (self.birthday.month, self.birthday.day):
        age -= 1
    return age

# Routes
@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form['username']
    password = request.form['password']
    
    user = User.query.filter_by(username=username).first()
    
    if user and user.check_password(password):
        session['user_id'] = user.id
        return redirect(url_for('home'))
    else:
        flash('Invalid username or password')
        return redirect(url_for('login'))

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register_post():
    username = request.form['username']
    password = request.form['password']
    name = request.form['name']
    birthday_str = request.form['birthday']
    address = request.form['address']
    
    # Check if username already exists
    if User.query.filter_by(username=username).first():
        flash('Username already exists')
        return redirect(url_for('register'))
    
    # Handle file upload
    image_filename = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            # Add timestamp to avoid filename conflicts
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            image_filename = timestamp + filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
    
    # Convert birthday string to date object
    try:
        birthday = datetime.strptime(birthday_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format')
        return redirect(url_for('register'))
    
    # Create new user
    user = User(
        username=username,
        name=name,
        birthday=birthday,
        address=address,
        image_filename=image_filename
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    flash('Registration successful! Please login.')
    return redirect(url_for('login'))

@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('login'))

    # Calculate age here
    today = date.today()
    birthday = user.birthday
    age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))

    return render_template('home.html', user=user, age=age)




# Create tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)