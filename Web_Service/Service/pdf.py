from con import Database
import tornado.web
from PyPDF2 import PdfWriter, PdfReader
from io import BytesIO
from reportlab.pdfgen import canvas
from bson.objectid import ObjectId  # Ensure this import is available

class PDFHandler(tornado.web.RequestHandler, Database):
    bookTable = Database.db['bookings']
    
    async def get(self):
        self.set_header('Content-Type', 'application/pdf')
        self.set_header('Content-Disposition', 'attachment; filename="booking_details.pdf"')

        booking_id = self.get_argument('bookingId', None)

        if not booking_id:
            self.write("No bookingId provided")
            self.finish()
            return

        try:
            # Fetch booking details from database
            booking = await self.bookTable.find_one({'_id': ObjectId(booking_id)})
            
            if not booking:
                self.write(f"No booking found with id: {booking_id}")
                self.finish()
                return
            
            # Generate PDF
            output = BytesIO()
            p = canvas.Canvas(output)

            # Example content, modify as per your requirement
            p.drawString(100, 750, f"Booking ID: {booking_id}")
            p.drawString(100, 730, f"Spot ID: {booking.get('spotId')}")
            p.drawString(100, 710, f"User ID: {booking.get('userId')}")
            p.drawString(100, 690, f"Name: {booking.get('name')}")
            p.drawString(100, 670, f"Email: {booking.get('email')}")
            p.drawString(100, 650, f"Mobile: {booking.get('mobile')}")
            p.drawString(100, 630, f"Available Dates: {booking.get('available dates')}")
            p.drawString(100, 610, f"Entry Fee (Adult): {booking['entry_fee']['adult']}")
            p.drawString(100, 590, f"Entry Fee (Child): {booking['entry_fee']['child']}")
            p.drawString(100, 570, f"Quantity (Adult): {booking['quantity']['adult']}")
            p.drawString(100, 550, f"Quantity (Child): {booking['quantity']['child']}")
            p.drawString(100, 530, f"Visiting Hours: {booking.get('visiting_hours')}")
            p.drawString(100, 510, f"Total: {booking.get('total')}")
            p.drawString(100, 490, f"Booking Date & Time: {booking.get('booking_date&time')}")
            p.drawString(100, 470, f"Status: {booking.get('status')}")

            p.showPage()
            p.save()

            # Prepare the PDF for download
            output.seek(0)
            pdf_reader = PdfReader(output)
            pdf_writer = PdfWriter()
            pdf_writer.add_page(pdf_reader.pages[0])

            final_output = BytesIO()
            pdf_writer.write(final_output)
            final_output.seek(0)

            self.write(final_output.read())
            self.finish()

        except Exception as e:
            self.write(f"Error generating PDF: {str(e)}")
            self.finish()
