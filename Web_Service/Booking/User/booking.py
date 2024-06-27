from datetime import datetime
import json
import re
from JWTConfiguration.auth import xenProtocol
import tornado.web
from bson.objectid import ObjectId
from con import Database
import time
from email.mime.text import MIMEText
import random


class BookingHandlerUser(tornado.web.RequestHandler, Database):
    bookTable = Database.db['bookings']
    spotTable = Database.db['spots']
    userTable = Database.db['users']

    @xenProtocol
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
                message = 'Invalid JSON'
                raise Exception

            # Extract and validate fields from the request
            mSpot = self.request.arguments.get('spotId')

             # Validation for spotId
            if not mSpot:
                message = 'SpotId is required'
                code = 4033
                raise Exception
            
            try:
                mSpot = ObjectId(mSpot)
            except Exception as e:
                message = 'Invalid spotId format'
                code = 4034
                raise Exception
            
            
            # Check if the spotId exists in the spotTable
            spot = await self.spotTable.find_one({'_id': ObjectId(mSpot)})
            if not spot:
                message = 'Invalid spotId. Spot not found.'
                code = 4034
                raise Exception

            mUser = self.user_id

            # Validation for userId
            if not mUser:
                message = 'UserId is required'
                code = 4033
                raise Exception
            
            try:
                mUser = ObjectId(mUser)
            except Exception as e:
                message = 'Invalid userId format'
                code = 4034
                raise Exception
            
            # Check if the userId exists in the userTable
            user = await self.userTable.find_one({'_id': ObjectId(mUser)})
            if not user:
                message = 'Invalid userId. User not found.'
                code = 4034
                raise Exception

            mName = self.request.arguments.get('name')

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
            

            # Assuming you have mMobile as a string from the request arguments
            mMobile = self.request.arguments.get('mobile')

            # Validation
            if not mMobile:
                code = 4039
                message = 'Mobile number is required'
                raise Exception

            # Check if mMobile is a valid integer
            try:
                mobile_number = int(mMobile)
            except ValueError:
                code = 4040
                message = 'Mobile number must be an integer'
                raise Exception

            # Check if the length of the mobile number is between 10 to 12 digits
            if not (10 <= len(str(mMobile)) <= 12):
                code = 4041
                message = 'Mobile number should be between 10 to 12 digits'
                raise Exception

            
            mEmail = self.request.arguments.get('Email')


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

            mAvailableDates = self.request.arguments.get('available dates')
            
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
            

            mEntryFee = self.request.arguments.get('entry_fee', {})
            mEntryFeeAd = mEntryFee.get('adult')

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
            

            mEntryFeeCh = mEntryFee.get('child')

            # Validation for entry fee
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
            

            mQuantity = self.request.arguments.get('quantity', {})
            mQuantityAd = mQuantity.get('adult')

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

            # Validation for quantity
            mQuantityCh = mQuantity.get('child')

            if mQuantityCh is not None:
                try:
                    mQuantityCh = int(mQuantityCh)
                    if mQuantityCh < 0:
                        raise Exception
                except Exception as e:
                    message = 'Quantity for child must be a positive integer'
                    code = 4066
                    raise Exception
                

            mVisitingHours = self.request.arguments.get('visiting_hours', {})
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
                
            
            mBookingDateTime = int(time.time())

            # Calculate total cost
            mTotal = 0
            if mQuantityAd is not None:
                mTotal += mQuantityAd * mEntryFeeAd
            if mQuantityCh is not None:
                mTotal += mQuantityCh * mEntryFeeCh


            self.request.arguments.get('status')

            mTicket = generate_ticket_id()

            # Check if available capacity is sufficient for booking
            total_guests = (mQuantityAd or 0) + (mQuantityCh or 0)
            if int(spot['available_capacity']) < total_guests:
                message = 'Insufficient available capacity for this booking'
                code = 4067
                raise Exception
            

            # Create the spot data dictionary
            booking_data = {
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
                'visiting_hours': mVisitingHours,
                'total': mTotal,
                'booking_date': mBookingDateTime,
                'ticketId': mTicket,
                'status': 'Pending'
            } 

            # Insert the booking into the database
            addBooking = await self.bookTable.insert_one(booking_data)
            if addBooking.inserted_id:
                code = 1004
                status = True
                message = 'Your booking is confirmed'
                result.append({
                    'bookingId': str(addBooking.inserted_id),
                    'total': mTotal,
                })


                # Update available capacity for the spot
                update_result = await self.spotTable.update_one(
                    {'_id': spot['_id']},
                    {'$inc': {'available_capacity': -total_guests}}
                )

                if update_result.modified_count != 1:
                    # If the update didn't modify exactly one document, handle accordingly
                    code = 1005
                    message = 'Failed to update available capacity for the spot'
                    raise Exception
               
               
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




def generate_ticket_id():
    prefix = '#'  # Prefix for the ticket ID
    ticket_number = random.randint(10000, 99999)  # Generate a random 5-digit number
    return f"{prefix}{ticket_number}"