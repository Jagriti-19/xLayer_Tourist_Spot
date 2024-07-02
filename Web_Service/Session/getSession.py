from datetime import datetime
from JWTConfiguration.auth import xenProtocol
import tornado.web
from bson.objectid import ObjectId
from con import Database
import json


class SessionHandler(tornado.web.RequestHandler, Database):
    userTable = Database.db['users']
    sessionTable = Database.db['sessions']

    @xenProtocol
    async def get(self):
        code = 4000
        status = False
        result = []
        message = ''

        try:
            try:
                mUserId = self.get_argument('user_id')
                if not mUserId:
                    code = 4511
                    message = "User ID is required"
                    raise Exception
                mUserId = ObjectId(mUserId)
                query = {'user_id': mUserId}
            except Exception as e:
                    code = 4511
                    message = "Error processing user_id"
                    raise Exception

            aggregation_pipeline = [
                {
                    '$match': query
                },
                {
                    '$lookup': {
                        'from': 'users',
                        'localField': 'user_id',
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
                        'userId': {'$toString': '$user_id'},
                        'name': '$user_details.name',
                        'login_time': 1,
                        'logout_time': 1,
                        'duration': 1,
                    }
                }
            ]

            cursor = self.sessionTable.aggregate(aggregation_pipeline)
            async for session in cursor:
                session['login_time'] = format_timestamp(session.get('login_time'))
                session['logout_time'] = format_timestamp(session.get('logout_time'))
                session['duration'] = format_duration(session.get('duration'))
                result.append(session)

            if result:
                message = 'Found'
                code = 2000
                status = True
            else:
                message = 'No data found for the given user_id'
                status = False
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
            message = 'Error in response serialization'
            code = 5011
            raise Exception
        


def format_timestamp(timestamp):
    try:
        if timestamp is None:
            return None
        dt_object = datetime.fromtimestamp(timestamp)
        return dt_object.strftime("%A, %d %B %Y, %H:%M:%S")
    except Exception as e:
        print(f"Error formatting timestamp: {e}")
        return "Invalid Date"


def format_duration(duration):
    try:
        if duration is None:
            return None
        duration_seconds = int(duration)
        hours, remainder = divmod(duration_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}h {minutes}m {seconds}s"
    except Exception as e:
        print(f"Error formatting duration: {e}")
        return "Invalid Duration"
