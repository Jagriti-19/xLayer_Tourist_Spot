

from Web_Service.Admin.getusers import AdminHandler
from Web_Service.Athentication.User.user import UserHandler
from Web_Service.Athentication.User.login import UserLogInHandler
from Web_Service.Athentication.logout import LogoutHandler
from Web_Service.Booking.Admin.booking import BookingHandlerAdmin
from Web_Service.Booking.Admin.bookingsbyspotid import GetBookingsBySpotId
from Web_Service.Booking.User.booking import BookingHandlerUser
from Web_Service.ForgetPassword.otp import OTPHandler
from Web_Service.ForgetPassword.reset import ResetPasswordHandler
from Web_Service.ForgetPassword.verify import VerifyOTPHandler
from Web_Service.Review.Admin.reviews import ReviewsHandler
from Web_Service.Review.User.review import ReviewHandler
from Web_Service.Service.pdf import PDFHandler
from Web_Service.Session.get import SessionHandler
from Web_Service.Status.User.checkIn import CheckInHandler
from Web_Service.Status.User.checkOut import CheckOutHandler
from Web_Service.Status.User.upcoming import UpcomingHandler
from Web_Service.Tourist.Admin.spot import SpotHandler
from Web_Service.Tourist.User.allSpots import GetAllSpotsHandler
from Web_Service.Tourist.User.getbydistrict import DistrictHandler
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
        (r'/web/', MainHandler),
        (r'/web/users', UserHandler),
        (r'/web/admins', AdminHandler),
        (r'/web/spots', SpotHandler),
        (r'/web/loginU', UserLogInHandler),
        (r'/web/log-out', LogoutHandler),
        (r'/web/otp-send', OTPHandler),
        (r'/web/verify', VerifyOTPHandler),
        (r'/web/reset', ResetPasswordHandler),
        (r'/web/search', SearchHandler),
        (r'/web/searching', GetAllSpotsHandler),
        (r'/web/booking', BookingHandlerUser),
        (r'/web/bookings', BookingHandlerAdmin),
        (r'/web/get-bookings', GetBookingsBySpotId),
        (r'/web/review', ReviewHandler),
        (r'/web/reviews', ReviewsHandler),
        (r'/web/upcoming', UpcomingHandler),
        (r'/web/check-in', CheckInHandler),
        (r'/web/check-out', CheckOutHandler),
        (r'/web/pdf', PDFHandler),
        (r'/web/district', DistrictHandler),
        (r'/web/session', SessionHandler),

        
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