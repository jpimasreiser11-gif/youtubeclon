"""
Security: Token Encryption/Decryption System
Protects sensitive OAuth tokens and API keys
"""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from dotenv import load_dotenv

load_dotenv()

def generate_encryption_key():
    """
    Genera una nueva clave de encriptación
    IMPORTANTE: Ejecutar solo UNA VEZ y guardar en .env
    """
    key = Fernet.generate_key()
    print("🔐 Nueva clave de encriptación generada:")
    print(f"ENCRYPTION_KEY={key.decode()}")
    print("\n⚠️ IMPORTANTE: Añade esta línea a tu archivo .env")
    print("⚠️ NUNCA compartas esta clave públicamente")
    return key

def get_cipher():
    """
    Obtiene el cipher para encriptar/desencriptar
    """
    encryption_key = os.getenv('ENCRYPTION_KEY')
    
    if not encryption_key:
        raise ValueError(
            "❌ ENCRYPTION_KEY no encontrada en .env\n"
            "Ejecuta: python scripts/encryption.py --generate-key"
        )
    
    return Fernet(encryption_key.encode())

def encrypt_token(token: str) -> str:
    """
    Encripta un token (OAuth, API key, etc.)
    
    Args:
        token: Token en texto plano
    
    Returns:
        Token encriptado como string
    """
    if not token:
        return ""
    
    cipher = get_cipher()
    encrypted = cipher.encrypt(token.encode())
    return encrypted.decode()

def decrypt_token(encrypted_token: str) -> str:
    """
    Desencripta un token
    
    Args:
        encrypted_token: Token encriptado
    
    Returns:
        Token en texto plano
    """
    if not encrypted_token:
        return ""
    
    cipher = get_cipher()
    decrypted = cipher.decrypt(encrypted_token.encode())
    return decrypted.decode()

def encrypt_file(input_path: str, output_path: str):
    """
    Encripta un archivo completo (útil para cookies, secrets, etc.)
    """
    cipher = get_cipher()
    
    with open(input_path, 'rb') as f:
        content = f.read()
    
    encrypted = cipher.encrypt(content)
    
    with open(output_path, 'wb') as f:
        f.write(encrypted)
    
    print(f"✅ Archivo encriptado: {output_path}")

def decrypt_file(input_path: str, output_path: str):
    """
    Desencripta un archivo
    """
    cipher = get_cipher()
    
    with open(input_path, 'rb') as f:
        encrypted_content = f.read()
    
    decrypted = cipher.decrypt(encrypted_content)
    
    with open(output_path, 'wb') as f:
        f.write(decrypted)
    
    print(f"✅ Archivo desencriptado: {output_path}")

# Ejemplo de uso con tokens de OAuth
def save_encrypted_youtube_token(access_token: str, refresh_token: str, user_id: str):
    """
    Guarda tokens de YouTube encriptados en la base de datos
    """
    import psycopg2
    
    encrypted_access = encrypt_token(access_token)
    encrypted_refresh = encrypt_token(refresh_token)
    
    conn = psycopg2.connect(
        user='n8n',
        password='n8n',
        host='localhost',
        port=5432,
        database='antigravity'
    )
    
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO platform_connections 
        (user_id, platform, access_token_encrypted, refresh_token_encrypted, connected)
        VALUES (%s, 'youtube', %s, %s, true)
        ON CONFLICT (user_id, platform) 
        DO UPDATE SET 
            access_token_encrypted = %s,
            refresh_token_encrypted = %s,
            connected = true
        """,
        (user_id, encrypted_access, encrypted_refresh, encrypted_access, encrypted_refresh)
    )
    
    conn.commit()
    cur.close()
    conn.close()
    
    print("✅ Tokens de YouTube guardados (encriptados)")

def get_decrypted_youtube_token(user_id: str):
    """
    Obtiene tokens de YouTube desencriptados de la base de datos
    """
    import psycopg2
    
    conn = psycopg2.connect(
        user='n8n',
        password='n8n',
        host='localhost',
        port=5432,
        database='antigravity'
    )
    
    cur = conn.cursor()
    cur.execute(
        """
        SELECT access_token_encrypted, refresh_token_encrypted
        FROM platform_connections
        WHERE user_id = %s AND platform = 'youtube'
        """,
        (user_id,)
    )
    
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    if result:
        access_token = decrypt_token(result[0])
        refresh_token = decrypt_token(result[1])
        return {
            'access_token': access_token,
            'refresh_token': refresh_token
        }
    
    return None

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Encryption utilities")
    parser.add_argument("--generate-key", action="store_true", help="Generate new encryption key")
    parser.add_argument("--encrypt", help="Encrypt a string")
    parser.add_argument("--decrypt", help="Decrypt a string")
    parser.add_argument("--test", action="store_true", help="Run encryption test")
    
    args = parser.parse_args()
    
    if args.generate_key:
        generate_encryption_key()
    
    elif args.encrypt:
        encrypted = encrypt_token(args.encrypt)
        print(f"Encrypted: {encrypted}")
    
    elif args.decrypt:
        decrypted = decrypt_token(args.decrypt)
        print(f"Decrypted: {decrypted}")
    
    elif args.test:
        print("🧪 Testing encryption...")
        test_token = "sk-test-1234567890-abcdef"
        
        encrypted = encrypt_token(test_token)
        print(f"Original:  {test_token}")
        print(f"Encrypted: {encrypted}")
        
        decrypted = decrypt_token(encrypted)
        print(f"Decrypted: {decrypted}")
        
        if test_token == decrypted:
            print("✅ Encryption test PASSED")
        else:
            print("❌ Encryption test FAILED")
    
    else:
        parser.print_help()
