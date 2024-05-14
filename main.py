# Import necessary modules
# Import necessary modules
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import db_helper
import generic_helper

# Initialize FastAPI app
app = FastAPI()

# Define a dictionary to store in-progress orders
inprogress_orders = {}

# Define function to track order status
def track_order(parameters) -> str:
    if isinstance(parameters, dict):
        order_ids = parameters.get('number')
    else:
        order_ids = parameters

    if order_ids is not None:
        if isinstance(order_ids, list):
            order_statuses = [db_helper.get_order_status(int(order_id)) for order_id in order_ids]
            fulfillment_text = "\n".join(
                [f"The order status for order ID: {order_id} is: {status}" if status else f"No order found with order ID: {order_id}" for order_id, status in zip(order_ids, order_statuses)]
            )
        else:
            order_id = int(order_ids)
            order_status = db_helper.get_order_status(order_id)
            fulfillment_text = (
                f"The order status for order ID: {order_id} is: {order_status}"
                if order_status
                else f"No order found with order ID: {order_id}"
            )
    else:
        fulfillment_text = "No order ID provided. Please provide an order ID."

    return {"fulfillmentText": fulfillment_text}


def remove_from_order(parameters: dict, session_id: str):
    if session_id not in inprogress_orders:
        fulfillment_text = "I'm having trouble finding your order. Sorry! Can you please place a new order?"
        return {"fulfillmentText": fulfillment_text}

    current_order = inprogress_orders[session_id]
    food_items = parameters.get("food-item", [])
    quantities = parameters.get("number", [])

    if not food_items or not quantities:
        fulfillment_text = "Sorry, I didn't understand. Please specify the food items and quantities clearly."
        return {"fulfillmentText": fulfillment_text}

    removed_items = []
    no_such_items = []

    for item, qty in zip(food_items, quantities):
        if item not in current_order:
            no_such_items.append(item)
        else:
            if current_order[item] >= qty:
                current_order[item] -= qty
                removed_items.append(f"{qty} {item}")
                if current_order[item] == 0:
                    del current_order[item]
            else:
                no_such_items.append(f"{qty} {item}")

    fulfillment_text = ""
    if removed_items:
        fulfillment_text += f"Removed {', '.join(removed_items)} from your order. "
    if no_such_items:
        fulfillment_text += f"Your current order does not have {' and '.join(no_such_items)}. "

    if not current_order:
        fulfillment_text += "Your order is empty!"
    else:
        order_str = generic_helper.get_str_from_food_dict(current_order)
        fulfillment_text += f"Here is what is left in your order: {order_str}, anything else?"

    # Update the inprogress_orders dictionary
    inprogress_orders[session_id] = current_order

    return {"fulfillmentText": fulfillment_text}

# Define function to add items to an order
def add_to_order(parameters: dict, session_id: str):
    food_items = parameters.get("food-item", [])
    quantities = parameters.get("number", [])
    
    # Check if number of food items matches number of quantities
    if len(food_items) != len(quantities):
        fulfillment_text = "Sorry, I didn't understand. Please specify your food items and quantities clearly."
        return {"fulfillmentText": fulfillment_text}

    new_food_dict = dict(zip(food_items, quantities))

    if session_id in inprogress_orders:
        current_food_dict = inprogress_orders[session_id]
        current_food_dict.update(new_food_dict)
        inprogress_orders[session_id] = current_food_dict
    else:
        inprogress_orders[session_id] = new_food_dict

    order_str = generic_helper.get_str_from_food_dict(inprogress_orders.get(session_id, {}))

    # Check if order_str is empty
    if not order_str:
        fulfillment_text = "Sorry, I couldn't process your order. Please try again."
    else:
        fulfillment_text = f"So far you have: {order_str}. Do you need anything else? To cancel your current order, you can just say \"cancel order"

    return {"fulfillmentText": fulfillment_text}



# Define function to complete an order
def complete_order(parameters: dict, session_id: str):
    if session_id not in inprogress_orders:
        fulfillment_text = "I'm having trouble finding your order. Sorry! Can you please place a new order?"
    else:
        order = inprogress_orders[session_id]
        order_id = save_to_db(order)

        if order_id == -1:
            fulfillment_text = "Sorry, I couldn't process your order due to a backend error. Please place a new order."
        else:
            order_total = db_helper.get_total_order_price(order_id)
            fulfillment_text = f"Awesome. We have placed your order. Here is your order ID #{order_id}. Your order total cost is ${order_total}.Visit our homepage's payment portal, use your order ID to pay for your order and delivery, and provide your delivery details. Thank you!"
            del inprogress_orders[session_id]
        
        #del inprogress_orders[session_id] #last change.

    return {"fulfillmentText": fulfillment_text}


# Define function to save order to the database
def save_to_db(order: dict):
    next_order_id = db_helper.get_next_order_id()

    if next_order_id == -1:  # Check for database connection error
        return -1

    for food_items, quantities in order.items():
        result = db_helper.insert_order_item(int(next_order_id), quantities, food_items)
        if result == -1:  # Check for insertion success
            return -1

    # If all items inserted successfully, update order status
    db_helper.insert_order_tracking(next_order_id, "in queue")
    
    # Return the order ID for further processing
    return next_order_id


# Define function to cancel an order
def cancel_order(parameters: dict, session_id: str):
    if session_id in inprogress_orders:
        del inprogress_orders[session_id]
        fulfillment_text = "Your current order has been canceled."
    else:
        fulfillment_text = "There is no active order to cancel."
    return {"fulfillmentText": fulfillment_text}


# Define route handler to handle incoming requests
@app.post("/")
async def handle_request(request: Request):
    try:
        # Retrieve the JSON data from the request
        payload = await request.json()

        # Extract the necessary information from the payload
        intent = payload['queryResult']['intent']['displayName']
        parameters = payload['queryResult']['parameters']

        # Extract session ID from the payload
        session_str = payload.get('session', '')
        session_id = generic_helper.extract_session_id(session_str)

        intent_handler_dict = {
            'track.order - context: ongoing-tracking': track_order,
            'order.remove - context: ongoing-order': lambda params, session_id=session_id: remove_from_order(params, session_id),
            'order.add - context: ongoing-order': lambda params, session_id=session_id: add_to_order(params, session_id),
            'order.complete - context: ongoing-order': lambda params, session_id=session_id: complete_order(params, session_id),
            'cancel.order - context: ongoing-order': lambda params, session_id=session_id: cancel_order(params, session_id)
        }

        if intent in intent_handler_dict:
            # Call the corresponding function based on the intent
            response_data = intent_handler_dict[intent](parameters)
        else:
            # Handle other cases or return a default response if needed
            response_data = {"fulfillmentText": "Unsupported intent"}

        # Return a JSONResponse object with the response data
        return JSONResponse(content=response_data)

    except Exception as e:
        # Handle exceptions gracefully and return a valid JSON response
        error_message = "An error occurred: {}".format(str(e))
        return JSONResponse(content={"fulfillmentText": error_message})