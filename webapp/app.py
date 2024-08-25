from flask import Flask, request, render_template, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import bcrypt
import os
from azure.storage.blob import BlobServiceClient  # Import the Azure Blob SDK

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = 'uploads'  # Directory to store uploaded files (if needed locally)
app.secret_key = 'secret_key'
db = SQLAlchemy(app)

# Azure Blob Storage credentials
sas_token = "<sv=2022-11-02&ss=b&srt=sco&sp=rwdlacytfx&se=2024-08-25T07:09:45Z&st=2024-08-24T23:09:45Z&spr=https&sig=JlUw223dS5raxeYi%2B5UFax8jweR3xBo8D4wmyz13fSA%3D>"
account_name = "<winproj1sa>"
container_name = "<winproj1container>"

# Initialize the BlobServiceClient
blob_service_client = BlobServiceClient(account_url=f"https://{account_name}.blob.core.windows.net", credential=sas_token)
container_client = blob_service_client.get_container_client(container_name)

# Ensure the upload folder exists (optional if still saving locally)
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        new_user = User(name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/login')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session['email'] = user.email
            return redirect('/dashboard')
        else:
            return render_template('login.html', error='Invalid user')

    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'email' in session:
        user = User.query.filter_by(email=session['email']).first()

        if request.method == 'POST':
            # Handle file upload
            file = request.files['file']
            if file:
                # Upload file to Azure Blob Storage
                blob_client = container_client.get_blob_client(file.requirements.txt)
                blob_client.upload_blob(file.stream)  # Upload file stream directly to Blob Storage
                flash('File uploaded to Azure Blob Storage successfully')
                return redirect('/dashboard')

        return render_template('dashboard.html', user=user)
    
    return redirect('/login')

@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
