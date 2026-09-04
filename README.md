# Compliance Checker - Department of Legal Metrology

A complete production-ready full-stack web application built for the **Department of Legal Metrology, Ministry of Consumer Affairs, Food & Public Distribution**.

The application allows authorized Legal Metrology officers to scan or upload packaged commodity label images, perform AI-powered OCR extractions, validate statutory declarations against the *Legal Metrology (Packaged Commodities) Rules, 2011*, calculate deterministic compliance scores, track inspection histories, and generate downloadable official PDF inspection reports.

---

## Key Features

- **Institutional Design System**: Designed to match official Government of India portal styling (Navy `#0B192C` headers, institutional badges, clean typography).
- **Public & Officer Portals**: Public informational pages (Home, Rules 2011, Contact Us, About Us, Guidelines) & Protected Officer Portal (Dashboard, New Inspection, Inspection Result, History).
- **AI-Powered OCR Pipeline**: Preprocessing with OpenCV (denoising, contrast enhancement, adaptive thresholding) + EasyOCR / Regex extraction for MRP, Net Qty, Mfg Date, Mfr Details, Consumer Care.
- **Statutory Compliance Engine**: Rule engine evaluating PCR 2011 rules (Rules 6(1)(a), 6(1)(c), 6(1)(d), 6(1)(e), 6(1)(n), Rule 7, Rule 11).
- **ReportLab PDF Generation**: Generates official PDF inspection reports on demand.
- **Secure Authentication**: JWT bearer tokens, bcrypt password hashing, and MongoDB storage.

---

## Tech Stack

- **Frontend**: React, Vite, Tailwind CSS v4, React Router v6, Axios, Recharts, Lucide Icons
- **Backend**: Python 3.10+, FastAPI, Pydantic, OpenCV, EasyOCR, ReportLab, Motor (Async MongoDB)
- **Database**: MongoDB

---

## Setup & Running Instructions

### 1. Backend Setup

```bash
cd backend
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend
# Install node dependencies
npm install

# Start Vite dev server
npm run dev
```

The frontend will run at `http://localhost:5173` and communicate with the backend at `http://localhost:8000`.

---
