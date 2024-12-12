import logging
import os
import uuid
from enum import Enum

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SenderType(Enum):
    CUSTOMER = "customer"
    SYSTEM = "system"


class DatabaseManager:
    _session_factory = None

    allowed_custom_field_sql_types = {"VARCHAR(255)", "INT", "BOOLEAN", "DATE", "MEDIUMTEXT"}

    def __init__(self):
        logger.debug("Initializing DatabaseManager")
        if DatabaseManager._session_factory is None:
            self._initialize_session_factory()

    def _initialize_session_factory(self):
        logger.debug("Initializing session factory")
        db_config = {
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'host': os.getenv('DB_HOST'),
            'pool_size': int(os.getenv('DB_POOL_SIZE', 200)),
            'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', 100)),
            'pool_timeout': int(os.getenv('DB_POOL_TIMEOUT', 10)),
            'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', 3600))
        }

        # Log the user and host information (but not the password)
        logger.info(f"Connecting to database as user: {db_config['user']} on host: {db_config['host']}")

        engine = create_engine(
            f"mysql+mysqlconnector://{db_config['user']}:{db_config['password']}@{db_config['host']}",
            pool_size=db_config['pool_size'],
            max_overflow=db_config['max_overflow'],
            pool_timeout=db_config['pool_timeout'],
            pool_recycle=db_config['pool_recycle']
        )

        DatabaseManager._session_factory = sessionmaker(bind=engine)
        logger.info("Session factory initialized")

    @staticmethod
    def get_customer_db(customer_guid):
        logger.debug(f"Getting database name for customer GUID: {customer_guid}")
        return 'customer_' + customer_guid

    def add_customer(self):
        logger.debug("Entering add_customer method")
        customer_guid = str(uuid.uuid4())
        customer_db_name = self.get_customer_db(customer_guid)

        session = DatabaseManager._session_factory()
        try:
            logger.debug(f"Creating database: {customer_db_name}")
            create_db_query = f"CREATE DATABASE `{customer_db_name}`"
            session.execute(text(create_db_query))

            logger.debug(f"Switching to database: {customer_db_name}")
            use_db_query = f"USE `{customer_db_name}`"
            session.execute(text(use_db_query))

            # Creating chat_messages table if not exists
            create_chat_messages_table_query = """
            CREATE TABLE chat_messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                chat_id VARCHAR(255) NOT NULL,
                customer_guid VARCHAR(255) NOT NULL,
                message MEDIUMTEXT NOT NULL,
                sender_type ENUM('customer', 'system') NOT NULL,
                timestamp TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6)
            );
            """
            session.execute(text(create_chat_messages_table_query))

            # Creating tickets table if not exists
            create_tickets_table_query = """
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id BIGINT AUTO_INCREMENT PRIMARY KEY,
                chat_id VARCHAR(255) NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                priority ENUM('Low', 'Medium', 'High') DEFAULT 'Medium',
                status VARCHAR(50) DEFAULT 'open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            );
            """
            session.execute(text(create_tickets_table_query))

            # Creating custom_fields table if not exists
            create_custom_fields_table_query = """
            CREATE TABLE IF NOT EXISTS custom_fields (
                field_name VARCHAR(255) PRIMARY KEY,
                field_type VARCHAR(255) NOT NULL,
                required BOOLEAN DEFAULT FALSE
            );
            """
            session.execute(text(create_custom_fields_table_query))

            # Creating ticket_field_values table if not exists
            create_custom_field_values_table_query = """
            CREATE TABLE IF NOT EXISTS custom_field_values ( 
                ticket_id BIGINT PRIMARY KEY, 
                FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE 
                -- Custom fields will be added here dynamically as columns 
            );
            """
            session.execute(text(create_custom_field_values_table_query))

            session.commit()

            logger.info(f"Customer added with GUID: {customer_guid}")
            return customer_guid

        except SQLAlchemyError as e:
            logger.error(f"Error adding customer: {e}")
            session.rollback()
            return None
        finally:
            logger.debug("Exiting add_customer method")
            session.close()

    def add_message(self, customer_guid, message, sender_type, chat_id=None):
        logger.debug("Entering add_message method")
        customer_db_name = self.get_customer_db(customer_guid)
        session = DatabaseManager._session_factory()

        try:
            # Check if the customer database exists
            logger.debug(f"Checking existence of database: {customer_db_name}")
            check_db_query = f"SHOW DATABASES LIKE '{customer_db_name}'"
            db_exists = session.execute(text(check_db_query)).fetchone()

            if not db_exists:
                logger.info(f"Database for customer_guid {customer_guid} does not exist.")
                return {"error": "customer_guid is not valid"}

            # Switch to the customer database
            use_db_query = f"USE `{customer_db_name}`"
            session.execute(text(use_db_query))

            # If chat_id is provided, check if it exists in the database
            if chat_id:
                logger.debug(f"Checking existence of chat ID: {chat_id}")
                check_chat_id_query = "SELECT 1 FROM chat_messages WHERE chat_id = :chat_id LIMIT 1"
                result = session.execute(text(check_chat_id_query), {'chat_id': chat_id}).fetchone()

                if not result:
                    logger.info(f"Chat ID: {chat_id} not found.")
                    return {"error": "chat_id is not valid"}
            else:
                chat_id = str(uuid.uuid4())
                logger.debug("Generated new chat ID")

            # Insert the message into the chat_messages table
            logger.debug(f"Inserting message into chat ID: {chat_id}")
            insert_message_query = """
            INSERT INTO chat_messages (chat_id, customer_guid, message, sender_type)
            VALUES (:chat_id, :customer_guid, :message, :sender_type)
            """
            session.execute(text(insert_message_query), {
                'chat_id': chat_id, 'customer_guid': customer_guid, 'message': message, 'sender_type': sender_type.value
            })
            session.commit()
            logger.info(f"Message added for chat ID: {chat_id} by {sender_type.value}")

            # Return success response in dict format
            return {"success": True, "chat_id": chat_id, "customer_guid": customer_guid}

        except SQLAlchemyError as e:
            logger.error(f"Error adding message: {e}")
            session.rollback()
            return {"error": "An error occurred while processing the request"}

        finally:
            logger.debug("Exiting add_message method")
            session.close()

    def get_paginated_chat_messages(self, customer_guid, chat_id, page=1, page_size=10):
        logger.debug("Entering get_paginated_chat_messages method")
        customer_db_name = self.get_customer_db(customer_guid)
        session = DatabaseManager._session_factory()
        try:
            logger.debug(f"Switching to customer database: {customer_db_name}")
            use_db_query = f"USE `{customer_db_name}`"
            session.execute(text(use_db_query))

            offset = (page - 1) * page_size
            logger.debug(f"Fetching messages with pagination: page={page}, page_size={page_size}, offset={offset}")
            select_messages_query = f"""
            SELECT * FROM chat_messages
            WHERE chat_id = :chat_id
            ORDER BY timestamp DESC
            LIMIT :page_size OFFSET :offset
            """
            result = session.execute(text(select_messages_query),
                                     {'chat_id': chat_id, 'page_size': page_size, 'offset': offset})

            messages = result.fetchall()
            messages_list = [{'chat_id': msg.chat_id, 'customer_guid': msg.customer_guid, 'message': msg.message,
                              'sender_type': msg.sender_type, 'timestamp': msg.timestamp} for msg in messages]

            logger.info(f"Retrieved {len(messages_list)} messages for chat ID: {chat_id}")
            return messages_list

        except SQLAlchemyError as e:
            logger.error(f"Error retrieving chat messages: {e}")
            return []
        finally:
            logger.debug("Exiting get_paginated_chat_messages method")
            session.close()

    def delete_chat_messages(self, customer_guid, chat_id):
        logger.debug("Entering delete_chat_messages method")
        customer_db_name = self.get_customer_db(customer_guid)

        session = DatabaseManager._session_factory()
        try:
            logger.debug(f"Switching to customer database: {customer_db_name}")
            use_db_query = f"USE `{customer_db_name}`"
            session.execute(text(use_db_query))

            logger.debug(f"Deleting messages for chat ID: {chat_id}")
            delete_messages_query = """
            DELETE FROM chat_messages
            WHERE chat_id = :chat_id
            """
            session.execute(text(delete_messages_query), {'chat_id': chat_id})
            session.commit()

            logger.info(f"Deleted all messages for chat ID: {chat_id}")
            return True

        except SQLAlchemyError as e:
            logger.error(f"Error deleting messages for chat ID {chat_id}: {e}")
            session.rollback()
            return False

        finally:
            logger.debug("Exiting delete_chat_messages method")
            session.close()

    def delete_customer_database(self, customer_guid):
        logger.debug("Entering delete_customer_database method")
        customer_db_name = self.get_customer_db(customer_guid)

        session = DatabaseManager._session_factory()
        try:
            logger.debug(f"Dropping database: {customer_db_name}")
            drop_db_query = f"DROP DATABASE `{customer_db_name}`"
            session.execute(text(drop_db_query))
            session.commit()

            logger.info(f"Deleted database for customer with GUID: {customer_guid}")

        except SQLAlchemyError as e:
            logger.error(f"Error deleting database for customer {customer_guid}: {e}")
            session.rollback()
            return None
        finally:
            logger.debug("Exiting delete_customer_database method")
            session.close()

    def check_customer_guid_exists(self, customer_guid):
        logger.debug(f"Checking if customer GUID exists: {customer_guid}")
        session = DatabaseManager._session_factory()

        try:
            customer_db_name = self.get_customer_db(customer_guid)
            logger.debug(f"Generated customer database name: {customer_db_name}")

            check_db_query = f"SHOW DATABASES LIKE '{customer_db_name}'"
            db_exists = session.execute(text(check_db_query)).fetchone()

            if db_exists:
                logger.info(f"Customer GUID {customer_guid} exists.")
                return True
            else:
                logger.info(f"Customer GUID {customer_guid} does not exist.")
                return False
        except SQLAlchemyError as e:
            logger.error(f"Error checking if customer GUID exists: {e}")
            raise RuntimeError(f"Failed to verify the existence of customer GUID '{customer_guid}'.") from e
        finally:
            session.close()

    #Custom Fields Related Functions
    def add_custom_field(self, customer_guid, field_name, field_type, required):
        customer_db_name = self.get_customer_db(customer_guid)
        session = DatabaseManager._session_factory()

        # Validate the field type
        if field_type not in self.allowed_custom_field_sql_types:
            raise ValueError(f"Unsupported field type: {field_type}. Allowed types are: {', '.join(self.allowed_custom_field_sql_types)}")

        try:
            logger.debug(f"Switching to customer database: {customer_db_name}")
            session.execute(text(f"USE `{customer_db_name}`"))

            # Add metadata to custom_fields table
            query = '''INSERT INTO custom_fields (field_name, field_type, required)
                       VALUES (:field_name, :field_type, :required)'''
            session.execute(
                text(query),
                {
                    "field_name": field_name,
                    "field_type": field_type,
                    "required": required,
                },
            )

            # Dynamically add column to custom_field_values table
            alter_table_query = f"""
            ALTER TABLE custom_field_values
            ADD COLUMN {field_name} {field_type};
            """
            session.execute(text(alter_table_query))

            # Verify if the column was added
            verify_column_query = f"""
            SHOW COLUMNS FROM custom_field_values LIKE '{field_name}';
            """
            result = session.execute(text(verify_column_query)).fetchone()

            if result:
                logger.info(f"Custom field '{field_name}' added successfully as a column in custom_field_values.")
            else:
                logger.error(f"Failed to add column '{field_name}' in custom_field_values.")
                session.rollback()
                raise ValueError(f"Column '{field_name}' was not added successfully.")

            session.commit()
            return True
        except IntegrityError as e:
            logger.error(f"Duplicate field name error: {e}")
            session.rollback()
            raise ValueError("A custom field with this name already exists.")
        except SQLAlchemyError as e:
            logger.error(f"Error adding custom field: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def list_custom_fields(self, customer_guid):
        customer_db_name = self.get_customer_db(customer_guid)
        session = DatabaseManager._session_factory()
        try:
            logger.debug(f"Switching to customer database: {customer_db_name}")
            session.execute(text(f"USE `{customer_db_name}`"))

            query = '''SELECT * FROM custom_fields'''
            results = session.execute(text(query)).fetchall()
            logger.debug(results)

            if results:
                return [
                    {"field_name": result[0] or "Unknown",  # Default if field_name is None
                     "field_type": result[1] or "Unknown",  # Default if field_type is None
                     "required": result[2] if result[2] is not None else False}  # Default if required is None
                    for result in results
                ]
            else:
                # If no results found, log and return an empty list
                logger.info(f"No custom fields found for customer: {customer_guid}")
                return []

        except SQLAlchemyError as e:
            # Log the error and return an empty list or raise an exception
            logger.error(f"Error listing custom fields for customer {customer_guid}: {e}")
            return []  # You could also raise a custom exception here, if needed
        finally:
            session.close()

    def delete_custom_field(self, customer_guid, field_name):
        customer_db_name = self.get_customer_db(customer_guid)
        session = DatabaseManager._session_factory()
        try:
            logger.debug(f"Switching to customer database: {customer_db_name}")
            session.execute(text(f"USE `{customer_db_name}`"))

            # Check if the field exists
            query_check = '''SELECT COUNT(*) FROM custom_fields WHERE field_name = :field_name'''
            result = session.execute(text(query_check), {"field_name": field_name}).scalar()

            if result == 0:
                logger.debug(f"No custom field found with name: {field_name}")
                return {"status": "not_found"}  # Field does not exist

            # Delete the column from custom_field_values table
            logger.debug(f"Dropping column {field_name} from custom_field_values table")
            alter_table_query = f"""ALTER TABLE custom_field_values DROP COLUMN `{field_name}`;"""
            session.execute(text(alter_table_query))

            # Remove the field details from the custom_fields table
            logger.debug(f"Deleting field {field_name} from custom_fields table")
            query_delete = '''DELETE FROM custom_fields WHERE field_name = :field_name'''
            session.execute(text(query_delete), {"field_name": field_name})

            session.commit()
            logger.info(f"Custom field {field_name} deleted successfully")
            return {"status": "deleted"}
        except SQLAlchemyError as e:
            logger.error(f"Error deleting custom field: {e}")
            session.rollback()
            return {"status": "error", "error": str(e)}
        finally:
            session.close()