import os
from unittest.mock import Mock

import pytest
from pytest import MonkeyPatch

from chatgpt.protocol import ValidationMessage
from chatgpt.utils.proof_of_contribution import proof_of_contribution


@pytest.fixture
def file_zip():
    return os.path.join(os.getcwd(), 'tests/data/chatgpt_1_conversation.zip')


@pytest.mark.asyncio
async def test_proof_of_contribution(mocker: MonkeyPatch, file_zip: str) -> None:
    # Mock the decryption function and return our mocked file
    mock_decrypt: Mock = mocker.patch('chatgpt.utils.proof_of_contribution.download_and_decrypt_file')
    mock_decrypt.return_value = file_zip
    mock_os: Mock = mocker.patch('chatgpt.utils.proof_of_contribution.os.remove')

    validation_message = await proof_of_contribution(ValidationMessage(input_url='url', input_encryption_key='key'))

    assert validation_message.output_is_valid is True
    assert validation_message.output_file_score > 0.5
    mock_decrypt.assert_called()
    mock_os.assert_called()
