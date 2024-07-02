from datetime import datetime
from JWTConfiguration.auth import xenProtocol
import tornado.web
from bson.objectid import ObjectId
from con import Database
import json

class GetBookingsBySpotId(tornado.web.RequestHandler, Database):
    bookTable = Database.db['bookings']
    userTable = Database.db['users']

    @xenProtocol
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
            try:
                mSpotId = self.get_argument('spotId')
                if not mSpotId:
                    raise Exception
                mSpotId = ObjectId(mSpotId)
            except:
                mSpotId = None
            

            mSpotId = {'spotId': mSpotId}
            
                
            cursor = self.bookTable.find(mSpotId)
            async for booking in cursor:
                booking['spotId'] = str(booking['spotId'])
                if 'booking_date' in booking:
                    booking['booking_date'] = await format_timestamp(int(booking['booking_date']))
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



async def format_timestamp(timestamp):
    try:
        dt_object = datetime.fromtimestamp(timestamp)
        return dt_object.strftime("%A, %d %B %Y, %H:%M:%S")
    except Exception as e:
        print(f"Error formatting timestamp: {e}")
        return "Invalid Date"
