import requests
import csv
import sys
import logging
import argparse
import json
import os
import smtplib
from email.message import EmailMessage
from datetime import datetime
from fpdf import FPDF
from fpdf.enums import XPos, YPos

# --- Configure Enterprise Logging ---
logging.basicConfig(
    filename='automation_execution.log', 
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def load_config():
    """Reads settings from config.json if it exists."""
    config_path = "config.json"
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error reading config.json: {e}")
    return {}

def setup_cli(config):
    """Sets up CLI arguments using config.json defaults as a fallback."""
    default_url = config.get("api_url", "http://127.0.0.1:8000/items/")
    default_format = config.get("default_format", "both")
    default_notify = config.get("notify_on_completion", False)

    parser = argparse.ArgumentParser(description="Redynox Automated Inventory Report Generator")
    parser.add_argument("--url", type=str, default=default_url, help="Target API URL")
    parser.add_argument("--format", type=str, choices=['csv', 'pdf', 'both'], default=default_format, help="Output format type")
    parser.add_argument("--notify", action="store_true", default=default_notify, help="Trigger console notification")
    
    args = parser.parse_args()
    if default_notify:
        args.notify = True
    return args

def generate_csv(inventory_data, timestamp):
    """Converts the JSON inventory payload into a CSV file."""
    filename = f"hardware_report_{timestamp}.csv"
    headers = inventory_data[0].keys() if inventory_data else []
    
    with open(filename, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(inventory_data)
    logging.info(f"CSV Report generated: {filename}")
    return filename

def generate_pdf(inventory_data, timestamp):
    """Converts the JSON inventory payload into a formatted PDF."""
    filename = f"hardware_report_{timestamp}.pdf"
    pdf = FPDF()
    pdf.add_page()
    
    # Title Block
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "Redynox Hardware Inventory Report", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(10)

    # Table Headers
    pdf.set_font("helvetica", "B", 10)
    col_widths = [15, 50, 30, 45, 15, 30] 
    headers = ["ID", "Name", "Category", "Serial Number", "Qty", "Status"]
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, border=1)
    pdf.ln()

    # Table Data Rows
    pdf.set_font("helvetica", "", 10)
    for item in inventory_data:
        pdf.cell(col_widths[0], 10, str(item.get('id', '')), border=1)
        pdf.cell(col_widths[1], 10, str(item.get('name', ''))[:25], border=1)
        pdf.cell(col_widths[2], 10, str(item.get('category', ''))[:15], border=1)
        pdf.cell(col_widths[3], 10, str(item.get('serial_number', ''))[:25], border=1)
        pdf.cell(col_widths[4], 10, str(item.get('quantity', '')), border=1)
        pdf.cell(col_widths[5], 10, str(item.get('status', ''))[:15], border=1)
        pdf.ln()

    pdf.output(filename)
    logging.info(f"PDF Report generated: {filename}")
    return filename

def send_email_notification(config, files_generated):
    """Handles SMTP connection and secure file attachment."""
    email_cfg = config.get("email_notifications", {})
    if not email_cfg.get("enabled"):
        return

    print(" [*] Preparing email notification...")
    msg = EmailMessage()
    msg['Subject'] = 'Automated Alert: Redynox Daily Inventory Report'
    msg['From'] = email_cfg.get("sender_email")
    msg['To'] = email_cfg.get("receiver_email")
    
    # Formatted Email Payload
    msg.set_content(
        f"The automated hardware inventory reporting cycle has completed successfully.\n\n"
        f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"Please find the generated system reports attached to this email.\n\n"
        f"--\n"
        f"Zeful Redynox IT Operations."
    )

    # Securely attach the generated files
    for file in files_generated:
        if file.endswith('.csv'):
            maintype, subtype = 'text', 'csv'
        elif file.endswith('.pdf'):
            maintype, subtype = 'application', 'pdf'
        else:
            maintype, subtype = 'application', 'octet-stream'
            
        try:
            with open(file, 'rb') as f:
                msg.add_attachment(f.read(), maintype=maintype, subtype=subtype, filename=file)
        except Exception as e:
            logging.error(f"Failed to attach {file}: {e}")

    # Dispatch the email through the SMTP server
    try:
        with smtplib.SMTP(email_cfg.get("smtp_server"), email_cfg.get("smtp_port")) as server:
            server.starttls() # Secure the connection
            server.login(email_cfg.get("sender_email"), email_cfg.get("sender_password"))
            server.send_message(msg)
        logging.info("Email notification dispatched successfully.")
        print(" [+] Email dispatched successfully to recipient.")
    except Exception as e:
        logging.error(f"SMTP Transmission Failed: {e}")
        print(f" [!] Email Transmission Failed: Check your network or App Password. Error: {e}")

def execute_pipeline(args, config):
    """Primary orchestration function to run the ingestion, transformation, and notification processes."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logging.info(f"Starting pipeline extraction from {args.url}")
    generated_files = []

    try:
        response = requests.get(args.url)
        response.raise_for_status() 
        inventory_data = response.json()

        if not inventory_data:
            logging.warning("Database is empty. Aborting.")
            sys.exit(0)

        # Route formats based on arguments
        if args.format in ['csv', 'both']:
            generated_files.append(generate_csv(inventory_data, timestamp))
        if args.format in ['pdf', 'both']:
            generated_files.append(generate_pdf(inventory_data, timestamp))
        
        logging.info("Data extraction and formatting complete.")

        # Trigger Console Notifications
        if args.notify:
            print("\n" + "="*50)
            print(" [NOTIFICATION] IT Operations Alert")
            print(f" Inventory reporting cycle completed successfully at {datetime.now().strftime('%H:%M:%S')}")
            print(f" Source: {args.url}")
            print("="*50 + "\n")
            
        # Trigger Email Notifications
        send_email_notification(config, generated_files)

    except requests.exceptions.ConnectionError:
        logging.critical("API Connection Failed. Is Uvicorn running?")
        print("[!] CRITICAL: Cannot connect to API.")
    except Exception as e:
        logging.error(f"System Error: {e}")
        print(f"[!] ERROR: {e}")

if __name__ == "__main__":
    global_config = load_config()
    cli_args = setup_cli(global_config)
    execute_pipeline(cli_args, global_config)