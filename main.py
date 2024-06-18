
from Web_Service.Log_In.adminLogin import AdminLogInHandler
from Web_Service.Log_In.userLogin import UserLogInHandler
from Web_Service.Search_Spot_By_Name_Location.search import SearchHandlerByNameLocation
from Web_Service.Search_Spot_By_Name_Location_District.search import SearchHandlerByNameLocationDistrict
from Web_Service.Tourist_Spot.spot import SpotHandler
import tornado.ioloop
import tornado.web
from Web_Service.Sign_Up.user import UserHandler
from Web_Service.Sign_Up.admin import AdminHandler
from con import Database

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        response = {
            'message': 'Hello, world!'
        }
        self.write(response)

def make_app(db):
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/users", UserHandler),
        (r"/admins", AdminHandler),
        (r"/loginU", UserLogInHandler),
        (r"/loginA", AdminLogInHandler),
        (r"/spots", SpotHandler),
        (r"/search", SearchHandlerByNameLocation),
        (r"/searching", SearchHandlerByNameLocationDistrict),
    ])

if __name__ == "__main__":
    db = Database().db
    if db is None:
        print("Failed to connect to the database. Exiting.")
    else:
        app = make_app(db)
        app.listen(8080)
        print("Server is running on http://localhost:8080")
        tornado.ioloop.IOLoop.current().start()