from datetime import datetime
from JWTConfiguration.auth import xenProtocol
import tornado.web
from bson.objectid import ObjectId
from con import Database
import time
import json


class CheckOutHandler(tornado.web.RequestHandler, Database):
    bookTable = Database.db['bookings']
    spotTable = Database.db['spots']
    userTable = Database.db['users']
    checkInTable = Database.db['check-ins']
    checkOutTable = Database.db['check-outs']


    @xenProtocol
    # Put method for update booking
    async def put(self):
        code = 4034
        status = False
        result = []
        message = ''

        try:
            user = await self.userTable.find_one({'_id': ObjectId(self.user_id)})
            if not user:
                message = 'User not found'
                code = 4002
                raise Exception

            mUserRole = user.get('role')
            if mUserRole != 'admin':
                message = 'Access forbidden: insufficient permissions'
                code = 4030
                raise Exception
            
            # Extract bookingId from URL params
            mBookingId = self.get_argument('bookingId')

            try:
                mBookingId = ObjectId(mBookingId)
            except Exception as e:
                message = 'Invalid bookingId format'
                code = 4031
                raise Exception(message)

            # Fetch existing booking details
            booking = await self.checkInTable.find_one({'_id': mBookingId})
            if not booking:
                message = 'Booking not found'
                code = 4021
                raise Exception(message)

            # Update status and check-out time
            updated_data = {
                '$set': {
                    'status': 'check-out',
                    'check-out': int(time.time())
                }
            }

            # Update the booking status and check-out time
            updated_result = await self.checkInTable.update_one(
                {'_id': mBookingId},
                updated_data
            )

            if updated_result.modified_count > 0:
                # Fetch updated booking after update operation
                updated_booking = await self.checkInTable.find_one({'_id': mBookingId})

                # Add to check-out table with updated status and check-out time
                addCheckOut = await self.checkOutTable.insert_one(updated_booking)
                if addCheckOut.inserted_id:
                    # Remove from booking table after successfully adding to check-out table
                    await self.checkInTable.delete_one({'_id': mBookingId})

                    code = 4039
                    status = True
                    message = 'Checked out successfully'
                else:
                    code = 4020
                    message = 'Failed to move to check-out table'
            else:
                code = 4021
                message = 'Booking not found or no changes made'

        except Exception as e:
            if not message:
                message = 'Internal Server Error'
                code = 1005
            print(f"Error in put method: {e}")

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
            print(f"Error in response handling: {e}")
            raise Exception(message)


    @xenProtocol
    # Get method for check out
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
                        'available dates': 1,
                        'status': 1,
                        'check-out': 1
                    }
                }
            ]

            cursor = self.checkOutTable.aggregate(aggregation_pipeline)
            async for booking in cursor:
                booking['check-out'] = format_timestamp(int(booking['check-out']))
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



