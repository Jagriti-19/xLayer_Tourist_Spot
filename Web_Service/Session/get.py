from datetime import datetime
from JWTConfiguration.auth import xenProtocol
import tornado.web
from bson.objectid import ObjectId
from con import Database
import time
import json


class SessionHandler(tornado.web.RequestHandler, Database):
    userTable = Database.db['users']
    sessionTable = Database.db['sessions']


    @xenProtocol
    # Get method for upcoming
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
                mUserId = str(mUserId)
            except:
                mUserId = None
            

            if mUserId:
                query = {'userId': mUserId}
 
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
                    '$addFields': {
                        'user_details': {
                            '$first': '$user_details'
                        }
                    }
                },
                {
                    '$project': {
                        '_id': {'$toString': '$_id'},
                        'userId': {'$toString': '$userId'},
                        'name': '$user_details.name',
                        'login_time': 1,
                        'logout_time': 1,
                        'duration': 1,
                    }
                }
            ]

            cursor = self.sessionTable.aggregate(aggregation_pipeline)
            async for session in cursor:
                session['login_time'] = format_timestamp(int(session['login_time']))
                session['login_out'] = format_timestamp(int(session['login_out']))
                session['duration'] = format_timestamp(int(session['duration']))
                result.append(session)

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



