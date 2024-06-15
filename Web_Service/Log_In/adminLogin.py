
import json
from bson.objectid import ObjectId
import tornado.web
from con import Database 

class AdminLogInHandler(tornado.web.RequestHandler, Database):
    adminTable = Database.db['admins']



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
            admin = await self.adminTable.find_one({'email': mEmail})
            if not admin:
                code = 4049
                message = 'Admin not found'
                raise Exception

            # Verify password
            admin = await self.adminTable.find_one({'password': mPassword})
            if not admin:
                code = 4050
                message = 'Invalid password'
                raise Exception

            # Successful login
            code = 1000
            status = True
            message = 'Admin Login successfully'

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