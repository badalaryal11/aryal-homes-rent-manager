# app.py

import os
import io
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import click

# --- ReportLab Imports ---
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- App and Database Configuration ---
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'rent.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production' # Required for session management

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' # Redirect to 'login' view if not authenticated

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Database Model Definition ---
# --- Database Model Definition ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# UPDATED: Changed 'water' to 'water_fill_count' and added 'water_cost'
class RentEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_name = db.Column(db.String(100), nullable=False)
    month = db.Column(db.String(50), nullable=False)
    entry_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    rent = db.Column(db.Float, nullable=False, default=0)
   
    # New: Store the count, then calculate the cost
    water_fill_count = db.Column(db.Integer, nullable=False, default=0)
    water = db.Column(db.Float, nullable=False, default=0) # This will store the CALCULATED water cost

    waste = db.Column(db.Float, nullable=False, default=0)
    
    electricity_previous_reading = db.Column(db.Float, nullable=False, default=0)
    electricity_present_reading = db.Column(db.Float, nullable=False, default=0)
    electricity = db.Column(db.Float, nullable=False, default=0) 
    
    repair = db.Column(db.Float, nullable=False, default=0)
    misc = db.Column(db.Float, nullable=False, default=0)
    
    # Calculate total on the fly
    @property
    def total(self):
        return self.rent + self.water + self.waste + self.electricity + self.repair + self.misc

    def __repr__(self):
        return f'<RentEntry for {self.tenant_name}>'

# --- Web Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        # --- UPDATED: Water Calculation Logic ---
        water_fill_count = int(request.form.get('water_fill_count') or 0)
        water_cost = water_fill_count * 250 # Price is Nrs. 250 per fill

        previous_reading = float(request.form.get('electricity_previous_reading') or 0)
        present_reading = float(request.form.get('electricity_present_reading') or 0)
        units_consumed = 0
        if present_reading >= previous_reading:
            units_consumed = present_reading - previous_reading
        electricity_cost = units_consumed * 13 # Price is Nrs. 13 per unit

        # Combine Nepali Month and Year
        nepali_month = request.form.get('nepali_month')
        nepali_year = request.form.get('nepali_year')
        month_str = f"{nepali_month} {nepali_year}"

        new_entry = RentEntry(
            tenant_name=request.form['tenant_name'],
             month = month_str,
            entry_date=datetime.strptime(request.form['entry_date'], '%Y-%m-%d').date(),
           
            rent=float(request.form.get('rent') or 0),
            
            water_fill_count=water_fill_count, # Store the count
            water=water_cost,                   # Store the calculated cost

            waste=float(request.form.get('waste') or 0),
            electricity_previous_reading=previous_reading,
            electricity_present_reading=present_reading,
            electricity=electricity_cost,
            repair=float(request.form.get('repair') or 0),
            misc=float(request.form.get('misc') or 0)
        )
        db.session.add(new_entry)
        db.session.commit()
        return redirect(url_for('index'))

    all_entries = RentEntry.query.order_by(RentEntry.entry_date.desc()).all()
    return render_template('index.html', entries=all_entries)

@app.route('/delete/<int:entry_id>', methods=['POST'])
@login_required
def delete_entry(entry_id):
    entry_to_delete = RentEntry.query.get_or_404(entry_id)
    db.session.delete(entry_to_delete)
    db.session.commit()
    return redirect(url_for('index'))

# In app.py

# ... (keep all your other imports and code) ...

