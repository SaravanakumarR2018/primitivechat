import logging
import os
import uuid
from enum import Enum

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError, DatabaseError
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
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', 'admin123'),
            'host': os.getenv('DB_HOST', '127.0.0.1'),
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
                timestamp TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6),
                INDEX (chat_id)
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
                reported_by VARCHAR(255),
                assigned VARCHAR(255),
                ticket_uuid VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (chat_id) REFERENCES chat_messages(chat_id) ON DELETE CASCADE
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

            # Creating ticket_comments table if not exists
            create_ticket_comments_table_query = """
            CREATE TABLE IF NOT EXISTS ticket_comments (
                comment_id BIGINT AUTO_INCREMENT PRIMARY KEY,
                ticket_id BIGINT NOT NULL,
                posted_by VARCHAR(255) NOT NULL,
                comment TEXT NOT NULL,
                is_edited BOOLEAN DEFAULT FALSE,
                comment_uuid VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE
            );
            """
            session.execute(text(create_ticket_comments_table_query))

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


    # Tickets related function
    def create_ticket(self, customer_guid, chat_id, title, description, priority, reported_by, assigned, custom_fields):
        customer_db_name = self.get_customer_db(customer_guid)
        session = DatabaseManager._session_factory()

        try:
            try:
                # Check if the database exists
                logger.debug(f"Checking if database {customer_db_name} exists")
                result = session.execute(
                    text("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = :db_name"),
                    {"db_name": customer_db_name}
                ).fetchone()
            except OperationalError as e:
                logger.error(f"Database connectivity issue during schema check: {e}")
                raise e

            if not result:
                raise ValueError(f"Database {customer_db_name} does not exist")

            # Switch to the customer database
            logger.debug(f"Switching to customer database: {customer_db_name}")
            session.execute(text(f"USE `{customer_db_name}`"))

            # Check if the chat_id exists in the chat_messages table
            chat_exists = session.execute(
                text("SELECT 1 FROM chat_messages WHERE chat_id = :chat_id LIMIT 1"),
                {"chat_id": chat_id}
            ).fetchone()

            if not chat_exists:
                raise ValueError(f"Invalid chat_id: {chat_id} does not exist.")

            # Validate custom fields against the database columns
            if custom_fields:
                # Fetch the valid column names from the custom_field_values table
                result = session.execute("SHOW COLUMNS FROM custom_field_values").fetchall()
                valid_columns = {row[0] for row in result}

                # Check for invalid fields
                invalid_fields = [field for field in custom_fields.keys() if field not in valid_columns]
                if invalid_fields:
                    raise ValueError(f"Invalid custom field(s): {', '.join(invalid_fields)}")

            # Begin transaction
            with session.begin_nested():
                # Insert into tickets table
                ticket_uuid = str(uuid.uuid4())

                query = '''INSERT INTO tickets (chat_id, title, description, priority, reported_by, assigned, ticket_uuid)
                           VALUES (:chat_id, :title, :description, :priority, :reported_by, :assigned, :ticket_uuid)'''
                session.execute(
                    text(query),
                    {
                        "chat_id": chat_id,
                        "title": title,
                        "description": description,
                        "priority": priority,
                        "reported_by":reported_by,
                        "assigned":assigned,
                        "ticket_uuid":ticket_uuid
                    },
                )
                logger.debug(f"ticket uuid {ticket_uuid}")
                # Fetch the generated ticket_id
                result = session.execute(
                    text("""
                        SELECT ticket_id 
                        FROM tickets 
                        WHERE ticket_uuid= :ticket_uuid
                    """),
                    {"ticket_uuid": ticket_uuid}
                ).fetchone()

                if result:
                    ticket_id = result[0]
                    logger.debug(f"Created ticket with ID: {ticket_id}")
                else:
                    raise Exception("Failed to retrieve the newly created ticket ID.")

                # Insert into custom_field_values if there are valid custom fields
                if custom_fields:
                    columns = ', '.join([f"`{field}`" for field in custom_fields.keys()])
                    placeholders = ', '.join([f":{field}" for field in custom_fields.keys()])

                    query_for_insert_custom_fields = f'''
                        INSERT INTO custom_field_values (ticket_id, {columns}) 
                        VALUES (:ticket_id, {placeholders})
                    '''
                    params = {"ticket_id": ticket_id}
                    params.update(custom_fields)

                    logger.debug(f"Inserting custom fields: {custom_fields}")
                    session.execute(text(query_for_insert_custom_fields), params)

            session.commit()
            logger.debug(f"Ticket ID {ticket_id} created successfully with custom fields")

            return {"ticket_id": ticket_id, "status": "created"}

        except ValueError as e:
            logger.error(f"Validation error: {e}")
            session.rollback()
            raise e  # Propagate the ValueError to the calling function

        except SQLAlchemyError as e:
            logger.error(f"Database error creating ticket for customer {customer_guid}: {e}")
            session.rollback()
            raise e  # Propagate the SQLAlchemyError to the calling function
        except OperationalError as e:
            logger.error(f"Database connectivity issue: {e}")
            raise e
        except DatabaseError as e:
            logger.error(f"Database connectivity issue: {e}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected error while creating ticket: {e}")
            session.rollback()
            raise e  # Propagate the general exception to the calling function

        finally:
            session.close()

    def get_ticket_by_id(self, ticket_id, customer_guid):
        customer_db_name = self.get_customer_db(customer_guid)
        session = DatabaseManager._session_factory()
        try:
            # Check if the database exists
            logger.debug(f"Checking if database {customer_db_name} exists")
            result = session.execute(
                text("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = :db_name"),
                {"db_name": customer_db_name}
            ).fetchone()

            if not result:
                raise ValueError(f"Database {customer_db_name} does not exist")

            logger.debug(f"Switching to customer database: {customer_db_name}")
            session.execute(text(f"USE `{customer_db_name}`"))

            # Retrieve ticket base details
            ticket_query = '''
                SELECT ticket_id, chat_id, title, description, priority, status, reported_by, assigned
                FROM tickets
                WHERE ticket_id = :ticket_id
            '''
            ticket_result = session.execute(
                text(ticket_query),
                {"ticket_id": ticket_id},
            ).fetchone()

            if not ticket_result:
                return None  # If ticket is not found, return None

            # Convert ticket result into a dictionary and filter specific fields
            logger.info(f"tickets by ticket id {ticket_result}")
            ticket_data = {
                column: value
                for column, value in zip(ticket_result.keys(), ticket_result)
                if column in ("ticket_id", "chat_id", "title", "description", "priority", "status", "reported_by", "assigned")
            }
            ticket_data["custom_fields"] = {}

            # Retrieve custom field values for the ticket
            custom_field_query = '''
                SELECT * 
                FROM custom_field_values
                WHERE ticket_id = :ticket_id
            '''
            custom_field_result = session.execute(
                text(custom_field_query),
                {"ticket_id": ticket_id},
            ).fetchone()

            if custom_field_result:
                ticket_data["custom_fields"] = {
                    column: value
                    for column, value in zip(custom_field_result.keys(), custom_field_result)
                    if column != "ticket_id" and value is not None
                }

            return ticket_data

        except (OperationalError, DatabaseError) as e:
            logger.error(f"Database error: {e}")
            raise Exception("Database connectivity issue")
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy error: {e}")
            raise Exception("Database query error")
        finally:
            session.close()

    def get_tickets_by_chat_id(self, customer_guid, chat_id):
        customer_db_name = self.get_customer_db(customer_guid)
        try:
            session = DatabaseManager._session_factory()
            # Add retry logic here for connection
        except OperationalError as e:
            logger.error(f"Database connection failed: {e}")
            return {"status": "db_unreachable", "reason": "Database is currently unreachable"}
        try:
                # Check if the database exists
            logger.debug(f"Checking if database {customer_db_name} exists")
            result = session.execute(
                text("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = :db_name"),
                {"db_name": customer_db_name}
            ).fetchone()
            if not result:
                raise ValueError(f"Database {customer_db_name} does not exist")

            logger.debug(f"Switching to customer database: {customer_db_name}")
            session.execute(text(f"USE `{customer_db_name}`"))

            # Check if the chat_id exists in the chat_messages table
            chat_exists = session.execute(
                    text("SELECT 1 FROM chat_messages WHERE chat_id = :chat_id LIMIT 1"),
                    {"chat_id": chat_id}
            ).fetchone()

            if not chat_exists:
                raise ValueError(f"Invalid chat_id: {chat_id} does not exist.")

            query = '''SELECT ticket_id, chat_id, title, description, priority, status
                FROM tickets WHERE chat_id = :chat_id'''
            results = session.execute(
                text(query),
                {"chat_id": chat_id},
            ).fetchall()
            logger.info(f"get by chat_id {results}")
            return [
                {column: value for column, value in zip(row.keys(), row) if column in ("ticket_id", "title", "status")}
                for row in results
            ]
        except (OperationalError, DatabaseError) as e:
            logger.error(f"Database error: {e}")
            raise Exception("Database connectivity issue")
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving tickets: {e}")
            return []
        finally:
            session.close()

    def update_ticket(self, ticket_id, customer_guid, ticket_update):
        customer_db_name = self.get_customer_db(customer_guid)

        try:
            session = DatabaseManager._session_factory()
            # Add retry logic here for connection
        except OperationalError as e:
            logger.error(f"Database connection failed: {e}")
            return {"status": "db_unreachable", "reason": "Database is currently unreachable"}

        try:
            # Check if the database exists
            logger.debug(f"Checking if database {customer_db_name} exists")
            try:
                result = session.execute(
                    text("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = :db_name"),
                    {"db_name": customer_db_name}
                ).fetchone()
            except OperationalError as e:
                logger.error(f"Database connectivity issue during schema check: {e}")
                return {"status": "db_unreachable", "reason": "Database is currently unreachable"}
            except DatabaseError as e:
                logger.error(f"Database connectivity issue during schema check: {e}")
                return {"status": "db_unreachable", "reason": "Database is currently unreachable"}

            if not result:
                return {"status": "unknown_db", "reason": f"Database {customer_db_name} does not exist"}

            logger.debug(f"Switching to customer database: {customer_db_name}")
            session.execute(text(f"USE `{customer_db_name}`"))

            # Check if the ticket exists
            result = session.execute(
                text("SELECT COUNT(*) FROM tickets WHERE ticket_id = :ticket_id"),
                {"ticket_id": ticket_id},
            ).fetchone()

            if result[0] == 0:
                return {"status": "not_found", "reason": f"Ticket ID {ticket_id} not found."}

            # Validate and update ticket fields
            ticket_fields = {
                k: v for k, v in ticket_update.dict().items()
                if k != "custom_fields" and v is not None
            }
            if ticket_fields:
                try:
                    set_clauses = [f"{column} = :{column}" for column in ticket_fields.keys()]
                    query = f"UPDATE tickets SET {', '.join(set_clauses)} WHERE ticket_id = :ticket_id"
                    ticket_fields["ticket_id"] = ticket_id
                    session.execute(text(query), ticket_fields)
                except SQLAlchemyError as e:
                    logger.error(f"Error updating ticket fields: {e}")
                    session.rollback()
                    return {
                        "status": "bad_request",
                        "reason": f"Invalid data provided for ticket fields. {str(e)}"
                    }

            # Validate and update custom fields
            if ticket_update.custom_fields:
                try:
                    custom_fields = ticket_update.custom_fields
                    column_values = ", ".join([f"`{col}` = :{col}" for col in custom_fields.keys()])
                    query = f'''
                        INSERT INTO custom_field_values (ticket_id, {", ".join(custom_fields.keys())})
                        VALUES (:ticket_id, {", ".join([f":{col}" for col in custom_fields.keys()])})
                        ON DUPLICATE KEY UPDATE {column_values}
                    '''
                    custom_fields["ticket_id"] = ticket_id
                    session.execute(text(query), custom_fields)
                except SQLAlchemyError as e:
                    logger.error(f"Error updating custom fields: {e}")
                    session.rollback()
                    return {
                        "status": "conflict",
                        "reason": f"Invalid custom fields provided: {str(e)}"
                    }

            session.commit()
            return {"status": "updated", "reason": None}

        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}")
            session.rollback()
            return {"status": "failure", "reason": f"Unknown database customer_{customer_guid}"}
        except OperationalError as e:
            logger.error(f"Database connectivity issue: {e}")
            return {"status": "db_unreachable", "reason": "Database is currently unreachable"}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            session.rollback()
            return {"status": "failure", "reason": "Unexpected error occurred during ticket update."}

        finally:
            session.close()

    def delete_ticket(self, ticket_id, customer_guid):
        customer_db_name = self.get_customer_db(customer_guid)

        try:
            session = DatabaseManager._session_factory()
            # Add retry logic here for connection
        except OperationalError as e:
            logger.error(f"Database connection failed: {e}")
            return {"status": "db_unreachable", "reason": "Database is currently unreachable"}

        try:
            # Check if the database exists
            logger.debug(f"Checking if database {customer_db_name} exists")
            try:
                result = session.execute(
                    text("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = :db_name"),
                    {"db_name": customer_db_name}
                ).fetchone()
            except OperationalError as e:
                logger.error(f"Database connectivity issue during schema check: {e}")
                return {"status": "db_unreachable", "reason": "Database is currently unreachable"}

            if not result:
                return {"status": "unknown_db", "reason": f"Database {customer_db_name} does not exist"}

            logger.debug(f"Switching to customer database: {customer_db_name}")
            try:
                session.execute(text(f"USE `{customer_db_name}`"))
            except OperationalError as e:
                logger.error(f"Database connectivity issue during USE statement: {e}")
                return {"status": "db_unreachable", "reason": "Database is currently unreachable"}

            # Check if the ticket exists
            try:
                result = session.execute(
                    text("SELECT COUNT(*) FROM tickets WHERE ticket_id = :ticket_id"),
                    {"ticket_id": ticket_id},
                ).fetchone()
            except OperationalError as e:
                logger.error(f"Database connectivity issue during ticket existence check: {e}")
                return {"status": "db_unreachable", "reason": "Database is currently unreachable"}

            if result[0] == 0:  # Ticket not found
                return {"status": "not_found"}

            # Attempt to delete custom fields
            try:
                delete_custom_fields_query = '''
                    DELETE FROM custom_field_values WHERE ticket_id = :ticket_id
                '''
                session.execute(
                    text(delete_custom_fields_query),
                    {"ticket_id": ticket_id},
                )
            except SQLAlchemyError as e:
                logger.error(f"Dependency error while deleting custom fields: {e}")
                session.rollback()
                return {"status": "dependency_error", "reason": str(e)}

            # Attempt to delete the ticket
            try:
                delete_ticket_query = '''DELETE FROM tickets WHERE ticket_id = :ticket_id'''
                session.execute(
                    text(delete_ticket_query),
                    {"ticket_id": ticket_id},
                )
                session.commit()
                return {"status": "deleted"}
            except SQLAlchemyError as e:
                logger.error(f"Error deleting ticket: {e}")
                session.rollback()
                return {"status": "failure", "reason": str(e)}

        except OperationalError as e:  # Handle database connectivity issues
            logger.error(f"Database connectivity issue: {e}")
            return {"status": "db_unreachable", "reason": "Database is currently unreachable"}
        except DatabaseError as e:
            logger.error(f"Database connectivity issue: {e}")
            return {"status": "db_unreachable", "reason": "Database is currently unreachable"}
        except Exception as e:
            logger.error(f"Unexpected error during deletion: {e}")
            session.rollback()
            return {"status": "failure", "reason": "Unexpected error occurred"}

        finally:
            session.close()


    #Comments related methods
    def create_comment(self, customer_guid, ticket_id, posted_by, comment):
        logger.debug("Starting create_comment method")
        customer_db_name = self.get_customer_db(customer_guid)
        logger.debug(f"Resolved customer_db_name: {customer_db_name}")
        session = DatabaseManager._session_factory()

        try:
            # Check if the database exists
            logger.debug(f"Checking if database {customer_db_name} exists")
            result = session.execute(
                text("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = :db_name"),
                {"db_name": customer_db_name}
            ).fetchone()

            logger.debug(f"Database existence check result: {result}")
            if not result:
                raise ValueError(f"Database {customer_db_name} does not exist")

            # Switch to the customer database
            logger.debug(f"Switching to customer database: {customer_db_name}")
            session.execute(text(f"USE `{customer_db_name}`"))

            # Check if the ticket_id exists in the tickets table
            logger.debug(f"Checking existence of ticket_id: {ticket_id}")
            ticket_exists = session.execute(
                text("SELECT 1 FROM tickets WHERE ticket_id = :ticket_id LIMIT 1"),
                {"ticket_id": ticket_id}
            ).fetchone()

            logger.debug(f"Ticket existence check result: {ticket_exists}")
            if not ticket_exists:
                raise ValueError(f"Invalid ticket_id: {ticket_id} does not exist.")

            # Begin transaction
            logger.debug("Starting transaction for comment creation")
            with session.begin_nested():
                comment_uuid=str(uuid.uuid4())
                # Insert into ticket_comments table
                query = '''INSERT INTO ticket_comments (ticket_id, posted_by, comment, comment_uuid)
                           VALUES (:ticket_id, :posted_by, :comment, :comment_uuid)'''
                session.execute(
                    text(query),
                    {
                        "ticket_id": ticket_id,
                        "posted_by": posted_by,
                        "comment": comment,
                        "comment_uuid":comment_uuid
                    },
                )

                logger.debug("Insert into ticket_comments executed")

                # Fetch the generated comment_id
                result = session.execute(
                    text("""
                        SELECT comment_id 
                        FROM ticket_comments 
                        WHERE ticket_id = :ticket_id AND comment_uuid = :comment_uuid AND posted_by = :posted_by
                    """),
                    {"ticket_id": ticket_id, "comment_uuid": comment_uuid, "posted_by": posted_by}
                ).fetchone()

                logger.debug(f"Fetch newly created comment_id result: {result}")

                if result:
                    comment_id = result[0]
                    logger.debug(f"Created comment with ID: {comment_id}")
                else:
                    raise Exception("Failed to retrieve the newly created comment ID.")

            session.commit()
            logger.debug(f"Transaction committed successfully for comment ID {comment_id}")

            return {"comment_id": comment_id, "status": "created"}

        except ValueError as e:
            logger.error(f"Validation error: {e}")
            session.rollback()
            raise e

        except SQLAlchemyError as e:
            logger.error(f"Database error creating comment for customer {customer_guid}: {e}")
            session.rollback()
            raise e

        except Exception as e:
            logger.error(f"Unexpected error while creating comment: {e}")
            session.rollback()
            raise e

        finally:
            logger.debug("Closing database session")
            session.close()

    def get_comment_by_id(self, comment_id, customer_guid):
        customer_db_name = self.get_customer_db(customer_guid)
        session = DatabaseManager._session_factory()
        try:
            # Check if the database exists
            logger.debug(f"Checking if database {customer_db_name} exists")
            result = session.execute(
                text("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = :db_name"),
                {"db_name": customer_db_name}
            ).fetchone()

            if not result:
                raise ValueError(f"Database {customer_db_name} does not exist")

            logger.debug(f"Switching to customer database: {customer_db_name}")
            session.execute(text(f"USE `{customer_db_name}`"))

            # Retrieve comment details
            comment_query = '''
            SELECT comment_id, ticket_id, posted_by, comment, created_at
                FROM ticket_comments
                WHERE comment_id = :comment_id
            '''
            comment_result = session.execute(
                text(comment_query),
                {"comment_id": comment_id},
            ).fetchone()

            if not comment_result:
                return None  # If comment is not found, return None

            # Convert comment result into a dictionary
            logger.info(f"Comment details by comment_id {comment_result}")
            comment_data = {
                column: value
                for column, value in zip(comment_result.keys(), comment_result)
            }

            return comment_data

        except (OperationalError, DatabaseError) as e:
            logger.error(f"Database error: {e}")
            raise Exception("Database connectivity issue")
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy error: {e}")
            raise Exception("Database query error")
        finally:
            session.close()

    def get_comments_by_ticket_id(self, customer_guid, ticket_id):
        customer_db_name = self.get_customer_db(customer_guid)
        session = DatabaseManager._session_factory()

        try:
            # Check if the database exists
            logger.debug(f"Checking if database {customer_db_name} exists")
            result = session.execute(
                text("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = :db_name"),
                {"db_name": customer_db_name}
            ).fetchone()
            if not result:
                raise ValueError(f"Database {customer_db_name} does not exist")

            logger.debug(f"Switching to customer database: {customer_db_name}")
            session.execute(text(f"USE `{customer_db_name}`"))

            # Check if the ticket_id exists in the tickets table
            ticket_exists = session.execute(
                text("SELECT 1 FROM tickets WHERE ticket_id = :ticket_id LIMIT 1"),
                {"ticket_id": ticket_id}
            ).fetchone()

            if not ticket_exists:
                raise ValueError(f"Invalid ticket_id: {ticket_id} does not exist.")

            # Retrieve comments for the given ticket_id
            query = '''
                SELECT comment_id, comment, created_at
                FROM ticket_comments
                WHERE ticket_id = :ticket_id
                ORDER BY created_at ASC
            '''
            results = session.execute(
                text(query),
                {"ticket_id": ticket_id},
            ).fetchall()

            logger.info(f"Comments retrieved for ticket_id {ticket_id}: {results}")

            return [
                {column: value for column, value in zip(row.keys(), row)}
                for row in results
            ]
        except (OperationalError, DatabaseError) as e:
            logger.error(f"Database error: {e}")
            raise Exception("Database connectivity issue")
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving comments: {e}")
            return []
        finally:
            session.close()

    def update_comment(self, ticket_id, comment_id, customer_guid, comment_update):
        customer_db_name = self.get_customer_db(customer_guid)

        try:
            session = DatabaseManager._session_factory()
            # Add retry logic here for connection
        except OperationalError as e:
            logger.error(f"Database connection failed: {e}")
            return {"status": "db_unreachable", "reason": "Database is currently unreachable"}

        try:
            # Check if the database exists
            logger.debug(f"Checking if database {customer_db_name} exists")
            try:
                result = session.execute(
                    text("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = :db_name"),
                    {"db_name": customer_db_name}
                ).fetchone()
            except (OperationalError, DatabaseError) as e:
                logger.error(f"Database connectivity issue during schema check: {e}")
                return {"status": "db_unreachable", "reason": "Database is currently unreachable"}

            if not result:
                return {"status": "unknown_db", "reason": f"Database {customer_db_name} does not exist"}

            logger.debug(f"Switching to customer database: {customer_db_name}")
            session.execute(text(f"USE `{customer_db_name}`"))

            # Check if the comment exists
            result = session.execute(
                text("SELECT COUNT(*) FROM ticket_comments WHERE ticket_id = :ticket_id AND comment_id = :comment_id"),
                {"ticket_id": ticket_id, "comment_id": comment_id},
            ).fetchone()

            if result[0] == 0:
                return {"status": "not_found",
                        "reason": f"Comment ID {comment_id} not found for Ticket ID {ticket_id}."}

            # Update the comment and set is_edited to true
            try:
                query = """
                    UPDATE ticket_comments
                    SET comment = :comment,
                        is_edited = true
                    WHERE ticket_id = :ticket_id AND comment_id = :comment_id
                """
                session.execute(
                    text(query),
                    {"ticket_id": ticket_id, "comment_id": comment_id, "comment": comment_update.comment}
                )

                # Fetch updated_at column after update
                updated_at_result = session.execute(
                    text(
                        "SELECT updated_at, is_edited FROM ticket_comments WHERE ticket_id = :ticket_id AND comment_id = :comment_id"),
                    {"ticket_id": ticket_id, "comment_id": comment_id}
                ).fetchone()

                session.commit()

                updated_at = updated_at_result[0] if updated_at_result else None
                is_edited = updated_at_result[1] if updated_at_result else False

                return {"status": "updated", "reason": None, "is_edited":is_edited, "updated_at": updated_at}
            except SQLAlchemyError as e:
                logger.error(f"Error updating comment: {e}")
                session.rollback()
                return {
                    "status": "conflict",
                    "reason": f"Invalid data provided for comment. {str(e)}"
                }

        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}")
            session.rollback()
            return {"status": "failure", "reason": "Unexpected database error."}
        except OperationalError as e:
            logger.error(f"Database connectivity issue: {e}")
            return {"status": "db_unreachable", "reason": "Database is currently unreachable"}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            session.rollback()
            return {"status": "failure", "reason": "Unexpected error occurred during comment update."}

        finally:
            session.close()

    def delete_comment(self, ticket_id, comment_id, customer_guid):
        customer_db_name = self.get_customer_db(customer_guid)

        try:
            session = DatabaseManager._session_factory()
        except OperationalError as e:
            logger.error(f"Database connection failed: {e}")
            return {"status": "db_unreachable", "reason": "Database is currently unreachable"}

        try:
            # Check if the database exists
            logger.debug(f"Checking if database {customer_db_name} exists")
            try:
                result = session.execute(
                    text("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = :db_name"),
                    {"db_name": customer_db_name}
                ).fetchone()
            except OperationalError as e:
                logger.error(f"Database connectivity issue during schema check: {e}")
                return {"status": "db_unreachable", "reason": "Database is currently unreachable"}

            if not result:
                return {"status": "unknown_db", "reason": f"Database {customer_db_name} does not exist"}

            logger.debug(f"Switching to customer database: {customer_db_name}")
            try:
                session.execute(text(f"USE `{customer_db_name}`"))
            except OperationalError as e:
                logger.error(f"Database connectivity issue during USE statement: {e}")
                return {"status": "db_unreachable", "reason": "Database is currently unreachable"}

            # Check if the comment exists
            try:
                result = session.execute(
                    text(
                        "SELECT COUNT(*) FROM ticket_comments WHERE ticket_id = :ticket_id AND comment_id = :comment_id"),
                    {"ticket_id": ticket_id, "comment_id": comment_id},
                ).fetchone()
            except OperationalError as e:
                logger.error(f"Database connectivity issue during comment existence check: {e}")
                return {"status": "db_unreachable", "reason": "Database is currently unreachable"}

            if result[0] == 0:  # Comment not found
                return {"status": "deleted"}

            # Attempt to delete the comment
            try:
                delete_comment_query = '''DELETE FROM ticket_comments WHERE ticket_id = :ticket_id AND comment_id = :comment_id'''
                session.execute(
                    text(delete_comment_query),
                    {"ticket_id": ticket_id, "comment_id": comment_id},
                )
                session.commit()
                return {"status": "deleted"}
            except SQLAlchemyError as e:
                logger.error(f"Error deleting comment: {e}")
                session.rollback()
                return {"status": "failure", "reason": str(e)}

        except OperationalError as e:  # Handle database connectivity issues
            logger.error(f"Database connectivity issue: {e}")
            return {"status": "db_unreachable", "reason": "Database is currently unreachable"}
        except DatabaseError as e:
            logger.error(f"Database connectivity issue: {e}")
            return {"status": "db_unreachable", "reason": "Database is currently unreachable"}
        except Exception as e:
            logger.error(f"Unexpected error during deletion: {e}")
            session.rollback()
            return {"status": "failure", "reason": "Unexpected error occurred"}

        finally:
            session.close()