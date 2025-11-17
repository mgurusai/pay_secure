import os
import random
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Load keys from .env file
load_dotenv()
key = os.getenv("FERNET_KEY")
cipher_suite = Fernet(key.encode())

def encrypt_data(data):
    """Encrypts any string data."""
    return cipher_suite.encrypt(data.encode())

def decrypt_data(encrypted_data):
    """Decrypts data."""
    return cipher_suite.decrypt(encrypted_data).decode()

def antivirus_scan(file_path):
    """Simulates an antivirus scan."""
    print(f'Simulated scan for {file_path}')
    return "No threats found"

def risk_analysis(amount, region):
    """Analyzes transaction risk."""
    risk_score = 0.5
    if amount > 5000:
        risk_score += 0.3
    if region.lower() in ["high risk country", "nigeria", "iran"]:
        risk_score += 0.4
    return min(risk_score, 1.0)

def generate_otp():
    """Generates a 6-digit OTP."""
    return str(random.randint(100000, 999999))

def requires_3ds_challenge(risk_score):
    """Checks if 3D Secure is needed."""
    return risk_score > 0.8