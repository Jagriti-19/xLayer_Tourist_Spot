import time
from bson.objectid import ObjectId
import tornado.web
import json
from con import Database 
from datetime import datetime

class ReviewsHandler(tornado.web.RequestHandler, Database):
    reviewTable = Database.db['pending_reviews']
    reviewsTable = Database.db['reviews']
    spotTable = Database.db['spots']
    userTable = Database.db['users']


    # Get method for checking reviews
    async def get(self):
        code = 4000
        status = False
        result = []
        message = ''

        try:
            try:
                mUserId = self.get_argument('userId')
                if not mUserId:
                    raise Exception
                mUserId = ObjectId(mUserId)
            except:
                mUserId = None
            
            try:
                mReviewId = self.get_argument('reviewId')
                if not mReviewId:
                    raise Exception
                mReviewId = ObjectId(mReviewId)
            except:
                mReviewId = None

            try:
                mSpotId = self.get_argument('spotId')
                if not mSpotId:
                    raise Exception
                mSpotId = ObjectId(mSpotId)
            except:
                mSpotId = None

            if mReviewId:
                query = {'_id': mReviewId}
            elif mUserId:
                query = {'userId': mUserId}
            elif mSpotId:
                query = {'spotId': mSpotId}
            else:
                query = {}

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
                        'from': 'spots',
                        'localField': 'spotId',
                        'foreignField': '_id',
                        'as': 'spot_details'
                    }
                },
                {
                    '$addFields': {
                        'user_details': {
                            '$first': '$user_details'
                        },
                        'spot_details': {
                            '$first': '$spot_details'
                        }
                    }
                },
                {
                    '$project': {
                        '_id': {'$toString': '$_id'},
                        'userId': {'$toString': '$userId'},
                        'user_name': '$user_details.name',
                        'spotId': {'$toString': '$spotId'},
                        'spot_name': '$spot_details.name',
                        'feedback': 1,
                        'rating': 1,
                        'review_time': 1,
                        'status': 1
                        
                    }
                }
            ]

            cursor = self.reviewTable.aggregate(aggregation_pipeline)
            async for review in cursor:
                review['review_time'] = format_timestamp(int(review['review_time']))
                result.append(review)

            if result:
                message = 'Found'
                code = 2000
                status = True
            else:
                message = 'No reviews found'
                code = 4002

        except Exception as e:
            if not message:
                message = 'Internal server error'
                code = 5010
            print(f"Error: {e}")

        response = {
            'code': code,
            'message': message,
            'status': status,
        }

        try:
            if result:
                response['result'] = result

            self.set_header('Content-Type', 'application/json')
            self.write(json.dumps(response, default=str))
            await self.finish()

        except Exception as e:
            message = 'There is some issue'
            code = 5011
            print(f"Error in response serialization: {e}") 
            raise Exception



    # Put method for approving the reviews
    async def put(self):
        code = 4014
        status = False
        result = []
        message = ''

        try:
            # Extract reviewId from URL params
            mReviewId = self.get_argument('reviewId')

            try:
                mReviewId = ObjectId(mReviewId)
            except Exception as e:
                message = 'Invalid reviewId format'
                code = 4031
                raise Exception

            # Fetch existing review details
            review = await self.reviewTable.find_one({'_id': mReviewId})
            if not review:
                message = 'Review not found'
                code = 4021
                raise Exception

            # Update status and approved time
            updated_data = {
                '$set': {
                    'status': 'approved',
                    'approved_time': int(time.time())
                }
            }

            # Update the booking status and check-in time
            updated_result = await self.reviewTable.update_one(
                {'_id': mReviewId},
                updated_data
            )

            if updated_result.modified_count > 0:

                updated_review = await self.reviewTable.find_one({'_id': mReviewId})

                addCheckIn = await self.reviewsTable.insert_one(updated_review)

                if addCheckIn.inserted_id:

                    await self.reviewTable.delete_one({'_id': mReviewId})

                    code = 4019
                    status = True
                    message = 'Approved successfully'
                else:
                    code = 4020
                    message = 'Failed to move to reviews table'
            else:
                code = 4021
                message = 'Review not found or no changes made'

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
        



def format_timestamp(timestamp):
    try:
        dt_object = datetime.fromtimestamp(timestamp)
        return dt_object.strftime("%A, %d %B %Y, %H:%M:%S")
    except Exception as e:
        print(f"Error formatting timestamp: {e}")
        return "Invalid Date"