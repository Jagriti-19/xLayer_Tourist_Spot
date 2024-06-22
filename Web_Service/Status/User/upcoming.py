from datetime import datetime
import tornado.web
from bson.objectid import ObjectId
from con import Database
import time


class UpcomingHandler(tornado.web.RequestHandler, Database):
    bookTable = Database.db['bookings']
    spotTable = Database.db['spots']
    userTable = Database.db['users']

    # GET method to get booking details using userId or bookingId
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
                cursor = self.bookTable.find(query)
                async for booking in cursor:
                    booking['_id'] = str(booking['_id'])
                    booking['userId'] = str(booking['userId'])
                    if 'booking_date&time' in booking:
                        booking['booking_date&time'] = await format_timestamp(int(booking['booking_date&time']))
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

                booking = await self.bookTable.find_one({'_id': mBookingId})
                if booking:
                    booking['_id'] = str(booking['_id'])
                    booking['userId'] = str(booking['userId'])
                    if 'booking_date&time' in booking:
                        booking['booking_date&time'] = await format_timestamp(int(booking['booking_date&time']))
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
            raise Exception



async def format_timestamp(timestamp):
    try:
        # Convert timestamp to datetime object
        dt_object = datetime.fromtimestamp(timestamp)
        # Format datetime object as required
        return dt_object.strftime("%A, %d %B %Y, %H:%M:%S")
    except Exception as e:
        print(f"Error formatting timestamp: {e}")
        return "Invalid Date"
