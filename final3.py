import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string

class ComplaintApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Student Complaint System")
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TLabel", background="#f0f0f0")
        self.style.configure("TButton", background="#007bff", foreground="#ffffff", font=("Arial", 10, "bold"))
        self.style.map("TButton", background=[("active", "#0056b3")])
        self.logged_in = False
        self.admin_mode = False
        self.semaphore = threading.Semaphore(1)
        self.waiting_time = 3 * 24 * 60 * 60  # 3 days in seconds
        self.db_conn = self.create_db_connection()
        self.create_table()
        self.create_login_widgets()

    def create_db_connection(self):
        conn = sqlite3.connect("complaints.db")
        return conn

    def create_table(self):
        cursor = self.db_conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS complaints
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        student_id TEXT,
                        email TEXT,
                        complaint TEXT,
                        status TEXT DEFAULT 'Pending',  -- Add 'status' column with default value
                        timestamp INTEGER,
                        responded INTEGER DEFAULT 0)''')
        self.db_conn.commit()

    def create_login_widgets(self):
        self.login_frame = ttk.Frame(self.master)
        self.login_frame.pack(padx=20, pady=20)

        self.login_label = ttk.Label(self.login_frame, text="Login", font=("Arial", 16, "bold"))
        self.login_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))

        self.username_label = ttk.Label(self.login_frame, text="Username:")
        self.username_label.grid(row=1, column=0, sticky="e", padx=(0, 10))
        self.username_entry = ttk.Entry(self.login_frame)
        self.username_entry.grid(row=1, column=1)

        self.password_label = ttk.Label(self.login_frame, text="Password:")
        self.password_label.grid(row=2, column=0, sticky="e", padx=(0, 10))
        self.password_entry = ttk.Entry(self.login_frame, show="*")
        self.password_entry.grid(row=2, column=1)

        self.login_button = ttk.Button(self.login_frame, text="Login", command=self.login)
        self.login_button.grid(row=3, column=0, columnspan=2, pady=(10, 0))

    def create_widgets(self):
        self.login_frame.destroy()

        self.main_frame = ttk.Frame(self.master)
        self.main_frame.pack(padx=20, pady=20)

        # Generate random student ID
        self.id_label = ttk.Label(self.main_frame, text="Student ID:")
        self.id_label.grid(row=1, column=0, sticky="e", padx=(0, 10), pady=(0, 10))

        self.id_entry = ttk.Entry(self.main_frame)
        self.id_entry.grid(row=1, column=1, pady=(0, 10))
        self.id_entry.insert(0, self.generate_student_id())

        self.name_label = ttk.Label(self.main_frame, text="Student Name:")
        self.name_label.grid(row=0, column=0, sticky="e", padx=(0, 10), pady=(0, 10))
        self.name_entry = ttk.Entry(self.main_frame)
        self.name_entry.grid(row=0, column=1, pady=(0, 10))

        self.email_label = ttk.Label(self.main_frame, text="Email:")
        self.email_label.grid(row=2, column=0, sticky="e", padx=(0, 10), pady=(0, 10))
        self.email_entry = ttk.Entry(self.main_frame)
        self.email_entry.grid(row=2, column=1, pady=(0, 10))

        self.complaint_label = ttk.Label(self.main_frame, text="Complaint:")
        self.complaint_label.grid(row=3, column=0, sticky="ne", padx=(0, 10), pady=(0, 10))
        self.complaint_text = tk.Text(self.main_frame, height=5, width=30)
        self.complaint_text.grid(row=3, column=1, sticky="w", pady=(0, 10))

        if self.admin_mode:
            self.retrieve_button = ttk.Button(self.main_frame, text="Retrieve Complaints", command=self.retrieve_complaints)
            self.retrieve_button.grid(row=4, column=0, columnspan=2, pady=(10, 0))

            self.reply_label = ttk.Label(self.main_frame, text="Reply:")
            self.reply_label.grid(row=5, column=0, sticky="ne", padx=(0, 10), pady=(0, 10))
            self.reply_text = tk.Text(self.main_frame, height=5, width=30)
            self.reply_text.grid(row=5, column=1, sticky="w", pady=(0, 10))

            self.reply_button = ttk.Button(self.main_frame, text="Reply", command=self.reply_to_complaint)
            self.reply_button.grid(row=6, column=0, columnspan=2, pady=(10, 0))

        self.submit_button = ttk.Button(self.main_frame, text="Submit Complaint", command=self.submit_complaint)
        self.submit_button.grid(row=7, column=0, columnspan=2, pady=(10, 0))

        self.pending_button = ttk.Button(self.main_frame, text="View Pending Messages", command=self.view_pending_messages)
        self.pending_button.grid(row=8, column=0, columnspan=2, pady=(10, 0))

        self.logout_button = ttk.Button(self.main_frame, text="Logout", command=self.logout)
        self.logout_button.grid(row=9, column=0, columnspan=2, pady=(10, 0))


    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        # You would typically check the credentials against a database, but for simplicity, we'll hardcode admin credentials here
        if username == "admin" and password == "adminpassword":
            self.logged_in = True
            self.admin_mode = True
            self.create_widgets()
        elif username == "user" and password == "userpassword":
            self.logged_in = True
            self.admin_mode = False
            self.create_widgets()
        else:
            messagebox.showerror("Login Error", "Invalid username or password.")

    def submit_complaint(self):
        if not self.logged_in:
            messagebox.showerror("Error", "Please log in first.")
            return

        # Initialize current_time here
        current_time = int(time.time())

        time_diff = current_time - self.get_last_complaint_time()

        if time_diff < self.waiting_time:
            remaining_time = self.waiting_time - time_diff
            remaining_days = remaining_time // (24 * 60 * 60)
            messagebox.showinfo("Error", f"Please wait for {remaining_days} days before submitting another complaint.")
            return

        if self.semaphore.acquire(blocking=False):
            self.insert_complaint_to_db()
            self.semaphore.release()
            messagebox.showinfo("Success", "Complaint submitted successfully.")
        else:
            messagebox.showinfo("Error", "Another student is currently submitting a complaint. Please try again later.")

    def insert_complaint_to_db(self):
        name = self.name_entry.get()
        student_id = self.id_entry.get()
        email = self.email_entry.get()
        complaint = self.complaint_text.get("1.0", tk.END).strip()
        status = "Pending"  # Add Pending status
        timestamp = int(time.time())

        cursor = self.db_conn.cursor()
        cursor.execute('''INSERT INTO complaints (name, student_id, email, complaint, status, timestamp)
                          VALUES (?, ?, ?, ?, ?, ?)''', (name, student_id, email, complaint, status, timestamp))
        self.db_conn.commit()

    def get_last_complaint_time(self):
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT MAX(timestamp) FROM complaints")
        result = cursor.fetchone()[0]
        if result is None:
            return 0
        return result

    def retrieve_complaints(self):
        student_id = self.id_entry.get()
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT name, email, complaint FROM complaints WHERE student_id = ?", (student_id,))
        result = cursor.fetchone()
        if result:
            self.name_entry.delete(0, tk.END)
            self.email_entry.delete(0, tk.END)
            self.complaint_text.delete("1.0", tk.END)
            self.name_entry.insert(0, result[0])
            self.email_entry.insert(0, result[1])
            self.complaint_text.insert("1.0", result[2])
            messagebox.showinfo("Success", "Complaint details retrieved successfully.")
        else:
            messagebox.showerror("Error", "No complaint found with that student ID.")

    def reply_to_complaint(self):
        if not self.admin_mode:
            messagebox.showerror("Error", "You are not authorized to reply.")
            return

        reply_text = self.reply_text.get("1.0", tk.END).strip()
        if not reply_text:
            messagebox.showerror("Error", "Please enter a reply.")
            return

        complaint_id = self.id_entry.get()  # Assuming complaint ID is the same as student ID for simplicity
        if not complaint_id:
            messagebox.showerror("Error", "Invalid complaint ID.")
            return

        # Send reply email
        student_email = self.email_entry.get()
        self.send_email(student_email, reply_text)

        cursor = self.db_conn.cursor()
        cursor.execute("UPDATE complaints SET responded = 1 WHERE student_id = ?", (complaint_id,))
        self.db_conn.commit()

        messagebox.showinfo("Reply", "Reply sent successfully.")

    def send_email(self, to_email, reply_text):
        # Change the following to your email server details
        email_sender = "guiddel016@gmail.com"
        email_password = "dgoq ycmx poli uups"

        msg = MIMEMultipart()
        msg['From'] = email_sender
        msg['To'] = to_email
        msg['Subject'] = "Complaint Response"

        body = f"Dear Student,\n\nYour complaint has been resolved. Here is the response:\n\n{reply_text}\n\nRegards,\nAdmin"
        msg.attach(MIMEText(body, 'plain'))

        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(email_sender, email_password)
            text = msg.as_string()
            server.sendmail(email_sender, to_email, text)
            server.quit()
        except Exception as e:
            messagebox.showerror("Email Error", f"Failed to send email: {e}")

    def view_pending_messages(self):
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT * FROM complaints WHERE status = 'Pending'")
        pending_messages = cursor.fetchall()
        if pending_messages:
            messagebox.showinfo("Pending Messages", "\n".join([f"{msg[1]}: {msg[3]}" for msg in pending_messages]))
        else:
            messagebox.showinfo("Pending Messages", "No pending messages.")

    def logout(self):
        self.logged_in = False
        self.admin_mode = False
        self.main_frame.destroy()
        self.create_login_widgets()
    
    def generate_student_id(self):
        prefix = 'ICTU'
        year = '2024'
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))  # Generates a 5-character random string
        return f"{prefix}{year}{random_suffix}"


if __name__ == "__main__":
    root = tk.Tk()
    app = ComplaintApp(root)
    root.mainloop()
