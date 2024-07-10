from bson.objectid import ObjectId
import tornado.web
from con import Database 
import time
from JWTConfiguration.auth import xenProtocol

class SignOutHandler(tornado.web.RequestHandler, Database):
    sessionTable = Database.db['sessions']

    @xenProtocol
    async def post(self):
        code = 4014
        status = False
        message = ''
        
        

        try:
            code = 1000
            status = True
            message = 'User logged out successfully'

            # Find the session by sessionId
            session = await self.sessionTable.find_one({"_id": ObjectId(self.sessionId)})
            
            if not session:
                code = 4049
                message = 'Session not found'
                status = False
                raise Exception

            # Check if the session is already logged out
            if session.get('logout_time'):
                code = 4080
                message = 'User already logged out'
                status = False
                raise Exception

            # Update the session with logout time, duration, and blacklisted flag
            logout_time = int(time.time())
            duration = logout_time - session['login_time']
            await self.sessionTable.update_one(
                {"_id": ObjectId(self.sessionId)},
                {"$set": {"logout_time": logout_time, "duration": duration, "blacklisted": True}}
            )
            
        except Exception as e:
            if not message:
                message = 'Internal Server Error'
                code = 1005
                status = False

        response = {
            'code': code,
            'message': message,
            'status': status
        }

        try:
            self.set_header("Content-Type", "application/json")
            self.write(response)
            self.finish()

        except Exception as e:
            message = 'There is some issue'
            code = 1006
            raise Exception
