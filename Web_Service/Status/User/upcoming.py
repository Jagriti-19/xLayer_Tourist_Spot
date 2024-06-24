from datetime import datetime
import tornado.web
from bson.objectid import ObjectId
from con import Database
import json

class UpcomingHandler(tornado.web.RequestHandler, Database):
    bookTable = Database.db['bookings']

    async def get(self):
        code = 4000
        status = False
        result = []
        message = ''

        try:
            try:
                mUserId = self.get_argument('userId')
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

            # Build the query
            match_query = {}
            if mUserId:
                match_query['userId'] = mUserId
            elif mBookingId:
                match_query['_id'] = mBookingId
            
            # Aggregation pipeline
            pipeline = [
                {
                    '$lookup': {
                        'from': 'users',
                        'localField': 'userId',
                        'foreignField': '_id',
                        'as': 'user_info'
                    }
                },
                {
                    '$lookup': {
                        'from': 'spots',
                        'localField': 'spotId',
                        'foreignField': '_id',
                        'as': 'spot_info'
                    }
                },
                {'$unwind': '$user_info'},
                {'$unwind': '$spot_info'},
                {
                    '$project': {
                        '_id': 1,
                        'userId': 1,
                        'spotId': 1,
                        'name': '$user_info.name',
                        'spot_name': '$spot_info.name',
                        'ticketId': 1,
                        'available_dates': 1,
                        'entry_fee': '$spot_info.entry_fee',
                        'quantity': 1,
                        'visiting_hours': '$spot_info.visiting_hours',
                        'total': 1,
                        'booking_date': 1,
                        'status': 1,
                        'check-in': 1,
                        'check-out': 1,
                    }
                }
            ]

            cursor = self.bookTable.aggregate(pipeline)
            async for booking in cursor:
                booking['_id'] = str(booking['_id'])
                booking['userId'] = str(booking['userId'])
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