@app.route('/generate_pdf/<int:entry_id>')
@login_required
def generate_pdf(entry_id):
    entry = RentEntry.query.get_or_404(entry_id)
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # --- Register Fonts ---
    font_path = "DejaVuSans.ttf"
    main_font = 'Helvetica'
    
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('DejaVu', font_path))
            pdfmetrics.registerFont(TTFont('DejaVu-Bold', font_path))
            pdfmetrics.registerFont(TTFont('DejaVu-Italic', font_path))
            pdfmetrics.registerFont(TTFont('DejaVu-BoldItalic', font_path))
            main_font = 'DejaVu'
        except Exception as e:
            app.logger.error(f"ReportLab: Error registering DejaVuSans.ttf: {e}. Falling back to Helvetica.")
            main_font = 'Helvetica' 
    else:
        app.logger.error("ReportLab: DejaVuSans.ttf not found. Using Helvetica.")
        main_font = 'Helvetica' 

    # --- PDF Content Drawing ---
    
    logo_path = "static/logo.jpeg"
    logo_height_points = 1.5 * inch # Define desired height for the logo (1.5 inches)
    logo_width_points = 1.5 * inch # Define desired width for the logo (1.5 inches)

    # --- NEW: DRAW THE LOGO WITH CORRECTED POSITIONING ---
    if os.path.exists(logo_path):
        # Calculate Y position: height - top_margin - logo_height
        # This places the TOP of the logo at (height - top_margin)
        top_margin = 0.75 * inch 
        logo_y_position = height - top_margin - logo_height_points
        
        # Calculate X position to center it (optional, you can keep it left if preferred)
        # For left alignment, use x=1*inch
        logo_x_position = (width - logo_width_points) / 2.0 # Center horizontally

        p.drawImage(logo_path, 
                    x=logo_x_position, # Centered X position
                    y=logo_y_position, # Corrected Y position for the top alignment
                    width=logo_width_points, 
                    height=logo_height_points, # Specify height explicitly for better control
                    preserveAspectRatio=True, 
                    mask='auto')
        
        # Adjust vertical spacing after the logo
        y_offset_after_logo = top_margin + logo_height_points + 0.2*inch # Space after logo
    else:
        y_offset_after_logo = 1.0 * inch # Default top margin if no logo

    # Invoice Title (adjusted to be below the logo)
    p.setFont(f"{main_font}-Bold", 16)
    p.drawCentredString(width / 2.0, height - y_offset_after_logo, "Aryal Homes - Rent Invoice")

    # Start main content further down to avoid overlapping with logo/title
    start_content_y = height - y_offset_after_logo - 0.5*inch # Adjust this value as needed

    p.setFont(main_font, 11)
    p.drawString(1*inch, start_content_y, f"Tenant Name: {entry.tenant_name}")
    p.drawString(1*inch, start_content_y- 0.2*inch, f"Month-Year: {entry.month}")
    p.drawString(1*inch, start_content_y - 0.4*inch, f"Invoice Date: {entry.entry_date.strftime('%B %d, %Y')}")   
   
    # --- The rest of the function (adjust y_position start) ---
    y_position = start_content_y - 0.7*inch # Adjusted start position for table

    table_left_margin = 1*inch
    table_right_margin = width - 1*inch
    
    p.setFont(f"{main_font}-Bold", 12)
    p.drawString(table_left_margin, y_position, "Category")
    p.drawRightString(table_right_margin, y_position, "Amount (NRS)")
    y_position -= 0.2*inch
    p.line(table_left_margin, y_position, table_right_margin, y_position)
    y_position -= 0.25*inch
    
    p.setFont(main_font, 11)
    charges = [("Rent", entry.rent)]
    for category, amount in charges:
        p.drawString(table_left_margin, y_position, category)
        p.drawRightString(table_right_margin, y_position, f"{amount:,.2f}")
        y_position -= 0.25*inch
    
    p.setFont(f"{main_font}-Bold", 11)
    p.drawString(table_left_margin, y_position, "Water Details")
    y_position -= 0.25*inch
    p.setFont(main_font, 10)
    p.drawString(table_left_margin + 0.2*inch, y_position, f"Times Filled: {entry.water_fill_count} @ NRS 250.00/fill")
    y_position -= 0.25*inch
    p.setFont(main_font, 11)
    p.drawString(table_left_margin, y_position, "Water Cost")
    p.drawRightString(table_right_margin, y_position, f"{entry.water:,.2f}")
    y_position -= 0.25*inch

    units_consumed = entry.electricity_present_reading - entry.electricity_previous_reading
    p.setFont(f"{main_font}-Bold", 11)
    p.drawString(table_left_margin, y_position, "Electricity Details")
    y_position -= 0.25*inch
    p.setFont(main_font, 10)
    p.drawString(table_left_margin + 0.2*inch, y_position, f"Present Reading: {entry.electricity_present_reading:,.2f}")
    y_position -= 0.20*inch
    p.drawString(table_left_margin + 0.2*inch, y_position, f"Previous Reading: {entry.electricity_previous_reading:,.2f}")
    y_position -= 0.20*inch
    p.drawString(table_left_margin + 0.2*inch, y_position, f"Units Consumed: {units_consumed:,.2f} units @ NRS 13.00/unit")
    y_position -= 0.25*inch
    p.setFont(main_font, 11)
    p.drawString(table_left_margin, y_position, "Electricity Cost")
    p.drawRightString(table_right_margin, y_position, f"{entry.electricity:,.2f}")
    y_position -= 0.25*inch

    other_charges = [
        ("Waste Management", entry.waste),
        ("Repair Costs", entry.repair),
        ("Miscellaneous", entry.misc),
    ]
    for category, amount in other_charges:
        p.drawString(table_left_margin, y_position, category)
        p.drawRightString(table_right_margin, y_position, f"{amount:,.2f}")
        y_position -= 0.25*inch
    
    y_position -= 0.2*inch
    p.line(table_left_margin, y_position, table_right_margin, y_position)
    y_position -= 0.25*inch
    p.setFont(f"{main_font}-Bold", 12)
    p.drawString(table_left_margin, y_position, "Total Amount Due")
    p.drawRightString(table_right_margin, y_position, f"{entry.total:,.2f}")

    # --- Authorized Signature ---
    y_position -= 0.6 * inch
    signature_path = "static/signature.png"
    
    # Define signature box
    sig_width = 1.5 * inch
    sig_height = 0.8 * inch
    
    # Position: Right aligned to the table margin
    sig_x = table_right_margin - sig_width
    sig_y = y_position - sig_height
    
    if os.path.exists(signature_path):
        p.drawImage(signature_path, sig_x, sig_y, width=sig_width, height=sig_height, mask='auto', preserveAspectRatio=True)
    
    # Draw 'Authorized Signature' text below the image area
    p.setFont(main_font, 10)
    p.drawCentredString(sig_x + sig_width/2.0, sig_y - 0.2*inch, "Authorized Signature")

    p.showPage()
    p.save()
    buffer.seek(0)
    
    filename = f'invoice_{entry.tenant_name}_{entry.entry_date}.pdf'
    
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )

# --- CLI Commands ---
@app.cli.command("create-admin")
@click.argument("username")
@click.argument("password")
def create_admin(username, password):
    """Creates a new admin user."""
    with app.app_context():
        db.create_all() # Ensure tables exist
        if User.query.filter_by(username=username).first():
            print(f"User {username} already exists.")
            return
        
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        print(f"Admin user {username} created successfully!")

# --- Main Execution ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)