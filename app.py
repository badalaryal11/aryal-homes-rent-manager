# app.py
import os
from flask import Flask, render_template, request, redirect, url_for, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from fpdf import FPDF

# --- App and Database Configuration ---
app = Flask(__name__)
# Defines the path for the SQLite database file
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'rent.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Database Model Definition ---
# This class defines the structure of our database table.
class RentEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_name = db.Column(db.String(100), nullable=False)
    entry_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    rent = db.Column(db.Float, nullable=False, default=0)
    water = db.Column(db.Float, nullable=False, default=0)
    waste = db.Column(db.Float, nullable=False, default=0)
    electricity = db.Column(db.Float, nullable=False, default=0)
    repair = db.Column(db.Float, nullable=False, default=0)
    misc = db.Column(db.Float, nullable=False, default=0)

    # Calculate total on the fly
    @property
    def total(self):
        return self.rent + self.water + self.waste + self.electricity + self.repair + self.misc

    def __repr__(self):
        return f'<RentEntry for {self.tenant_name}>'

# --- PDF Generation Class ---
# A helper class to create the PDF invoice.
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Aryal Homes - Rent Invoice', 0, 1, 'C')
        self.ln(10) # Line break

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

# --- Web Routes ---
@app.route('/', methods=['GET', 'POST'])
def index():
    # If the form is submitted...
    if request.method == 'POST':
        # Get data from the form, converting to float and handling empty values
        tenant_name = request.form['tenant_name']
        entry_date = datetime.strptime(request.form['entry_date'], '%Y-%m-%d').date()
        rent = float(request.form.get('rent') or 0)
        water = float(request.form.get('water') or 0)
        waste = float(request.form.get('waste') or 0)
        electricity = float(request.form.get('electricity') or 0)
        repair = float(request.form.get('repair') or 0)
        misc = float(request.form.get('misc') or 0)

        # Create a new entry and add it to the database
        new_entry = RentEntry(
            tenant_name=tenant_name,
            entry_date=entry_date,
            rent=rent,
            water=water,
            waste=waste,
            electricity=electricity,
            repair=repair,
            misc=misc
        )
        db.session.add(new_entry)
        db.session.commit()
        return redirect(url_for('index'))

    # If it's a GET request, just show the page with all entries
    all_entries = RentEntry.query.order_by(RentEntry.entry_date.desc()).all()
    return render_template('index.html', entries=all_entries)

@app.route('/generate_pdf/<int:entry_id>')
def generate_pdf(entry_id):
    # Find the specific entry in the database
    entry = RentEntry.query.get_or_404(entry_id)

    # Create PDF object
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', '', 12)

    # Add content to the PDF
    pdf.cell(0, 10, f'Tenant Name: {entry.tenant_name}', 0, 1)
    pdf.cell(0, 10, f'Date: {entry.entry_date.strftime("%B %d, %Y")}', 0, 1)
    pdf.ln(5)

    # Table for charges
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(95, 10, 'Category', 1, 0, 'C')
    pdf.cell(95, 10, 'Amount (NPR)', 1, 1, 'C')

    pdf.set_font('Arial', '', 12)
    charges = {
        'Rent': entry.rent,
        'Water': entry.water,
        'Waste Management': entry.waste,
        'Electricity': entry.electricity,
        'Repair Costs': entry.repair,
        'Miscellaneous': entry.misc
    }

    for category, amount in charges.items():
        pdf.cell(95, 10, f'  {category}', 1, 0)
        pdf.cell(95, 10, f'  {amount:,.2f}', 1, 1)

    # Total
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(95, 10, '  Total Amount', 1, 0)
    pdf.cell(95, 10, f'  {entry.total:,.2f}', 1, 1)

    # Return the PDF as a response to the browser
    return Response(pdf.output(dest='S').encode('latin-1'),
                    mimetype='application/pdf',
                    headers={'Content-Disposition': f'attachment;filename=invoice_{entry.tenant_name}_{entry.entry_date}.pdf'})


# This part runs the app
if __name__ == '__main__':
    with app.app_context():
        # This will create the database file and table if they don't exist
        db.create_all()
    app.run(debug=True) # debug=True allows you to see errors and auto-reloads the server