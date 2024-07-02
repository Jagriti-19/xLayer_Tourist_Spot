import json
import re
import bcrypt
from JWTConfiguration.auth import xenProtocol
from bson.objectid import ObjectId
import tornado.web
from con import Database 

class UserHandler(tornado.web.RequestHandler, Database):
    userTable = Database.db['users']


    @xenProtocol
    # Get user By Id
    async def get(self):
        code = 4000
        status = False
        result = []
        message = ''

        try:
            mUserId = self.user_id
            if not mUserId:
                message = 'Please enter userId'
                code = 4022
                raise Exception
            mUserId = ObjectId(mUserId)

            query = {'_id': mUserId}
            mUser = self.userTable.find(query)

            async for user in mUser:
                user['_id'] = str(user.get('_id'))
                user['password'] = user.get('password').decode()  # Ensure password is string
                result.append(user)

            if result:
                message = 'Found'
                code = 2000
                status = True
            else:
                message = 'No data found'
                code = 4002
                raise Exception

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
            self.write(response)
            await self.finish()

        except Exception as e:
            message = 'There is some issue'
            code = 5011
            raise Exception


    @xenProtocol
    # PUT method for Updating user
    async def put(self):
        code = 5014
        status = False
        result = None
        message = ''

        try:
            try:
                # Parse the request body as JSON
                self.request.arguments = json.loads(self.request.body.decode())
            except Exception as e:
                code = 5015
                message = 'Invalid JSON'
                raise Exception

            mUserId = self.user_id
            if not mUserId:
                code = 5016
                message = 'User ID is required'
                raise Exception

            try:
                mUserId = ObjectId(mUserId)
            except Exception as e:
                code = 5017
                message = "Invalid user ID format"
                raise Exception

            mName = self.request.arguments.get('name')
            
            # Validation
            if not mName:
                message = 'Name is required'
                code = 4033
                raise Exception
            elif not isinstance(mName, str):
                message = 'Invalid name'
                code = 4034
                raise Exception
            elif len(mName) < 2:
                message = 'Name should be at least 2 characters long'
                code = 4035
                raise Exception
            elif not all(char.isalpha() or char.isspace() for char in mName):
                message = 'Name must only contain alphabetic characters and spaces'
                code = 4036
                raise Exception(message, code)

            mEmail = self.request.arguments.get('email')

            # Validation
            if not mEmail:
                code = 4037
                message = 'Email is required'
                raise Exception

            # Regular expression for validating email format
            email_regex = r'^[\w\.-]+@[a-zA-Z\d\-]+(\.[a-zA-Z\d\-]+)*\.[a-zA-Z]+$'
            if not re.match(email_regex, mEmail):
                code = 4038
                message = 'Invalid email format'
                raise Exception

            mMobile = self.request.arguments.get('mobile')

            # Validation
            if not mMobile:
                code = 4039
                message = 'Mobile number is required'
                raise Exception

            # Regular expression for validating mobile format (10 to 12 digits)
            mobile_regex = r'^\d{10,12}$'
            if not re.match(mobile_regex, mMobile):
                code = 4040
                message = 'Invalid mobile number format. Mobile number must be between 10 to 12 digits and contain only digits.'
                raise Exception


            mAddress = self.request.arguments.get('address')


            # Validation 
            if not mAddress:
                code = 40455
                message = 'Address is required'
                raise Exception


            # Prepare updated data
            updated_data = {
                'name': mName,
                'email': mEmail,
                'mobile': mMobile,
            }

            # Update user in the database
            result = await self.userTable.update_one(
                {'_id': mUserId},
                {'$set': updated_data}
            )

            if result.modified_count > 0:
                code = 4019
                status = True
                message = 'Updated Successfully'
            else:
                code = 4020
                message = "User not found or no changes made"

        except Exception as e:
            if not message:
                code = 4021
                message = 'Internal server error'
                raise Exception

        response = {
            'code': code,
            'message': message,
            'status': status,
        }

        try:
            if result is not None:
                response['result'] = {
                    'matched_count': result.matched_count,
                    'modified_count': result.modified_count
                }

            self.write(response)
            self.finish()

        except Exception as e:
            message = 'There is some issue'
            code = 4025
            raise Exception
