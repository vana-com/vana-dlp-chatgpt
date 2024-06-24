import argparse
import pytest
from unittest.mock import Mock, patch

from chatgpt.nodes.validator import Validator
from vana.config import Config

class MockChainManager:
    def __init__(self, *args, **kwargs):
        self.current_block = 0
        self.db = Mock()
        self.db_namespace = "test_namespace"
        self.state = Mock(return_value=MockState())
        self.web3 = Mock()

    def get_current_block(self):
        return self.current_block

    def increment_block(self, amount=1):
        self.current_block += amount

    def get_active_node_servers(self, omit=[]):
        return []

    @staticmethod
    def add_args(parser):
        pass

class MockState:
    def sync(self, block=None, lite=False, chain_manager=None):
        self.node_servers = []

    def set_hotkeys(self, hotkeys):
        pass

class MockDLPContract:
    def __init__(self):
        self.files = {}
        self.file_scores = {}

    def functions(self):
        return self

    def files(self, file_id):
        return self.files.get(file_id, {})

    def fileScores(self, file_id, validator):
        return self.file_scores.get(file_id, {}).get(validator, {})

    def activeValidatorsListsCount(self):
        return 1

    def activeValidatorsLists(self, _):
        return ["validator_1", "validator_2", "validator_3"]

    def add_file(self, file_id, data):
        self.files[file_id] = data

    def add_file_score(self, file_id, validator, score):
        if file_id not in self.file_scores:
            self.file_scores[file_id] = {}
        self.file_scores[file_id][validator] = score

@pytest.fixture
def setup_validator():
    with patch('vana.ChainManager', new=MockChainManager), patch('vana.Wallet') as MockWallet:
        # Create an argument parser and add necessary arguments
        parser = argparse.ArgumentParser()
        mock_config = Config(parser=parser, args=[], strict=False)

        # Initialize the necessary configuration values
        if 'node' not in mock_config:
            mock_config['node'] = Config()
        mock_config['node']['max_wait_blocks'] = 5

        if 'chain' not in mock_config:
            mock_config['chain'] = Config()
        mock_config['chain']['network'] = 'testnet'

        if 'dlp' not in mock_config:
            mock_config['dlp'] = Config()
        mock_config['dlp']['contract'] = Mock()
        mock_config['dlp']['tempo'] = 10

        # Set up the mock wallet and its attributes
        mock_wallet = MockWallet.return_value
        mock_wallet.hotkey.address = "validator_1"

        # Initialize the validator with the mock config
        validator = Validator(config=mock_config)

        validator.chain_manager = MockChainManager()
        validator.dlp_contract = MockDLPContract()
        validator.state = {'needs_peer_scoring': []}
        return validator

def test_record_file_score(setup_validator):
    validator = setup_validator
    validator.record_file_score(1, {"score": 0.8})
    assert len(validator.state['needs_peer_scoring']) == 1
    assert validator.state['needs_peer_scoring'][0].file_id == 1

@pytest.mark.asyncio
@patch('chatgpt.nodes.validator.Validator.update_validator_weights')
async def test_process_peer_scoring_queue(mock_update_weights, setup_validator):
    validator = setup_validator
    validator.dlp_contract.add_file(1, {"addedAtBlock": 0})
    validator.dlp_contract.add_file_score(1, "validator_1", {
        "score": 0.8,
        "authenticity": 0.9,
        "ownership": 1.0,
        "quality": 0.7,
        "uniqueness": 0.8,
        "reportedAtBlock": 2
    })
    validator.record_file_score(1, {
        "score": 0.75,
        "authenticity": 0.85,
        "ownership": 0.95,
        "quality": 0.8,
        "uniqueness": 0.7
    })

    await validator.process_peer_scoring_queue()
    assert len(validator.state['needs_peer_scoring']) == 0
    mock_update_weights.assert_called_once()

def test_score_validator_performance(setup_validator):
    validator = setup_validator
    own_submission = {
        "score": 0.75,
        "authenticity": 0.85,
        "ownership": 0.95,
        "quality": 0.8,
        "uniqueness": 0.7
    }
    validator_score = {
        "score": 0.8,
        "authenticity": 0.9,
        "ownership": 1.0,
        "quality": 0.7,
        "uniqueness": 0.8,
        "reportedAtBlock": 2
    }
    file_data = {"addedAtBlock": 0}

    score = validator.score_validator_performance(own_submission, validator_score, file_data)
    assert 0 < score < 1

def test_update_validator_weights(setup_validator):
    validator = setup_validator
    validator_scores = {
        "validator_1": [0.8, 0.9],
        "validator_2": [0.7, 0.75]
    }
    validator.state.add_weight = Mock()

    validator.update_validator_weights(validator_scores)
    validator.state.add_weight.assert_called()
    assert validator.state.add_weight.call_count == 2

@pytest.mark.asyncio
@patch('chatgpt.nodes.validator.Validator.process_peer_scoring_queue')
async def test_run_processes_queue_on_tempo(mock_process_queue, setup_validator):
    validator = setup_validator
    validator.config.dlp.tempo = 10
    validator.concurrent_forward = Mock()
    validator.sync = Mock()
    validator.should_exit = Mock(side_effect=[False, False, True])

    await validator.run()
    assert mock_process_queue.call_count == 1
