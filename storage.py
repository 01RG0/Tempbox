import json
import os

class Storage:
    def __init__(self):
        self.file_path = "tempbox_accounts.json"
        self.accounts = self._load_accounts()

    def _load_accounts(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_account(self, email, password):
        self.accounts.append({
            "email": email,
            "password": password
        })
        with open(self.file_path, 'w') as f:
            json.dump(self.accounts, f, indent=2)

    def get_accounts(self):
        return self.accounts

    def remove_account(self, email):
        """Remove an account from storage"""
        self.accounts = [acc for acc in self.accounts if acc["email"] != email]
        with open(self.file_path, 'w') as f:
            json.dump(self.accounts, f, indent=2)