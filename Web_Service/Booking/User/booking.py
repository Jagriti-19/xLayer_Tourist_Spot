from datetime import datetime
import json
import re
import tornado.web
from bson.objectid import ObjectId
from con import Database
import time

class BookingHandlerUser(tornado.web.RequestHandler, Database):
    bookTable = Database.db['bookings']
    spotTable = Database.db['spots']
    userTable = Database.db['users']

    # POST method for create booking
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
            mSpot = self.request.arguments.get('spotId')
            mUser = self.request.arguments.get('userId')
            mName = self.request.arguments.get('name')
            mMobile = self.request.arguments.get('mobile')
            mEmail = self.request.arguments.get('Email')
            mAvailableDates = self.request.arguments.get('available dates')
            mEntryFee = self.request.arguments.get('entry_fee', {})
            mEntryFeeAd = mEntryFee.get('adult')
            mEntryFeeCh = mEntryFee.get('child')
            mQuantity = self.request.arguments.get('quantity', {})
            mQuantityAd = mQuantity.get('adult')
            mQuantityCh = mQuantity.get('child')
            mVisitingHours = self.request.arguments.get('visiting_hours', {})
            mMonday = mVisitingHours.get('monday')
            mTuesday = mVisitingHours.get('tuesday')
            mWednesday = mVisitingHours.get('wednesday')
            mThursday = mVisitingHours.get('thursday')
            mFriday = mVisitingHours.get('friday')
            mSaturday = mVisitingHours.get('saturday')
            mSunday = mVisitingHours.get('sunday')

            # Validation for spotId
            if not mSpot:
                message = 'SpotId is required'
                code = 4033
                raise Exception

            # Check if the spotId exists in the spotTable
            spot = await self.spotTable.find_one({'_id': ObjectId(mSpot)})
            if not spot:
                message = 'Invalid spotId. Spot not found.'
                code = 4034
                raise Exception
            
             # Validation for userId
            if not mUser:
                message = 'UserId is required'
                code = 4033
                raise Exception

            # Check if the spotId exists in the spotTable
            user = await self.userTable.find_one({'_id': ObjectId(mUser)})
            if not user:
                message = 'Invalid userId. User not found.'
                code = 4034
                raise Exception

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

            # Validation for Email
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

            # Validation for Mobile
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
                raise Exception(message)
            try:
                mEntryFeeCh = float(mEntryFeeCh)
                if mEntryFeeCh < 0:
                    raise Exception
            except Exception as e:
                message = 'Entry fee for child must be a positive number'
                code = 4051
                raise Exception
            
            # Validation for quantity
            if mQuantityAd is None and mQuantityCh is None:
                message = 'At least one of adult or child quantity is required'
                code = 4064
                raise Exception

            if mQuantityAd is not None:
                try:
                    mQuantityAd = int(mQuantityAd)
                    if mQuantityAd < 0:
                        raise Exception
                except Exception as e:
                    message = 'Quantity for adult must be a positive integer'
                    code = 4065
                    raise Exception

            if mQuantityCh is not None:
                try:
                    mQuantityCh = int(mQuantityCh)
                    if mQuantityCh < 0:
                        raise Exception
                except Exception as e:
                    message = 'Quantity for child must be a positive integer'
                    code = 4066
                    raise Exception

            # Validation for available booking date
            if not mAvailableDates:
                message = 'Available booking date is required'
                code = 4060
                raise Exception

            # Ensure date is in dd-mm-yyyy format
            date_pattern = r'^\d{2}-\d{2}-\d{4}$'
            if not re.match(date_pattern, mAvailableDates):
                message = 'Date must be in "dd-mm-yyyy" format'
                code = 4061
                raise Exception

            # Check if date is current or future date
            try:
                booking_date = datetime.strptime(mAvailableDates, '%d-%m-%Y')
                if booking_date < datetime.now():
                    message = 'Booking date must be current or future date'
                    code = 4062
                    raise Exception
            except Exception as e:
                message = 'Invalid date'
                code = 4063
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
                
            
            mBookingDateTime = int(time.time())
            # formatted_time = time.strftime("%d %B %Y %H:%M:%S", time.localtime(mBookingDateTime))

            # Calculate total cost
            mTotal = 0
            if mQuantityAd is not None:
                mTotal += mQuantityAd * mEntryFeeAd
            if mQuantityCh is not None:
                mTotal += mQuantityCh * mEntryFeeCh

            # Create the spot data dictionary
            data = {
                'spotId': mSpot,
                'userId': mUser,
                'name': mName,
                'email': mEmail,
                'mobile': mMobile,
                'available dates': mAvailableDates,
                'entry_fee': {
                    'adult': mEntryFeeAd,
                    'child': mEntryFeeCh
                },
                'quantity': {
                    'adult': mQuantityAd,
                    'child': mQuantityCh
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
                'total': mTotal,
                'booking_date&time': mBookingDateTime
            }

            # Insert the booking into the database
            addBooking = await self.bookTable.insert_one(data)
            if addBooking.inserted_id:
                code = 1004
                status = True
                message = 'Your booking is confirmed'
                result.append({
                    'bookId': str(addBooking.inserted_id),
                    'total': mTotal,
                })
            else:
                code = 1005
                message = 'Failed to book'
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



   # GET method to get booking details using userId or bookingId
    async def get(self):
        code = 4000
        status = False
        result = []
        message = ''

        try:
            mUserId = self.get_argument('userId', None)
            mBookingId = self.get_argument('bookingId', None)

            if mUserId:
                query = {'userId': mUserId}
                cursor = self.bookTable.find(query)
                async for booking in cursor:
                    booking['_id'] = str(booking['_id'])
                    booking['userId'] = str(booking['userId'])
                    if 'booking_date&time' in booking:
                        booking['booking_date&time'] = format_timestamp(int(booking['booking_date&time']))
                    result.append(booking)

                if result:
                    message = 'Found'
                    code = 2000
                    status = True
                else:
                    message = 'No data found for the given userId'
                    code = 4002

            elif mBookingId:
                try:
                    mBookingId = ObjectId(mBookingId)
                except Exception as e:
                    message = 'Invalid bookingId format'
                    code = 4023
                    raise Exception

                booking = await self.bookTable.find_one({'_id': mBookingId})
                if booking:
                    booking['_id'] = str(booking['_id'])
                    booking['userId'] = str(booking['userId'])
                    if 'booking_date&time' in booking:
                        booking['booking_date&time'] = format_timestamp(int(booking['booking_date&time']))
                    result.append(booking)
                    message = 'Found'
                    code = 2000
                    status = True
                else:
                    message = 'No data found for the given bookingId'
                    code = 4002
            else:
                message = 'Please enter userId or bookingId'
                code = 4022

        except Exception as e:
            if not message:
                message = 'Internal server error'
                code = 5010
            print(e)

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
            print(e)
            raise Exception



# formatted_time = time.strftime("%d %B %Y %H:%M:%S", time.localtime(ts))


def format_timestamp(timestamp):
    try:
        # Convert timestamp to datetime object
        dt_object = datetime.fromtimestamp(timestamp)
        # Format datetime object as required
        return dt_object.strftime("%A, %d %B %Y, %H:%M:%S")
    except Exception as e:
        print(f"Error formatting timestamp: {e}")
        return "Invalid Date"
