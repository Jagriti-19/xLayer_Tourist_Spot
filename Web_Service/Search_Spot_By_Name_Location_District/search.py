import tornado.web
from bson.objectid import ObjectId
from con import Database

class SearchHandlerByNameLocationDistrict(tornado.web.RequestHandler, Database):
    spotTable = Database.db['spots']

    async def get(self):
        code = 4000
        status = False
        result = []
        message = ''

        try:
            # Get query parameters  
            mSearch = str(self.get_argument('search'))
            if not mSearch:
                message = 'Please provide any name, location, district, category'
                code = 2000
                raise Exception

           
            # Execute the query
            mSpots = self.spotTable.find(
                {
                    '$or': [
                        {
                            'name': {
                                '$regex': mSearch,
                                '$options': 'i'
                            }
                        },
                        {
                            'location': {
                                '$regex': mSearch,
                                '$options': 'i'
                            }
                        },
                        {
                            'district': {
                                '$regex': mSearch,
                                '$options': 'i'
                            }
                        },
                        {
                            'category': {
                                '$regex': mSearch,
                                '$options': 'i'
                            }
                        }
                    ]
                    
                }
            )

            # Process the results
            async for spot in mSpots:
                spot['_id'] = str(spot.get('_id'))
                result.append(spot)

            # Check if any results were found
            if result:
                message = 'Found'
                code = 2000
                status = True
            else:
                message = 'No spots found'
                code = 4002

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
            print(e)
            message = 'There is some issue'
            code = 5011
            raise Exception