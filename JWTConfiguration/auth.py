import json
import time
from bson.objectid import ObjectId
from con import Database
import jwt

SECRET_KEY = "Xlayer.in"

sessionTable = Database.db['sessions']
logTable = Database.db['logs']

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
        
        # Decode request body with fallback
        try:
            body = self.request.body.decode('utf-8')
        except UnicodeDecodeError:
            body = self.request.body.hex()  # Store as hex string if decoding fails

        # Handle JSON body
        try:
            json_body = json.loads(body)
        except json.JSONDecodeError:
            json_body = {}

        # Collect all arguments including query and body
        all_arguments = {k: self.get_argument(k) for k in self.request.arguments}
        if self.request.method in ['POST', 'PUT', 'DELETE'] and json_body:
            all_arguments.update(json_body)

        # Log the token usage
        try:
            operation_name = method.__name__
        except AttributeError:
            operation_name = str(method)  # Fallback to string representation if __name__ fails

        log_entry = {
            "user_id": self.user_id,
            "session_id": self.sessionId,
            "operation": operation_name,
            "timestamp": int(time.time()),
            "request_data": {
                "path": self.request.path,
                "headers": dict(self.request.headers),
                "arguments": all_arguments
            }
        }
        await logTable.insert_one(log_entry)

        await method(self, *args, **kwargs)

    return wrapper
