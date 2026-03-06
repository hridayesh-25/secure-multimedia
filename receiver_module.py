import boto3
import os
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives import serialization, hashes
from dotenv import load_dotenv

load_dotenv()

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET = os.getenv("S3_BUCKET")
ENCRYPTED_FILE = "encrypted_files/encrypted.bin"
ENCRYPTED_KEY_FILE = "encrypted_files/encrypted_key.bin"
SIGNATURE_FILE = "encrypted_files/signature.bin"
FILENAME_FILE = "encrypted_files/filename.txt"

s3 = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)

def download_from_s3():
    s3.download_file(S3_BUCKET, "encrypted.bin", ENCRYPTED_FILE)
    s3.download_file(S3_BUCKET, "encrypted_key.bin", ENCRYPTED_KEY_FILE)
    s3.download_file(S3_BUCKET, "signature.bin", SIGNATURE_FILE)
    s3.download_file(S3_BUCKET, "filename.txt", FILENAME_FILE)

def load_private_key():
    with open("private_key.pem", "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)

def decrypt_aes_key(private_key):

    with open(ENCRYPTED_KEY_FILE, "rb") as f:
        encrypted_key = f.read()

    return private_key.decrypt(
        encrypted_key,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

def decrypt_file(aes_key):

    with open(ENCRYPTED_FILE, "rb") as f:
        data = f.read()

    iv = data[:16]
    ciphertext = data[16:]

    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
    decryptor = cipher.decryptor()

    padded = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = padding.PKCS7(128).unpadder()
    plaintext = unpadder.update(padded) + unpadder.finalize()

    with open(FILENAME_FILE, "r") as f:
        filename = f.read().strip()

    decrypted_path = os.path.join("decrypted_files", filename)

    with open(decrypted_path, "wb") as f:
        f.write(plaintext)

    return decrypted_path

def receiver_pipeline():

    download_from_s3()

    private_key = load_private_key()
    aes_key = decrypt_aes_key(private_key)

    decrypted_path = decrypt_file(aes_key)

    return decrypted_path