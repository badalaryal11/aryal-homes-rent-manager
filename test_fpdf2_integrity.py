# test_fpdf2_integrity.py
import os
from fpdf import FPDF
import sys

print("--- Starting FPDF2 Integrity Test ---")
output_filename = "valid_test_document.pdf"

try:
    pdf = FPDF()

    # Check for font file and add it
    font_file = "DejaVuSans.ttf"
    if not os.path.exists(font_file):
        print(f"Error: Font file '{font_file}' not found. Please ensure it's in the same directory as this script.")
        print("Using built-in Arial. Non-ASCII characters (like Nepali) may not display correctly.")
        pdf.set_font("Arial", size=12) # Fallback to Arial
    else:
        pdf.add_font("DejaVu", style="", fname=font_file)
        pdf.add_font("DejaVu", style="B", fname=font_file)
        pdf.set_font("DejaVu", size=12)
        print(f"Font '{font_file}' loaded successfully.")

    pdf.add_page()
    pdf.cell(0, 10, "Hello, FPDF2 Test Document!", 0, 1, 'C')
    pdf.cell(0, 10, "This is a basic document to test library functionality.", 0, 1, 'C')
    pdf.ln(10)

    # Test special characters (if DejaVuSans.ttf is loaded)
    if pdf.font_family == "DejaVu":
        pdf.cell(0, 10, "Testing Unicode characters: नमस्ते (Namaste) in Nepali.", 0, 1)
        pdf.cell(0, 10, "Accented characters: éàüçñ", 0, 1)

    # Output to a file on disk
    pdf.output(output_filename)

    print(f"Successfully attempted to create '{output_filename}' in the current directory.")

    # Verify file size
    if os.path.exists(output_filename):
        file_size = os.path.getsize(output_filename)
        print(f"File size: {file_size} bytes.")
        if file_size == 0:
            print("Warning: The generated PDF file is empty (0 bytes). This indicates a serious issue with FPDF2.")
        elif file_size < 500: # Typical small PDF is at least a few KB
            print(f"Warning: The generated PDF file is very small ({file_size} bytes). It might still be corrupted.")
        else:
            print("File seems to have content. Please try opening it.")
    else:
        print("Error: The output file was NOT created on disk.")

except Exception as e:
    print(f"A critical error occurred during FPDF2 generation: {e}", file=sys.stderr)
    sys.exit(1) # Exit with an error code

print("--- FPDF2 Integrity Test Finished ---")