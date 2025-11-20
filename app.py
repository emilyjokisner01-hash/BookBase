from flask import Flask, request, jsonify, render_template
import mysql.connector
import os

app = Flask(__name__)

# Database configuration
db_config = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'bookbase_user'),
    'password': os.environ.get('DB_PASSWORD', 'password123'),
    'database': os.environ.get('DB_NAME', 'bookbase_db')
}

def get_db_connection():
    try:
        return mysql.connector.connect(**db_config)
    except mysql.connector.Error as e:
        print(f"Database connection error: {e}")
        return None
# Initialising the Database
def init_database():
    conn = get_db_connection()
    if conn is None:
        return False
        
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            author VARCHAR(255) NOT NULL,
            isbn VARCHAR(20),
            publisher VARCHAR(255),
            year INT,
            genre VARCHAR(100),
            rating INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()
    return True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/books', methods=['GET'])
def get_books():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM books ORDER BY title ASC")
        books = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'books': books,
            'count': len(books)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/books', methods=['POST'])
def add_book():
    try:
        data = request.get_json()
        
        if not data.get('title') or not data.get('author'):
            return jsonify({'success': False, 'error': 'Title and author are required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO books (title, author, isbn, publisher, year, genre, rating)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (
            data['title'].strip(),
            data['author'].strip(),
            data.get('isbn', ''),
            data.get('publisher', ''),
            data.get('year'),
            data.get('genre', ''),
            data.get('rating')
        ))
        
        conn.commit()
        book_id = cursor.lastrowid
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Book added successfully',
            'book_id': book_id
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM books WHERE id = %s', (book_id,))
        
        if cursor.rowcount == 0:
            return jsonify({'success': False, 'error': 'Book not found'}), 404
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Book deleted successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    init_database()
    app.run(host='0.0.0.0', port=port, debug=False)
