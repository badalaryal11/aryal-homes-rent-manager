# app.py
import os
# from flask import Flask, render_template, request, redirect, url_for, Response
from flask import Flask, render_template, request, send_file, redirect, url_for, Response, make_response
from flask import make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from fpdf import FPDF
import io

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


# In app.py

# ... (keep all your other imports and code) ...

# In app.py

# ... (keep all your other imports and code) ...

# In app.py

# Ensure you have 'send_file' imported, and 'io' is no longer needed if you remove it from the imports.

# ... (rest of your app.py, including app config, RentEntry model, PDF class, and index route) ...


# In app.py



# ... (rest of your app.py, including app config, RentEntry model, PDF class, and index route) ...


@app.route('/generate_pdf/<int:entry_id>')
def generate_pdf(entry_id):
    # Find the specific entry in the database
    entry = RentEntry.query.get_or_404(entry_id)

    pdf = PDF()
    
    # Add the Unicode font and set it for different styles
    try:
        if not os.path.exists("DejaVuSans.ttf"):
            # Provide a more specific error for the log and return, but try to proceed with Arial
            app.logger.error("DejaVuSans.ttf not found in the project directory. Falling back to Arial.")
            pdf.set_font("Arial", size=12) # Fallback if font file is not found
            pdf.add_page()
            pdf.cell(0, 10, "Warning: DejaVuSans.ttf not found. Using Arial font. Non-ASCII characters may not display correctly.", 0, 1)
        else:
            pdf.add_font("DejaVu", style="", fname="DejaVuSans.ttf")
            pdf.add_font("DejaVu", style="B", fname="DejaVuSans.ttf")
            pdf.set_font("DejaVu", size=12) # Default to regular
    except Exception as e:
        # Catch any other font loading issues
        app.logger.error(f"Error loading DejaVuSans.ttf font: {e}. Falling back to Arial.")
        pdf.set_font("Arial", size=12)
        pdf.add_page()
        pdf.cell(0, 10, f"Warning: Error loading DejaVuSans.ttf: {e}. Using Arial font. Non-ASCII characters may not display correctly.", 0, 1)

    # Add content to the PDF - ensure a page is added before drawing cells
    if not pdf.page: # Check if a page has already been added by the error handling
         pdf.add_page()
    
    # Use the font that was successfully set (DejaVu or Arial fallback)
    # Be careful to use only the 'B' style if DejaVu was successfully loaded.
    current_font_name = pdf.font_family # Get the currently active font family
    
    pdf.set_font(current_font_name, style='', size=12) # Set to regular for tenant name etc.
    pdf.cell(0, 10, f'Tenant Name: {entry.tenant_name}', 0, 1)
    pdf.cell(0, 10, f'Date: {entry.entry_date.strftime("%B %d, %Y")}', 0, 1)
    pdf.ln(5)
    
    # Set to bold for categories, if bold was added for the current font
    if current_font_name == "DejaVu":
        pdf.set_font("DejaVu", style='B', size=12)
    else: # If Arial or other fallback, just use default bold if available or regular
        pdf.set_font(current_font_name, style='B', size=12) 
        
    pdf.cell(95, 10, 'Category', 1, 0, 'C')
    pdf.cell(95, 10, 'Amount (NPR)', 1, 1, 'C')

    pdf.set_font(current_font_name, style='', size=12) # Revert to regular for data
    charges = {
        'Rent': entry.rent, 'Water': entry.water, 'Waste Management': entry.waste,
        'Electricity': entry.electricity, 'Repair Costs': entry.repair, 'Miscellaneous': entry.misc
    }
    for category, amount in charges.items():
        pdf.cell(95, 10, f'  {category}', 1, 0)
        pdf.cell(95, 10, f'  {amount:,.2f}', 1, 1)
        
    # Set to bold for total, if bold was added for the current font
    if current_font_name == "DejaVu":
        pdf.set_font("DejaVu", style='B', size=12)
    else:
        pdf.set_font(current_font_name, style='B', size=12)
        
    pdf.cell(95, 10, '  Total Amount', 1, 0)
    pdf.cell(95, 10, f'  {entry.total:,.2f}', 1, 1)

    # --- THE CORRECT fpdf2 + io.BytesIO + send_file APPROACH ---
    try:
        buffer = io.BytesIO()
        # This is the correct way for fpdf2 to write its content into a BytesIO buffer
        pdf.output(dest=buffer) 
        buffer.seek(0) # IMPORTANT: Rewind the buffer to the beginning for reading
        
        filename = f'invoice_{entry.tenant_name}_{entry.entry_date}.pdf'

        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename,
            last_modified=datetime.now()
        )
            
    except Exception as e:
        app.logger.error(f"Error during PDF output or send_file for entry {entry_id}: {e}")
        return f"An error occurred during PDF generation/sending: {e}", 500
      

@app.route('/delete/<int:entry_id>', methods=['POST'])
def delete_entry(entry_id):
    entry_to_delete = RentEntry.query.get_or_404(entry_id)
    db.session.delete(entry_to_delete)
    db.session.commit()
    return redirect(url_for('index'))


# This part runs the app
if __name__ == '__main__':
    with app.app_context():
        # This will create the database file and table if they don't exist
        db.create_all()
    app.run(debug=True) # debug=True allows you to see errors and auto-reloads the server

# --- IGNORE ---
# --- FINAL, ROBUST METHod-

    # 1. Generate the PDF output as bytes. 
    #    The output() method already returns a bytes-like object.
    #pdf_output = pdf.output()
    
    # 2. Use make_response to create a response object from the bytes.
    #response = make_response(pdf_output)
    
    # 3. Set the appropriate headers to tell the browser it's a downloadable PDF.
   # response.headers['Content-Type'] = 'application/pdf'
    #response.headers['Content-Disposition'] = f'attachment;filename=invoice_{entry.tenant_name}_{entry.entry_date}.pdf'
    
    #return response