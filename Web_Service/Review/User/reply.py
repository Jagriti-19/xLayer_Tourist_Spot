import json
import time
from JWTConfiguration.auth import xenProtocol
from bson.objectid import ObjectId
import tornado.web
from con import Database 

class ReplyHandler(tornado.web.RequestHandler, Database):
    reviewTable = Database.db['reviews']
    spotTable = Database.db['spots']
    userTable = Database.db['users']

    @xenProtocol
    async def put(self):
        code = 4014
        status = False
        result = []
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
                message = "Invalid reviewId format"
                raise Exception

            # Retrieve the review from the database
            review = await self.reviewTable.find_one({'_id': mReviewId})
            if not review:
                code = 4034
                message = 'Invalid reviewId. Review not found.'
                raise Exception
            
            # Ensure expiry_time exists in the review and is a valid timestamp
            if 'expiry_time' not in review:
                code = 4038
                message = 'Expiry time not found in review'
                raise Exception
            
            current_time = int(time.time())
            if current_time > review['expiry_time']:
                code = 4039
                message = 'Update period has expired'
                raise Exception

            mUserId = self.user_id

            # Validation for userId
            if not mUserId:
                code = 4033
                message = 'UserId is required'
                raise Exception
            
            # Check if the userId exists in the userTable
            user = await self.userTable.find_one({'_id': ObjectId(mUserId)})
            if not user:
                code = 4034
                message = 'Invalid userId. User not found.'
                raise Exception
            

            mComment = self.request.arguments.get('comment')

            # Validation for comment
            if not (1 <= len(mComment) <= 500):
                code = 4037
                message = 'Comment must be between 1 and 500 characters'
                raise Exception

            # Check if the review already has a reply from the same user
            if 'replies' in review and any(reply['userId'] == ObjectId(mUserId) for reply in review['replies']):
                # Update the existing reply
                update = {
                    '$set': {'replies.$[element]': {
                        'userId': ObjectId(mUserId),
                        'comment': mComment,
                        'reply_time': current_time
                    }}
                }
                await self.reviewTable.update_one({'_id': mReviewId, 'replies.userId': ObjectId(mUserId)}, update)
            else:
                # Add a new reply
                update = {
                    '$push': {
                        'replies': {
                            'userId': ObjectId(mUserId),
                            'comment': mComment,
                            'reply_time': current_time
                        }
                    }
                }
                await self.reviewTable.update_one({'_id': mReviewId}, update)

            code = 1004
            status = True
            message = 'Reply added to the review'
            result.append({
                'reviewId': str(mReviewId)
            })

        except Exception as e:
            code = code if code != 4014 else 1005
            message = message if message else 'Internal Server Error'

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
            self.finish()

        except Exception as e:
            message = 'Error in response handling: {}'.format(str(e))
            code = 1006
