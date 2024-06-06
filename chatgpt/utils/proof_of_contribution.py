import os
import tempfile
import traceback
import requests
import vana
import gnupg
import base64
import chatgpt.protocol
from chatgpt.utils.validator import evaluate_chatgpt_zip


async def proof_of_contribution(message: chatgpt.protocol.ValidationMessage) -> chatgpt.protocol.ValidationMessage:
    vana.logging.info(f"Received {message.input_url} and encrypted key: {message.input_encryption_key}")

    decrypted_file_path = download_and_decrypt_file(message.input_url, message.input_encryption_key)

    if decrypted_file_path is None:
        message.output_is_valid = False
        message.output_file_score = 0
    else:
        is_valid, file_score = proof_of_quality(decrypted_file_path)
        message.output_is_valid = is_valid
        message.output_file_score = file_score

        proof_of_ownership(decrypted_file_path)
        proof_of_uniqueness(decrypted_file_path)

        # Clean up
        os.remove(decrypted_file_path)  # Remove the decrypted file
        vana.logging.info(f"Decrypted data removed from the node")

    return message


def download_and_decrypt_file(input_url, input_encryption_key):
    """
    Download the file from the input URL and decrypt it using the input encryption key.
    :param input_url:
    :param input_encryption_key:
    :return:
    """
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, "data.zip")
    response = requests.get(input_url)

    if response.status_code != 200:
        vana.logging.error(f"Failed to download file from {input_url}")
        return None
    else:
        with open(file_path, 'wb') as f:
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

        # Print decrypted symmetric key
        vana.logging.info(f"Decrypted symmetric key: {decrypted_symmetric_key.data}")

        # Decrypt the file using the symmetric key
        decrypted_file_path = os.path.join(temp_dir, "decrypted_data.zip")
        with open(file_path, 'rb') as encrypted_file, open(decrypted_file_path, 'wb') as decrypted_file:
            # Decrypt the file using the decrypted symmetric key bytes and gnupg library
            decrypted_data = gpg.decrypt_file(encrypted_file,
                                              passphrase=decrypted_symmetric_key.data.decode('utf-8'))
            vana.logging.info(f"Decryption status: {decrypted_data.status}")
            # Write decrypted data to the decrypted file
            decrypted_file.write(decrypted_data.data)

        return decrypted_file_path


def proof_of_quality(decrypted_file_path):
    """
    Validate the decrypted file.
    :param decrypted_file_path:
    :return:  is_valid, file_score
    """
    try:
        # Validate the decrypted file
        validation_result = evaluate_chatgpt_zip(decrypted_file_path)

        vana.logging.info(f"Validation result: {validation_result}")

        is_valid = validation_result["is_valid"]
        file_score = validation_result["score"]

        return is_valid, file_score
    except Exception as e:
        vana.logging.error(f"Error during validation, assuming file is invalid: {e}")
        vana.logging.error(traceback.format_exc())
        return False, 0


def proof_of_ownership(decrypted_file_path):
    """
    Check the ownership of the decrypted file.
    :param decrypted_file_path:
    :return:
    """
    # TODO: Implement ownership check via sharing a chat with the user's wallet address,
    #  and scraping it to ensure the wallet owner owns the Zip file
    pass


def proof_of_uniqueness(decrypted_file_path):
    """
    Check the similarity of the decrypted file with previously validated files.
    :param decrypted_file_path:
    :return:
    """
    # TODO: Implement a similarity check to ensure the file is not a duplicate
    #  (or very similar) to a previously validated file
    pass

