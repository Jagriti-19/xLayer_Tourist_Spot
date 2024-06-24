import json
from bson.objectid import ObjectId
import tornado.web
from con import Database 


class AdminHandler(tornado.web.RequestHandler, Database):
    userTable = Database.db['users']


    # GET method for retrieving users by ID or all users
    async def get(self):
        code = 4000
        status = False
        result = []
        message = ''

        try:
            mUserId = self.get_argument('userId', default=None)

            if mUserId:
                mUserId = ObjectId(mUserId)
                query = {'_id': mUserId}
            else:
                query = {}

            mUser = self.userTable.find(query)

            for user in await mUser.to_list(length=None):
                user['_id'] = str(user.get('_id'))  # Convert ObjectId to string
                # Remove sensitive fields before appending to result
                user.pop('password', None)
                result.append(user)

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
        