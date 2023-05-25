from flask import Flask, request, render_template, session
from PIL import Image
import ibm_db
import sys
import os
import requests
import bcrypt


app = Flask(__name__)
app.secret_key = 'a'
# Database connection configuration
dsn_driver = "{IBM DB2 ODBC DRIVER}"
dsn_database = "bludb"
dsn_hostname = "98538591-7217-4024-b027-8baa776ffad1.c3n41cmd0nqnrk39u98g.databases.appdomain.cloud"
dsn_port = "30875"
dsn_protocol = "TCPIP"
dsn_uid = "pvp81078"
dsn_pwd = "mQVuB3Pnf3XIfPBJ"
dsn_ssl = "DigiCertGlobalRootCA.crt"

try:
    conn = ibm_db.connect(f"DRIVER={dsn_driver};DATABASE={dsn_database};HOSTNAME={dsn_hostname};PORT={dsn_port};PROTOCOL={dsn_protocol};SECURITY=SSL;SSLServerCertificate={dsn_ssl};UID={dsn_uid};PWD={dsn_pwd}","", "")
    print("Connected to database: ", dsn_database, "as user: ", dsn_uid, "on host: ", dsn_hostname)
    server =ibm_db.server_info(conn)
    print("DBMS_NAME: ", server.DBMS_NAME)  
    print("DBMS_VER:  ", server.DBMS_VER)
    print("DB_NAME:   ", server.DB_NAME)
except:
    print("Unable to connect: ", ibm_db.conn_errormsg())
  

    # Perform database operations here
 #Close the database connection

def hash_PASSWORD(PASSWORD):
    # Hash the PASSWORD with a salt and return the hashed value
    salt = bcrypt.gensalt()
    hashed_PASSWORD = bcrypt.hashpw(PASSWORD.encode('utf-8'), salt)
    return hashed_PASSWORD

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/profile')
def profile():
    username = session.get('username')
    if username and session.get('loggedin'):
        username = session['username']
        return render_template('profile.html', username=username)
    else:
        return render_template('index.html')

@app.route('/register', methods=['GET','POST'])
def register():
    error=None
    msg=None
    if request.method=='POST':
        USERNAME = request.form['username']
        PASSWORD = request.form['password']
        CONFIRM_PASSWORD = request.form['confirm_password']
        
        # Check if the PASSWORD and confirm PASSWORD fields match
        if PASSWORD != CONFIRM_PASSWORD:
            error = 'PASSWORDs do not match'
            return render_template('register.html', error=error)
        
        # Hash the PASSWORD and insert the new user into the database
        hashed_PASSWORD = hash_PASSWORD(PASSWORD)
        
        # Replace <table_name> with the name of your user table
        query = "INSERT INTO LOGIN (USERNAME, PASSWORD) VALUES (?, ?)"
        
        # Prepare the SQL statement and execute it with the provided parameters
        stmt = ibm_db.prepare(conn, query)
        ibm_db.bind_param(stmt, 1, USERNAME)
        ibm_db.bind_param(stmt, 2, hashed_PASSWORD.decode('utf-8'))
        ibm_db.execute(stmt)
        
        msg=("User created successfully")
        return render_template('register.html',msg=msg)
        
    
    else:
        pass        
    return render_template('register.html',error=error)



@app.route('/increase_resolution', methods=['POST'])
def increase_resolution():
    file = request.files['image']

    # Check if file is an image
    if not file.content_type.startswith('image'):
        return render_template('error.html', message='The uploaded file is not an image.')

    try:
        img = Image.open(file.stream)
    except OSError:
        return render_template('error.html', message='The uploaded file cannot be opened.')

    # Save original image
    img.save('static/original.jpg')

    # Increase resolution
    increase_factor = int(request.form.get('increase_factor', 2))
    width, height = img.size
    new_width = width * increase_factor
    new_height = height * increase_factor
    img = img.resize((new_width, new_height), Image.ANTIALIAS)

    # Save new image
    img.save('static/new.jpg')

    return render_template('result.html', increase_factor=increase_factor)


@app.route('/login', methods=['GET','POST'])
def login():
    error = None
    msg = None
    if request.method == "POST":
        USERNAME = request.form["username"]
        PASSWORD = request.form["password"]
        sql = "SELECT * FROM LOGIN WHERE USERNAME=? AND PASSWORD=?"
        stmt = ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt, 1, USERNAME)
        ibm_db.bind_param(stmt, 2, PASSWORD)
        ibm_db.execute(stmt)
        account = ibm_db.fetch_assoc(stmt)
        print(account)
        if account:
            session['Loggedin'] = True
            session['username'] = account['USERNAME']
            print("Logged in successfully!")
            return render_template('index.html')
        else:
            error = "Incorrect useename/password"
            return render_template('login.html', error=error)
    
    return render_template('login.html', error=error)



if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)
