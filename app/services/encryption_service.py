from cryptography.fernet import Fernet
from ..config import settings

# สร้าง key สำหรับการเข้ารหัส
encryption_key = settings.ENCRYPTION_KEY.encode()
cipher_suite = Fernet(encryption_key)

def encrypt_password(password: str) -> str:
    """เข้ารหัสรหัสผ่าน"""
    encrypted_password = cipher_suite.encrypt(password.encode())
    return encrypted_password.decode()

def decrypt_password(encrypted_password: str) -> str:
    """ถอดรหัสรหัสผ่าน"""
    decrypted_password = cipher_suite.decrypt(encrypted_password.encode())
    return decrypted_password.decode()