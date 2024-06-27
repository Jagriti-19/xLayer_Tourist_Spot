import json
import re
from JWTConfiguration.auth import xenProtocol
import tornado.web
from con import Database
from bson.objectid import ObjectId
from mimetypes import MimeTypes
from uuid import uuid4

class SpotHandler(tornado.web.RequestHandler, Database):
    spotTable = Database.db['spots']
    userTable = Database.db['users']

    @xenProtocol
    # POST method for creating spots
    async def post(self):
        code = 4014
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
            try:
                files = {}
                args = {}
                b = self.request.headers.get('Content-Type')
                tornado.httputil.parse_body_arguments(b, self.request.body, args, files)
                data = json.loads(args['basic'][0])
            except Exception as e:
                message = 'Expected type in Form-Data.'
                code = 4036
                raise Exception

            # Extract and validate fields from the request
            mName = data.get('name')

            # Validation for name
            if not mName:
                message = 'Name is required'
                code = 4033
                raise Exception
            if not isinstance(mName, str):
                message = 'Invalid name'
                code = 4034
                raise Exception
            if len(mName) < 2:
                message = 'Name should be at least 2 characters long'
                code = 4035
                raise Exception
            if not all(char.isalpha() or char.isspace() for char in mName):
                message = 'Name must only contain alphabetic characters and spaces'
                code = 4036
                raise Exception
            
            mName = mName.title()

            mDescription = data.get('description')

            # Validation for description
            if not mDescription:
                message = 'Description is required'
                code = 4033
                raise Exception
        

            mLocation = data.get('location')

            # Validation for location
            if not mLocation:
                message = 'Location is required'
                code = 4039
                raise Exception

            mDistrict = data.get('district')

            # Validation for district
            if not mDistrict:
                message = 'District is required'
                code = 4040
                raise Exception
            
            mCategory = data.get('category')

            # Validation for category
            if not mCategory:
                message = 'Category is required'
                code = 4045
                raise Exception
            
            mEntryFee = data.get('entry_fee', {})
            mEntryFeeAd = mEntryFee.get('adult')
            mEntryFeeCh = mEntryFee.get('child')

            # Validation for entry fee
            if mEntryFeeAd is None:
                message = 'Entry fee for adult is required'
                code = 4048
                raise Exception
            try:
                mEntryFeeAd = float(mEntryFeeAd)
                if mEntryFeeAd < 0:
                    raise Exception
            except Exception as e:
                message = 'Entry fee for adult must be a positive number'
                code = 4049
                raise Exception

            if mEntryFeeCh is None:
                message = 'Entry fee for child is required'
                code = 4050
                raise Exception
            try:
                mEntryFeeCh = float(mEntryFeeCh)
                if mEntryFeeCh < 0:
                    raise Exception
            except Exception as e:
                message = 'Entry fee for child must be a positive number'
                code = 4051
                raise Exception

            mVisitingHours = data.get('visiting_hours', {})
            days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

            # Validation for visiting hours
            for day in days:
                if not mVisitingHours.get(day):
                    message = f'{day.capitalize()} visiting hours are required'
                    code = 4045
                    raise Exception

                visiting_hours_pattern = r'^\d{2}:\d{2} (AM|PM) - \d{2}:\d{2} (AM|PM)$'
                
                if not re.match(visiting_hours_pattern, mVisitingHours.get(day)):
                    message = f'{day.capitalize()} visiting hours must be in "HH:MM AM/PM - HH:MM AM/PM" format'
                    code = 4046
                    raise Exception


            files = self.request.files.get('photos', [])  # Assuming files are in a list under 'photos' key
            images = []
            for index, mPhoto in enumerate(files):
                try:
                    if not mPhoto:
                        raise Exception(f'{index} photo is missing')
                    mImage = self.save_photo(mPhoto, f'photo_{index}')
                    images.append({'fileName': mImage})
                except Exception as e:
                    message = str(e)
                    code = 4553
                    raise Exception

           
            # Validation for photos
            if not images:
                message = 'Photos are required'
                code = 4054
                raise Exception



            mAvailableCapacity = data.get('available_capacity')

            # Validation for capacity
            if mAvailableCapacity is None:
                message = 'Available Capacity is required'
                code = 4033
                raise Exception
            
            if mAvailableCapacity <= 0:
                    message = 'Available Capacity must be an integer'
                    code = 4034
                    raise Exception


            # Create the spot data dictionary
            spot_data = {
                'name': mName,
                'description': mDescription,
                'location': mLocation,
                'district': mDistrict,
                'category': mCategory,
                'entry_fee': {
                    'adult': mEntryFeeAd,
                    'child': mEntryFeeCh
                },
                'visiting_hours': mVisitingHours,
                'available_capacity': mAvailableCapacity,
                'images': images
                
            }

            try:
                # Insert the spot into the database
                addSpot = await self.spotTable.insert_one(spot_data)
                if addSpot.inserted_id:
                    code = 1004
                    status = True
                    message = 'Spot added successfully'
                    result.append({
                        'spotId': str(addSpot.inserted_id)
                    })
                else:
                    code = 1005
                    message = 'Failed to add spot'
                    raise Exception
                
            except Exception as e:
                exe = str(e).split(':')
                if 'name' in exe[2]:
                    message = 'Spot name already exists.'
                    code = 5477
                    raise Exception

        except Exception as e:
            if not message:
                message = 'Internal Server Error'
                code = 1005

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


    # GET method for retrieving spots by ID or all spots
    async def get(self):
        code = 4000
        status = False
        result = []
        message = ''

        try:
            mSpotId = self.get_argument('spotId', default=None)

            if mSpotId:
                mSpotId = ObjectId(mSpotId)
                query = {'_id': mSpotId}
            else:
                query = {}

            mSpot = self.spotTable.find(query)
            async for spot in mSpot:
                spot['_id'] = str(spot.get('_id'))
                
                for img in spot.get('images', []):
                    img['link'] = 'http://10.10.10.132/uploads/{}'.format(img.get('fileName'))
                
                result.append(spot)

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
        
    
    @xenProtocol
    # PUT method for Updating spots by ID
    async def put(self):
        code = 5014
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
            try:
                files = {}
                args = {}
                b = self.request.headers.get('Content-Type')
                tornado.httputil.parse_body_arguments(b, self.request.body, args, files)
                data = json.loads(args['basic'][0])
            except Exception as e:
                message = 'Expected type in Form-Data.'
                code = 4036
                raise Exception
            
            mSpotId = data.get('spotId')
            if not mSpotId:
                code = 5025
                message = 'Spot ID is required'
                raise Exception

            try:
                mSpotId = ObjectId(mSpotId)
            except Exception as e:
                code = 5026
                message = "Invalid spot ID format"
                raise Exception

            mName = data.get('name')

            # Validation for name
            if not mName:
                message = 'Name is required'
                code = 5033
                raise Exception
            elif not isinstance(mName, str):
                message = 'Invalid name'
                code = 5034
                raise Exception
            elif len(mName) < 2:
                message = 'Name should be at least 2 characters long'
                code = 5035
                raise Exception
            elif not all(char.isalpha() or char.isspace() for char in mName):
                message = 'Name must only contain alphabetic characters and spaces'
                code = 5036
                raise Exception
            

            mDescription = data.get('description')

            # Validation for description
            if not mDescription:
                message = 'Description is required'
                code = 5037
                raise Exception
            
            mLocation = data.get('location')

             # Validation for location
            if not mLocation:
                message = 'Location is required'
                code = 5038
                raise Exception
            
            mDistrict = data.get('district')

            # Validation for district
            if not mDistrict:
                message = 'District is required'
                code = 5039
                raise Exception
            
            mCategory = data.get('category')

            # Validation for category
            if not mCategory:
                message = 'Category is required'
                code = 5040
                raise Exception
            
            mEntryFee = data.get('entry_fee', {})
            mEntryFeeAd = mEntryFee.get('adult')

             # Validation for entry fee
            if mEntryFeeAd is None:
                message = 'Entry fee for adult is required'
                code = 5041
                raise Exception
            try:
                mEntryFeeAd = float(mEntryFeeAd)
                if mEntryFeeAd < 0:
                    raise Exception
            except Exception as e:
                message = 'Entry fee for adult must be a positive number'
                code = 5042
                raise Exception
            
            mEntryFeeCh = mEntryFee.get('child')

            if mEntryFeeCh is None:
                message = 'Entry fee for child is required'
                code = 5043
                raise Exception
            try:
                mEntryFeeCh = float(mEntryFeeCh)
                if mEntryFeeCh < 0:
                    raise Exception
            except Exception as e:
                message = 'Entry fee for child must be a positive number'
                code = 5044
                raise Exception
            
            mVisitingHours = data.get('visiting_hours', {})
            days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

            # Validation for Visiting hours
            for day in days:
                if not mVisitingHours.get(day):
                    message = f'{day.capitalize()} visiting hours are required'
                    code = 4045
                    raise Exception

                visiting_hours_pattern = r'^\d{2}:\d{2} (AM|PM) - \d{2}:\d{2} (AM|PM)$'
                
                if not re.match(visiting_hours_pattern, mVisitingHours.get(day)):
                    message = f'{day.capitalize()} visiting hours must be in "HH:MM AM/PM - HH:MM AM/PM" format'
                    code = 4046
                    raise Exception

            files = self.request.files.get('photos', [])  # Assuming files are in a list under 'photos' key
            images = []
            for index, mPhoto in enumerate(files):
                try:
                    if not mPhoto:
                        raise Exception(f'{index} photo is missing')
                    mImage = self.save_photo(mPhoto, f'photo_{index}')
                    images.append({'fileName': mImage})
                except Exception as e:
                    message = str(e)
                    code = 4553
                    raise Exception

            if not images:
                message = 'Photos are required'
                code = 4048
                raise Exception

            # Validation for photos
            if not images:
                message = 'Photos are required'
                code = 5047
                raise Exception


            mAvailableCapacity = data.get('available_capacity')

            # Validation for capacity
            if mAvailableCapacity is None:
                message = 'Available Capacity is required'
                code = 4033
                raise Exception
            
            if mAvailableCapacity <= 0:
                    message = 'Available Capacity must be an integer'
                    code = 4034
                    raise Exception
            

            # Updated data
            updated_data = {
                'name': mName,
                'description': mDescription,
                'location': mLocation,
                'district': mDistrict,
                'category': mCategory,
                'entry_fee': {
                    'adult': mEntryFeeAd,
                    'child': mEntryFeeCh
                },
                'visiting_hours': mVisitingHours,
                'available_capacity': mAvailableCapacity,
                'images': images
                
            }

            # Update spot in the database
            result = await self.spotTable.update_one(
                {'_id': mSpotId},
                {'$set': updated_data}
            )

            if result.modified_count > 0:
                code = 5019
                status = True
                message = 'Spot updated successfully'
            else:
                code = 5020
                message = "Spot not found or no changes made"

        except Exception as e:
            if not message:
                message = 'Internal server error'
                code = 5021
            print(e)

        response = {
            'code': code,
            'message': message,
            'status': status,
        }

        try:
            if result:
                response['result'] = {
                    'matched_count': result.matched_count,
                    'modified_count': result.modified_count
                }

            self.write(response)
            self.finish()

        except Exception as e:
            message = 'There is some issue'
            code = 5022
            raise Exception


    @xenProtocol
    # DELETE method for deleting spots by ID
    async def delete(self):
        code = 6014
        status = False
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
            
            mSpotId = self.get_argument('spotId', None)
            if not mSpotId:
                code = 6088
                message = 'Spot ID is required'
                raise Exception
            try:
                mSpotId = ObjectId(mSpotId)
            except Exception:
                code = 6035
                message = 'Invalid Spot ID'
                raise Exception

            # Perform spot deletion
            result = await self.spotTable.delete_one({"_id": mSpotId})

            if result.deleted_count:
                code = 6019
                status = True
                message = 'Spot deleted successfully'
            else:
                code = 6020
                message = 'Spot not found'

        except Exception as e:
            if not message:
                message = 'Internal server error'
                code = 6021
                raise Exception
            
        response = {
            'code': code,
            'message': message,
            'status': status,
        }

        try:
            self.set_header('Content-Type', 'application/json')
            self.write(json.dumps(response))
            await self.finish()

        except Exception as e:
            message = 'There is some issue'
            code = 6022
            raise Exception



    def save_photo(self, photo, key):
        unique_id = str(uuid4())
        mime_type, _ = MimeTypes().guess_type(photo['filename'])
        extension = MimeTypes().guess_extension(mime_type)
        file_name = f"{unique_id}{extension}"
        with open("uploads/" + file_name, 'wb') as output_file:
            output_file.write(photo['body'])
        return file_name