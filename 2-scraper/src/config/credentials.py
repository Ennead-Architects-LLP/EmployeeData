"""
GUI module for setting up credentials.
"""

import tkinter as tk
from tkinter import messagebox, ttk
from ..services.auth import AutoLogin


class CredentialsGUI:
    """
    GUI for setting up credentials interactively.
    """
    
    def __init__(self):
        self.root = None
        self.auto_login = AutoLogin()
    
    def create_credentials(self):
        """Create credentials file from GUI input."""
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not email or not password:
            messagebox.showerror("Error", "Please enter both email and password!")
            return
        
        if '@ennead.com' not in email.lower():
            result = messagebox.askyesno("Warning", 
                                       "The email doesn't contain '@ennead.com'. Continue anyway?")
            if not result:
                return
        
        # Create credentials file
        if self.auto_login.create_credentials_file(email, password):
            messagebox.showinfo("Success", 
                               "Credentials saved successfully!\n\n" +
                               "File: credentials.json\n" +
                               "Location: 2-scraper/\n" +
                               "Status: NOT tracked in git (secure)")
            self.root.destroy()
            return True
        else:
            messagebox.showerror("Error", "Failed to save credentials!")
            return False
    
    def show_gui(self):
        """Show the credentials setup GUI."""
        # Create GUI
        self.root = tk.Tk()
        self.root.title("Employee Scraper - Setup Credentials")
        self.root.geometry("450x280")
        self.root.resizable(False, False)
        
        # Center the window
        self.root.eval('tk::PlaceWindow . center')
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Enter your Ennead credentials", 
                               font=("Arial", 12, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Security notice
        security_label = ttk.Label(main_frame, 
                                  text="🔒 Credentials will be stored locally in credentials.json\n(This file is NOT tracked in git for security)",
                                  font=("Arial", 9),
                                  foreground="blue")
        security_label.grid(row=1, column=0, columnspan=2, pady=(0, 15))
        
        # Email field
        email_label = ttk.Label(main_frame, text="Email:")
        email_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        self.email_entry = ttk.Entry(main_frame, width=30)
        self.email_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Password field
        password_label = ttk.Label(main_frame, text="Password:")
        password_label.grid(row=3, column=0, sticky=tk.W, pady=5)
        self.password_entry = ttk.Entry(main_frame, width=30, show="*")
        self.password_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(20, 0))
        
        # Create credentials button
        create_btn = ttk.Button(button_frame, text="Save Credentials", 
                               command=self.create_credentials)
        create_btn.grid(row=0, column=0, padx=5)
        
        # Cancel button
        cancel_btn = ttk.Button(button_frame, text="Cancel", 
                               command=self.root.destroy)
        cancel_btn.grid(row=0, column=1, padx=5)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Focus on email field
        self.email_entry.focus()
        
        # Bind Enter key to create credentials
        self.root.bind('<Return>', lambda e: self.create_credentials())
        
        # Start the GUI
        self.root.mainloop()
        
        return self.auto_login.credentials_file.exists()


def show_credentials_gui():
    """Show credentials GUI and return True if credentials were created."""
    gui = CredentialsGUI()
    gui.show_gui()
    return gui.auto_login.credentials_file.exists()
