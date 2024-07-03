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
import vana
from abc import ABC, abstractmethod

import hotdog
from hotdog.utils.config import check_config, add_args, config
from hotdog.utils.misc import ttl_get_block
from hotdog.utils.validator import as_wad


class BaseNode(ABC):
    """
    Base class for all network participants. It contains the core logic for all nodes; validators and miners.

    In addition to creating a wallet, this class also handles the synchronization of the network state
    """

    node_type: str = "BaseNode"

    @classmethod
    def check_config(cls, config: vana.Config):
        check_config(cls, config)

    @classmethod
    def add_args(cls, parser):
        add_args(cls, parser)

    @classmethod
    def config(cls):
        return config(cls)

    wallet: vana.Wallet

    @property
    def block(self):
        return ttl_get_block(self)

    @staticmethod
    def setup_config(config: vana.Config):
        if config.get("__is_set", {}).get("dlp.contract"):
            return config.dlp.contract
        else:
            return BaseNode.determine_dlp_contract(config.chain.network)

    @staticmethod
    def setup_config_token(config: vana.Config):
        if config.get("__is_set", {}).get("dlp.token_contract"):
            return config.dlp.token_contract
        else:
            return BaseNode.determine_dlp_token_contract(config.chain.network)

    def __init__(self, config=None):
        base_config = copy.deepcopy(config or BaseNode.config())
        self.config = self.config()
        self.config.merge(base_config)
        self.check_config(self.config)

        self.config.dlp.contract = BaseNode.setup_config(self.config)
        self.config.dlp.token_contract = BaseNode.setup_config_token(self.config)

        # Set up logging with the provided configuration and directory.
        vana.logging(config=self.config, logging_dir=self.config.full_path)

        # Log the configuration for reference.
        vana.logging.info(self.config)

        # Build Vana objects
        # These are core Vana classes to interact with the network.
        vana.logging.info("Setting up Vana objects.")

        self.last_synced_block = None

        # TODO: this try-except block was added mindlessly to prevent crashes and may need to be refactored
        try:
            self.wallet = vana.Wallet(config=self.config)
            self.chain_manager = vana.ChainManager(config=self.config)
            self.state = self.chain_manager.state(self.config.dlpuid) if self.chain_manager else None

            with open(self.config.dlp.abi_path) as f:
                self.dlp_contract = self.chain_manager.web3.eth.contract(
                    address=self.config.dlp.contract,
                    abi=json.load(f)
                )

            with open(self.config.dlp.token_abi_path) as f:
                self.dlp_token_contract = self.chain_manager.web3.eth.contract(
                    address=self.config.dlp.token_contract,
                    abi=json.load(f)
                )

            # Ensure hotkey is available before registering
            # This will throw if the hotkey is not available
            if self.wallet.hotkey.address:
                vana.logging.info(f"Wallet: {self.wallet}")
                vana.logging.info(f"Chain Manager: {self.chain_manager}")

                # Check if the validator is registered on the network before proceeding further.
                self.check_registered()

                vana.logging.info(
                    f"Running node on data liquidity pool: {self.config.dlpuid} with hotkey {self.wallet.hotkey.address} using network: {self.chain_manager.config.chain.chain_endpoint}")
        except vana.KeyFileError as e:
            vana.logging.error(f"Keyfile error: {e}")
            vana.logging.warning(
                "Keyfile not found, skipping network join. Please create a wallet and restart the service.")
            self.wallet = None
            self.chain_manager = None

        vana.logging.info(f"State: {self.state}" if self.state else "State: Not initialized")

        self.step = 0

    @abstractmethod
    async def forward(self, message: vana.Message) -> vana.Message:
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
        if self.chain_manager:
            current_block = self.block
            if self.last_synced_block == current_block:
                vana.logging.info(f"Sync already performed for block {current_block}. Skipping.")
                return

            self.last_synced_block = current_block

            # Ensure validator hotkey is still registered on the network.
            self.check_registered()

            if current_block % self.config.node.epoch_length == 0:
                self.resync_state()
                self.state.save()

            if current_block % self.config.dlp.tempo == 0:
                self.save_weights()

    def save_weights(self):
        """
        Save the weights of all validators to the chain.
        """
        self.state.weights[self.wallet.hotkey.address] = 1.0  # The current node always has a weight of 1
        vana.logging.info(f"Writing weights on-chain: {self.state.weights}")
        update_weights_fn = self.dlp_contract.functions.updateWeights(
            list(self.state.weights.keys()),
            [as_wad(weight) for weight in self.state.weights.values()]
        )
        self.chain_manager.send_transaction(update_weights_fn, self.wallet.hotkey)

    def check_registered(self):
        validator_count = self.chain_manager.read_contract_fn(self.dlp_contract.functions.activeValidatorsListsCount())
        active_validator_addresses: list[str] = self.chain_manager.read_contract_fn(
            self.dlp_contract.functions.activeValidatorsLists(validator_count))
        self.state.set_hotkeys(active_validator_addresses)

        if not active_validator_addresses.__contains__(self.wallet.hotkey.address):
            vana.logging.error(
                f"Wallet: {self.wallet} is not registered on DLP {self.config.dlpuid}."
            )
            # Do not exit, registration status can change
            # exit()

    @staticmethod
    def determine_dlp_contract(network: str):
        """Determines the appropriate DLP contract address based on the given network.

        Args:
            network (str): The network name. The choices are: "vana", "base_sepolia".

        Returns:
            str: The contract address for the specified network.
        """
        if os.environ.get("DLP_CONTRACT_ADDRESS"):
            return os.environ.get("DLP_CONTRACT_ADDRESS")

        if network is None:
            return None

        if network == "vana":
            return hotdog.__dlp_vana_contract__
        elif network == "satori":
            return hotdog.__dlp_satori_contract__
        elif network == "moksha":
            return hotdog.__dlp_moksha_contract__
        else:
            return "unknown"

    @staticmethod
    def determine_dlp_token_contract(network: str):
        """Determines the appropriate DLP token contract address based on the given network.

        Args:
            network (str): The network name. The choices are: "vana", "base_sepolia".

        Returns:
            str: The token contract address for the specified network.
        """
        if os.environ.get("DLP_TOKEN_CONTRACT_ADDRESS"):
            return os.environ.get("DLP_TOKEN_CONTRACT_ADDRESS")

        if network is None:
            return None

        if network == "vana":
            return hotdog.__dlp_token_vana_contract__
        elif network == "satori":
            return hotdog.__dlp_token_satori_contract__
        elif network == "moksha":
            return hotdog.__dlp_token_moksha_contract__
        else:
            return "unknown"
