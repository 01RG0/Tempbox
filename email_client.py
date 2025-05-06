import requests
import random
import string
from prettytable import PrettyTable
import time
import os
from dotenv import load_dotenv
import json
from datetime import datetime
import html2text

load_dotenv()

class TempEmailClient:
    def __init__(self):
        self.base_url = "https://api.mail.tm"
        self.session = requests.Session()
        self.account = None
        self.token = None
        self.domain = None
        self.current_password = None

    def reset_state(self):
        """Reset the client state between account switches"""
        self.account = None
        self.token = None
        self.current_password = None
        self.session.headers.pop('Authorization', None)
        
    def get_domains(self):
        """Get available domains for email creation"""
        try:
            response = self.session.get(f"{self.base_url}/domains")
            response.raise_for_status()
            domains = response.json().get('hydra:member', [])
            if domains:
                self.domain = domains[0]['domain']
                return domains
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error fetching domains: {e}")
            return None
    
    def generate_random_username(self, length=10):
        """Generate a random username for email"""
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for _ in range(length))
    
    def authenticate_account(self, email, password):
        """Authenticate an existing account and get a new token"""
        self.reset_state()  # Reset state before authenticating
        try:
            # Get token for the account
            token_payload = {
                "address": email,
                "password": password
            }
            token_response = self.session.post(f"{self.base_url}/token", json=token_payload)
            token_response.raise_for_status()
            self.token = token_response.json().get('token')
            
            # Store account info
            self.account = {
                "address": email,
                "password": password
            }
            self.current_password = password
            
            # Set authorization header
            self.session.headers.update({
                "Authorization": f"Bearer {self.token}"
            })
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error authenticating account: {e}")
            self.reset_state()
            return False

    def create_account(self, username=None, password=None):
        """Create a new temporary email account"""
        self.reset_state()  # Reset state before creating new account
        if not self.domain:
            self.get_domains()
            if not self.domain:
                print("No domains available")
                return False
        
        if not username:
            username = self.generate_random_username()
        
        if not password:
            password = self.generate_random_username(16)
            
        self.current_password = password
        email = f"{username}@{self.domain}"
        
        try:
            # First try to create the account
            payload = {
                "address": email,
                "password": password
            }
            response = self.session.post(f"{self.base_url}/accounts", json=payload)
            response.raise_for_status()
            
            # Then authenticate to get the token
            auth_payload = {
                "address": email,
                "password": password
            }
            auth_response = self.session.post(f"{self.base_url}/token", json=auth_payload)
            auth_response.raise_for_status()
            
            self.token = auth_response.json().get('token')
            if not self.token:
                print("Failed to get authentication token")
                return False
                
            # Set authorization header
            self.session.headers.update({
                "Authorization": f"Bearer {self.token}"
            })
            
            # Store account info
            self.account = {
                "address": email,
                "password": password
            }
            
            print(f"Account created successfully! Email: {email}, Password: {password}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"Error creating account: {e}")
            self.current_password = None
            self.account = None
            return False

    def get_messages(self):
        """Retrieve messages for the current account"""
        if not self.token:
            print("No account authenticated")
            return None
        
        try:
            response = self.session.get(f"{self.base_url}/messages")
            response.raise_for_status()
            messages = response.json().get('hydra:member', [])
            
            # Process message IDs to ensure they're valid
            for msg in messages:
                # Extract the ID from @id if it exists, otherwise use id
                msg_id = msg.get('@id', '').split('/')[-1]
                if not msg_id:
                    msg_id = msg.get('id', '')
                msg['id'] = msg_id
            
            return messages
        except requests.exceptions.RequestException as e:
            print(f"Error fetching messages: {e}")
            return None
    
    def display_messages(self):
        """Display messages in a nice table format with more details"""
        messages = self.get_messages()
        if not messages:
            print("No messages found")
            return
        
        table = PrettyTable()
        table.field_names = ["ID", "From", "Subject", "Received At", "Has Attachments"]
        table.max_width = 40
        
        for msg in messages:
            table.add_row([
                msg.get('id', 'N/A')[:8],
                msg.get('from', {}).get('address', 'N/A'),
                msg.get('subject', 'N/A')[:30] + ('...' if len(msg.get('subject', '')) > 30 else ''),
                msg.get('createdAt', 'N/A'),
                'Yes' if msg.get('attachments', []) else 'No'
            ])
        
        print(table)
    
    def get_message_content(self, message_id):
        """Get the content of a specific message"""
        if not self.token or not message_id:
            print("No account authenticated or invalid message ID")
            return None
        
        try:
            # Clean up the message ID if it contains the full URL
            if '/' in message_id:
                message_id = message_id.split('/')[-1]
                
            response = self.session.get(f"{self.base_url}/messages/{message_id}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching message content: {e}")
            return None

    def delete_message(self, message_id):
        """Delete a specific message"""
        if not self.token:
            print("No account authenticated")
            return False
        
        try:
            response = self.session.delete(f"{self.base_url}/messages/{message_id}")
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error deleting message: {e}")
            return False

    def search_messages(self, query):
        """Search messages by subject or sender"""
        messages = self.get_messages()
        if not messages:
            return []
        
        query = query.lower()
        return [msg for msg in messages if 
                query in msg.get('subject', '').lower() or 
                query in msg.get('from', {}).get('address', '').lower()]

    def save_message_to_file(self, message_id):
        """Save a message content to a file"""
        message = self.get_message_content(message_id)
        if not message:
            return False
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tempbox_message_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(message, f, indent=2)
            print(f"Message saved to {filename}")
            return True
        except Exception as e:
            print(f"Error saving message: {e}")
            return False

    def display_message_content(self, message_id):
        """Display full message content with HTML converted to text"""
        message = self.get_message_content(message_id)
        if not message:
            return
        
        h = html2text.HTML2Text()
        h.ignore_links = False
        
        print("\n" + "="*50)
        print("TempBox - Message Details")
        print("="*50)
        print(f"From: {message.get('from', {}).get('address', 'N/A')}")
        print(f"Subject: {message.get('subject', 'N/A')}")
        print(f"Date: {message.get('createdAt', 'N/A')}")
        print("="*50 + "\n")
        
        html_content = message.get('text', '')
        if html_content:
            print(h.handle(html_content))
        else:
            print("No content available")

    def wait_for_new_messages(self, interval=10, max_checks=10):
        """Wait for new messages to arrive"""
        if not self.token:
            print("No account authenticated")
            return
        
        initial_messages = self.get_messages() or []
        initial_ids = {msg['id'] for msg in initial_messages}
        
        print(f"Waiting for new messages (checking every {interval} seconds)...")
        
        for _ in range(max_checks):
            time.sleep(interval)
            current_messages = self.get_messages() or []
            current_ids = {msg['id'] for msg in current_messages}
            
            new_ids = current_ids - initial_ids
            if new_ids:
                print("\nNew messages received!")
                self.display_messages()
                return
            
            print(".", end="", flush=True)
        
        print("\nNo new messages received within the expected time.")