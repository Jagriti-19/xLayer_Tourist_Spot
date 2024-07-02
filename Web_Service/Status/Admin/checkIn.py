from datetime import datetime
from JWTConfiguration.auth import xenProtocol
import tornado.web
from bson.objectid import ObjectId
from con import Database
import time
import json


class CheckInHandlerAdmin(tornado.web.RequestHandler, Database):
    bookTable = Database.db['bookings']
    spotTable = Database.db['spots']
    userTable = Database.db['users']
    checkInTable = Database.db['check-ins'] 


    @xenProtocol
    # Put method for update booking
    async def put(self):
        code = 4014
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
                raise Exception

            # Fetch existing booking details
            booking = await self.bookTable.find_one({'_id': mBookingId})
            if not booking:
                message = 'Booking not found'
                code = 4021
                raise Exception

            # Update status and check-in time
            updated_data = {
                '$set': {
                    'status': 'check-in',
                    'check-in': int(time.time())
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

                # Add to check-in table with updated status and check-in time
                addCheckIn = await self.checkInTable.insert_one(updated_booking)
                if addCheckIn.inserted_id:
                    # Remove from booking table after successfully adding to check-in table
                    await self.bookTable.delete_one({'_id': mBookingId})

                    code = 4019
                    status = True
                    message = 'Checked in successfully'
                else:
                    code = 4020
                    message = 'Failed to move to check-in table'
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
            raise Exception