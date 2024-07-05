import json
import tornado.web
from con import Database
from bson.objectid import ObjectId
import tornado.ioloop
from datetime import datetime, timedelta

class CapacityHandler(tornado.web.RequestHandler, Database):
    capacityTable = Database.db['capacity']
    bookTable = Database.db['bookings']
    spotTable = Database.db['spots']
    userTable = Database.db['users']

    async def post(self):
        code = 4014
        status = False
        result = []
        message = ''

        try:
            try:
                self.request.arguments = json.loads(self.request.body.decode())
            except Exception as e:
                code = 4024
                message = "Invalid JSON"
                raise Exception
            
            mSpotId = self.request.arguments.get('spotId')
            
            if not mSpotId:
                message = 'SpotId is required'
                code = 4033
                raise Exception

            try:
                mSpot = ObjectId(mSpotId)
            except Exception as e:
                message = 'Invalid spotId format'
                code = 4034
                raise Exception
            
            mTotalCapacity = self.request.arguments.get('total_capacity')
            
            if mTotalCapacity is None:
                message = 'Total Capacity is required'
                code = 4033
                raise Exception

            try:
                mTotalCapacity = int(mTotalCapacity)
            except Exception as e:
                message = 'Total Capacity must be an integer'
                code = 4034
                raise Exception

            if mTotalCapacity <= 0:
                message = 'Total Capacity must be greater than zero'
                code = 4035
                raise Exception
            
            mDays = self.request.arguments.get('days') 

            # Get total guests from the booking table
            bookings = await self.bookTable.find({'spotId': mSpot}).to_list(length=None)
            total_guests = sum((booking.get('quantityAd', 0) + booking.get('quantityCh', 0)) for booking in bookings)

            spot = await self.spotTable.find_one({'_id': mSpot})
            if not spot:
                message = 'Spot not found'
                code = 4044
                raise Exception

            # Check if available capacity is sufficient for booking
            if mTotalCapacity < total_guests:
                message = 'Insufficient available capacity for this booking'
                code = 4067
                raise Exception

            for day in range(mDays):
                mDate = (datetime.now() + timedelta(days=day)).strftime('%d-%m-%Y')
                data = {
                    'spotId': mSpot,
                    'totalCapacity': mTotalCapacity,
                    'availableCapacity': mTotalCapacity,
                    'date': mDate
                }

                try:
                    addCapacity = await self.capacityTable.insert_one(data)
                    if addCapacity.inserted_id:
                        result.append({
                            'capacityId': str(addCapacity.inserted_id),
                            'date': mDate
                        })
                    else:
                        code = 1005
                        message = 'Failed to add capacity'
                        raise Exception
                
                except Exception as e:
                    exe = str(e).split(':')
                    if 'spotId' in exe[2]:
                        message = 'Spot Id already exists.'
                        code = 5477
                        raise Exception
                    if 'date' in exe[2]:
                        message = 'Date already exists.'
                        code = 5477
                        raise Exception

            code = 1004
            status = True
            message = 'Capacity added successfully'

        except Exception as e:
            if not len(message):
                message = 'Internal Server Error'
                code = 1005
                raise Exception

        response = {
            'code': code,
            'message': message,
            'status': status,
        }

        try:
            if len(result):
                response['result'] = result

            self.write(response)
            self.finish()

        except Exception as e:
            message = 'There is some issue'
            code = 1006
            raise Exception


async def reset_capacity():
    # Function to reset available capacity
    total_capacity = 200
    date_today = datetime.now().strftime('%d-%m-%Y')

    # Update capacity in the database
    await Database.db['capacity'].update_many(
        {'date': date_today},
        {'$set': {'availableCapacity': total_capacity}}
    )

def schedule_capacity_reset():
    # Schedule the reset_capacity function to run every 24 hours
    reset_interval = timedelta(hours=24)
    tornado.ioloop.PeriodicCallback(reset_capacity, reset_interval.total_seconds() * 1000).start()

# Schedule the reset_capacity function to run every 24 hours
schedule_capacity_reset()
