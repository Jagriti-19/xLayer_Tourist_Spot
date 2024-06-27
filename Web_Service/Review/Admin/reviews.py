import json
from JWTConfiguration.auth import xenProtocol
from bson.objectid import ObjectId
import tornado.web
from con import Database 

class ReviewsHandler(tornado.web.RequestHandler, Database):
    reviewTable = Database.db['reviews']
    spotTable = Database.db['spots']
    userTable = Database.db['users']


    @xenProtocol
    # Get method for reviews 
    async def get(self):
        code = 4000
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
            
            mReviewId = self.get_argument('reviewId', None)
            mUserId = self.get_argument('userId', None)
            mSpotId = self.get_argument('spotId', None)

            query = {}

            if mReviewId:
                try:
                    query['_id'] = ObjectId(mReviewId)
                except Exception as e:
                    message = 'Invalid review ID format'
                    code = 4022
                    raise Exception

            elif mUserId:
                try:
                    query['userId'] = ObjectId(mUserId)
                    query = {'userId': str(mUserId)}
                except Exception as e:
                    message = 'Invalid user ID format'
                    code = 4022
                    raise Exception

            elif mSpotId:
                try:
                    query['spotId'] = ObjectId(mSpotId)
                    query = {'spotId': str(mSpotId)}
                except Exception as e:
                    message = 'Invalid spot ID format'
                    code = 4022
                    raise Exception

            # If no specific ID is provided, retrieve all reviews
            if not (mReviewId or mUserId or mSpotId):
                query = {}

            mReviews = self.reviewTable.find(query)

            async for review in mReviews:
                review['_id'] = str(review.get('_id'))
                review['userId'] = str(review.get('userId'))
                review['spotId'] = str(review.get('spotId'))
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


