import json
from bson.objectid import ObjectId
from con import Database
import tornado.web


class GetAllSpotsHandler(tornado.web.RequestHandler, Database):
    spotTable = Database.db['spots']

    async def get(self):
        code = 4000
        status = False
        result = []
        message = ''

        try:
            mSpot = self.spotTable.find({})  # Fetch all spots

            async for spot in mSpot:
                spot['_id'] = str(spot.get('_id'))  # Convert ObjectId to string
                
                # Iterate through each image in the 'images' array of the spot
                for img in spot.get('images', []):
                    img['link'] = 'http://10.10.10.132/uploads/{}'.format(img.get('fileName'))
                
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
            print(e)
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
            await self.finish()

        except Exception as e:
            message = 'There is some issue'
            code = 5011
            raise Exception
