import os
import time
import csv
import hashlib
import boto3
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives import serialization, hashes


# ---------------------------
# CONFIG
# ---------------------------
INPUT_FILE = "input_files/100mb.mp4"
ENCRYPTED_FILE = "encrypted_files/encrypted.bin"
DECRYPTED_FILE = "decrypted_files/100mb.mp4"
RESULT_FILE = "results/hybrid_results.csv"
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
CRYPTO_RESULT_FILE = "results/crypto_results.csv"
CLOUD_RESULT_FILE = "results/cloud_results.csv"
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET = os.getenv("S3_BUCKET")
S3_OBJECT = "encrypted.bin"
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

if AWS_ACCESS_KEY is None or AWS_SECRET_KEY is None:
    raise ValueError("AWS credentials not set in environment variables")

# ---------------------------
# KEY GENERATION (AES 25
# ---------------------------
def generate_key():
    return os.urandom(32)

# ---------------------------
# upload to s3 function
# ---------------------------
def upload_to_s3():
    start = time.perf_counter()
    s3.upload_file(ENCRYPTED_FILE, S3_BUCKET, S3_OBJECT)
    return time.perf_counter() - start

# ---------------------------
# download from s3 function
# ---------------------------
def download_from_s3():
    start = time.perf_counter()
    s3.download_file(S3_BUCKET, S3_OBJECT, ENCRYPTED_FILE)
    return time.perf_counter() - start

# ---------------------------
# AES ENCRYPTION
# ---------------------------
def encrypt_file(key):
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    with open(INPUT_FILE, "rb") as f:
        data = f.read()

    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(data) + padder.finalize()

    start = time.perf_counter()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    aes_enc_time = time.perf_counter() - start

    with open(ENCRYPTED_FILE, "wb") as f:
        f.write(iv + ciphertext)

    return aes_enc_time


# ---------------------------
# AES DECRYPTION
# ---------------------------
def decrypt_file(key):
    with open(ENCRYPTED_FILE, "rb") as f:
        file_data = f.read()

    iv = file_data[:16]
    ciphertext = file_data[16:]

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()

    start = time.perf_counter()
    padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = padding.PKCS7(128).unpadder()
    plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
    aes_dec_time = time.perf_counter() - start

    with open(DECRYPTED_FILE, "wb") as f:
        f.write(plaintext)

    return aes_dec_time


# ---------------------------
# RSA KEY LOADING
# ---------------------------
def load_public_key():
    with open("public_key.pem", "rb") as f:
        return serialization.load_pem_public_key(f.read())


