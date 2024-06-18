import tornado.web
from bson.objectid import ObjectId
from con import Database
import re

class SearchHandlerByNameLocation(tornado.web.RequestHandler, Database):
    spotTable = Database.db['spots']

    # Get spot By Name and Location
    async def get(self):
        code = 4000
        status = False
        result = []
        message = ''

        try:
            mName = str(self.get_argument('name'))
            mLocation = str(self.get_argument('location'))

            if not mName or not mLocation:
                message = 'Please provide both name and location'
                code = 4022
                raise Exception

            # Execute the query
            mSpots = self.spotTable.find(
                {
                    '$and': [
                        {
                            'name': {
                                '$regex': mName,
                                '$options': 'i'
                            }
                        },
                        {
                            'location': {
                                '$regex': mLocation,
                                '$options': 'i'
                            }
                        }
                    ]
                    
                }
            )

            async for spot in mSpots:
                spot['_id'] = str(spot.get('_id'))
                result.append(spot)

            if result:
                message = 'Found'
                code = 2000
                status = True
            else:
                message = 'No spots found matching the provided name and location'
                code = 4002
                raise Exception

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
            raise Exception
