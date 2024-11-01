from flask import Flask, request, jsonify
from datetime import datetime
import mysql.connector
from mysql.connector import Error
import os
import logging

app = Flask(__name__)

# MySQL configuration
host = 'db'  # Use the service name defined in docker-compose.yml
username = 'root'
password = os.getenv('MYSQL_PASSWORD')  # Ensure this matches your MySQL root password
database = 'test_db'

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Function to create a database and tables for each customer
def initialize_customer_database(customer_id: str) -> None:
    try:
        # Create database for each customer
        db = mysql.connector.connect(user=username, password=password, host=host)
        cursor = db.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS customer_{}".format(customer_id))
        db.close()

        # Connect to the new database and create tables
        db = mysql.connector.connect(user=username, password=password, host=host,
                                     database="customer_{}".format(customer_id))
        cursor = db.cursor()

        # Create the chats table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chats (
              chat_id VARCHAR(255) PRIMARY KEY,
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Create the messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
              message_id INT AUTO_INCREMENT PRIMARY KEY,
              chat_id VARCHAR(255),
              question TEXT,
              response TEXT,
              timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY (chat_id) REFERENCES chats(chat_id)
            );
        """)

        db.commit()  # Commit changes to the database
        db.close()

    except Error as e:
        logger.error(f"Error while connecting to MySQL: {e}")


# Helper function to generate responses for the bot
def generate_recommendation(question: str) -> str:
    if "movie" in question.lower():
        return "I recommend 'Inception' or 'The Matrix'."
    elif "tv show" in question.lower():
        return "I recommend 'Breaking Bad' or 'Stranger Things'."
    else:
        return "I'm here to recommend movies or TV shows! Ask me for a recommendation."


# Initialize chats storage as a dictionary for temporary storage
chats = {}

# Endpoint to test database connection
@app.route('/testdb', methods=['GET'])
def test_db_connection():
    try:
        conn = mysql.connector.connect(
            host=host,
            user=username,
            password=password,
            database=database
        )
        if conn.is_connected():
            return jsonify({"message": "Connected to MySQL successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API to add a new customer
@app.route('/customer', methods=['POST'])
def add_customer():
    data = request.json
    customer_id = data.get('customer_id')

    # Validation checks
    if not customer_id:
        return jsonify({"error": "Customer ID is required."}), 400

    initialize_customer_database(customer_id)
    return jsonify({"message": f"Customer with ID {customer_id} added successfully."}), 201


# API to create a new chat
@app.route('/chat', methods=['POST'])
def create_chat():
    data = request.json
    chat_id = data.get('chat_id')
    customer_id = data.get('customer_id')
    question = data.get('question')

    # Validation checks
    if not chat_id or not customer_id or not question:
        return jsonify({"error": "Chat ID, Customer ID, and question are required."}), 400

    # Check if customer ID exists
    try:
        db = mysql.connector.connect(
            user=username,
            password=password,
            host=host
        )
        cursor = db.cursor()
        cursor.execute("SHOW DATABASES LIKE %s", ('customer_' + customer_id,))
        result = cursor.fetchone()
        db.close()

        if not result:
            return jsonify({"error": f"Customer with ID {customer_id} does not exist."}), 404

    except Error as e:
        logger.error(f"Error while connecting to MySQL: {e}")
        return jsonify({"error": "Internal Server Error: Database connection issue"}), 500

    # Initialize chat entry if it doesn't exist
    if chat_id not in chats:
        chats[chat_id] = {"customer_id": customer_id, "conversation": []}

    # Check if question already exists
    for entry in chats[chat_id]["conversation"]:
        if entry["question"] == question:
            return jsonify({"error": "Duplicate question found for this chat."}), 409

    # Generate a response and add to chat log
    response = generate_recommendation(question)
    chats[chat_id]["conversation"].append({
        "timestamp": datetime.now().isoformat(),
        "question": question,
        "response": response
    })

    # Log successful creation of chat
    logger.info(f"Chat created successfully: {chats[chat_id]}")

    return jsonify(
        {"chat_id": chat_id, "customer_id": customer_id, "response_logs": chats[chat_id]["conversation"]}
    ), 201


@app.route('/getallchats', methods=['GET'])
def get_all_chats():
    customer_id = request.args.get('customer_id')
    chat_id = request.args.get('chat_id')

    # Validate chat_id and customer_id presence in `chats`
    if chat_id in chats and (customer_id is None or chats[chat_id]["customer_id"] == customer_id):
        # Retrieve the conversation in latest-to-oldest order
        conversation = list(reversed(chats[chat_id]["conversation"])) if chats[chat_id]["conversation"] else []

        return jsonify({
            "chat_id": chat_id,
            "customer_id": chats[chat_id]["customer_id"],
            "conversation": conversation
        }), 200
    else:
        return jsonify({"error": "Chat ID and Customer ID not found."}), 404


@app.route('/deletechat', methods=['DELETE'])
def delete_chat():
    customer_id = request.args.get('customer_id')
    chat_id = request.args.get('chat_id')

    # Validate and delete chat entry if it exists
    if chat_id in chats and (customer_id is None or chats[chat_id]["customer_id"] == customer_id):
        del chats[chat_id]

        # Delete the chat from the database
        try:
            db = mysql.connector.connect(user=username, password=password, host=host,
                                         database=f"customer_{customer_id}")
            cursor = db.cursor()
            cursor.execute("DELETE FROM chats WHERE chat_id = %s", (chat_id,))
            db.commit()
            db.close()
        except Error as e:
            logger.error(f"Error while deleting chat: {e}")
            return jsonify({"error": "Failed to delete chat."}), 500

        return jsonify({"message": f"Chat with ID {chat_id} deleted successfully."}), 200
    else:
        return jsonify({"error": "Chat ID and Customer ID not found."}), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
