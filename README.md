# Foodie-Chatbot-Model
This NLP chatbot serves as a waiter for a Nigerian food restaurant website, handling a high volume of customers simultaneously. It facilitates order creation, modification, cancellation, tracking, and cost calculation. It allows flexible conversation using NLP techniques like NER and REGEX for processing customer input.

## Setup

1. Create a `.env` file in the root of the project with the following content; you can do this in Visual studio code or any terminal you're using for your project:
   ```plaintext
   DB_USER=your_database_user
   DB_PASSWORD=your_database_password
   DB_HOST=your_database_host
   DB_NAME=your_database_name
2. Run the following command to install the required python packages for your .env file to be used
    'pip install -r requirements.txt'
3. Run the main.py file using ngrok to generate a https link from your http server connection as diagflow wont be able to connect to your local http link.
4. Ensure you create an ngrok account before doing this to enable seamless and non frequent reconnection of your generated ngrok https server link.
5. Have all these files under a folder and within a virtual environment; its an ethic. 
