import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import errorcode

# Load environment variables from .env file
load_dotenv()

# Your database connection setup
cnx = mysql.connector.connect(
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    host=os.getenv('DB_HOST'),
    database=os.getenv('DB_NAME')
)


def insert_order_tracking(order_id, status):
    cursor = cnx.cursor()
    insert_query = "INSERT INTO order_tracking (order_id, status_) VALUES (%s, %s)"
    cursor.execute(insert_query, (order_id, status))
    cnx.commit()
    cursor.close()


def get_total_order_price(order_id):
    cursor = cnx.cursor()
    query = f"SELECT get_total_order_price({order_id})"
    cursor.execute(query)
    result = cursor.fetchone()[0]
    cursor.close()
    return result

def get_next_order_id():
    cursor = cnx.cursor()

    # executing the SQL query to get the next available order_id
    query = "SELECT MAX(Order_id) FROM order_table"
    cursor.execute(query)

    # Fetching the result
    result = cursor.fetchone()[0]

    # Closing the cursor
    cursor.close()

    # Returning the next available order_id
    if result is None:
        return 1
    else:
        return result + 1



def insert_order_item(order_id, quantity, food_item):
    try:
        cursor = cnx.cursor()
        cursor.callproc('insert_order_item', (order_id, quantity, food_item))
        cnx.commit()
        cursor.close()
        print("Order item inserted successfully!")
        return 1
    except mysql.connector.Error as err:
        print(f"Error inserting order item: {err}")
        cnx.rollback()
        return -1
    except Exception as e:
        print(f"An error occurred: {e}")
        cnx.rollback()
        return -1


def get_order_status(order_id):
    try:
        cursor = cnx.cursor()
        query = "SELECT status_ FROM order_tracking WHERE Order_id = %s"
        cursor.execute(query, (order_id,))
        result = cursor.fetchone()
        if result:
            order_status = result[0]
        else:
            order_status = None
        cursor.close()
        return order_status
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Error: Access denied.")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Error: Database does not exist.")
        else:
            print(f"Error: {err}")
        return None
