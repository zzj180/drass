from typing import Optional, Dict, Any
from datetime import datetime
import uuid
from app.core.security import verify_password
from app.core.logging import get_logger

logger = get_logger(__name__)


class AuthService:
    """
    Simple in-memory authentication service for development
    In production, this should be replaced with a database-backed service
    """

    def __init__(self):
        # In-memory user storage for development
        # Password for test@example.com is "testpassword123"
        self.users = {
            "test-user-id": {
                "id": "test-user-id",
                "email": "test@example.com",
                "password": "$2b$12$oVwSmHPGAvWjkU5RMvqbHuQ0g2gqowxQhKJgulychBhd32ceKVLX2",  # "testpassword123"
                "name": "Test User",
                "role": "user",
                "is_active": True,
                "created_at": datetime.utcnow()
            },
            "admin-user-id": {
                "id": "admin-user-id",
                "email": "admin@example.com",
                "password": "$2b$12$oVwSmHPGAvWjkU5RMvqbHuQ0g2gqowxQhKJgulychBhd32ceKVLX2",  # "testpassword123"
                "name": "Admin User",
                "role": "admin",
                "is_active": True,
                "created_at": datetime.utcnow()
            }
        }
        self.email_to_id = {
            "test@example.com": "test-user-id",
            "admin@example.com": "admin-user-id"
        }

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        user_id = self.email_to_id.get(email)
        if user_id:
            return self.users.get(user_id)
        return None

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        return self.users.get(user_id)

    async def create_user(self, email: str, password: str, name: str) -> Dict[str, Any]:
        """Create a new user"""
        user_id = str(uuid.uuid4())
        user = {
            "id": user_id,
            "email": email,
            "password": password,  # Should already be hashed
            "name": name,
            "role": "user",
            "is_active": True,
            "created_at": datetime.utcnow()
        }
        self.users[user_id] = user
        self.email_to_id[email] = user_id
        logger.info(f"Created new user: {email}")
        return user

    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user"""
        user = await self.get_user_by_email(email)
        if not user:
            logger.warning(f"Authentication failed: User not found for email {email}")
            return None

        if not verify_password(password, user["password"]):
            logger.warning(f"Authentication failed: Invalid password for email {email}")
            return None

        if not user.get("is_active", True):
            logger.warning(f"Authentication failed: User {email} is not active")
            return None

        logger.info(f"User {email} authenticated successfully")
        return user

    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update user information"""
        user = self.users.get(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Update user fields
        for key, value in updates.items():
            if key in ["id", "email"]:  # Don't allow updating these fields
                continue
            user[key] = value

        logger.info(f"Updated user {user_id}")
        return user


# Global auth service instance
auth_service = AuthService()