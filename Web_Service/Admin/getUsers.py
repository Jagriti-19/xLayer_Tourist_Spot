import json
from JWTConfiguration.auth import xenProtocol
import tornado.web
from con import Database 
from bson.objectid import ObjectId


class AdminHandler(tornado.web.RequestHandler, Database):
    userTable = Database.db['users']


    @xenProtocol
    # GET method for retrieving users by ID or all users
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
            

            mUserId = self.get_argument('userId', default=None)

            if mUserId:
                try:
                    mUserId = ObjectId(mUserId)
                except Exception as e:
                    message = 'Invalid user ID format'
                    code = 4002
                    raise Exception

                query = {'_id': mUserId}
            else:
                query = {}

            mUser = self.userTable.find(query)

            for user in await mUser.to_list(length=None):
                user['_id'] = str(user.get('_id'))  # Convert ObjectId to string
                user.pop('password', None)  # Remove sensitive fields
                result.append(user)

            if result:
                message = 'Found'
                code = 2000
                status = True
            else:
                message = 'No users found'
                code = 4040
                status = False

        except Exception as e:
            if not message:
                message = 'Internal server error'
                code = 5000

        try:
            response = {
                'code': code,
                'message': message,
                'status': status,
            }

            if result:
                response['result'] = result

            self.set_header('Content-Type', 'application/json')
            self.write(json.dumps(response, default=str))
            self.finish()

        except Exception as e:
            message = 'There is some issue'
            code = 5001
            raise Exception
