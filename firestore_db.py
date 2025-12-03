import firebase_admin
from firebase_admin import credentials, firestore
import json
from config import FIREBASE_SERVICE_ACCOUNT

class FirestoreDB:
    def __init__(self):
        # Initialize Firebase
        if not firebase_admin._apps:
            if FIREBASE_SERVICE_ACCOUNT:
                # Load service account from JSON string
                cred_dict = json.loads(FIREBASE_SERVICE_ACCOUNT)
                cred = credentials.Certificate(cred_dict)
            else:
                # Load from file
                cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
        
        self.db = firestore.client()
    
    async def add_user(self, user_id, chat_id, username=None, full_name=None):
        """Add a new user or update existing user with new allowed group"""
        user_ref = self.db.collection("users").document(str(user_id))
        user_data = user_ref.get()
        
        if user_data.exists:
            # Update existing user
            data = user_data.to_dict()
            allowed_groups = data.get("allowed_groups", [])
            
            if str(chat_id) not in allowed_groups:
                allowed_groups.append(str(chat_id))
                user_ref.update({
                    "allowed_groups": allowed_groups,
                    "username": username or data.get("username", ""),
                    "full_name": full_name or data.get("full_name", ""),
                    "updated_at": firestore.SERVER_TIMESTAMP
                })
                return "updated"
        else:
            # Create new user
            user_ref.set({
                "user_id": str(user_id),
                "username": username or "",
                "full_name": full_name or "",
                "allowed_groups": [str(chat_id)],
                "balance_tk": 0.0,
                "balance_usdt": 0.0,
                "is_active": True,
                "created_at": firestore.SERVER_TIMESTAMP,
                "updated_at": firestore.SERVER_TIMESTAMP
            })
            return "created"
    
    async def remove_user(self, user_id, chat_id=None):
        """Remove user completely or remove from specific group"""
        user_ref = self.db.collection("users").document(str(user_id))
        user_data = user_ref.get()
        
        if not user_data.exists:
            return "user_not_found"
        
        data = user_data.to_dict()
        
        if chat_id:
            # Remove from specific group only
            allowed_groups = data.get("allowed_groups", [])
            if str(chat_id) in allowed_groups:
                allowed_groups.remove(str(chat_id))
                
                if not allowed_groups:
                    # No more allowed groups, delete user
                    user_ref.delete()
                    return "deleted_completely"
                else:
                    # Update with remaining groups
                    user_ref.update({
                        "allowed_groups": allowed_groups,
                        "updated_at": firestore.SERVER_TIMESTAMP
                    })
                    return "removed_from_group"
            else:
                return "user_not_in_group"
        else:
            # Remove completely
            user_ref.delete()
            return "deleted_completely"
    
    async def get_user(self, user_id):
        """Get user data"""
        user_ref = self.db.collection("users").document(str(user_id))
        user_data = user_ref.get()
        
        if user_data.exists:
            return user_data.to_dict()
        return None
    
    async def get_all_users(self):
        """Get all users"""
        users = []
        docs = self.db.collection("users").stream()
        for doc in docs:
            users.append(doc.to_dict())
        return users
    
    async def is_user_allowed(self, user_id, chat_id):
        """Check if user is allowed in this group"""
        user_data = await self.get_user(user_id)
        if not user_data:
            return False
        
        allowed_groups = user_data.get("allowed_groups", [])
        return str(chat_id) in allowed_groups
    
    async def is_admin(self, user_id):
        """Check if user is admin"""
        from config import ADMIN_USER_IDS
        return user_id in ADMIN_USER_IDS
    
    async def update_balance(self, user_id, currency, amount, operation="add"):
        """Update user balance"""
        user_ref = self.db.collection("users").document(str(user_id))
        user_data = user_ref.get()
        
        if not user_data.exists:
            return False
        
        data = user_data.to_dict()
        current_balance = data.get(f"balance_{currency}", 0.0)
        
        if operation == "add":
            new_balance = current_balance + amount
        elif operation == "subtract":
            new_balance = current_balance - amount
        else:
            new_balance = amount
        
        user_ref.update({
            f"balance_{currency}": new_balance,
            "updated_at": firestore.SERVER_TIMESTAMP
        })
        
        return True

# Global database instance
db = FirestoreDB()
