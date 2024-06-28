from datetime import datetime
from JWTConfiguration.auth import xenProtocol
import tornado.web
from bson.objectid import ObjectId
from con import Database
import time
import json

class CancelHandler(tornado.web.RequestHandler, Database):
    bookTable = Database.db['bookings']
    spotTable = Database.db['spots']
    userTable = Database.db['users']
    cancelTable = Database.db['cancels']

    @xenProtocol
    # Put method for update booking
    async def put(self):
        code = 4014
        status = False
        result = []
        message = ''

        try:  
            # Extract bookingId from URL params
            mBookingId = self.get_argument('bookingId')

            try:
                mBookingId = ObjectId(mBookingId)
            except Exception as e:
                message = 'Invalid bookingId format'
                code = 4031
                raise Exception

            # Fetch existing booking details
            booking = await self.bookTable.find_one({'_id': mBookingId})
            if not booking:
                message = 'Booking not found'
                code = 4021
                raise Exception

            # Calculate the total guests to be added back to capacity
            total_guests = (booking['quantity']['adult'] or 0) + (booking['quantity']['child'] or 0)

            # Update status and cancel time
            updated_data = {
                '$set': {
                    'status': 'cancel',
                    'cancel': int(time.time())
                }
            }

            # Update the booking status and check-in time
            updated_result = await self.bookTable.update_one(
                {'_id': mBookingId},
                updated_data
            )

            if updated_result.modified_count > 0:
                # Fetch updated booking after update operation
                updated_booking = await self.bookTable.find_one({'_id': mBookingId})

                # Add to cancel table with updated status and cancel-time
                addCheckIn = await self.cancelTable.insert_one(updated_booking)
                if addCheckIn.inserted_id:
                    # Remove from booking table after successfully adding to check-in table
                    await self.bookTable.delete_one({'_id': mBookingId})

                    # Update the available capacity for the spot
                    update_result = await self.spotTable.update_one(
                        {'_id': booking['spotId']},
                        {'$inc': {'available_capacity': total_guests}}
                    )

                    if update_result.modified_count != 1:
                        code = 1005
                        message = 'Failed to update available capacity for the spot'
                        raise Exception

                    code = 4019
                    status = True
                    message = 'Canceled successfully'
                else:
                    code = 4020
                    message = 'Failed to move to cancel table'
            else:
                code = 4021
                message = 'Booking not found or no changes made'

        except Exception as e:
            if not message:
                message = 'Internal Server Error'
                code = 1005

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


    @xenProtocol
    # Get method for cancels
    async def get(self):
        code = 4000
        status = False
        result = []
        message = ''

        try:
            try:
                mUserId = self.user_id
                if not mUserId:
                    raise Exception
                mUserId = ObjectId(mUserId)
            except:
                mUserId = None
            
            try:
                mBookingId = self.get_argument('bookingId')
                if not mBookingId:
                    raise Exception
                mBookingId = ObjectId(mBookingId)
            except:
                mBookingId = None

            if mUserId:
                query = {'userId': mUserId}
            else:
                query = {'_id': mBookingId}
 
            aggregation_pipeline = [
                {
                    '$match': query
                },
                {
                    '$lookup': {
                        'from': 'users',
                        'localField': 'userId',
                        'foreignField': '_id',
                        'as': 'user_details'
                    }
                },
                {
                    '$lookup': {
                        'from': 'spots',
                        'localField': 'spotId',
                        'foreignField': '_id',
                        'as': 'spot_details'
                    }
                },
                {
                    '$addFields': {
                        'user_details': {
                            '$first': '$user_details'
                        },
                        'spot_details': {
                            '$first': '$spot_details'
                        }
                    }
                },
                {
                    '$project': {
                        '_id': {'$toString': '$_id'},
                        'userId': {'$toString': '$userId'},
                        'ticketId': 1,
                        'name': '$user_details.name',
                        'spot_name': '$spot_details.name',
                        'total': 1,
                        'available_dates': 1,
                        'status': 1,
                        'cancel': 1
                    }
                }
            ]

            cursor = self.cancelTable.aggregate(aggregation_pipeline)
            async for booking in cursor:
                booking['cancel'] = format_timestamp(int(booking['cancel']))
                result.append(booking)

            if result:
                message = 'Found'
                code = 2000
                status = True
            else:
                message = 'No data found for the given userId'
                code = 4002

        except Exception as e:
            if not message:
                message = 'Internal server error'
                code = 5010

        response = {
            'code': code,
            'message': message,
            'status': status,
        }

        try:
            if result:
                response['result'] = result

            self.set_header('Content-Type', 'application/json')
            self.write(json.dumps(response, default=str))
            await self.finish()

        except Exception as e:
            message = 'There is some issue'
            code = 5011
            print(f"Error in response serialization: {e}") 
            raise Exception


def format_timestamp(timestamp):
    try:
        dt_object = datetime.fromtimestamp(timestamp)
        return dt_object.strftime("%A, %d %B %Y, %H:%M:%S")
    except Exception as e:
        print(f"Error formatting timestamp: {e}")
        return "Invalid Date"
