from datetime import datetime
import json
from JWTConfiguration.auth import xenProtocol
import tornado.web
from bson.objectid import ObjectId
from con import Database


class BookingHandlerAdmin(tornado.web.RequestHandler, Database):
    bookTable = Database.db['bookings']
    userTable = Database.db['users']

    @xenProtocol
    # GET method for retrieving booking details by BookingId or all bookings
    async def get(self):
        code = 4000
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
            
            mBookingId = self.get_argument('bookingId', default=None)

            if mBookingId:
                mBookingId = ObjectId(mBookingId)
                query = {'_id': mBookingId}
            else:
                query = {}

            mBooking = self.bookTable.find(query)

            for booking in await mBooking.to_list(length=None):
                booking['_id'] = str(booking.get('_id')) 
                if 'booking_date' in booking:
                    booking['booking_date'] = format_timestamp(int(booking['booking_date']))
                result.append(booking)

            if len(result):
                message = 'Found'
                code = 2000
                status = True
            else:
                message = 'Not found'
                code = 4002

        except Exception as e:
            if not len(message):
                message = 'There is some issue'
                code = 5010
                print(e)
                raise Exception

        try:
            response = {
                'code': code,
                'message': message,
                'status': status,
            }

            if len(result):
                response['result'] = result

            # Serialize response using custom encoder to handle ObjectId
            self.set_header('Content-Type', 'application/json')
            self.write(json.dumps(response, default=str))
            self.finish()

        except Exception as e:
            message = 'There is some issue'
            code = 5011
            raise Exception
        


def format_timestamp(timestamp):
    try:
        # Convert timestamp to datetime object
        dt_object = datetime.fromtimestamp(timestamp)
        # Format datetime object as required
        return dt_object.strftime("%A, %d %B %Y, %H:%M:%S")
    except Exception as e:
        print(f"Error formatting timestamp: {e}")
        return "Invalid Date"    