import json
from bson.objectid import ObjectId
import tornado.web
from con import Database 

class ReviewHandler(tornado.web.RequestHandler, Database):
    reviewTable = Database.db['reviews']
    spotTable = Database.db['spots']
    userTable = Database.db['users']


    # POST method for creating a reivew
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

            mUser = self.request.arguments.get('userId')

            # Validation for userId
            if not mUser:
                message = 'UserId is required'
                code = 4033
                raise Exception
            
            # Check if the userId exists in the userTable
            user = await self.userTable.find_one({'_id': ObjectId(mUser)})
            if not user:
                message = 'Invalid userId. User not found.'
                code = 4034
                raise Exception

            mRating = self.request.arguments.get('rating')
            
            # Validation for rating

            try:
                mRating = float(mRating)
            except ValueError:
                message = 'Rating must be a number'
                code = 4035
                raise Exception
            
            if not (1 <= mRating <= 5):
                message = 'Rating must be between 1 and 5'
                code = 4036
                raise Exception

            mFeedBack = self.request.arguments.get('feedback')

            # Validation for feedback
            if not (10 <= len(mFeedBack) <= 500):
                message = 'Feedback must be between 10 and 500 characters'
                code = 4037
                raise Exception
            
            # Profanity filter example (simple)
            profanity_list = ["badword1", "badword2"]
            if any(bad_word in mFeedBack.lower() for bad_word in profanity_list):
                message = 'Feedback contains inappropriate language'
                code = 4038
                raise Exception


            # Create the user data dictionary
            data = {
                'spotId': mSpot,
                'userId': mUser,
                'rating': mRating,
                'feedback': mFeedBack
            }

            # Insert the user into the database
            addReview = await self.reviewTable.insert_one(data)
            if addReview.inserted_id:
                code = 1004
                status = True
                message = 'Review added successfully'
                result.append({
                    'reviewId': str(addReview.inserted_id)
                })
            else:
                code = 1005
                message = 'Failed to add review'
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
 
   

    # Get method for reviews By spotId
    async def get(self):
        code = 4000
        status = False
        result = []
        message = ''

        try:
            mSpotId = self.get_argument('spotId')
            if not mSpotId:
                message = 'Please enter spotId'
                code = 4022
                raise Exception
            mSpotId = ObjectId(mSpotId)

            query = {'spotId': str(mSpotId)}
            mReviews = self.reviewTable.find(query)

            async for review in mReviews:
                review['_id'] = str(review.get('_id'))
                result.append(review)

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



    # Delete method for deleting reviews 
    async def delete(self):
        code = 6014
        status = False
        message = ''

        try:
            mReviewId = self.get_argument('reviewId')
            if not mReviewId:
                code = 6088
                message = 'Review ID is required'
                raise Exception
            try:
                mReviewId = ObjectId(mReviewId)
            except Exception:
                code = 6035
                message = 'Invalid review ID'
                raise Exception

            # Perform spot deletion
            result = await self.reviewTable.delete_one({"_id": mReviewId})

            if result.deleted_count:
                code = 6019
                status = True
                message = 'Reviews deleted successfully'
            else:
                code = 6020
                message = 'No reviews found for this review ID'

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




    # PUT method for updating reviews by reviewId
    async def put(self):
        code = 4014
        status = False
        result = None
        message = ''

        try:
            # Parse the request body as JSON
            try:
                self.request.arguments = json.loads(self.request.body.decode())
            except Exception as e:
                code = 5015
                message = 'Invalid JSON'
                raise Exception

            mReviewId = self.request.arguments.get('reviewId')

            if not mReviewId:
                code = 5016
                message = 'ReviewId is required'
                raise Exception

            try:
                mReviewId = ObjectId(mReviewId)
            except Exception as e:
                code = 5017
                message = "Invalid reviewId. Review not found."
                raise Exception

            # Extract and validate fields from the request
            mSpot = self.request.arguments.get('spotId')

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

            mUser = self.request.arguments.get('userId')

            # Validation for userId
            if not mUser:
                message = 'UserId is required'
                code = 4033
                raise Exception
            
            # Check if the userId exists in the userTable
            user = await self.userTable.find_one({'_id': ObjectId(mUser)})
            if not user:
                message = 'Invalid userId. User not found.'
                code = 4034
                raise Exception

            mRating = self.request.arguments.get('rating')
            
            # Validation for rating
            try:
                mRating = float(mRating)
            except ValueError:
                message = 'Rating must be a number'
                code = 4035
                raise Exception
            
            if not (1 <= mRating <= 5):
                message = 'Rating must be between 1 and 5'
                code = 4036
                raise Exception

            mFeedBack = self.request.arguments.get('feedback')

            # Validation for feedback
            if not (10 <= len(mFeedBack) <= 500):
                message = 'Feedback must be between 10 and 500 characters'
                code = 4037
                raise Exception
            

            # Create the review data dictionary
            updated_data = {
                'spotId': mSpot,
                'userId': mUser,
                'rating': mRating,
                'feedback': mFeedBack
            }

            # Update review in the database
            update_result = await self.reviewTable.update_one(
                {'_id': ObjectId(mReviewId)},
                {'$set': updated_data}
            )

            if update_result.modified_count > 0:
                code = 4019
                status = True
                message = 'Updated Successfully'
            else:
                code = 4020
                message = "Review not found or no changes made"

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
            self.write(response)
            self.finish()

        except Exception as e:
            message = 'There is some issue'
            code = 1006
            raise Exception
