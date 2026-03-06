import os
import boto3
import hashlib
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives import serialization, hashes
from dotenv import load_dotenv
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

load_dotenv()

ENCRYPTED_FILE = "encrypted_files/encrypted.bin"
ENCRYPTED_KEY_FILE = "encrypted_files/encrypted_key.bin"
SIGNATURE_FILE = "encrypted_files/signature.bin"
FILENAME_FILE = "encrypted_files/filename.txt"
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET = os.getenv("S3_BUCKET")

def generate_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    public_key = private_key.public_key()

    with open("private_key.pem", "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            )
        )

    with open("public_key.pem", "wb") as f:
        f.write(
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        )

s3 = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)

def load_public_key():
    if not os.path.exists("public_key.pem"):
        generate_keys()

    with open("public_key.pem", "rb") as f:
        return serialization.load_pem_public_key(f.read())

def load_private_key():
    with open("private_key.pem", "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)

def generate_key():
    return os.urandom(32)

def encrypt_file(input_file, key):
    iv = os.urandom(16)

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()

    with open(input_file, "rb") as f:
        data = f.read()

    padder = padding.PKCS7(128).padder()
    padded = padder.update(data) + padder.finalize()

    ciphertext = encryptor.update(padded) + encryptor.finalize()

    with open(ENCRYPTED_FILE, "wb") as f:
        f.write(iv + ciphertext)

def encrypt_aes_key(aes_key, public_key):
    encrypted_key = public_key.encrypt(
        aes_key,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    with open(ENCRYPTED_KEY_FILE, "wb") as f:
        f.write(encrypted_key)

def compute_hash(file_path):
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as f:
        sha256.update(f.read())

    return sha256.digest()

def sign_hash(private_key, hash_value):
    signature = private_key.sign(
        hash_value,
        asym_padding.PSS(
            mgf=asym_padding.MGF1(hashes.SHA256()),
            salt_length=asym_padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

    with open(SIGNATURE_FILE, "wb") as f:
        f.write(signature)

def upload_to_s3():
    s3.upload_file(ENCRYPTED_FILE, S3_BUCKET, "encrypted.bin")
    s3.upload_file(ENCRYPTED_KEY_FILE, S3_BUCKET, "encrypted_key.bin")
    s3.upload_file(SIGNATURE_FILE, S3_BUCKET, "signature.bin")
    s3.upload_file(FILENAME_FILE, S3_BUCKET, "filename.txt")

def sender_pipeline(input_file):

    public_key = load_public_key()
    private_key = load_private_key()

    aes_key = generate_key()

    encrypt_file(input_file, aes_key)
    encrypt_aes_key(aes_key, public_key)

    file_hash = compute_hash(ENCRYPTED_FILE)
    sign_hash(private_key, file_hash)

    # save original filename
    filename = os.path.basename(input_file)

    with open(FILENAME_FILE, "w") as f:
        f.write(filename)

    upload_to_s3()