import json
import re
import tornado.web
from bson.objectid import ObjectId
from con import Database

class SpotHandler(tornado.web.RequestHandler, Database):
    spotTable = Database.db['spots']

    # POST method for creating a new spot
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

            # Extract and validate fields from the request
            mName = self.request.arguments.get('name')
            mDescription = self.request.arguments.get('description')
            mLocation = self.request.arguments.get('location')
            mDistrict = self.request.arguments.get('district')
            mCategory = self.request.arguments.get('category')
            mEntryFee = self.request.arguments.get('entry_fee', {})
            mEntryFeeAd = mEntryFee.get('adult')
            mEntryFeeCh = mEntryFee.get('child')
            mVisitingHours = self.request.arguments.get('visiting_hours', {})
            mMonday = mVisitingHours.get('monday')
            mTuesday = mVisitingHours.get('tuesday')
            mWednesday = mVisitingHours.get('wednesday')
            mThursday = mVisitingHours.get('thursday')
            mFriday = mVisitingHours.get('friday')
            mSaturday = mVisitingHours.get('saturday')
            mSunday = mVisitingHours.get('sunday')
            mPhotos = self.request.arguments.get('photos', {})
            mPhoto1 = mPhotos.get('photo1')
            mPhoto2 = mPhotos.get('photo2')
            mPhoto3 = mPhotos.get('photo3')

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

            # Validation for description
            if not mDescription:
                message = 'Description is required'
                code = 4033
                raise Exception

            # Validation for location
            if not mLocation:
                message = 'Location is required'
                code = 4039
                raise Exception
            
            # Validation for district
            if not mDistrict:
                message = 'District is required'
                code = 4040
                raise Exception

            # Validation for category
            if not mCategory:
                message = 'Category is required'
                code = 4045
                raise Exception

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

            # Validation for visiting hours
            visiting_hours_pattern = r'^\d{2} (AM|PM) - \d{2} (AM|PM)$'
            days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            for day in days:
                if not self.request.arguments['visiting_hours'].get(day):
                    message = f'{day.capitalize()} visiting hours are required'
                    code = 4052
                    raise Exception
                if not re.match(visiting_hours_pattern, self.request.arguments['visiting_hours'].get(day)):
                    message = f'{day.capitalize()} visiting hours must be in "HH AM/PM - HH AM/PM" format'
                    code = 4053
                    raise Exception

            # Validation for photos
            if not mPhotos:
                message = 'Photos are required'
                code = 4054
                raise Exception

            # Create the spot data dictionary
            data = {
                'name': mName,
                'description': mDescription,
                'location': mLocation,
                'district': mDistrict,
                'category': mCategory,
                'entry_fee': {
                    'adult': mEntryFeeAd,
                    'child': mEntryFeeCh
                },
                'visiting_hours': {
                    'monday': mMonday,
                    'tuesday': mTuesday,
                    'wednesday': mWednesday,
                    'thursday': mThursday,
                    'friday': mFriday,
                    'saturday': mSaturday,
                    'sunday': mSunday
                },
                'photos': {
                    'photo1': mPhoto1,
                    'photo2': mPhoto2,
                    'photo3': mPhoto3
                }
            }

            try:
                # Insert the spot into the database
                addSpot = await self.spotTable.insert_one(data)
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
            print(e)

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

            for spot in await mSpot.to_list(length=None):
                spot['_id'] = str(spot.get('_id'))  # Convert ObjectId to string   
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
        


    # PUT method for Updating spots by ID
    async def put(self):
        code = 5014
        status = False
        result = None
        message = ''

        try:
            # Parse the request body as JSON
            try:
                self.request.arguments = json.loads(self.request.body.decode())
            except Exception as e:
                code = 5024
                message = "Invalid JSON"
                raise Exception(message)

            mSpotId = self.request.arguments.get('spotId')
            if not mSpotId:
                code = 5025
                message = 'Spot ID is required'
                raise Exception(message)

            try:
                mSpotId = ObjectId(mSpotId)
            except Exception as e:
                code = 5026
                message = "Invalid spot ID format"
                raise Exception(message)

            mName = self.request.arguments.get('name')
            mDescription = self.request.arguments.get('description')
            mLocation = self.request.arguments.get('location')
            mDistrict = self.request.arguments.get('district')
            mCategory = self.request.arguments.get('category')
            mEntryFee = self.request.arguments.get('entry_fee', {})
            mEntryFeeAd = mEntryFee.get('adult')
            mEntryFeeCh = mEntryFee.get('child')
            mVisitingHours = self.request.arguments.get('visiting_hours', {})
            mMonday = mVisitingHours.get('monday')
            mTuesday = mVisitingHours.get('tuesday')
            mWednesday = mVisitingHours.get('wednesday')
            mThursday = mVisitingHours.get('thursday')
            mFriday = mVisitingHours.get('friday')
            mSaturday = mVisitingHours.get('saturday')
            mSunday = mVisitingHours.get('sunday')
            mPhotos = self.request.arguments.get('photos', {})
            mPhoto1 = mPhotos.get('photo1')
            mPhoto2 = mPhotos.get('photo2')
            mPhoto3 = mPhotos.get('photo3')

            # Validation for name
            if not mName:
                message = 'Name is required'
                code = 5033
                raise Exception(message)
            elif not isinstance(mName, str):
                message = 'Invalid name'
                code = 5034
                raise Exception(message)
            elif len(mName) < 2:
                message = 'Name should be at least 2 characters long'
                code = 5035
                raise Exception(message)
            elif not all(char.isalpha() or char.isspace() for char in mName):
                message = 'Name must only contain alphabetic characters and spaces'
                code = 5036
                raise Exception(message)

            # Validation for description
            if not mDescription:
                message = 'Description is required'
                code = 5037
                raise Exception(message)

            # Validation for location
            if not mLocation:
                message = 'Location is required'
                code = 5038
                raise Exception(message)
            
            # Validation for district
            if not mDistrict:
                message = 'District is required'
                code = 5039
                raise Exception(message)

            # Validation for category
            if not mCategory:
                message = 'Category is required'
                code = 5040
                raise Exception(message)

            # Validation for entry fee
            if mEntryFeeAd is None:
                message = 'Entry fee for adult is required'
                code = 5041
                raise Exception(message)
            try:
                mEntryFeeAd = float(mEntryFeeAd)
                if mEntryFeeAd < 0:
                    raise Exception
            except Exception as e:
                message = 'Entry fee for adult must be a positive number'
                code = 5042
                raise Exception(message)

            if mEntryFeeCh is None:
                message = 'Entry fee for child is required'
                code = 5043
                raise Exception(message)
            try:
                mEntryFeeCh = float(mEntryFeeCh)
                if mEntryFeeCh < 0:
                    raise Exception
            except Exception as e:
                message = 'Entry fee for child must be a positive number'
                code = 5044
                raise Exception(message)

            # Validation for visiting hours
            visiting_hours_pattern = r'^\d{2} (AM|PM) - \d{2} (AM|PM)$'
            days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            for day in days:
                if not mVisitingHours.get(day):
                    message = f'{day.capitalize()} visiting hours are required'
                    code = 5045
                    raise Exception(message)
                if not re.match(visiting_hours_pattern, mVisitingHours.get(day)):
                    message = f'{day.capitalize()} visiting hours must be in "HH AM/PM - HH AM/PM" format'
                    code = 5046
                    raise Exception(message)

            # Validation for photos
            if not mPhotos:
                message = 'Photos are required'
                code = 5047
                raise Exception(message)

            # Prepare updated data
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
                'visiting_hours': {
                    'monday': mMonday,
                    'tuesday': mTuesday,
                    'wednesday': mWednesday,
                    'thursday': mThursday,
                    'friday': mFriday,
                    'saturday': mSaturday,
                    'sunday': mSunday
                },
                'photos': {
                    'photo1': mPhoto1,
                    'photo2': mPhoto2,
                    'photo3': mPhoto3
                }
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
            raise Exception(message)




    #DELETE method for deleting spots by ID
    async def delete(self):
        code = 6014
        status = False
        message = ''

        try:
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

