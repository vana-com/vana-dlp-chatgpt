# The MIT License (MIT)
# Copyright © 2024 Corsali, Inc. dba Vana

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import copy
import json
import os
from abc import ABC, abstractmethod

import chatgpt
import vana as opendata
from chatgpt.utils.config import check_config, add_args, config
from chatgpt.utils.misc import ttl_get_block
from chatgpt.utils.validator import as_wad

dlp_implementation_abi_path = os.path.join(os.path.dirname(__file__), "../dlp-implementation-abi.json")


class BaseNode(ABC):
    """
    Base class for all network participants. It contains the core logic for all nodes; validators and miners.

    In addition to creating a wallet, this class also handles the synchronization of the network state
    """

    node_type: str = "BaseNode"

    @classmethod
    def check_config(cls, config: opendata.Config):
        check_config(cls, config)

    @classmethod
    def add_args(cls, parser):
        add_args(cls, parser)

    @classmethod
    def config(cls):
        return config(cls)

    wallet: opendata.Wallet

    @property
    def block(self):
        return ttl_get_block(self)

    @staticmethod
    def setup_config(config: opendata.Config):
        if config.get("__is_set", {}).get("dlp.contract"):
            return config.dlp.contract
        else:
            return BaseNode.determine_dlp_contract(config.chain.network)

    def __init__(self, config=None):
        base_config = copy.deepcopy(config or BaseNode.config())
        self.config = self.config()
        self.config.merge(base_config)
        self.check_config(self.config)

        self.config.dlp.contract = BaseNode.setup_config(self.config)

        # Set up logging with the provided configuration and directory.
        opendata.logging(config=self.config, logging_dir=self.config.full_path)

        # Log the configuration for reference.
        opendata.logging.info(self.config)

        # Build Vana objects
        # These are core Vana classes to interact with the network.
        opendata.logging.info("Setting up Vana objects.")

        self.last_synced_block = None

        # TODO: this try-except block was added mindlessly to prevent crashes and may need to be refactored
        try:
            self.wallet = opendata.Wallet(config=self.config)
            self.chain_manager = opendata.ChainManager(config=self.config)
            with open(dlp_implementation_abi_path) as f:
                self.dlp_contract = self.chain_manager.web3.eth.contract(address=self.config.dlp.contract,
                                                                         abi=json.load(f))

            self.state = self.chain_manager.state(self.config.dlpuid)
            opendata.logging.info(f"State: {self.state}")

            # Ensure hotkey is available before registering
            # This will throw if the hotkey is not available
            if self.wallet.hotkey.address:
                # Register the wallet with the chain manager
                self.chain_manager.register(self.wallet, self.config.dlpuid)

                opendata.logging.info(f"Wallet: {self.wallet}")
                opendata.logging.info(f"Chain Manager: {self.chain_manager}")

                # Check if the validator is registered on the network before proceeding further.
                # self.check_registered()

                opendata.logging.info(
                    f"Running node on data liquidity pool: {self.config.dlpuid} with hotkey {self.wallet.hotkey.address} using network: {self.chain_manager.config.chain_endpoint}")
        except opendata.KeyFileError as e:
            opendata.logging.error(f"Keyfile error: {e}")
            opendata.logging.warning(
                "Keyfile not found, skipping network join. Please create a wallet and restart the service.")
            self.wallet = None
            self.chain_manager = None

        self.state = self.chain_manager.state(self.config.dlpuid) if self.chain_manager else None
        opendata.logging.info(f"State: {self.state}" if self.state else "State: Not initialized")

        self.step = 0

    @abstractmethod
    async def forward(self, message: opendata.Message) -> opendata.Message:
        ...

    @abstractmethod
    def run(self):
        ...

    @abstractmethod
    def resync_state(self):
        ...

    def sync(self):
        """
        Wrapper for synchronizing the state of the network for the given miner or validator.
        """
        current_block = self.block
        if self.last_synced_block == current_block:
            opendata.logging.info(f"Sync already performed for block {current_block}. Skipping.")
            return

        self.last_synced_block = current_block

        # Ensure validator hotkey is still registered on the network.
        self.check_registered()

        if self.should_sync_state():
            self.resync_state()
            self.state.save()

        if current_block % self.config.dlp.tempo == 0:
            self.save_weights()

    def save_weights(self):
        """
        Save the weights of all validators to the chain.
        """
        self.state.weights[self.wallet.hotkey.address] = 1.0  # The current node always has a weight of 1
        opendata.logging.info(f"Writing weights on-chain: {self.state.weights}")
        update_weights_fn = self.dlp_contract.functions.updateWeights(
            list(self.state.weights.keys()),
            [as_wad(weight) for weight in self.state.weights.values()]
        )
        self.chain_manager.send_transaction(update_weights_fn, self.wallet.hotkey)

    def check_registered(self):
        validator_count = self.dlp_contract.functions.activeValidatorListsCount().call()
        active_validator_addresses: list[str] = self.dlp_contract.functions.activeValidatorLists(validator_count).call()
        self.state.set_hotkeys(active_validator_addresses)

        if not active_validator_addresses.__contains__(self.wallet.hotkey.address):
            opendata.logging.error(
                f"Wallet: {self.wallet} is not registered on DLP {self.config.dlpuid}."
            )
            exit()

    def should_sync_state(self):
        """
        Check if enough epoch blocks have elapsed since the last checkpoint to sync.
        """
        return (self.block - self.state.last_update) > self.config.node.epoch_length

    @staticmethod
    def determine_dlp_contract(network: str):
        """Determines the appropriate DLP contract address based on the given network.

        Args:
            network (str): The network name. The choices are: "vana", "base_sepolia".

        Returns:
            str: The contract address for the specified network.
        """
        if network is None:
            return None

        if network == "vana":
            return chatgpt.__dlp_vana_contract__
        elif network == "base_sepolia":
            return chatgpt.__dlp_base_sepolia_contract__
        else:
            return "unknown"
