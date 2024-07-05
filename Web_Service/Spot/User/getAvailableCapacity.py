import json
import tornado.web
from con import Database
from bson.objectid import ObjectId
from mimetypes import MimeTypes
from uuid import uuid4

class GetAvailableCapacity(tornado.web.RequestHandler, Database):
    spotTable = Database.db['spots']
    userTable = Database.db['users']
    capacityTable = Database.db['capacity'] 

    # GET method for retrieving spots by ID or all spots
    async def get(self):
        code = 4000
        status = False
        result = []
        message = ''

        try:
            mSpotId = self.get_argument('spotId', default=None)
            mDate = self.get_argument('date', default=None)

            if mSpotId and mDate:
                mSpotId = ObjectId(mSpotId)
                query = {'_id': mSpotId}
            else:
                message = 'spotId and date are required'
                code = 4001
                raise Exception
            

            # Define your MongoDB aggregation pipeline
            pipeline = [
                {
                    '$match': query  # Match the spotId
                },
                {
                    '$lookup': {
                        'from': 'capacity',
                        'localField': '_id',
                        'foreignField': 'spotId',
                        'as': 'capacity_details'
                    }
                },
                {
                    '$unwind': '$capacity_details'
                },
                {
                    '$match': {
                        'capacity_details.date': mDate
                    }
                },
                {
                    '$project': {
                        '_id': {'$toString': '$_id'},
                        'name': 1,
                        'description': 1,
                        'location': 1,
                        'images': 1,
                        'visiting_hours': 1,
                        'availableCapacity': '$capacity_details.availableCapacity',
                        'date': '$capacity_details.date'
                    }
                }
            ]

            # Execute the aggregation pipeline
            mSpot = self.spotTable.aggregate(pipeline)

            async for spot in mSpot:
                # Add image links
                for img in spot.get('images', []):
                    img['link'] = 'http://10.10.10.136/uploads/{}'.format(img.get('fileName'))
                
                result.append(spot)

            if len(result) > 0:
                message = 'Found'
                code = 2000
                status = True
            else:
                message = 'Not found'
                code = 4002

        except Exception as e:
            message = 'There is some issue'
            code = 5010
            raise Exception

        try:
            response = {
                'code': code,
                'message': message,
                'status': status,
            }

            if len(result) > 0:
                response['result'] = result

            # Serialize response using custom encoder to handle ObjectId
            self.set_header('Content-Type', 'application/json')
            self.write(json.dumps(response, default=str))
            self.finish()

        except Exception as e:
            message = 'There is some issue'
            code = 5011
            raise Exception
