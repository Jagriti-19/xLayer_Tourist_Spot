from bson import ObjectId
from con import Database
import jwt

SECRET_KEY = "Xlayer.in"

sessionTable = Database.db['sessions']

def xenProtocol(method):
    async def wrapper(self, *args, **kwargs):
        auth_header = self.request.headers.get("Authorization")
        if not auth_header:
            self.set_status(401)
            self.write({
                'code': 4026,
                'message': "Authorization header missing",
                'status': False
            })
            self.finish()
            return
        
        try:
            token = auth_header.split()[1]
            decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            self.sessionId = decoded.get("_id")
            self.user_id = decoded.get("user_id")
            
            session = await sessionTable.find_one({"_id": ObjectId(self.sessionId)})
            if not session or session.get('blacklisted'):
                self.set_status(401)
                self.write({
                    'code': 4077,
                    'message': 'Invalid or blacklisted token',
                    'status': False
                })
                self.finish()
                return
        except jwt.ExpiredSignatureError:
            self.set_status(401)
            self.write({
                'code': 4012,
                'message': 'Token has expired, Login again!',
                'status': False
            })
            self.finish()
            return
        except jwt.InvalidTokenError:
            self.set_status(401)
            self.write({
                    'code': 4020,
                    'message': 'Invalid token',
                    'status': False
            })
            self.finish()
            return
        except Exception as e:
            self.set_status(500)
            self.write({
                'code': 5000,
                'message': str(e),
                'status': False
            })
            self.finish()
            return

        await method(self, *args, **kwargs)
    return wrapper
