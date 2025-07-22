from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
from typing import Union, Optional
import logging

logger = logging.getLogger(__name__)

class EncryptionService:
    """Encryption service for sensitive NETHRA data"""
    
    def __init__(self, key_path: str = "./encryption.key"):
        self.key_path = key_path
        self.cipher_suite = None
        self._initialize_encryption()
    
    def _initialize_encryption(self):
        """Initialize encryption with key"""
        try:
            # Try to load existing key
            if os.path.exists(self.key_path):
                with open(self.key_path, 'rb') as key_file:
                    key = key_file.read()
            else:
                # Generate new key
                key = Fernet.generate_key()
                with open(self.key_path, 'wb') as key_file:
                    key_file.write(key)
                logger.info(f"Generated new encryption key: {self.key_path}")
            
            self.cipher_suite = Fernet(key)
            logger.info("Encryption service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {str(e)}")
            raise
    
    def encrypt(self, data: Union[str, bytes]) -> str:
        """Encrypt data and return base64 encoded string"""
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            encrypted_data = self.cipher_suite.encrypt(data)
            return base64.b64encode(encrypted_data).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt base64 encoded data and return string"""
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = self.cipher_suite.decrypt(encrypted_bytes)
            return decrypted_data.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise
    
    def encrypt_dict(self, data: dict) -> str:
        """Encrypt dictionary as JSON"""
        import json
        json_string = json.dumps(data)
        return self.encrypt(json_string)
    
    def decrypt_dict(self, encrypted_data: str) -> dict:
        """Decrypt and parse as dictionary"""
        import json
        decrypted_json = self.decrypt(encrypted_data)
        return json.loads(decrypted_json)

# Global encryption service
_encryption_service = None

def get_encryption_service() -> EncryptionService:
    """Get or create global encryption service"""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service
