import json
import re
import tornado.web
from con import Database


class DistrictHandler(tornado.web.RequestHandler, Database):
    spotTable = Database.db['spots']

    # GET method for retrieving spots by district
    async def get(self):
        code = 4000
        status = False
        result = []
        message = ''

        try:
            mDistrict = self.get_argument('district', default=None)

            if not mDistrict:
                message = 'District is required'
                code = 4001
                raise Exception

            query = {'district': mDistrict}

            mSpots = self.spotTable.find(query)
            async for spot in mSpots:
                spot['_id'] = str(spot.get('_id'))  # Convert ObjectId to string
                
                for img in spot.get('images', []):
                    img['link'] = 'http://10.10.10.114/uploads/{}'.format(img.get('fileName'))
                
                result.append(spot)

            if len(result):
                message = 'Found'
                code = 2000
                status = True
            else:
                message = 'Not found'
                code = 4002

        except Exception as e:
            if not message:
                message = 'There is some issue'
                code = 5010
                print(e)

        response = {
            'code': code,
            'message': message,
            'status': status,
        }

        if len(result):
            response['result'] = result

        # Serialize response using custom encoder to handle ObjectId
        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps(response, default=str))
        self.finish()


