from JWTConfiguration.auth import xenProtocol
from con import Database
import tornado.web
from PyPDF2 import PdfWriter, PdfReader
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
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

            # Define greenish colors
            header_background_color = colors.HexColor("#006400")  # Dark Green for header
            header_text_color = colors.whitesmoke
            body_background_color = colors.HexColor("#98FB98")  # Pale Green for body
            grid_color = colors.HexColor("#006400")  # Dark Green for grid lines

            # Generate PDF
            output = BytesIO()
            doc = SimpleDocTemplate(output, pagesize=letter)

            styles = getSampleStyleSheet()
            elements = []

            title = Paragraph("Booking Details", styles['Title'])
            elements.append(title)
            elements.append(Spacer(1, 12))

            data = [
                ["Ticket Number", booking.get('ticketId')],
                ["Spot Name", booking.get('spot_name')],
                ["Name", booking.get('name')],
                ["Total", booking.get('total')],
                ["Date", booking.get('date')],
                ["Status", booking.get('status')],
                ["Entry Fee (Adult)", booking['entry_fee']['adult']],
                ["Entry Fee (Child)", booking['entry_fee']['child']],
                ["Quantity (Adult)", booking['quantity']['adult']],
                ["Quantity (Child)", booking['quantity']['child']]
            ]

            table = Table(data, colWidths=[2*inch, 4*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), header_background_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), header_text_color),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), body_background_color),
                ('GRID', (0, 0), (-1, -1), 1, grid_color),
                ('BOX', (0, 0), (-1, -1), 2, grid_color),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, grid_color),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ]))

            elements.append(table)
            doc.build(elements)

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
