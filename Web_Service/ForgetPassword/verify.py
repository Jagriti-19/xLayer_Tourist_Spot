import json
import tornado.web
import time
from con import Database
from bson.objectid import ObjectId

SECRET_KEY = "Xlayer.in"

class VerifyHandler(tornado.web.RequestHandler, Database):
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

            otp = self.request.arguments.get('otp')
            mEmail = self.request.arguments.get('email')

            # Validation
            if not otp:
                code = 4037
                message = 'OTP is required'
                raise Exception

            if not mEmail:
                code = 4037
                message = 'Email is required'
                raise Exception

            # Find user by OTP and email
            user = await self.userTable.find_one({'otp': otp, 'email': mEmail})
            if not user:
                code = 4049
                message = 'Invalid OTP or Email'
                raise Exception

            # Verify OTP expiration time
            otp_expiry = user.get('otp_expiry')

            if not otp_expiry or time.time() > otp_expiry:
                code = 4052
                message = 'OTP has expired'
                raise Exception

            # OTP is valid
            code = 1000
            status = True
            message = 'OTP is valid. Proceed with password reset.'

        except Exception as e:
            message = 'Internal Server Error'
            code = 1005

        response = {
            'code': code,
            'message': message,
            'status': status,
        }

        try:
            self.set_header("Content-Type", "application/json")
            self.write(response)
            self.finish()
        except Exception as e:
            message = 'There is some issue'
            code = 1006
            raise Exception
