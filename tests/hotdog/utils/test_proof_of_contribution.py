import pytest
from unittest.mock import Mock, patch, mock_open, call
from hotdog.utils.proof_of_contribution import proof_of_contribution, download_and_decrypt_file

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
@patch('hotdog.utils.proof_of_contribution.download_and_decrypt_file')
@patch('hotdog.utils.proof_of_contribution.proof_of_quality')
@patch('hotdog.utils.proof_of_contribution.proof_of_ownership')
@patch('hotdog.utils.proof_of_contribution.proof_of_uniqueness')
@patch('hotdog.utils.proof_of_contribution.proof_of_authenticity')
@patch('hotdog.utils.proof_of_contribution.os.remove')
async def test_proof_of_contribution(mock_remove, mock_authenticity, mock_uniqueness, mock_ownership, mock_quality, mock_download):
    # Setup mock returns
    mock_download.return_value = 'mock_file_path'
    mock_quality.return_value = 0.8
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
    mock_quality.assert_called_once_with('mock_file_path')
    mock_ownership.assert_called_once_with('mock_file_path')
    mock_uniqueness.assert_called_once_with('mock_file_path')
    mock_authenticity.assert_called_once_with('mock_file_path')
    mock_remove.assert_called_once_with('mock_file_path')
