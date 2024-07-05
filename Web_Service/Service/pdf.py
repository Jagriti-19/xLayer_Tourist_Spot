from JWTConfiguration.auth import xenProtocol
from con import Database
import tornado.web
from PyPDF2 import PdfWriter, PdfReader
from io import BytesIO
from reportlab.pdfgen import canvas
from bson.objectid import ObjectId

class PDFHandler(tornado.web.RequestHandler, Database):
    bookTable = Database.db['bookings']
    userTable = Database.db['users']

    @xenProtocol
    async def get(self):
            
        self.set_header('Content-Type', 'application/pdf')
        self.set_header('Content-Disposition', 'attachment; filename="booking_details.pdf"')

        booking_id = self.get_argument('bookingId', None)
        user_id = self.user_id


        if not booking_id:
            self.write("No bookingId provided")
            self.finish()
            return

        try:
            # Aggregation pipeline to retrieve booking details
            aggregation_pipeline = [
                {
                    '$match': {'_id': ObjectId(booking_id)}
                },
                {
                    '$lookup': {
                        'from': 'users',
                        'localField': 'userId',
                        'foreignField': '_id',
                        'as': 'user_details'
                    }
                },
                {
                    '$lookup': {
                        'from': 'spots',
                        'localField': 'spotId',
                        'foreignField': '_id',
                        'as': 'spot_details'
                    }
                },
                {
                    '$addFields': {
                        'user_details': {
                            '$first': '$user_details'
                        },
                        'spot_details': {
                            '$first': '$spot_details'
                        }
                    }
                },
                {
                    '$project': {
                        'ticketId': 1,
                        'name': '$user_details.name',
                        'spot_name': '$spot_details.name',
                        'total': 1,
                        'date': 1,
                        'status': 1,
                        'entry_fee': 1,
                        'quantity': 1,
                    }
                }
            ]

            # Perform aggregation and fetch the booking details
            booking = await self.bookTable.aggregate(aggregation_pipeline).to_list(length=1)

            if not booking:
                self.write(f"No booking found with id: {booking_id}")
                self.finish()
                return

            booking = booking[0]

            # Generate PDF
            output = BytesIO()
            p = canvas.Canvas(output)

            # Add details to the PDF with correct vertical spacing
            y_position = 730
            line_height = 20

            p.drawString(100, y_position, f"Ticket Number: {booking.get('ticketId')}")
            y_position -= line_height
            p.drawString(100, y_position, f"Spot Name: {booking.get('spot_name')}")
            y_position -= line_height
            p.drawString(100, y_position, f"Name: {booking.get('name')}")
            y_position -= line_height
            p.drawString(100, y_position, f"Total: {booking.get('total')}")
            y_position -= line_height
            p.drawString(100, y_position, f"Date: {booking.get('date')}")
            y_position -= line_height
            p.drawString(100, y_position, f"Status: {booking.get('status')}")
            y_position -= line_height
            p.drawString(100, y_position, f"Entry Fee (Adult): {booking['entry_fee']['adult']}")
            y_position -= line_height
            p.drawString(100, y_position, f"Entry Fee (Child): {booking['entry_fee']['child']}")
            y_position -= line_height
            p.drawString(100, y_position, f"Quantity (Adult): {booking['quantity']['adult']}")
            y_position -= line_height
            p.drawString(100, y_position, f"Quantity (Child): {booking['quantity']['child']}")

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