def load_private_key():
    with open("private_key.pem", "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)


# ---------------------------
# RSA KEY WRAPPING
# ---------------------------
def encrypt_aes_key(aes_key, public_key):
    start = time.perf_counter()
    encrypted_key = public_key.encrypt(
        aes_key,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    rsa_enc_time = time.perf_counter() - start

    with open("encrypted_files/encrypted_key.bin", "wb") as f:
        f.write(encrypted_key)

    return rsa_enc_time


def decrypt_aes_key(private_key):
    with open("encrypted_files/encrypted_key.bin", "rb") as f:
        encrypted_key = f.read()

    start = time.perf_counter()
    decrypted_key = private_key.decrypt(
        encrypted_key,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    rsa_dec_time = time.perf_counter() - start

    return decrypted_key, rsa_dec_time


# ---------------------------
# HASHING (SHA-256)
# ---------------------------
def compute_file_hash(file_path):
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            sha256.update(chunk)

    return sha256.digest()


def save_hash(hash_value):
    with open("encrypted_files/file_hash.bin", "wb") as f:
        f.write(hash_value)


def verify_hash():
    with open("encrypted_files/file_hash.bin", "rb") as f:
        stored_hash = f.read()

    current_hash = compute_file_hash(ENCRYPTED_FILE)
    return stored_hash == current_hash


# ---------------------------
# DIGITAL SIGNATURE (RSA-PSS)
# ---------------------------
def sign_hash(private_key, hash_value):
    start = time.perf_counter()
    signature = private_key.sign(
        hash_value,
        asym_padding.PSS(
            mgf=asym_padding.MGF1(hashes.SHA256()),
            salt_length=asym_padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    sign_time = time.perf_counter() - start

    with open("encrypted_files/signature.bin", "wb") as f:
        f.write(signature)

    return sign_time


def verify_signature(public_key, hash_value):
    with open("encrypted_files/signature.bin", "rb") as f:
        signature = f.read()

    start = time.perf_counter()
    try:
        public_key.verify(
            signature,
            hash_value,
            asym_padding.PSS(
                mgf=asym_padding.MGF1(hashes.SHA256()),
                salt_length=asym_padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        verify_time = time.perf_counter() - start
        return True, verify_time
    except Exception:
        return False, 0


# ---------------------------
# LOG RESULTS
# ---------------------------
def log_results(file_size,
                aes_enc, rsa_enc,
                sign_time, rsa_dec,
                aes_dec, hash_time,
                verify_time, total_time):

    non_aes_time = rsa_enc + sign_time + rsa_dec + verify_time + hash_time

    overhead_percent = (
        (non_aes_time / total_time) * 100
        if total_time > 0 else 0
    )

    file_exists = os.path.isfile(RESULT_FILE)

    with open(RESULT_FILE, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)

        if not file_exists:
            writer.writerow([
                "File Size (bytes)",
                "AES Enc (s)",
                "RSA Enc (s)",
                "Sign Time (s)",
                "RSA Dec (s)",
                "AES Dec (s)",
                "Hash Time (s)",
                "Verify Time (s)",
                "Total Time (s)",
                "Non-AES Time (s)",
                "Overhead (%)"
            ])

        writer.writerow([
            file_size,
            aes_enc,
            rsa_enc,
            sign_time,
            rsa_dec,
            aes_dec,
            hash_time,
            verify_time,
            total_time,
            non_aes_time,
            overhead_percent
        ])

# ---------------------------
# log crypto results
# ---------------------------
def log_crypto_results(mode, file_size,
                       aes_enc, rsa_enc,
                       sign_time, rsa_dec,
                       aes_dec, hash_time,
                       verify_time, crypto_time):

    non_aes_time = rsa_enc + sign_time + rsa_dec + verify_time + hash_time
    overhead_percent = (non_aes_time / crypto_time) * 100 if crypto_time > 0 else 0

    file_exists = os.path.isfile(CRYPTO_RESULT_FILE)

    with open(CRYPTO_RESULT_FILE, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)

        if not file_exists:
            writer.writerow([
                "Mode",
                "File Size (bytes)",
                "AES Enc",
                "RSA Enc",
                "Sign",
                "RSA Dec",
                "AES Dec",
                "Hash",
                "Verify",
                "Crypto Time",
                "Overhead (%)"
            ])

        writer.writerow([
            mode,
            file_size,
            aes_enc,
            rsa_enc,
            sign_time,
            rsa_dec,
            aes_dec,
            hash_time,
            verify_time,
            crypto_time,
            overhead_percent
        ])
        
# ----------------------------
# log cloud results
# ----------------------------
def log_cloud_results(mode, file_size,
                      upload_time,
                      download_time,
                      crypto_time,
                      end_to_end_time):

    crypto_percent = (crypto_time / end_to_end_time) * 100 if end_to_end_time > 0 else 0

    file_exists = os.path.isfile(CLOUD_RESULT_FILE)

    with open(CLOUD_RESULT_FILE, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)

        if not file_exists:
            writer.writerow([
                "Mode",
                "File Size (bytes)",
                "Upload Time",
                "Download Time",
                "Crypto Time",
                "End-to-End Time",
                "Crypto Percentage (%)"
            ])

        writer.writerow([
            mode,
            file_size,
            upload_time,
            download_time,
            crypto_time,
            end_to_end_time,
            crypto_percent
        ])

# ---------------------------
# RUN MODE
# ---------------------------
def run_mode(mode, repetitions=3):

    public_key = load_public_key()
    private_key = load_private_key()

    file_size = os.path.getsize(INPUT_FILE)

    aes_enc_total = 0
    rsa_enc_total = 0
    sign_total = 0
    rsa_dec_total = 0
    aes_dec_total = 0
    hash_total = 0
    verify_total = 0
    upload_total = 0
    download_total = 0
    crypto_total_time = 0
    end_to_end_total = 0

    for _ in range(repetitions):

        aes_key = generate_key()

        start_end_to_end = time.perf_counter()

        # ---------------- CRYPTO START ----------------
        start_crypto = time.perf_counter()

        aes_enc_time = encrypt_file(aes_key)

        rsa_enc_time = 0
        rsa_dec_time = 0
        hash_time = 0
        sign_time = 0
        verify_time = 0

        if mode in ["AES_RSA", "FULL"]:
            rsa_enc_time = encrypt_aes_key(aes_key, public_key)

        if mode == "FULL":
            start_hash = time.perf_counter()
            file_hash = compute_file_hash(ENCRYPTED_FILE)
            hash_time = time.perf_counter() - start_hash

            save_hash(file_hash)
            sign_time = sign_hash(private_key, file_hash)

        crypto_phase_time = time.perf_counter() - start_crypto

        # ---------------- CLOUD PHASE ----------------
        upload_time = 0
        download_time = 0

        if mode == "FULL":
            upload_time = upload_to_s3()
            download_time = download_from_s3()

        # ---------------- RECEIVER CRYPTO ----------------
        if mode == "FULL":

            if not verify_hash():
                print("Integrity failed")
                return

            current_hash = compute_file_hash(ENCRYPTED_FILE)
            valid, verify_time = verify_signature(public_key, current_hash)

            if not valid:
                print("Signature failed")
                return

        if mode in ["AES_RSA", "FULL"]:
            decrypted_key, rsa_dec_time = decrypt_aes_key(private_key)
        else:
            decrypted_key = aes_key

        aes_dec_time = decrypt_file(decrypted_key)

        end_to_end_time = time.perf_counter() - start_end_to_end

        # Accumulate
        aes_enc_total += aes_enc_time
        rsa_enc_total += rsa_enc_time
        sign_total += sign_time
        rsa_dec_total += rsa_dec_time
        aes_dec_total += aes_dec_time
        hash_total += hash_time
        verify_total += verify_time
        upload_total += upload_time
        download_total += download_time
        crypto_total_time += crypto_phase_time
        end_to_end_total += end_to_end_time

    # Averages
    aes_enc_avg = aes_enc_total / repetitions
    rsa_enc_avg = rsa_enc_total / repetitions
    sign_avg = sign_total / repetitions
    rsa_dec_avg = rsa_dec_total / repetitions
    aes_dec_avg = aes_dec_total / repetitions
    hash_avg = hash_total / repetitions
    verify_avg = verify_total / repetitions
    upload_avg = upload_total / repetitions
    download_avg = download_total / repetitions
    crypto_avg = crypto_total_time / repetitions
    end_to_end_avg = end_to_end_total / repetitions

    # Log crypto results for all modes
    log_crypto_results(
        mode,
        file_size,
        aes_enc_avg,
        rsa_enc_avg,
        sign_avg,
        rsa_dec_avg,
        aes_dec_avg,
        hash_avg,
        verify_avg,
        crypto_avg
    )

    # Log cloud results only for FULL mode
    if mode == "FULL":
        log_cloud_results(
            mode,
            file_size,
            upload_avg,
            download_avg,
            crypto_avg,
            end_to_end_avg
        )

    print("\n----- RESULTS -----")
    print("Crypto Time:", crypto_avg)
    print("Upload Time:", upload_avg)
    print("Download Time:", download_avg)
    print("End-to-End Time:", end_to_end_avg)

# ---------------------------
# MAIN
# ---------------------------

if __name__ == "__main__":
    print("Running All Modes Automatically")

    for mode in ["AES_ONLY", "AES_RSA", "FULL"]:
        print(f"Running mode: {mode}")
        run_mode(mode,repetitions=3)

    print("All comparison experiments completed")