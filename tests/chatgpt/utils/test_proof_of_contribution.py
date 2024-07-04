import pytest
from unittest.mock import Mock, patch, mock_open, call
from chatgpt.utils.proof_of_contribution import proof_of_contribution, download_and_decrypt_file

@pytest.fixture
def mock_file_content():
    return b'mocked_file_content'

@pytest.fixture
def mock_decrypted_content():
    return b'mocked_decrypted_content'

@pytest.fixture
def mock_encryption_key():
    return 'bW9ja19lbmNyeXB0aW9uX2tleQ=='  # base64 encoded 'mock_encryption_key'

@pytest.mark.asyncio
@patch('chatgpt.utils.proof_of_contribution.download_and_decrypt_file')
@patch('chatgpt.utils.proof_of_contribution.evaluate_chatgpt_zip')
@patch('chatgpt.utils.proof_of_contribution.proof_of_ownership')
@patch('chatgpt.utils.proof_of_contribution.proof_of_uniqueness')
@patch('chatgpt.utils.proof_of_contribution.proof_of_authenticity')
@patch('chatgpt.utils.proof_of_contribution.os.remove')
async def test_proof_of_contribution(mock_remove, mock_authenticity, mock_uniqueness, mock_ownership, mock_evaluate, mock_download, mock_file_content):
    # Setup mock returns
    mock_download.return_value = 'mock_file_path'
    mock_evaluate.return_value = {
        "score": 0.8,
        "messages": ["Test message"],
        "valid": True
    }
    mock_ownership.return_value = 0.1
    mock_uniqueness.return_value = 0.2
    mock_authenticity.return_value = 0.3

    contribution = await proof_of_contribution(file_id=1, input_url='mock_url', input_encryption_key='mock_key')

    assert contribution.is_valid is True
    assert contribution.scores.quality == 0.8
    assert contribution.scores.ownership == 0.1
    assert contribution.scores.uniqueness == 0.2
    assert contribution.scores.authenticity == 0.3

    # Check that all mocks are called correctly
    mock_download.assert_called_once_with('mock_url', 'mock_key')
    mock_evaluate.assert_called_once_with('mock_file_path')
    mock_ownership.assert_called_once_with('mock_file_path')
    mock_uniqueness.assert_called_once_with('mock_file_path')
    mock_authenticity.assert_called_once_with('mock_file_path')
    mock_remove.assert_called_once_with('mock_file_path')

@patch.dict('os.environ', {'PRIVATE_FILE_ENCRYPTION_PUBLIC_KEY_BASE64': 'mock_private_key'})
@patch('chatgpt.utils.proof_of_contribution.tempfile.mkdtemp')
@patch('chatgpt.utils.proof_of_contribution.requests.get')
@patch('chatgpt.utils.proof_of_contribution.gnupg.GPG')
@patch('builtins.open', new_callable=mock_open)
@patch('chatgpt.utils.proof_of_contribution.base64.b64decode')
def test_download_and_decrypt_file(mock_b64decode, mock_open, mock_gpg, mock_get, mock_mkdtemp,
                                   mock_file_content, mock_decrypted_content, mock_encryption_key):
    # Set up mocks
    mock_mkdtemp.return_value = '/mock/temp/dir'
    mock_response = Mock(status_code=200, content=mock_file_content)
    mock_get.return_value = mock_response
    mock_gpg_instance = Mock()
    mock_gpg_instance.decrypt.return_value = Mock(data=b'mock_symmetric_key')
    mock_gpg_instance.decrypt_file.return_value = Mock(status='decryption ok', data=mock_decrypted_content)
    mock_gpg.return_value = mock_gpg_instance
    mock_b64decode.side_effect = [b'mock_encrypted_symmetric_key', b'mock_private_key_bytes']

    # Call the function
    result = download_and_decrypt_file('mock_url', mock_encryption_key)

    # Assertions
    assert result.endswith('decrypted_file.bin')
    mock_get.assert_called_once_with('mock_url')
    mock_gpg.assert_called_once()
    mock_gpg_instance.import_keys.assert_called_once()
    mock_gpg_instance.decrypt.assert_called_once()
    mock_gpg_instance.decrypt_file.assert_called_once()
    assert mock_b64decode.call_count == 2
    mock_b64decode.assert_has_calls([
        call(mock_encryption_key),
        call('mock_private_key')
    ])

# TODO: Fix this test. @patch.dict('os.environ', {}) is not clearing os.environ
# @patch.dict('os.environ', {})
# @patch('chatgpt.utils.proof_of_contribution.tempfile.mkdtemp')
# @patch('chatgpt.utils.proof_of_contribution.requests.get')
# @patch('builtins.open', new_callable=mock_open)
# @patch('chatgpt.utils.proof_of_contribution.base64.b64decode')
# def test_download_and_decrypt_file_missing_env_var(mock_b64decode, mock_open, mock_get, mock_mkdtemp,
#                                                    mock_file_content, mock_encryption_key):
#     # Set up mocks
#     mock_mkdtemp.return_value = '/mock/temp/dir'
#     mock_response = Mock(status_code=200, content=mock_file_content)
#     mock_get.return_value = mock_response
#     mock_b64decode.return_value = b'mock_encrypted_symmetric_key'
#
#     # Call the function and check for the exception
#     with pytest.raises(KeyError) as exc_info:
#         download_and_decrypt_file('mock_url', mock_encryption_key)
#
#     assert 'PRIVATE_FILE_ENCRYPTION_PUBLIC_KEY_BASE64' in str(exc_info.value)
#
#     # Assertions
#     mock_get.assert_called_once_with('mock_url')
#     mock_b64decode.assert_called_once_with(mock_encryption_key)
