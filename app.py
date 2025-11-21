from flask import Flask, request, jsonify, render_template
import mysql.connector
import csv
import io
import re
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
    """
    Establishes and returns a connection to the MySQL database.
    Returns None if connection fails to allow for error handling.
    """
    try:
        return mysql.connector.connect(**db_config)
    except mysql.connector.Error as e:
        print(f"Database connection error: {e}")
        return None

def init_database():
    """
    Initializes the database by creating the books table if it doesn't exist.
    Returns True if successful, False if database connection fails.
    """
    conn = get_db_connection()
    if conn is None:
        return False
        
    cursor = conn.cursor()
    
    # Create books table with all necessary fields
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            author VARCHAR(255) NOT NULL,
            isbn VARCHAR(20) UNIQUE,
            publisher VARCHAR(255),
            year INT,
            genre VARCHAR(100),
            rating INT CHECK (rating >= 1 AND rating <= 5),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()
    return True

def validate_book_data(data):
    """
    Validates book data before insertion or update.
    Checks for required fields, valid ISBN format, publication year, and rating.
    Returns list of error messages if validation fails.
    """
    errors = []
    
    if not data.get('title') or not data['title'].strip():
        errors.append("Title is required")
    
    if not data.get('author') or not data['author'].strip():
        errors.append("Author is required")
    
    isbn = data.get('isbn', '')
    if isbn and not re.match(r'^\d{10}(\d{3})?$', isbn.replace('-', '')):
        errors.append("Invalid ISBN format. Must be 10 or 13 digits")
    
    year = data.get('year')
    if year and (not year.isdigit() or int(year) < 1000 or int(year) > 2030):
        errors.append("Invalid publication year")
    
    rating = data.get('rating')
    if rating and (not rating.isdigit() or int(rating) < 1 or int(rating) > 5):
        errors.append("Rating must be between 1 and 5 stars")
    
    return errors

def is_duplicate_isbn(isbn):
    """
    Checks if a book with the given ISBN already exists in the database.
    Returns the existing book data if duplicate found, otherwise False.
    """
    if not isbn:
        return False
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, author FROM books WHERE isbn = %s", (isbn,))
    existing_book = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return existing_book

def build_search_query(filters):
    """
    Builds a dynamic SQL query based on provided filters.
    Supports search by title/author, genre filtering, year range, and rating.
    Returns the SQL query and parameters for safe execution.
    """
    query = "SELECT * FROM books WHERE 1=1"
    params = []
    if filters.get('search'):
        query += " AND (title LIKE %s OR author LIKE %s)"
        search_term = f"%{filters['search']}%"
        params.extend([search_term, search_term])
    
    if filters.get('genre'):
        query += " AND genre = %s"
        params.append(filters['genre'])
    
    if filters.get('author'):
        query += " AND author LIKE %s"
        params.append(f"%{filters['author']}%")
    
    if filters.get('year_min'):
        query += " AND year >= %s"
        params.append(filters['year_min'])
    
    if filters.get('year_max'):
        query += " AND year <= %s"
        params.append(filters['year_max'])
    
    if filters.get('rating_min'):
        query += " AND rating >= %s"
        params.append(filters['rating_min'])
    
    # Sorting functionality
    sort_by = filters.get('sort_by', 'title')
    sort_order = filters.get('sort_order', 'ASC')
    valid_sort_columns = ['title', 'author', 'year', 'rating', 'genre']
    
    if sort_by in valid_sort_columns:
        query += f" ORDER BY {sort_by} {sort_order}"
    return query, params

@app.route('/')
def index():
    """
    Serves the main application interface.
    Returns the HTML template for the BookBase frontend.
    """
    return render_template('index.html')

