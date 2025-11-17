import mysql.connector
from mysql.connector import errorcode
import os
from werkzeug.security import generate_password_hash
import security_utils
from dotenv import load_dotenv

# Load database config from .env
load_dotenv()
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")

def get_db_connection():
    """Establishes a connection to the MySQL database."""
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            use_pure=True  # Fix for CMySQLCursor error
        )
        return conn
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
            print(f"(Hint: Check your .env file. User='{DB_USER}', Pass='{DB_PASS}')")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print(f"Database '{DB_NAME}' does not exist")
        else:
            print(err)
        return None

def init_db():
    """Initializes the database using the schema.sql file."""
    conn = get_db_connection()
    if not conn:
        print("Could not connect to database. Exiting.")
        return

    # Use dictionary=True to get results as dicts (like sqlite3.Row)
    cursor = conn.cursor(dictionary=True)
    
    # --- Fix for 'multi=True' error ---
    # Read the schema file
    with open('schema.sql', 'r') as f:
        sql_script = f.read()

    # Split the script into individual statements
    sql_statements = sql_script.split(';')

    try:
        # Execute each statement one by one
        for statement in sql_statements:
            # Skip empty strings that result from splitting
            if statement.strip():
                cursor.execute(statement)  # No 'multi=True'
        
        print("Database schema created.")
    except mysql.connector.Error as err:
        print(f"Failed to execute schema: {err}")
        conn.close()
        return
    # --- End of Fix ---

    # Create a demo user
    try:
        # MySQL uses %s as a placeholder, NOT ?
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
            ("demo_user", generate_password_hash("secure_pass"))
        )
        conn.commit()
        print("Demo_user created.")
    except mysql.connector.Error as err:
        if err.errno == 1062: # Duplicate entry
            print("Database already initialized (demo_user exists).")
        else:
            print(f"Failed to create demo user: {err}")
        
    cursor.close()
    conn.close()

def get_user(username):
    """Gets a user by their username."""
    conn = get_db_connection()
    if not conn:
        return None
        
    cursor = conn.cursor(dictionary=True)
    
    # Use %s for placeholders
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    
    cursor.close()
    conn.close()
    return user

def save_transaction(username, card_number, amount, region, risk_score, status):
    """Saves a transaction record to the database."""
    conn = get_db_connection()
    if not conn:
        print("Failed to save transaction: No DB connection.")
        return

    cursor = conn.cursor(dictionary=True)
    
    # Encrypt the card number before saving
    encrypted_card = security_utils.encrypt_data(card_number)
    
    user = get_user(username)
    if user:
        try:
            # Use %s for placeholders
            cursor.execute(
                """INSERT INTO transactions 
                (user_id, encrypted_card, amount, region, risk_score, status) 
                VALUES (%s, %s, %s, %s, %s, %s)""",
                (user['id'], encrypted_card, amount, region, risk_score, status)
            )
            conn.commit()
            print("Transaction saved to MySQL.")
        except mysql.connector.Error as err:
            print(f"Failed to save transaction: {err}")
    
    cursor.close()
    conn.close()

#
# --- FIX: This function was indented incorrectly. It is now fixed. ---
#
def create_user(username, password_hash):
    """Creates a new user in the database."""
    conn = get_db_connection()
    if not conn:
        print("Failed to create user: No DB connection.")
        return False
        
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
            (username, password_hash)
        )
        conn.commit()
        return True
    except mysql.connector.Error as err:
        if err.errno == 1062: # Duplicate entry for username
            print("Error: Username already exists.")
        else:
            print(f"Failed to create user: {err}")
        return False
    finally:
        cursor.close()
        conn.close()

# If you run this file directly, it will initialize the database
if __name__ == "__main__":
    init_db()