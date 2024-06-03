import serial
import time
import json
from pymongo import MongoClient

# Set up the serial connection (replace 'COM3' with your Bluetooth serial port)
ser = serial.Serial('COM6', 9600, timeout=1)

# Set up MongoDB connection
client = MongoClient('mongodb+srv://codeswithroh:codeswithroh@cluster0.frga0.mongodb.net/')
db = client['FarmCast']
collection = db['readings']

while True:
    try:
        # Read a line from the serial port
        line = ser.readline().decode('utf-8').strip()
        
        if line:
            print("Received data: ", line)
            
            # Convert the JSON data to a Python dictionary
            data = json.loads(line)
            
            # Insert the data into MongoDB
            collection.insert_one(data)
            print("Data inserted into MongoDB")
        
        # Wait before reading the next line
        time.sleep(1)
    except json.JSONDecodeError:
        print("Error decoding JSON data")
    except KeyboardInterrupt:
        print("Exiting...")
        break

ser.close()
client.close()
