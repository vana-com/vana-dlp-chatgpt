import os
import tempfile
import traceback
import requests
import vana
import gnupg
import base64
from urllib.parse import urlparse
from hotdog.models.contribution import Contribution


async def proof_of_contribution(file_id: int, input_url: str, input_encryption_key: str) -> Contribution:
    contribution = Contribution(file_id=file_id, is_valid=False)
    decrypted_file_path = download_and_decrypt_file(input_url, input_encryption_key)

    if decrypted_file_path is not None:
        contribution.scores.quality = proof_of_quality(decrypted_file_path)
        contribution.scores.ownership = proof_of_ownership(decrypted_file_path)
        contribution.scores.uniqueness = proof_of_uniqueness(decrypted_file_path)
        contribution.scores.authenticity = proof_of_authenticity(decrypted_file_path)
        contribution.is_valid = all([
            contribution.scores.quality > 0.5,
            contribution.scores.ownership >= 0.0,
            contribution.scores.uniqueness >= 0.0,
            contribution.scores.authenticity >= 0.0
        ])

        # Clean up
        os.remove(decrypted_file_path)
    return contribution


def download_and_decrypt_file(input_url, input_encryption_key):
    """
    Download the file from the input URL and decrypt it using the input encryption key.
    :param input_url: URL of the encrypted file
    :param input_encryption_key: Base64 encoded encrypted symmetric key
    :return: Path to the decrypted file
    """
    temp_dir = tempfile.mkdtemp()

    # Extract file extension from URL
    parsed_url = urlparse(input_url)
    file_extension = os.path.splitext(parsed_url.path)[1]
    if not file_extension:
        file_extension = '.bin'  # Default extension if none is found

    encrypted_file_path = os.path.join(temp_dir, f"encrypted_file{file_extension}")
    response = requests.get(input_url)

    if response.status_code != 200:
        vana.logging.error(f"Failed to download file from {input_url}")
        return None

    with open(encrypted_file_path, 'wb') as f:
        f.write(response.content)

    # Decode symmetric key from base64 and decrypt it using private key
    encrypted_symmetric_key = base64.b64decode(input_encryption_key)
    private_key_base64 = os.environ["PRIVATE_FILE_ENCRYPTION_PUBLIC_KEY_BASE64"]
    private_key_bytes = base64.b64decode(private_key_base64)

    # Import the private key into the gnupg keyring
    gpg = gnupg.GPG()
    import_result = gpg.import_keys(private_key_bytes)
    vana.logging.info(f"Private key import result: {import_result}")

    # Decrypt the symmetric key using the private key and gnupg library
    decrypted_symmetric_key = gpg.decrypt(encrypted_symmetric_key)

    # Decrypt the file using the symmetric key
    decrypted_file_path = os.path.join(temp_dir, f"decrypted_file{file_extension}")
    with open(encrypted_file_path, 'rb') as encrypted_file, open(decrypted_file_path, 'wb') as decrypted_file:
        decrypted_data = gpg.decrypt_file(encrypted_file,
                                          passphrase=decrypted_symmetric_key.data.decode('utf-8'))
        vana.logging.info(f"Decryption status: {decrypted_data.status}")
        decrypted_file.write(decrypted_data.data)

    vana.logging.info(f"Successfully decrypted file: {decrypted_file_path}")
    return decrypted_file_path


def proof_of_quality(decrypted_file_path):
    """
    Validate the decrypted file as a hotdog image.
    :param decrypted_file_path:
    :return: is_valid, file_score, authenticity, ownership, quality, uniqueness
    """
    try:
        is_valid = decrypted_file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))
        return 1.0 if is_valid else 0.0
    except Exception as e:
        vana.logging.error(f"Error during validation, assuming file is invalid: {e}")
        vana.logging.error(traceback.format_exc())
        return 0.0


def proof_of_ownership(decrypted_file_path):
    """
    Check the ownership of the decrypted file.
    :param decrypted_file_path:
    :return:
    """
    # TODO: Implement ownership check via sharing a chat with the user's wallet address,
    #  and scraping it to ensure the wallet owner owns the Zip file
    return 0.0


def proof_of_uniqueness(decrypted_file_path):
    """
    Check the similarity of the decrypted file with previously validated files.
    :param decrypted_file_path:
    :return:
    """
    # TODO: Implement a similarity check to ensure the file is not a duplicate
    #  (or very similar) to a previously validated file
    return 0.0


def proof_of_authenticity(decrypted_file_path) -> float:
    """
    Check the authenticity of the decrypted file.
    :param decrypted_file_path:
    :return: authenticity score
    """
    # TODO: Implement a authenticity check to ensure it is an authentic hot dog.
    return 0.0
