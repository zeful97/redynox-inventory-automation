# Zeful Redynox IT Operations: Automated Inventory Pipeline

## Problem Statement
Manual asset tracking introduces operational latency and human error. This project provides an automated backend pipeline to extract live hardware statuses from the Inventory API and generate compliance-ready CSV and PDF reports.

## Features
* **Automated Extraction:** Securely pulls JSON data from the local API.
* **Multi-Format Generation:** Compiles data into pandas-style CSVs and stylized fpdf2 PDFs.
* **Notification Engine:** Dispatches SMTP email alerts with attachments and console notifications.
* **Automated Scheduling:** Configured to run headlessly via Windows Task Scheduler.

## Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone <your-repository-url>
   cd redynox_inventory_api

2. **Set Up the Virtual Environment (Windows)**
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate  
   pip install requests fpdf2