@app.route('/api/books', methods=['GET'])
def get_books():
    """
    Enhanced book retrieval with advanced filtering and search capabilities.
    Supports multiple filter criteria and sorting options.
    Returns paginated and filtered book results.
    """
    try:
        filters = {
            'search': request.args.get('search', ''),
            'genre': request.args.get('genre', ''),
            'author': request.args.get('author', ''),
            'year_min': request.args.get('year_min', ''),
            'year_max': request.args.get('year_max', ''),
            'rating_min': request.args.get('rating_min', ''),
            'sort_by': request.args.get('sort_by', 'title'),
            'sort_order': request.args.get('sort_order', 'ASC')
        }
        
        query, params = build_search_query(filters)
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
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
    """
    Enhanced book addition with comprehensive data validation.
    Validates all fields and checks for duplicate ISBNs.
    Returns detailed error messages for validation failures.
    """
    try:
        data = request.get_json()
        
        # Validate book data using comprehensive validation function
        errors = validate_book_data(data)
        if errors:
            return jsonify({'success': False, 'errors': errors}), 400
        
        # Check for duplicate ISBN to maintain data integrity
        if data.get('isbn'):
            duplicate = is_duplicate_isbn(data['isbn'])
            if duplicate:
                return jsonify({
                    'success': False, 
                    'error': f'Duplicate ISBN: Book "{duplicate[1]}" by {duplicate[2]} already exists with this ISBN'
                }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO books (title, author, isbn, publisher, year, genre, rating)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (
            data['title'].strip(),
            data['author'].strip(),
            data.get('isbn', '').strip(),
            data.get('publisher', '').strip(),
            data.get('year'),
            data.get('genre', '').strip(),
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

@app.route('/api/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    """
    Updates an existing book's information.
    Validates input data and ensures book exists before updating.
    Returns appropriate success or error messages.
    """
    try:
        data = request.get_json()
        
        # Validate book data using the same validation function
        errors = validate_book_data(data)
        if errors:
            return jsonify({'success': False, 'errors': errors}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE books 
            SET title=%s, author=%s, isbn=%s, publisher=%s, year=%s, genre=%s, rating=%s
            WHERE id=%s
        ''', (
            data['title'].strip(),
            data['author'].strip(),
            data.get('isbn', '').strip(),
            data.get('publisher', '').strip(),
            data.get('year'),
            data.get('genre', '').strip(),
            data.get('rating'),
            book_id
        ))
        
        if cursor.rowcount == 0:
            return jsonify({'success': False, 'error': 'Book not found'}), 404
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Book updated successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    """
    Deletes a book from the database by ID.
    Returns success message or error if book not found.
    """
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

@app.route('/api/books/import-csv', methods=['POST'])
def import_csv():
    """
    Handles bulk import of books from CSV files.
    Validates each row, checks for duplicates, and provides detailed import report.
    Supports error handling for malformed data and duplicate entries.
    """
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'error': 'File must be a CSV'}), 400
        
        # Read and parse CSV file
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        required_fields = ['title', 'author']
        imported_books = []
        errors = []
        duplicates = []
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Process each row in the CSV file
        for row_num, row in enumerate(csv_reader, start=2):  # start=2 to account for header
            # Validate required fields are present
            missing_fields = [field for field in required_fields if not row.get(field)]
            if missing_fields:
                errors.append(f"Row {row_num}: Missing required fields: {', '.join(missing_fields)}")
                continue
            
            # Validate data format and constraints
            validation_errors = validate_book_data(row)
            if validation_errors:
                errors.append(f"Row {row_num}: {', '.join(validation_errors)}")
                continue
            
            # Check for duplicate ISBN to maintain data integrity
            if row.get('isbn'):
                duplicate = is_duplicate_isbn(row['isbn'])
                if duplicate:
                    duplicates.append(f"Row {row_num}: ISBN {row['isbn']} already exists for '{duplicate[1]}'")
                    continue
            
            try:
                # Insert valid book record
                cursor.execute('''
                    INSERT INTO books (title, author, isbn, publisher, year, genre, rating)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (
                    row['title'].strip(),
                    row['author'].strip(),
                    row.get('isbn', '').strip(),
                    row.get('publisher', '').strip(),
                    row.get('year'),
                    row.get('genre', '').strip(),
                    row.get('rating')
                ))
                imported_books.append(row['title'])
                
            except Exception as e:
                errors.append(f"Row {row_num}: Database error - {str(e)}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Return comprehensive import report
        return jsonify({
            'success': True,
            'imported_count': len(imported_books),
            'imported_titles': imported_books,
            'errors': errors,
            'duplicates': duplicates
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/books/export-csv', methods=['GET'])
def export_csv():
    """
    Exports books data to CSV format with filtering support.
    Allows users to download their library data for backup or external use.
    Returns CSV file with all book information.
    """
    try:
        # Apply same filters as search functionality
        filters = {
            'search': request.args.get('search', ''),
            'genre': request.args.get('genre', ''),
            'author': request.args.get('author', ''),
            'year_min': request.args.get('year_min', ''),
            'year_max': request.args.get('year_max', ''),
            'rating_min': request.args.get('rating_min', '')
        }
        
        query, params = build_search_query(filters)
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        books = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Create CSV file in memory
        output = io.StringIO()
        fieldnames = ['title', 'author', 'isbn', 'publisher', 'year', 'genre', 'rating']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        
        writer.writeheader()
        for book in books:
            writer.writerow({
                'title': book['title'],
                'author': book['author'],
                'isbn': book['isbn'] or '',
                'publisher': book['publisher'] or '',
                'year': book['year'] or '',
                'genre': book['genre'] or '',
                'rating': book['rating'] or ''
            })
        
        response = output.getvalue()
        output.close()
        
        # Return CSV file as downloadable attachment
        return response, 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment; filename=bookbase_export.csv'
        }
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health')
def health_check():
    """
    Health check endpoint for deployment monitoring.
    Returns application status and database connectivity information.
    """
    try:
        conn = get_db_connection()
        if conn and conn.is_connected():
            conn.close()
            return jsonify({'status': 'healthy', 'database': 'connected'})
        else:
            return jsonify({'status': 'unhealthy', 'database': 'disconnected'}), 500
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

if __name__ == '__main__':
    """
    Main application entry point.
    Initializes database and starts the Flask application server.
    Configures for production deployment with environment variables.
    """
    print(" Initializing BookBase Application...")
    if init_database():
        port = int(os.environ.get('PORT', 5000))
        print(f" BookBase is running on http://0.0.0.0:{port}")
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        print(" Failed to initialize database. Please check your database connection.")
