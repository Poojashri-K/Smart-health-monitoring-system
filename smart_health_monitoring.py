"""
smart_health_monitoring_customtk.py
Reworked Clean Version:
- Role-based login (doctor/patient)
- Patient input form
- Doctor dashboard with recommendations
- Matplotlib graph
- Recommendations now linked via username
- CustomTkinter UI
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from dotenv import load_dotenv
import os, oracledb, threading, smtplib, sys
from email.mime.text import MIMEText
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from PIL import Image

# -------------------- Load environment variables --------------------
load_dotenv()
ORACLE_USER = os.getenv("ORACLE_USER")
ORACLE_PASS = os.getenv("ORACLE_PASS")
ORACLE_DSN  = os.getenv("ORACLE_DSN")

SMTP_HOST = os.getenv("SMTP_HOST") or "sandbox.smtp.mailtrap.io"
SMTP_PORT = int(os.getenv("SMTP_PORT") or 2525)
SMTP_USER = os.getenv("SMTP_USER") or "5ad4424a8c4f8f"
SMTP_PASS = os.getenv("SMTP_PASS") or "990a011463927c"
SENDER_EMAIL = os.getenv("SENDER_EMAIL") or "from@example.com"

# -------------------- Oracle Connection --------------------
try:
    conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASS, dsn=ORACLE_DSN)
    cursor = conn.cursor()
    print("✅ Database connected")
except Exception as e:
    print("❌ DB connect error:", e)
    cursor = None

# -------------------- Email Alert --------------------
def send_email_alert(email, name, message):
    def send_email():
        try:
            msg = MIMEText(message)
            msg['Subject'] = f"⚠️ Health Alert for {name}"
            msg['From'] = SENDER_EMAIL
            msg['To'] = email
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.send_message(msg)
            print(f"📧 Alert sent to {email}")
        except Exception as e:
            print("Email Error:", e)
    threading.Thread(target=send_email, daemon=True).start()

# -------------------- Health Tips --------------------
def get_health_tips(hr, bp, oxy, temp):
    tips = []
    try:
        if hr > 100:
            tips.append("💓 Relax, reduce stress, and limit caffeine.")
        if oxy < 94:
            tips.append("🌬️ Deep breathing or consult a doctor if O₂ remains low.")
        if temp > 38:
            tips.append("🌡️ Stay hydrated and rest. Seek help if fever persists.")
        if bp != "120/80":
            tips.append("🩸 Maintain low-sodium diet and exercise.")
    except Exception:
        pass
    return "\n".join(tips) if tips else "✅ All readings normal."

# -------------------- App Setup --------------------
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Smart Health Monitor")
app.geometry("1200x800")
app.resizable(True, True)

container = ctk.CTkFrame(app, fg_color="#f0f4f8")
container.pack(fill="both", expand=True)

frames = {}
current_user = {"username": None, "role": None}

def show_frame(name):
    frame = frames.get(name)
    if frame:
        frame.tkraise()

# -------------------- Shared Tk variables --------------------
login_username_var = tk.StringVar()
login_password_var = tk.StringVar()
signup_username_var = tk.StringVar()
signup_password_var = tk.StringVar()
signup_role_var = tk.StringVar(value="patient")

fields = {
    "Name": tk.StringVar(),
    "Age": tk.StringVar(),
    "Email": tk.StringVar(),
    "Heart Rate (bpm)": tk.StringVar(),
    "Blood Pressure": tk.StringVar(),
    "Oxygen Level (%)": tk.StringVar(),
    "Temperature (°C)": tk.StringVar()
}

def clear_patient_fields():
    for v in fields.values():
        v.set("")

# -------------------- LOGIN FRAME --------------------
login_frame = ctk.CTkFrame(container, fg_color="#f7fbff")
login_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
frames["login"] = login_frame

ctk.CTkLabel(login_frame, text="Smart Health Monitoring System", font=("Segoe UI", 28, "bold"), text_color="#0b5fa5").pack(pady=(40,20))
ctk.CTkLabel(login_frame, text="Username", font=("Segoe UI", 14)).pack(pady=(6,0))
ctk.CTkEntry(login_frame, textvariable=login_username_var, width=360, height=38, placeholder_text="Enter username", font=("Segoe UI", 13)).pack(pady=(6,8))
ctk.CTkLabel(login_frame, text="Password", font=("Segoe UI", 14)).pack(pady=(6,0))
ctk.CTkEntry(login_frame, textvariable=login_password_var, show="*", width=360, height=38, placeholder_text="Enter password", font=("Segoe UI", 13)).pack(pady=(6,12))

def do_login():
    user = login_username_var.get().strip()
    pwd = login_password_var.get().strip()
    if not user or not pwd:
        messagebox.showwarning("Warning", "Please enter both username and password.")
        return
    try:
        cursor.execute("SELECT username, role FROM users_info WHERE username=:1 AND password=:2", (user, pwd))
        res = cursor.fetchone()
        if res:
            username, role = res
            current_user["username"] = username
            current_user["role"] = role
            login_username_var.set("")
            login_password_var.set("")
            if role == "patient":
                clear_patient_fields()
                show_frame("patient_info")
                load_patient_recommendations()
            else:
                show_frame("doctor_frame")
                load_all_patients()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")
    except Exception as e:
        messagebox.showerror("Error", f"Login failed: {e}")
    

ctk.CTkButton(login_frame, text="Login", command=do_login, width=220, height=44, font=("Segoe UI", 14, "bold")).pack(pady=(10,8))
ctk.CTkButton(login_frame, text="Create New Account", command=lambda: show_frame("signup"), width=220, height=36).pack(pady=(6,20))

img_path = os.path.join(os.getcwd(), "med.jpg")
pil_img = Image.open(img_path)
pil_img = pil_img.resize((1200, 300))  # width x height for bottom space

# Convert to CTkImage
ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(1200, 300))

lbl_login_img = ctk.CTkLabel(login_frame, text="", image=ctk_img)
lbl_login_img.pack(side="bottom", fill="x", expand=True)

# -------------------- SIGNUP FRAME --------------------
signup_frame = ctk.CTkFrame(container, fg_color="#f7fbff")
signup_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
frames["signup"] = signup_frame

ctk.CTkLabel(signup_frame, text="Create New Account", font=("Segoe UI", 28, "bold"), text_color="#0a5a8a").pack(pady=(30,10))
ctk.CTkLabel(signup_frame, text="Username", font=("Segoe UI", 14)).pack(pady=(6,0))
ctk.CTkEntry(signup_frame, textvariable=signup_username_var, width=360, height=38, placeholder_text="Choose username", font=("Segoe UI", 13)).pack(pady=(6,8))
ctk.CTkLabel(signup_frame, text="Password", font=("Segoe UI", 14)).pack(pady=(6,0))
ctk.CTkEntry(signup_frame, textvariable=signup_password_var, show="*", width=360, height=38, placeholder_text="Choose password", font=("Segoe UI", 13)).pack(pady=(6,8))
ctk.CTkLabel(signup_frame, text="Role", font=("Segoe UI", 14)).pack(pady=(6,0))
ctk.CTkOptionMenu(signup_frame, values=["patient", "doctor"], variable=signup_role_var, width=220).pack(pady=(6,12))

def create_account():
    user = signup_username_var.get().strip()
    pwd = signup_password_var.get().strip()
    role = signup_role_var.get().strip()
    if not user or not pwd:
        messagebox.showwarning("Warning", "Please enter username and password.")
        return
    try:
        cursor.execute("INSERT INTO users_info (username, password, role) VALUES (:1, :2, :3)", (user, pwd, role))
        conn.commit()
        messagebox.showinfo("Success", "Account created successfully! Please login.")
        signup_username_var.set("")
        signup_password_var.set("")
        signup_role_var.set("patient")
        show_frame("login")
    except oracledb.IntegrityError:
        messagebox.showerror("Error", "Username already exists.")
    except Exception as e:
        messagebox.showerror("Error", f"Account creation failed: {e}")

ctk.CTkButton(signup_frame, text="Sign Up", command=create_account, width=220, height=40).pack(pady=(6,8))
ctk.CTkButton(signup_frame, text="← Back to Login", command=lambda: show_frame("login"), width=220, height=36).pack(pady=(6,8))

# Signup frame image
img_path = os.path.join(os.getcwd(), "med1.jpg")
pil_img = Image.open(img_path)
pil_img = pil_img.resize((1200, 300))

ctk_img_signup = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(1200, 300))

lbl_signup_img = ctk.CTkLabel(signup_frame, text="", image=ctk_img_signup)
lbl_signup_img.pack(side="bottom", fill="x", expand=True)

# -------------------- PATIENT INFO FRAME --------------------
patient_frame = ctk.CTkFrame(container, fg_color="#eef6f8")
patient_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
frames["patient_info"] = patient_frame

ctk.CTkLabel(patient_frame, text="Enter Patient Details", font=("Segoe UI", 26, "bold"), text_color="#0b4f86").pack(pady=(20,10))

form_frame = ctk.CTkFrame(patient_frame, fg_color="transparent")
form_frame.pack(pady=(6,10))

for i, (label_text, var) in enumerate(fields.items()):
    ctk.CTkLabel(form_frame, text=label_text, font=("Segoe UI", 14)).grid(row=i, column=0, sticky="w", padx=(10,6), pady=(6,4))
    ctk.CTkEntry(form_frame, textvariable=var, width=420, height=40, font=("Segoe UI", 13)).grid(row=i, column=1, padx=(6,20), pady=(6,4))

def save_and_show_graph():
    try:
        name = fields["Name"].get().strip()
        age = int(fields["Age"].get().strip())
        email = fields["Email"].get().strip()
        hr = int(fields["Heart Rate (bpm)"].get().strip())
        bp_raw = fields["Blood Pressure"].get().strip()
        if "/" in bp_raw:
            systolic = int(bp_raw.split("/")[0])
        else:
            messagebox.showerror("Error", "Enter Blood Pressure as Systolic/Diastolic (e.g. 120/80).")
            return
        oxy = int(fields["Oxygen Level (%)"].get().strip())
        temp = float(fields["Temperature (°C)"].get().strip())

        cursor.execute("""
            INSERT INTO patients (name, age, username, email, heart_rate, blood_pressure, oxygen_level, temperature, reading_time)
            VALUES (:1,:2,:3,:4,:5,:6,:7,:8,CURRENT_TIMESTAMP)
        """, (name, age, current_user["username"], email, hr, bp_raw, oxy, temp))
        conn.commit()

        tips = get_health_tips(hr, bp_raw, oxy, temp)
        if "✅" not in tips:
            send_email_alert(email, name, f"⚠️ Abnormal health readings detected!\n\n{tips}")

        clear_patient_fields()
        show_frame("graph")
        update_graph(hr, systolic, oxy, temp)
    except ValueError:
        messagebox.showerror("Error", "Ensure numeric fields are valid.")
    except Exception as e:
        messagebox.showerror("Error", f"{e}")

ctk.CTkButton(patient_frame, text="Submit & View Graph", command=save_and_show_graph, width=260, height=44, font=("Segoe UI", 14, "bold")).pack(pady=(10,6))
ctk.CTkButton(patient_frame, text="Logout", command=lambda: (clear_patient_fields(), show_frame("login")), width=200, height=38).pack(pady=(6,12))

# Recommendations display
rec_frame = ctk.CTkFrame(patient_frame, fg_color="#dbeeff", corner_radius=8)
rec_frame.pack(fill="x", padx=20, pady=(10, 20))
ctk.CTkLabel(rec_frame, text="💡 Doctor Recommendations", font=("Segoe UI", 16, "bold"), anchor="w").pack(padx=10, pady=(8,4), fill="x")
rec_textbox = tk.Text(rec_frame, height=8, font=("Segoe UI", 20), wrap="word", bg="#dbeeff", bd=0)
rec_textbox.pack(fill="both", padx=10, pady=(0,8))
rec_textbox.configure(state="disabled")

def load_patient_recommendations():
    if not current_user["username"]:
        return
    try:
        cursor.execute("""
            SELECT doctor_name, recommendation, created_at
            FROM recommendations
            WHERE patient_username=:1
            ORDER BY created_at DESC
        """, (current_user["username"],))
        recs = cursor.fetchall()
        rec_textbox.configure(state="normal")
        rec_textbox.delete("1.0", tk.END)
        if recs:
            for doc, text, ts in recs:
                rec_textbox.insert(tk.END, f"From Dr. {doc} ({ts.strftime('%Y-%m-%d %H:%M')}):\n{text}\n\n")
        else:
            rec_textbox.insert(tk.END, "No recommendations from doctors yet.")
        rec_textbox.configure(state="disabled")
    except Exception as e:
        print("Failed to fetch recommendations:", e)

ctk.CTkButton(rec_frame, text="🔄 Refresh Recommendations", width=220, height=36, command=load_patient_recommendations).pack(pady=(0,8))

# -------------------- GRAPH FRAME --------------------
graph_frame = ctk.CTkFrame(container, fg_color="#ffffff")
graph_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
frames["graph"] = graph_frame
ctk.CTkLabel(graph_frame, text="Patient vs Healthy Comparison", font=("Segoe UI", 22, "bold"), text_color="#0b61a6").pack(pady=(18,8))
fig, (ax_patient, ax_healthy) = plt.subplots(1, 2, figsize=(8,4))
canvas = FigureCanvasTkAgg(fig, master=graph_frame)
canvas.get_tk_widget().pack(fill="both", expand=True, padx=12, pady=12)
fig.tight_layout()
def update_graph(hr, bp, oxy, temp):
    ax_patient.clear(); ax_healthy.clear()
    ax_patient.bar(['HR','BP','O2','Temp'], [hr,bp,oxy,temp], color=['#ff9800','#e91e63','#03a9f4','#4caf50'])
    ax_patient.set_ylim(0,200); ax_patient.set_title("Patient")
    healthy = [75,120,98,37]
    ax_healthy.bar(['HR','BP','O2','Temp'], healthy, color=['#8bc34a']*4)
    ax_healthy.set_ylim(0,200); ax_healthy.set_title("Healthy")
    fig.tight_layout(); canvas.draw()
ctk.CTkButton(graph_frame, text="← Back to Input", command=lambda: (clear_patient_fields(), show_frame("patient_info")), width=220, height=40).pack(pady=(8,6))
ctk.CTkButton(graph_frame, text="Logout", command=lambda: show_frame("login"), width=180, height=36).pack(pady=(4,12))

# -------------------- DOCTOR FRAME --------------------
doctor_frame = ctk.CTkFrame(container, fg_color="#f0f7fb")
doctor_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
frames["doctor_frame"] = doctor_frame
ctk.CTkLabel(doctor_frame, text="Doctor Dashboard", font=("Segoe UI", 26, "bold"), text_color="#043962").pack(pady=(18,8))
doctor_scrollable = ctk.CTkScrollableFrame(doctor_frame, width=1000, height=520, fg_color="#eef6ff")
doctor_scrollable.pack(padx=12, pady=(8,12), fill="both", expand=True)

def load_all_patients():
    for widget in doctor_scrollable.winfo_children():
        widget.destroy()
    try:
        cursor.execute("SELECT name, age, username, email, heart_rate, blood_pressure, oxygen_level, temperature, reading_time FROM patients ORDER BY reading_time DESC")
        rows = cursor.fetchall()
        if not rows:
            ctk.CTkLabel(doctor_scrollable, text="No patient records found.", font=("Segoe UI", 14)).pack(pady=12)
            return
        for row in rows:
            name, age, username, email, hr, bp, oxy, temp, time = row
            card = ctk.CTkFrame(doctor_scrollable, fg_color="#ffffff", corner_radius=8)
            card.pack(fill="x", padx=12, pady=8)
            top = ctk.CTkFrame(card, fg_color="transparent"); top.pack(fill="x", pady=(8,4), padx=8)
            ctk.CTkLabel(top, text=f"{name}  (Age: {age})", font=("Segoe UI",16,"bold")).pack(side="left", padx=(0,6))
            ctk.CTkLabel(top, text=str(time), font=("Segoe UI",11), text_color="#666666").pack(side="right")
            body = ctk.CTkFrame(card, fg_color="transparent"); body.pack(fill="x", padx=8, pady=(2,10))
            ctk.CTkLabel(body, text=f"HR:{hr}  BP:{bp}  O₂:{oxy}%  Temp:{temp}°C", font=("Segoe UI",14)).pack(anchor="w")
            ctk.CTkLabel(body, text=f"Username: {username}", font=("Segoe UI",13), text_color="#444444").pack(anchor="w", pady=(6,0))
            rec_var = tk.StringVar()
            ctk.CTkEntry(body, textvariable=rec_var, width=400, placeholder_text="Enter recommendation").pack(pady=(6,4))
            def submit_recommendation(patient_username=username, rec_var=rec_var):
                text = rec_var.get().strip()
                if not text: messagebox.showwarning("Warning", "Enter recommendation."); return
                try:
                    cursor.execute("INSERT INTO recommendations (patient_username, doctor_name, recommendation) VALUES (:1,:2,:3)", (patient_username,current_user["username"],text))
                    conn.commit()
                    messagebox.showinfo("Success", f"Recommendation sent to {patient_username}.")
                    rec_var.set("")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save: {e}")
            ctk.CTkButton(body, text="Send Recommendation", command=submit_recommendation, width=200, height=30).pack(pady=(4,6))
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load patients: {e}")
ctk.CTkButton(doctor_frame, text="Logout", width=200, height=40, command=lambda: show_frame("login")).pack(pady=(8,12))

# -------------------- Exit Handling --------------------
def on_closing():
    try:
        if cursor: cursor.close()
        if conn: conn.close()
    except: pass
    app.destroy(); sys.exit()

app.protocol("WM_DELETE_WINDOW", on_closing)
show_frame("login")
app.mainloop()






