# VitalGuard AI: Smart Hospital Discharge Monitoring System

![Healthcare AI](https://img.shields.io/badge/AI-Healthcare-blue?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-green?style=for-the-badge)
![React](https://img.shields.io/badge/Frontend-React-blue?style=for-the-badge)
![MongoDB](https://img.shields.io/badge/Database-MongoDB_Atlas-emerald?style=for-the-badge)

**VitalGuard AI** is a state-of-the-art **Smart Healthcare Decision Support System** designed to streamline hospital discharge management. By combining **Agentic AI architecture** with **Computer Vision (OCR)**, the system autonomously monitors patient health, evaluates recovery progress, and provides a data-driven discharge decision support for medical professionals.

---

## 🚀 Core Vision

In a busy hospital environment, discharge decisions are often complex and manually tracked. **VitalGuard AI** automates this by orchestrating multiple specialized AI agents that collaborate to ensure a patient is medically stable and administratively cleared before discharge.

---

## 🧠 Agentic AI Architecture

The system operates using a multi-agent collaboration framework where each agent handles a specific domain of the hospital workflow:

### 1. 🛡️ Risk Assessment Agent (OCR + Vision)
*   **Function**: Transforms raw data into clinical insights.
*   **OCR Engine**: Uses **PaddleOCR** to extract vitals (Heart Rate, SpO2, Temperature, Blood Pressure) directly from medical monitor snapshots.
*   **Intelligence**: Analyzes extracted data against strict clinical thresholds to determine a **Risk Level (Low/High)** and triggers **Critical Alerts** for dangerously abnormal vitals.

### 2. 👨‍⚕️ Doctor Agent (The Decision Maker)
*   **Function**: Provides the final discharge recommendation.
*   **Logic**: Evaluates three core pillars:
    *   **Clinical Stability**: Vitals must be stable (within normal ranges) for the last **48 continuous hours**.
    *   **Risk Profile**: Must be classified as `LOW_RISK`.
    *   **Financial Clearance**: Verifies that the hospital bill is fully paid.

### 3. 💊 Pharmacy Agent (Inventory Manager)
*   **Function**: Manages medications and prescriptions.
*   **Intelligence**: Checks a dynamic inventory (CSV-based) for medicine availability and calculates costs based on real-time pricing. It alerts the system if essential medications are out of stock.

### 4. 💳 Billing & Insurance Agents
*   **Function**: Handles the financial lifecycle.
*   **Billing**: Dynamically calculates costs for bed/ward (based on admission length), treatment, and medicine.
*   **Insurance**: Simulates eligibility checks and coverage approvals to calculate the final remaining balance for the patient.

---

## 🛠️ Technical Stack

### **Backend**
*   **Framework**: FastAPI (Python) - High performance, asynchronous API.
*   **OCR/Vision**: PaddleOCR & OpenCV for medical monitor vital extraction.
*   **Database**: MongoDB Atlas (Cloud-based NoSQL) for scalable health record storage.
*   **Agent Logic**: Custom Python-based rule engines for autonomous decision-making.

### **Frontend**
*   **Framework**: React (Vite) - Modern, reactive user interface.
*   **Styling**: Tailwind CSS with a "Glassmorphism" dark-themed design.
*   **Animations**: Framer Motion for smooth transitions and interactive elements.
*   **Telemetry**: Chart.js for real-time visualization of vital sign trends.

---

## ✨ Key Features

*   **Dual-Perspective Dashboard**:
    *   **Admin Mode**: Register patients, upload monitor snapshots for OCR analysis, assign prescriptions, and manage billing/payments.
    *   **Patient Mode**: A secure, read-only portal to track vitals history, telemetry trends, and discharge readiness progress.
*   **Automated Vital Extraction**: Simply take a photo of a medical monitor, and the system automatically populates the patient's record using AI vision.
*   **Real-time Alerts**: Visual and database alerts for critical medical conditions (e.g., SpO2 < 85%).
*   **Dynamic Billing**: Automatic bed cost calculation from admission date to current time.

---

## 📂 Project Structure

```text
├── agents/               # AI Agent Logic (Risk, Doctor, Pharmacy, etc.)
├── backend/              # FastAPI Application (app.py)
├── database/             # MongoDB Connection & Schema
├── dataset/              # Pharmacy Inventory Data
├── frontend_react/       # Modern React UI (Vite)
├── uploads/              # Storage for Vital Sign Snapshots
└── vital_extractor/      # OCR Engine and Image Preprocessing
```

---

## 🚦 Getting Started

### Prerequisites
*   Python 3.10+
*   Node.js (for React frontend)
*   MongoDB Atlas Account (URI configured in `database/mongodb.py`)

### Setup Instructions

1.  **Clone the Repository**:
    ```bash
    git clone [repository-url]
    cd [repository-name]
    ```

2.  **Backend Setup**:
    ```bash
    python -m venv .venv
    .\.venv\Scripts\activate
    pip install -r requirements.txt
    python app.py
    ```

3.  **Frontend Setup**:
    ```bash
    cd frontend_react
    npm install
    npm run dev
    ```

---

## 🔒 Security & Roles

The system uses a header-based role verification (`X-Role`) to distinguish between **Admin** and **Patient** access.
*   **Default Admin**: `admin@hospital.com` / `admin123`
*   **Patient Login**: Requires a unique 8-character **Patient ID** generated during registration.

---

## 📝 License

This project is developed for educational and research purposes in the field of Agentic AI and Smart Healthcare Decision Support Systems.

---
*Created by [Your Name/Team Name]*
