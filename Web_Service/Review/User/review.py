import json
import time
from JWTConfiguration.auth import xenProtocol
from bson.objectid import ObjectId
import tornado.web
from con import Database 

class ReviewHandlerUser(tornado.web.RequestHandler, Database):
    reviewTable = Database.db['reviews']
    spotTable = Database.db['spots']
    userTable = Database.db['users']


    @xenProtocol
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
            try:
                mSpot = ObjectId(mSpot)
            except Exception as e:
                message = 'Invalid spotId format'
                code = 4033
                raise Exception
            
            spot = await self.spotTable.find_one({'_id': mSpot})
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
            
            # Check if the userId exists in the userTable
            try:
                mUser = ObjectId(mUser)
            except Exception as e:
                message = 'Invalid userId format'
                code = 4033
                raise Exception
            
            user = await self.userTable.find_one({'_id': mUser})
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
            current_time = int(time.time())
            expiry_time = current_time + (50 * 60)
            
            data = {
                'spotId': mSpot,
                'userId': mUser,
                'rating': mRating,
                'feedback': mFeedBack,
                'review_time': int(time.time()),
                'expiry_time': expiry_time,
                'replies': [],
                'approved': False
            }

            # Insert the review into the database
            addReview = await self.reviewTable.insert_one(data)
            if addReview.inserted_id:
                code = 1004
                status = True
                message = 'Review submitted for approval'
                result.append({
                    'reviewId': str(addReview.inserted_id)
                })
            else:
                code = 1005
                message = 'Failed to add review'
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
            if result:
                response['result'] = result

            self.write(response)
            self.finish()

        except Exception as e:
            message = 'There is some issue'
            code = 1006



    # Get reviews using Spot Id
    async def get(self):
        code = 4000
        status = False
        result = []
        message = ''
        average_rating = 0

        try:
            try:
                mSpotId = self.get_argument('spotId')
                if not mSpotId:
                    raise Exception
                mSpotId = ObjectId(mSpotId)
            except:
                mSpotId = None

            query = {}
            if mSpotId:
                query['spotId'] = mSpotId
            query['approved'] = True

            aggregation_pipeline = [
                {
                    '$match': query
                },
                {
                    '$lookup': {
                        'from': 'users',
                        'localField': 'userId',
                        'foreignField': '_id',
                        'as': 'user_details'
                    }
                },
                {
                    '$lookup': {
                        'from': 'users',
                        'localField': 'replies.userId',
                        'foreignField': '_id',
                        'as': 'reply_users'
                    }
                },
                {
                    '$addFields': {
                        'user_details': {
                            '$first': '$user_details'
                        },
                        'replies': {
                            '$map': {
                                'input': '$replies',
                                'as': 'reply',
                                'in': {
                                    'user_name': {
                                        '$arrayElemAt': ['$reply_users.name', {'$indexOfArray': ['$reply_users._id', '$$reply.userId']}]
                                    },
                                    'comment': '$$reply.comment'
                                }
                            }
                        }
                    }
                },
                {
                    '$project': {
                        '_id': 0,
                        'user_name': '$user_details.name',
                        'feedback': 1,
                        'rating': 1,
                        'replies': 1
                    }
                }
            ]

            cursor = self.reviewTable.aggregate(aggregation_pipeline)
            async for reviews in cursor:
                result.append(reviews)

            # Calculate the average rating
            if mSpotId:
                rating_pipeline = [
                    {
                        '$match': {
                            'spotId': mSpotId,
                            'approved': True
                        }
                    },
                    {
                        '$group': {
                            '_id': '$spotId',
                            'averageRating': {'$avg': '$rating'}
                        }
                    }
                ]

                async for rating_result in self.reviewTable.aggregate(rating_pipeline):
                    average_rating = rating_result.get('averageRating', 0)

            if result:
                message = 'Found'
                code = 2000
                status = True
            else:
                message = 'No reviews found'
                code = 4002

        except Exception:
            if not message:
                message = 'Internal server error'
                code = 5010

        response = {
            'code': code,
            'message': message,
            'status': status,
            'average_rating': average_rating
        }

        try:
            if result:
                response['result'] = result

            self.set_header('Content-Type', 'application/json')
            self.write(json.dumps(response, default=str))
            await self.finish()

        except Exception:
            message = 'There is some issue'
            code = 5011
            raise Exception


    

    @xenProtocol
    # Delete method for deleting review
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