from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

# Establishing connection to SQLite database (or creating one if it doesn't exist)
def get_db_connection():
    conn = sqlite3.connect("movie_theatre.db")
    conn.row_factory = sqlite3.Row
    return conn

# Create tables
with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Movies (
        movie_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        genre TEXT,
        duration INTEGER,
        rating REAL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Showtimes (
        showtime_id INTEGER PRIMARY KEY AUTOINCREMENT,
        movie_id INTEGER NOT NULL,
        show_date TEXT NOT NULL,
        show_time TEXT NOT NULL,
        available_seats INTEGER,
        FOREIGN KEY (movie_id) REFERENCES Movies(movie_id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Customers (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Bookings (
        booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        showtime_id INTEGER NOT NULL,
        seats_booked INTEGER NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES Customers(customer_id),
        FOREIGN KEY (showtime_id) REFERENCES Showtimes(showtime_id)
    )
    ''')

# Routes
@app.route('/')
def index():
    conn = get_db_connection()
    movies = conn.execute('SELECT * FROM Movies').fetchall()
    conn.close()
    return render_template('index.html', movies=movies)

@app.route('/add_movie', methods=['GET', 'POST'])
def add_movie():
    if request.method == 'POST':
        title = request.form['title']
        genre = request.form['genre']
        duration = request.form['duration']
        rating = request.form['rating']
        conn = get_db_connection()
        conn.execute('INSERT INTO Movies (title, genre, duration, rating) VALUES (?, ?, ?, ?)',
                     (title, genre, duration, rating))
        conn.commit()
        conn.close()
        return redirect('/')
    return render_template('add_movie.html')

@app.route('/showtimes/<int:movie_id>')
def showtimes(movie_id):
    conn = get_db_connection()
    showtimes = conn.execute('SELECT * FROM Showtimes WHERE movie_id = ?', (movie_id,)).fetchall()
    conn.close()
    return render_template('showtimes.html', showtimes=showtimes, movie_id=movie_id)

@app.route('/add_showtime/<int:movie_id>', methods=['GET', 'POST'])
def add_showtime(movie_id):
    if request.method == 'POST':
        show_date = request.form['show_date']
        show_time = request.form['show_time']
        available_seats = request.form['available_seats']
        conn = get_db_connection()
        conn.execute('INSERT INTO Showtimes (movie_id, show_date, show_time, available_seats) VALUES (?, ?, ?, ?)',
                     (movie_id, show_date, show_time, available_seats))
        conn.commit()
        conn.close()
        return redirect(f'/showtimes/{movie_id}')
    return render_template('add_showtime.html', movie_id=movie_id)

@app.route('/book_ticket/<int:showtime_id>', methods=['GET', 'POST'])
def book_ticket(showtime_id):
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        seats_booked = int(request.form['seats_booked'])

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT available_seats FROM Showtimes WHERE showtime_id = ?', (showtime_id,))
        available_seats = cursor.fetchone()['available_seats']

        if available_seats >= seats_booked:
            cursor.execute('INSERT INTO Customers (name, email) VALUES (?, ?) ON CONFLICT(email) DO NOTHING', (name, email))
            cursor.execute('SELECT customer_id FROM Customers WHERE email = ?', (email,))
            customer_id = cursor.fetchone()['customer_id']

            cursor.execute('INSERT INTO Bookings (customer_id, showtime_id, seats_booked) VALUES (?, ?, ?)',
                           (customer_id, showtime_id, seats_booked))
            cursor.execute('UPDATE Showtimes SET available_seats = available_seats - ? WHERE showtime_id = ?',
                           (seats_booked, showtime_id))
            conn.commit()
        conn.close()
        return redirect('/')
    return render_template('book_ticket.html', showtime_id=showtime_id)

@app.route('/delete_showtime/<int:showtime_id>', methods=['POST'])
def delete_showtime(showtime_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM Showtimes WHERE showtime_id = ?', (showtime_id,))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/delete_movie/<int:movie_id>', methods=['POST'])
def delete_movie(movie_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Delete all related data
    cursor.execute('DELETE FROM Bookings WHERE showtime_id IN (SELECT showtime_id FROM Showtimes WHERE movie_id = ?)', (movie_id,))
    cursor.execute('DELETE FROM Showtimes WHERE movie_id = ?', (movie_id,))
    cursor.execute('DELETE FROM Movies WHERE movie_id = ?', (movie_id,))

    conn.commit()
    conn.close()
    return redirect('/')


# @app.route('/test',methods=['GET'])
# def test():
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     data= cursor.execute('SELECT * FROM Showtimes')
#     conn.commit()
#     conn.close()
#     print(data)


if __name__ == "__main__":
    app.run(debug=True)
