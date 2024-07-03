import pytest
from unittest.mock import patch, Mock, AsyncMock

from hotdog.nodes.validator import Validator, PeerScoringTask
from vana.config import Config


class MockChainManager:
    def __init__(self, dlp_contract):
        self.dlp_contract = dlp_contract
        self.current_block = 0
        self.read_contract_fn = Mock(side_effect=self._read_contract_fn)

    def _read_contract_fn(self, function):
        if callable(function):
            result = function()
            return result
        return None

    def get_current_block(self):
        return self.current_block

    def increment_block(self, amount=1):
        self.current_block += amount


class MockState:
    def __init__(self):
        self.weights = {}
        self.needs_peer_scoring = []

    def sync(self, block=None, lite=False, chain_manager=None):
        self.node_servers = []

    def set_hotkeys(self, hotkeys):
        pass

    def add_weight(self, validator, weight):
        self.weights[validator] = weight

    def save(self):
        pass

class MockDLPContract:
    def __init__(self):
        self.files = {}
        self.file_scores = {}
        self.functions = self.MockFunctions(self)

    class MockFunctions:
        def __init__(self, outer):
            self.outer = outer

        def files(self, file_id):
            return lambda: self.outer.files.get(file_id, {})

        def fileScores(self, file_id, validator):
            return lambda: self.outer.file_scores.get(file_id, {}).get(validator, {})

        def activeValidatorsListsCount(self):
            return lambda: 1

        def activeValidatorsLists(self, _):
            return lambda: ["validator_1", "validator_2", "validator_3"]

    def add_file(self, file_id, data):
        self.files[file_id] = data

    def add_file_score(self, file_id, validator, score):
        if file_id not in self.file_scores:
            self.file_scores[file_id] = {}
        self.file_scores[file_id][validator] = score

@pytest.fixture
def setup_validator():
    mock_dlp_contract = MockDLPContract()
    mock_chain_manager = MockChainManager(mock_dlp_contract)

    with patch('vana.ChainManager', return_value=mock_chain_manager), \
            patch('vana.Wallet') as MockWallet, \
            patch('vana.ChainManager.read_contract_fn', side_effect=mock_chain_manager.read_contract_fn):

        mock_config = Config()
        mock_config.node = Config()
        mock_config.node.max_wait_blocks = 5
        mock_config.chain = Config()
        mock_config.chain.network = 'testnet'
        mock_config.dlp = Config()
        mock_config.dlp.contract = Mock()
        mock_config.dlp.tempo = 10

        mock_wallet = MockWallet.return_value
        mock_wallet.hotkey.address = "validator_1"

        def mock_init(self, config=None):
            self.config = mock_config
            self.wallet = mock_wallet
            self.chain_manager = mock_chain_manager  # Directly assign the instance
            self.dlp_contract = mock_dlp_contract
            self.state = MockState()

        with patch.object(Validator, '__init__', mock_init):
            validator = Validator()
            validator.get_active_validators = Mock(return_value=["validator_1", "validator_2", "validator_3"])
            return validator

def test_record_file_score(setup_validator):
    validator = setup_validator
    validator.record_file_score(1, {"score": 0.8})
    assert len(validator.state.needs_peer_scoring) == 1
    assert validator.state.needs_peer_scoring[0].file_id == 1

@pytest.mark.asyncio
@patch('hotdog.nodes.validator.Validator.update_validator_weights')
async def test_process_peer_scoring_queue(mock_update_weights, setup_validator):
    validator = setup_validator

    file_data = (
        1,                    # fileId
        "owner",              # ownerAddress
        "url",                # url
        "key",                # encryptedKey
        1000,                 # addedTimestamp
        100,                  # addedAtBlock
        True,                 # valid
        int(0.8 * 1e18),      # score
        int(0.9 * 1e18),      # authenticity
        int(1.0 * 1e18),      # ownership
        int(0.7 * 1e18),      # quality
        int(0.8 * 1e18),      # uniqueness
        int(100 * 1e18),      # reward
        False,                # rewardWithdrawn
        1                     # verificationsCount
    )

    validator.dlp_contract.add_file(1, file_data)

    validator.dlp_contract.add_file_score(1, "validator_1", (
        True,                 # valid
        int(0.8 * 1e18),      # score
        105,                  # reportedAtBlock
        int(0.9 * 1e18),      # authenticity
        int(1.0 * 1e18),      # ownership
        int(0.7 * 1e18),      # quality
        int(0.8 * 1e18)       # uniqueness
    ))

    validator.dlp_contract.add_file_score(1, "validator_2", (
        True,                 # valid
        int(0.75 * 1e18),     # score
        105,                  # reportedAtBlock
        int(0.85 * 1e18),     # authenticity
        int(0.95 * 1e18),     # ownership
        int(0.8 * 1e18),      # quality
        int(0.7 * 1e18)       # uniqueness
    ))

    validator.dlp_contract.add_file_score(1, "validator_3", (
        True,                 # valid
        int(0.9 * 1e18),      # score
        105,                  # reportedAtBlock
        int(0.95 * 1e18),     # authenticity
        int(0.9 * 1e18),      # ownership
        int(0.85 * 1e18),     # quality
        int(0.8 * 1e18)       # uniqueness
    ))

    task = PeerScoringTask(
        file_id=1,
        active_validators=["validator_1", "validator_2", "validator_3"],
        own_submission={
            "score": 0.75,
            "authenticity": 0.85,
            "ownership": 0.95,
            "quality": 0.8,
            "uniqueness": 0.7,
        },
        added_at_block=100
    )
    validator.state.needs_peer_scoring = [task]

    await validator.process_peer_scoring_queue()
    assert len(validator.state.needs_peer_scoring) == 0
    mock_update_weights.assert_called_once()
    assert validator.chain_manager.read_contract_fn.called

def test_update_validator_weights(setup_validator):
    validator = setup_validator
    validator_scores = {
        "validator_1": [0.8, 0.9],
        "validator_2": [0.7, 0.75]
    }

    validator.update_validator_weights(validator_scores)
    assert len(validator.state.weights) == 2
    assert 0.8 < validator.state.weights["validator_1"] < 0.9
    assert 0.7 < validator.state.weights["validator_2"] < 0.75

@pytest.mark.asyncio
@patch('hotdog.nodes.validator.Validator.process_peer_scoring_queue')
@patch('hotdog.nodes.validator.Validator.concurrent_forward', new_callable=AsyncMock)
async def test_run_processes_queue_on_tempo(mock_concurrent_forward, mock_process_queue, setup_validator):
    validator = setup_validator
    validator.sync = Mock()
    validator.should_exit = Mock(side_effect=[False] * 11 + [True])

    async def mock_run(self):
        while not self.should_exit():
            await self.concurrent_forward()
            if self.chain_manager.get_current_block() % self.config.dlp.tempo == 0:
                await self.process_peer_scoring_queue()
            self.sync()
            self.chain_manager.increment_block()

    with patch.object(Validator, 'run', mock_run):
        await validator.run()

    assert mock_process_queue.call_count == 2
    assert mock_concurrent_forward.call_count == 11
