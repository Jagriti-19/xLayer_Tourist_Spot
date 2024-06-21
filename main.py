

from Web_Service.Admin.admin import AdminHandler
from Web_Service.Athentication.Admin.adminLogin import AdminLogInHandler
from Web_Service.Athentication.User.user import UserHandler
from Web_Service.Athentication.User.userLogin import UserLogInHandler
from Web_Service.Booking.Admin.booking import BookingHandlerAdmin
from Web_Service.Booking.User.booking import BookingHandlerUser
from Web_Service.Tourist.Admin.spot import SpotHandler
from Web_Service.Tourist.User.allSpots import GetAllSpotsHandler
from Web_Service.Tourist.User.search import SearchHandler
import tornado.ioloop
import tornado.web
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
        (r"/web/users", UserHandler),
        (r"/web/admins", AdminHandler),
        (r"/web/loginU", UserLogInHandler),
        (r"/web/loginA", AdminLogInHandler),
        (r"/web/spots", SpotHandler),
        (r"/web/search", SearchHandler),
        (r"/web/searching", GetAllSpotsHandler),
        (r"/web/booking", BookingHandlerUser),
        (r"/web/bookings", BookingHandlerAdmin),
        
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