import motor.motor_asyncio 

class Database:
    try:
        client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
        db = client['tourist_spot_db']
        print("Database connection established successfully")
    except Exception as e:
        print(f"Error connecting to database: {e}")
        db = None
