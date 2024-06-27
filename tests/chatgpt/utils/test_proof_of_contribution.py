import os
import pytest
from chatgpt.utils.proof_of_contribution import proof_of_contribution, download_and_decrypt_file
from pytest import MonkeyPatch
from typing import Dict
from unittest.mock import Mock


@pytest.fixture
def local_file():
    return os.path.join(os.getcwd(), 'tests/data/chatgpt_5_conversations.zip')


@pytest.fixture
def onchain_file():
    return {
        'url': 'https://www.dropbox.com/scl/fi/v06k9rbw70d4ludr695c5/encrypted_chatgpt_1_conversation.zip?rlkey=z0sbrofptu7qmt58fggvwlqhd&dl=1',
        'key': 'LS0tLS1CRUdJTiBQR1AgTUVTU0FHRS0tLS0tCgp3Y0RNQTVMUUhBZSt6M3BBQVF2L2ZwWEtXMHQ4U3U2cEs4VlhpL0VNc0VUTzYxTFBMbUlESkxmb21Kb1cKSnJ0b2JzckpabEVNMFdxUlRFaU94Z1JCaXJmaXozSFp0TDh5M3c2Tktaa2F5NDVKaFBsRzFsc0N4ci9wCmIyUm54UldwT3BuOHhhUS9mTUFQZFdySjNRcEljaVdjUE9wZDhSSngyOHVGcC9wL0x2azZlUjZCZlpzaApQWStUZzVCSk5EMGVxTi9ZWmlUd2ZVVnU0YU9pRUszenhhTlkwNkNzYTVsWm9MNnVaanVVRGRVOWlrQTQKZDFJd0szRnNkaVFLWlhORzdhcC82RzM4SW9yN3ZHd1dFeXlBWjlOV2Jta0lJTG5WSmZwZklDV2lwRmdCCmt4V0wrRzdHNksycUI1OU92b2V3UHJ3RDh2eVpMSE1GUmJBM09BNEtSaVRWdWcveFRjeXkxeEZJaUxpNgo4KzFOSzh2US9GUndESDRtdzVSVWVKWXJjcnkvUFZnWVdXRlBGLzdUM01yRDREOVBiTkxUSkhhVEwyaUgKM0dTeDFTM0pHUEVyMGNJTUhncDNMYlovdnprMzA0ek9QQ242VWVlWlJ0aThWbEtwYzFnV2hxdy9OZ0U0CjY2Z0JkN1hOM3l4MG5zbTZoVnlXM3VBeGUxczYwR2MrUmM3RG0zTHdEUmV1UlViZFBCUHEwclVCNzJCNQpLbkZCanh5VWoycmZEeHBmdnFwTEpDLzcyQW1NUkpxLzI4VHNCQXBlYnNFbWk4UU10QkI4MzdIRGxPS2oKVitBWjVIV2tDREVGRnNic1RZaU82UHQ2Q2FsVS9uOFVQbVlvOE16V3FQb2wzMUFvNGhTNHE1cFk0M25XClZTUVhYaEZXaGlVcFgyK3Vudm1iVEdIdHl3Z2htQXlxMC9RK004MFRyOHh6dkIrY3hkRWZxRkRDVXZkcQpiOHJ6YzVxZkRzZG41elIzcWN5ZmdqQS9Gb3ExaC9VWXZxMlBvYlFteHZveGFnQzJzOHR2c0Z0Sgo9ODlFRAotLS0tLUVORCBQR1AgTUVTU0FHRS0tLS0tCg==',
    }


@pytest.mark.asyncio
async def test_proof_of_contribution(mocker: MonkeyPatch, local_file: str) -> None:
    # Mock the decryption function and return our mocked file
    mock_decrypt: Mock = mocker.patch('chatgpt.utils.proof_of_contribution.download_and_decrypt_file')
    mock_decrypt.return_value = local_file
    mock_os: Mock = mocker.patch('chatgpt.utils.proof_of_contribution.os.remove')

    contribution = await proof_of_contribution(file_id=1, input_url='url', input_encryption_key='key')

    assert contribution.is_valid is True
    assert contribution.scores.quality > 0.5
    mock_decrypt.assert_called()
    mock_os.assert_called()


def test_download_and_decrypt_file(mocker: MonkeyPatch, onchain_file: Dict[str, str]) -> None:
    decrypted_file_path = download_and_decrypt_file(input_url=onchain_file['url'],
                                                    input_encryption_key=onchain_file['key'])

    assert len(decrypted_file_path) > 0
