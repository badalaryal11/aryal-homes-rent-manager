# 🏠 Aryal Homes - Rent Management App

![Aryal Homes Logo](static/logo.jpeg)

A simple and robust web application built with Python and Flask to manage rent and utility payments for Aryal Homes. This app allows for detailed entry of expenses (rent, water, electricity, etc.), stores them in a database, and generates professional PDF invoices.

---

## ✨ Features

* **Full CRUD Functionality**: Create, Read, and Delete rent entries.
* **Detailed Expense Categories**: Track Rent, Waste, Repair, and Miscellaneous costs.
* **Smart Utility Calculation**:
    * **💧 Water**: Automatically calculates the total cost based on the number of tanker fills (`@ NRS 250/fill`).
    * **⚡️ Electricity**: Automatically calculates units consumed and total cost based on previous and present meter readings (`@ NRS 13/unit`).
* **Persistent Database**: All entries are saved to a production-ready SQLite database using `Flask-SQLAlchemy`.
* **Detailed View**: A dedicated page to view a full, itemized breakdown of any entry before generating a PDF.
* **Dynamic PDF Generation**: Uses `ReportLab` to create a custom, professional PDF invoice for any entry, complete with the Aryal Homes logo.
* **Production Ready**: Configured to run with a Gunicorn WSGI server.

---

## 🛠 Tech Stack

* **Backend**: Python
* **Framework**: Flask
* **Database**: SQLite (managed with `Flask-SQLAlchemy`)
* **PDF Generation**: ReportLab
* **Frontend**: HTML, CSS, (minimal JavaScript)
* **Production Server**: Gunicorn
* **Configuration**: `python-dotenv`

---

## 🚀 Getting Started

Follow these instructions to get a copy of the project up and running on your local machine for development and testing.

### Prerequisites

* Python 3.9+
* `pip` and `venv`

### 1. Create `requirements.txt`

Before you can install the project, you need to generate a `requirements.txt` file from your current environment so others (or your future self) can install the same packages.

In your terminal (with your virtual environment activated), run:
```bash
pip freeze > requirements.txt
