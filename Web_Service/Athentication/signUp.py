import json
import re
import bcrypt
from bson.objectid import ObjectId
import tornado.web
from con import Database 

class SignUpHandler(tornado.web.RequestHandler, Database):
    userTable = Database.db['users']

    # POST method for creating a new user
    async def post(self):
        code = 4014
        status = False
        result = []
        message = ''

        try:
            # Parse the request body as JSON
            try:
                self.request.arguments = json.loads(self.request.body.decode())
            except Exception as e:
                code = 4024
                message = "Invalid JSON"
                raise Exception


            mName = self.request.arguments.get('name')
            

            #Validation
            if not (mName):
                message = 'Name is required'
                code = 4033
                raise Exception
            elif not isinstance(mName, str):
                message = 'Invalid name'
                code = 4034
                raise Exception
            elif len(mName)< 2:
                message = 'Name should be at least 2 characters long'
                code = 4035
                raise Exception
            elif not all(char.isalpha() or char.isspace() for char in mName):
                message = 'Name must only contain alphabetic characters and spaces'
                code = 4036
                raise Exception
            
            mName = mName.title()


            mEmail = self.request.arguments.get('email')


            # Validation
            if not (mEmail):
                code = 4037
                message = 'Email is required'
                raise Exception
            

            # Regular expression for validating email format
            email_regex = r'^[\w\.-]+@[a-zA-Z\d\-]+(\.[a-zA-Z\d\-]+)*\.[a-zA-Z]+$'
            if not re.match(email_regex, mEmail):
                code = 4038
                message = 'Invalid email format'
                raise Exception


           # Assuming you have mMobile as a string from the request arguments
            mMobile = self.request.arguments.get('mobile')

            # Validation
            if not mMobile:
                code = 4039
                message = 'Mobile number is required'
                raise Exception

            # Check if mMobile is a valid integer
            try:
                mMobile = int(mMobile)
            except Exception as e:
                code = 4040
                message = 'Mobile number must be an integer'
                raise Exception

            # Check if the length of the mobile number is between 10 to 12 digits
            if not (10 <= len(str(mMobile)) <= 12):
                code = 4041
                message = 'Mobile number should be between 10 to 12 digits'
                raise Exception


            mAddress = self.request.arguments.get('address')


            # Validation 
            if not mAddress:
                code = 40455
                message = 'Address is required'
                raise Exception

   
            mPassword = self.request.arguments.get('password')


            # Validation
            if not mPassword:
                code = 4041
                message = 'Password is required'
                raise Exception

            # Password complexity requirements
            if len(mPassword) < 8:
                code = 4042
                message = 'Password should be at least 8 characters long'
                raise Exception

            if not any(char.isupper() for char in mPassword):
                code = 4043
                message = 'Password should contain at least one uppercase letter'
                raise Exception

            if not any(char.islower() for char in mPassword):
                code = 4044
                message = 'Password should contain at least one lowercase letter'
                raise Exception

            if not any(char.isdigit() for char in mPassword):
                code = 4045
                message = 'Password should contain at least one digit'
                raise Exception

            special_characters = '!@#$%^&*()_+-=[]{}|;:,.<>?'
            if not any(char in special_characters for char in mPassword):
                code = 4046
                message = 'Password should contain at least one special character: !@#$%^&*()_+-=[]{}|;:,.<>?'
                raise Exception

            # No common passwords check (example list, adjust as needed)
            common_passwords = ['password', 'password123', '123456', 'qwerty']
            if mPassword.lower() in common_passwords:
                code = 4047
                message = 'Password must not be a commonly used password'
                raise Exception


            mConfirmPassword = self.request.arguments.get('confirmPassword')


            # Validation
            if not mConfirmPassword:
                code = 4048
                message = 'Confirm password is required'
                raise Exception


            # Validate password confirmation
            if mPassword != mConfirmPassword:
                code = 1003
                message = 'Passwords do not match'
                raise Exception


            # Hash the password
            mPassword = self.request.arguments.get('password')
            hashed_password = bcrypt.hashpw(mPassword.encode(), bcrypt.gensalt())

            # Create the user data dictionary
            data = {
                'name': mName,
                'email': mEmail,
                'mobile': mMobile,
                'address': mAddress,
                'password': hashed_password
            }

            # Insert the user into the database
            try:
                addUser = await self.userTable.insert_one(data)
                if addUser.inserted_id:
                    code = 1004
                    status = True
                    message = 'User added successfully'
                    result.append({
                        'userId': str(addUser.inserted_id)
                    })
                else:
                    code = 1005
                    message = 'Failed to add user'
                    raise Exception
            except Exception as e:
                exe = str(e).split(':')
                if 'mobile_number' in exe[2]:
                    message = 'Mobile number already exists.'
                    code = 5477
                    raise Exception
                if 'email' in exe[2]:
                    message = 'email already exists.'
                    code = 5477
                    raise Exception
            
        except Exception as e:
            if not len(message):
                message = 'Internal Server Error'
                code = 1005
                raise Exception
            

        response = {
            'code': code,
            'message': message,
            'status': status,
        }

        try:
            if len(result):
                response['result'] = result

            self.write(response)
            self.finish()

        except Exception as e:
            message = 'There is some issue'
            code = 1006
            raise Exception
 
   