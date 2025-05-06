import tkinter as tk
from tkinter import ttk, messagebox
from email_client import TempEmailClient
from storage import Storage
import threading
import time
import pyperclip  # For clipboard operations

class EmailApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TempBox - Temporary Email Client")
        self.root.geometry("800x600")
        
        self.client = TempEmailClient()
        self.storage = Storage()
        self.selected_email = None  # Track selected email
        self.refresh_thread = None  # Track refresh thread
        self.is_refreshing = False  # Track refresh state
        
        # Configure root grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        
        self._create_header()
        self._create_main_content()
        self._create_status_bar()
        
        # Load saved accounts
        self._load_saved_accounts()
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_header(self):
        header_frame = ttk.Frame(self.root)
        header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        ttk.Button(header_frame, text="New Email", command=self._create_new_email).pack(side=tk.LEFT, padx=5)
        ttk.Button(header_frame, text="Refresh", command=self._refresh_messages).pack(side=tk.LEFT, padx=5)
        
        refresh_frame = ttk.Frame(header_frame)
        refresh_frame.pack(side=tk.LEFT, padx=5)
        
        self.auto_refresh_var = tk.BooleanVar(value=False)
        self.auto_refresh_checkbox = ttk.Checkbutton(
            refresh_frame, 
            text="Auto Refresh", 
            variable=self.auto_refresh_var,
            command=self._toggle_auto_refresh
        )
        self.auto_refresh_checkbox.pack(side=tk.LEFT)
        
        # Add refresh interval selector
        ttk.Label(refresh_frame, text="Interval (sec):").pack(side=tk.LEFT, padx=(10, 2))
        self.refresh_interval = ttk.Spinbox(
            refresh_frame,
            from_=5,
            to=300,
            width=5,
            wrap=True
        )
        self.refresh_interval.set("30")
        self.refresh_interval.pack(side=tk.LEFT)

    def _create_main_content(self):
        content_frame = ttk.Frame(self.root)
        content_frame.grid(row=1, column=0, sticky="nsew", padx=5)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # Left sidebar for email accounts
        self.accounts_frame = ttk.Frame(content_frame)
        self.accounts_frame.grid(row=0, column=0, sticky="ns", padx=5)
        ttk.Label(self.accounts_frame, text="Email Accounts").pack(pady=5)
        
        # Create a frame for the accounts list and its scrollbar
        accounts_list_frame = ttk.Frame(self.accounts_frame)
        accounts_list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create Treeview for accounts instead of Listbox
        self.accounts_tree = ttk.Treeview(accounts_list_frame, columns=("Email", "Password"), show="headings", height=15)
        self.accounts_tree.heading("Email", text="Email")
        self.accounts_tree.heading("Password", text="Password")
        self.accounts_tree.column("Email", width=200)
        self.accounts_tree.column("Password", width=100)
        self.accounts_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add scrollbar for accounts
        accounts_scrollbar = ttk.Scrollbar(accounts_list_frame, orient=tk.VERTICAL, command=self.accounts_tree.yview)
        accounts_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.accounts_tree.configure(yscrollcommand=accounts_scrollbar.set)
        
        # Add right-click menu for accounts
        self.account_menu = tk.Menu(self.root, tearoff=0)
        self.account_menu.add_command(label="Copy Email", command=self._copy_email)
        self.account_menu.add_command(label="Copy Password", command=self._copy_password)
        self.account_menu.add_separator()
        self.account_menu.add_command(label="Remove Account", command=self._remove_account, foreground="red")
        
        # Bind account selection events
        self.accounts_tree.bind("<Button-3>", self._show_account_menu)  # Right-click
        self.accounts_tree.bind("<Double-1>", self._copy_email)  # Double-click
        self.accounts_tree.bind("<ButtonRelease-1>", self._on_account_select)  # Left-click
        
        # Right side for messages
        messages_frame = ttk.Frame(content_frame)
        messages_frame.grid(row=0, column=1, sticky="nsew", padx=5)
        messages_frame.grid_rowconfigure(1, weight=1)
        messages_frame.grid_columnconfigure(0, weight=1)
        
        # Messages list
        self.message_label = ttk.Label(messages_frame, text="Messages")
        self.message_label.grid(row=0, column=0, pady=5)
        
        # Create Treeview for messages with ID column
        self.messages_tree = ttk.Treeview(messages_frame, columns=("ID", "From", "Subject", "Date"), show="headings")
        self.messages_tree.grid(row=1, column=0, sticky="nsew")
        
        # Configure treeview columns
        self.messages_tree.heading("ID", text="ID")
        self.messages_tree.heading("From", text="From")
        self.messages_tree.heading("Subject", text="Subject")
        self.messages_tree.heading("Date", text="Date")
        
        # Hide ID column but keep it for reference
        self.messages_tree.column("ID", width=0, stretch=False)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(messages_frame, orient=tk.VERTICAL, command=self.messages_tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.messages_tree.configure(yscrollcommand=scrollbar.set)
        
        # Bind double-click event
        self.messages_tree.bind("<Double-1>", self._show_message_content)

    def _create_status_bar(self):
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=2, column=0, sticky="ew")
        self.status_var.set("Ready")
        
    def _create_new_email(self):
        if self.client.create_account():
            # Check if account creation was successful
            if not self.client.account:
                messagebox.showerror("Error", "Failed to create account - no account data returned")
                return
                
            email = self.client.account["address"]
            password = self.client.current_password
            
            # Save and display the new account
            self.storage.save_account(email, password)
            item = self.accounts_tree.insert("", tk.END, values=(email, password))
            
            # Select and highlight the new account
            self.accounts_tree.selection_set(item)
            self.accounts_tree.see(item)
            self.selected_email = email
            self.message_label.config(text=f"Messages for {email}")
            
            messagebox.showinfo("Success", f"New email created:\nEmail: {email}\nPassword: {password}")
            self._refresh_messages()
        else:
            messagebox.showerror("Error", "Failed to create new email account")

    def _load_saved_accounts(self):
        """Load saved accounts and select the first one"""
        accounts = self.storage.get_accounts()
        first_item = None
        for account in accounts:
            item = self.accounts_tree.insert("", tk.END, values=(account["email"], account["password"]))
            if not first_item:
                first_item = item
        
        # Select and authenticate the first account if available
        if first_item:
            self.accounts_tree.selection_set(first_item)
            self.accounts_tree.see(first_item)
            # Trigger the account selection event
            self._on_account_select(None)
            
    def _on_account_select(self, event=None):
        """Handle account selection (can be triggered manually or by event)"""
        selection = self.accounts_tree.selection()
        if selection:
            item = selection[0]
            email = self.accounts_tree.item(item)["values"][0]
            password = self.accounts_tree.item(item)["values"][1]
            
            # Update selected email
            self.selected_email = email
            self.message_label.config(text=f"Messages for {email}")
            
            # Highlight selected account (remove previous tags)
            for item in self.accounts_tree.get_children():
                self.accounts_tree.item(item, tags=())
            self.accounts_tree.item(selection, tags=('selected',))
            self.accounts_tree.tag_configure('selected', background='lightblue')
            
            # Authenticate with selected account
            if self.client.authenticate_account(email, password):
                self._refresh_messages()
                self.status_var.set(f"Authenticated as {email}")
            else:
                messagebox.showerror("Error", "Failed to authenticate account")
                self.selected_email = None
                self.message_label.config(text="Messages")

    def _refresh_messages(self):
        """Refresh messages with error handling"""
        try:
            self.messages_tree.delete(*self.messages_tree.get_children())
            if not self.selected_email:
                return
                
            messages = self.client.get_messages()
            if messages:
                for msg in messages:
                    # Get the message ID correctly
                    msg_id = msg.get('id', '')
                    if not msg_id and '@id' in msg:
                        msg_id = msg['@id'].split('/')[-1]
                    
                    self.messages_tree.insert("", tk.END, values=(
                        msg_id,  # Store the cleaned message ID
                        msg.get("from", {}).get("address", "N/A"),
                        msg.get("subject", "N/A"),
                        msg.get("createdAt", "N/A")
                    ))
                if not self.auto_refresh_var.get():
                    self.status_var.set(f"Found {len(messages)} messages")
            else:
                if not self.auto_refresh_var.get():
                    self.status_var.set("No messages found")
        except Exception as e:
            self.status_var.set(f"Error refreshing messages: {str(e)}")
            if self.auto_refresh_var.get():
                self._stop_auto_refresh()
                self.auto_refresh_var.set(False)

    def _show_message_content(self, event):
        selection = self.messages_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.messages_tree.item(item)["values"]
        if not values or not values[0]:  # Check if we have a valid message ID
            messagebox.showerror("Error", "Invalid message selected")
            return
            
        msg_id = values[0]  # Get the message ID
        
        # Create a new window for message content
        msg_window = tk.Toplevel(self.root)
        msg_window.title("TempBox - Message Content")
        msg_window.geometry("600x400")
        
        # Add text widget for content
        text_widget = tk.Text(msg_window, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(msg_window, orient=tk.VERTICAL, command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        # Get message content
        message = self.client.get_message_content(msg_id)
        if message:
            from_address = message.get('from', {}).get('address', 'N/A')
            subject = message.get('subject', 'N/A')
            date = message.get('createdAt', 'N/A')
            text = message.get('text', 'No content available')
            
            content = f"""From: {from_address}
Subject: {subject}
Date: {date}

{text}"""
            text_widget.insert(tk.END, content)
            text_widget.config(state='disabled')  # Make text read-only
        else:
            text_widget.insert(tk.END, "Failed to load message content")
            text_widget.config(state='disabled')

    def _remove_account(self):
        selection = self.accounts_tree.selection()
        if selection:
            item = selection[0]
            email = self.accounts_tree.item(item)["values"][0]
            if messagebox.askyesno("Confirm Removal", f"Remove account {email}?"):
                # Remove from storage
                self.storage.remove_account(email)
                # Remove from tree
                self.accounts_tree.delete(item)
                # Clear messages if this was the selected account
                if self.selected_email == email:
                    self.selected_email = None
                    self.messages_tree.delete(*self.messages_tree.get_children())
                    self.message_label.config(text="Messages")
                self.status_var.set(f"Removed account: {email}")

    def _toggle_auto_refresh(self):
        if self.auto_refresh_var.get():
            self._start_auto_refresh()
        else:
            self._stop_auto_refresh()
            self.status_var.set("Auto-refresh stopped")
    
    def _start_auto_refresh(self):
        if not self.selected_email:
            messagebox.showwarning("Warning", "Please select an email account first")
            self.auto_refresh_var.set(False)
            return
            
        if self.is_refreshing:
            return
            
        self.is_refreshing = True
        
        def refresh_loop():
            while self.is_refreshing and self.auto_refresh_var.get():
                try:
                    # Update UI in thread-safe way
                    self.root.after(0, self._refresh_messages)
                    # Get interval from spinbox, default to 30 if invalid
                    try:
                        interval = int(self.refresh_interval.get())
                    except ValueError:
                        interval = 30
                        self.refresh_interval.set("30")
                    
                    # Show refresh status
                    self.root.after(0, lambda: self.status_var.set(f"Auto-refresh active - Next refresh in {interval} seconds"))
                    
                    # Sleep in small increments to check if we should stop
                    for _ in range(interval):
                        if not self.is_refreshing:
                            break
                        time.sleep(1)
                        
                except Exception as e:
                    self.root.after(0, lambda: self.status_var.set(f"Auto-refresh error: {str(e)}"))
                    self.is_refreshing = False
                    self.auto_refresh_var.set(False)
                    break
        
        self.refresh_thread = threading.Thread(target=refresh_loop, daemon=True)
        self.refresh_thread.start()
        self.status_var.set("Auto-refresh started")
    
    def _stop_auto_refresh(self):
        self.is_refreshing = False
        if self.refresh_thread and self.refresh_thread.is_alive():
            self.refresh_thread.join(timeout=1.0)
    
    def _on_closing(self):
        """Handle window close event"""
        self._stop_auto_refresh()
        self.root.destroy()

    def _show_account_menu(self, event):
        item = self.accounts_tree.identify_row(event.y)
        if item:
            self.accounts_tree.selection_set(item)
            self.account_menu.post(event.x_root, event.y_root)

    def _copy_email(self, event=None):
        selection = self.accounts_tree.selection()
        if selection:
            item = selection[0]
            email = self.accounts_tree.item(item)["values"][0]
            pyperclip.copy(email)
            self.status_var.set(f"Email copied: {email}")

    def _copy_password(self):
        selection = self.accounts_tree.selection()
        if selection:
            item = selection[0]
            password = self.accounts_tree.item(item)["values"][1]
            pyperclip.copy(password)
            self.status_var.set("Password copied to clipboard")

def main():
    root = tk.Tk()
    app = EmailApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()