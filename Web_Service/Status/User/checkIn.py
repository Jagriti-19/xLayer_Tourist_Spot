from datetime import datetime
from JWTConfiguration.auth import xenProtocol
import tornado.web
from bson.objectid import ObjectId
from con import Database
import time
import json


class CheckInHandlerUser(tornado.web.RequestHandler, Database):
    bookTable = Database.db['bookings']
    spotTable = Database.db['spots']
    userTable = Database.db['users']
    checkInTable = Database.db['check-ins']


    @xenProtocol
    # Get method for upcoming
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
                        'date': 1,
                        'status': 1,
                        'check-in': 1
                    }
                }
            ]

            cursor = self.checkInTable.aggregate(aggregation_pipeline)
            async for booking in cursor:
                booking['check-in'] = format_timestamp(int(booking['check-in']))
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



