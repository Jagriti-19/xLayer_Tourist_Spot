from datetime import datetime
import tornado.web
from bson.objectid import ObjectId
from con import Database
import time


class CheckOutHandler(tornado.web.RequestHandler, Database):
    bookTable = Database.db['bookings']
    spotTable = Database.db['spots']
    userTable = Database.db['users']
    checkInTable = Database.db['check-ins']
    checkOutTable = Database.db['check-outs']


    # Put method for update booking
    async def put(self):
        code = 4034
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

    


    # GET method to get check-in using userId or bookingId
    async def get(self):
        code = 4000
        status = False
        result = []
        message = ''

        try:
            mUserId = self.get_argument('userId', None)
            mBookingId = self.get_argument('bookingId', None)

            if mUserId:
                query = {'userId': mUserId}
                cursor = self.checkOutTable.find(query)
                async for booking in cursor:
                    booking['_id'] = str(booking['_id'])
                    booking['userId'] = str(booking['userId'])
                    if 'booking_date' in booking:
                        booking['booking_date'] = await format_timestamp(int(booking['booking_date']))
                    if 'check-out' in booking:
                        booking['check-out'] = await format_timestamp(int(booking['check-out']))
                    result.append(booking)

                if result:
                    message = 'Found'
                    code = 2000
                    status = True
                else:
                    message = 'No data found for the given userId'
                    code = 4002

            elif mBookingId:
                try:
                    mBookingId = ObjectId(mBookingId)
                except Exception as e:
                    message = 'Invalid bookingId format'
                    code = 4023
                    raise Exception

                booking = await self.checkOutTable.find_one({'_id': mBookingId})
                if booking:
                    booking['_id'] = str(booking['_id'])
                    booking['userId'] = str(booking['userId'])
                    if 'booking_date' in booking:
                        booking['booking_date'] = await format_timestamp(int(booking['booking_date']))
                    if 'check-out' in booking:
                        booking['check-out'] = await format_timestamp(int(booking['check-out']))
                    result.append(booking)
                    message = 'Found'
                    code = 2000
                    status = True
                else:
                    message = 'No data found for the given bookingId'
                    code = 4002
            else:
                message = 'Please enter userId or bookingId'
                code = 4022

        except Exception as e:
            if not message:
                message = 'Internal server error'
                code = 5010
            print(e)

        response = {
            'code': code,
            'message': message,
            'status': status,
        }

        try:
            if result:
                response['result'] = result

            self.set_header('Content-Type', 'application/json')
            self.write(response)
            await self.finish()

        except Exception as e:
            message = 'There is some issue'
            code = 5011
            print(e)
            raise Exception






async def format_timestamp(timestamp):
    try:
        # Convert timestamp to datetime object
        dt_object = datetime.fromtimestamp(timestamp)
        # Format datetime object as required
        # formatted_time = time.strftime("%d %B %Y %H:%M:%S", time.localtime(ts))
        return dt_object.strftime("%A, %d %B %Y, %H:%M:%S")
    except Exception as e:
        print(f"Error formatting timestamp: {e}")
        return "Invalid Date"



