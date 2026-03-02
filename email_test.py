# email_test.py
from dotenv import load_dotenv
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load environment variables
load_dotenv()

# SMTP credentials from Mailtrap
SMTP_HOST = os.getenv("SMTP_HOST") 
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USER = os.getenv("SMTP_USER") 
SMTP_PASS = os.getenv("SMTP_PASS")  # full password

# Sender & recipient
SENDER_EMAIL = os.getenv("SENDER_EMAIL") 
TO_EMAIL = os.getenv("TEST_RECIPIENT") 

# Create multipart email (plain + HTML)
msg = MIMEMultipart("alternative")
msg["From"] = f"Magic Elves <{SENDER_EMAIL}>"
msg["To"] = TO_EMAIL
msg["Subject"] = "SmartHealth — Test Email"

# Plain text version
text = "Congrats for sending test email with Mailtrap!\nIf you see this in your sandbox, it works."

# HTML version
html = """
<!doctype html>
<html>
  <body>
    <h1>Congrats for sending test email with Mailtrap!</h1>
    <p>If you are viewing this email in your sandbox — the integration works.</p>
  </body>
</html>
"""

msg.attach(MIMEText(text, "plain"))
msg.attach(MIMEText(html, "html"))

# Send email
try:
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SENDER_EMAIL, TO_EMAIL, msg.as_string())
    print("Email sent! Check Mailtrap inbox.")
except Exception as e:
    print("Failed to send email:", e)
