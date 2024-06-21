import json
import bcrypt
from bson.objectid import ObjectId
import tornado.web
from con import Database 

class UserLogInHandler(tornado.web.RequestHandler, Database):
    userTable = Database.db['users']


    async def post(self):
        code = 4014
        status = False
        message = ''

        try:
            # Parse the request body as JSON
            try:
                self.request.arguments = json.loads(self.request.body.decode())
            except Exception as e:
                code = 4024
                message = "Invalid JSON"
                raise Exception

            mEmail = self.request.arguments.get('email')
            mPassword = self.request.arguments.get('password')

            # Validation
            if not (mEmail and mPassword):
                code = 4037
                message = 'Email and password are required'
                raise Exception
            

            # Find user by email
            user = await self.userTable.find_one({'email': mEmail})
            if not user:
                code = 4049
                message = 'User not found'
                raise Exception

            # Verify password
            if not bcrypt.checkpw(mPassword.encode(), user['password']):
                code = 4050
                message = 'Invalid password'
                raise Exception

            # Successful login
            code = 1000
            status = True
            message = 'User Login successfully'

        except Exception as e:
            if not len(message):
                message = 'Internal Server Error'
                code = 1005
                print(e)

        response = {
            'code': code,
            'message': message,
            'status': status,
        }

        try:
            self.write(response)
            self.finish()
        except Exception as e:
            message = 'There is some issue'
            code = 1006
            raise Exception




