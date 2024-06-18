
from Web_Service.Admin.admin import AdminHandler
from Web_Service.Athentication.Admin.adminLogin import AdminLogInHandler
from Web_Service.Athentication.User.user import UserHandler
from Web_Service.Athentication.User.userLogin import UserLogInHandler
from Web_Service.Booking.User.book import BookingHandler
from Web_Service.Tourist.Admin.search import SearchHandlerByNameLocation
from Web_Service.Tourist.Admin.spot import SpotHandler
from Web_Service.Tourist.User.search import SearchHandlerByNameLocationDistrict
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
        (r"/web/search", SearchHandlerByNameLocation),
        (r"/web/searching", SearchHandlerByNameLocationDistrict),
        (r"/web/booking", BookingHandler),
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