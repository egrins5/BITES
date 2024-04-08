from flask import Flask, render_template, request, redirect, url_for, session, g, flash
import sqlite3
from datetime import datetime

# Flask Init
app = Flask(__name__)
app.secret_key = 'your_secret_key'


# Connect to DB
def get_db(db_name):
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(db_name)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# Login route
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor = get_db("users.db").cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        if user:
            session['username'] = username
            session['is_admin'] = user[3]  # Assuming is_admin is in the fourth column
            return redirect(url_for('dashboard'))
        else:
            return "Invalid username or password"
    return render_template('login.html')


# Dashboard route
@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        cursor = get_db("database.db").cursor()
        cursor.execute("PRAGMA table_info(data)")
        columns_info = cursor.fetchall()
        
        # Extract column names except for the id column
        column_names = [column[1] for column in columns_info if column[1] != 'id']
        
        cursor.execute("SELECT * FROM data")
        data = cursor.fetchall()
        
        return render_template('dashboard.html', data=data, columns=column_names, is_admin=session.get('is_admin', False))
    return redirect(url_for('login'))


# Add data route
@app.route('/add_data', methods=['POST'])
def add_data():
    if 'username' in session and session['is_admin']:
        if request.method == 'POST':
            date = request.form['date']
            temperature = float(request.form['temperature'])  # Convert to float
            humidity = request.form['humidity']
            
            # Parse and format the date string
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%d-%m-%Y')
            
            # Format humidity value
            humidity_percent = str(humidity) + '%'
            
            cursor = get_db("database.db").cursor()
            cursor.execute("INSERT INTO data (date, temperature, humidity) VALUES (?, ?, ?)", (formatted_date, temperature, humidity_percent))
            get_db("database.db").commit()
            flash('Data added successfully', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('You do not have permission to perform this action', 'error')
        return redirect(url_for('dashboard'))


# Edit data route
@app.route('/edit_data/<int:data_id>', methods=['POST'])
def edit_data(data_id):
    if 'username' in session and session['is_admin']:
        if request.method == 'POST':
            date = request.form['date']
            temperature = request.form['temperature']
            humidity = request.form['humidity']
            
            # Ensure date format is dd-mm-yyyy
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%d')
                formatted_date = date_obj.strftime('%d-%m-%Y')
            except ValueError:
                flash('Please enter a valid date in the format dd-mm-yyyy', 'error')
                return redirect(url_for('dashboard'))
            
            # Format temperature value to one decimal point
            temperature_float = '{:.1f}'.format(float(temperature))
            
            # Format humidity value with %
            humidity_percent = str(int(humidity)) + '%'
            
            cursor = get_db("database.db").cursor()
            cursor.execute("UPDATE data SET date=?, temperature=?, humidity=? WHERE id=?", (formatted_date, temperature_float, humidity_percent, data_id))
            get_db("database.db").commit()
            flash('Data updated successfully', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('You do not have permission to perform this action', 'error')
        return redirect(url_for('dashboard'))


# Delete data route
@app.route('/delete_data/<int:data_id>', methods=['GET', 'POST'])
def delete_data(data_id):
    if 'username' in session and session['is_admin']:
        cursor = get_db("database.db").cursor()
        cursor.execute("DELETE FROM data WHERE id=?", (data_id,))
        get_db("database.db").commit()
        flash('Data deleted successfully', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('You do not have permission to perform this action', 'error')
        return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(debug=True)