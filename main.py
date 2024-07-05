

from Web_Service.Admin.getUsers import AdminHandler
from Web_Service.Athentication.signIn import SignInHandler
from Web_Service.Athentication.signOut import SignOutHandler
from Web_Service.Athentication.signUp import SignUpHandler
from Web_Service.Booking.Admin.bookingsBySpotId import GetBookingsBySpotId
from Web_Service.Booking.Admin.getBookings import BookingHandlerAdmin
from Web_Service.Booking.User.booking import BookingHandlerUser
from Web_Service.Capacity.capacity import CapacityHandler
from Web_Service.ForgetPassword.otp import OTPHandler
from Web_Service.ForgetPassword.reset import ResetHandler
from Web_Service.ForgetPassword.verify import VerifyHandler
from Web_Service.Review.Admin.reply import ReplyHandler
from Web_Service.Review.Admin.review import ReviewHandlerAdmin
from Web_Service.Review.User.review import ReviewHandlerUser
from Web_Service.Service.excel import ExcelHandler
from Web_Service.Service.pdf import PDFHandler
from Web_Service.Session.getSession import SessionHandler
from Web_Service.Spot.Admin.spot import SpotHandler
from Web_Service.Spot.User.allSpots import GetAllSpotsHandler
from Web_Service.Spot.User.getAvailableCapacity import GetAvailableCapacity
from Web_Service.Spot.User.getByDistrict import DistrictHandler
from Web_Service.Spot.User.search import SearchHandler
from Web_Service.Status.Admin.checkIn import CheckInHandlerAdmin
from Web_Service.Status.Admin.checkOut import CheckOutHandlerAdmin
from Web_Service.Status.User.cancel import CancelHandler
from Web_Service.Status.User.checkIn import CheckInHandlerUser
from Web_Service.Status.User.checkOut import CheckOutHandlerUser
from Web_Service.Status.User.upcoming import UpcomingHandler
from Web_Service.User.user import UserHandler
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
        (r'/web/sign-up', SignUpHandler),
        (r'/web/sign-in', SignInHandler),
        (r'/web/sign-out', SignOutHandler),
        (r'/web/session', SessionHandler),
        (r'/web/otp-send', OTPHandler),
        (r'/web/verify', VerifyHandler),
        (r'/web/reset', ResetHandler),
        (r'/web/admins', AdminHandler),
        (r'/web/users', UserHandler),
        (r'/web/spots', SpotHandler),
        (r'/web/search', SearchHandler),
        (r'/web/district', DistrictHandler),
        (r'/web/list', GetAllSpotsHandler),
        (r'/web/booking/user', BookingHandlerUser),
        (r'/web/booking/admin', BookingHandlerAdmin),
        (r'/web/bookings', GetBookingsBySpotId),
        (r'/web/upcoming', UpcomingHandler),
        (r'/web/check-in/admin', CheckInHandlerAdmin),
        (r'/web/check-in/user', CheckInHandlerUser),
        (r'/web/check-out/admin', CheckOutHandlerAdmin),
        (r'/web/check-out/user', CheckOutHandlerUser),
        (r'/web/cancels', CancelHandler),
        (r'/web/pdf', PDFHandler),
        (r'/web/excel', ExcelHandler),
        (r'/web/review/user', ReviewHandlerUser),
        (r'/web/review/admin', ReviewHandlerAdmin),
        (r'/web/reply', ReplyHandler),
        (r'/web/capacity/admin', CapacityHandler),
        (r'/web/capacity/user', GetAvailableCapacity),
        
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