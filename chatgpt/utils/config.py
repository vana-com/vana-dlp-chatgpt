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

import argparse
import os

import vana
from munch import Munch, munchify

# Validation config for the DLP based on network
validation_config: Munch = munchify(
    {
        # Testnet
        "satori": {
            "MIN_CONVERSATIONS": 5,
            "MIN_AVG_MESSAGES": 2,
            "MIN_AVG_MESSAGE_LENGTH": 30,
            "THRESHOLD_SCORE": 60,
            "SAMPLE_SIZE": 1,
            "MAX_VALIDATION_CHUNK_SIZE": 4000,
        },
        # Mainnet
        "mainnet": {
            "MIN_CONVERSATIONS": 10,
            "MIN_AVG_MESSAGES": 3,
            "MIN_AVG_MESSAGE_LENGTH": 50,
            "THRESHOLD_SCORE": 80,
            "SAMPLE_SIZE": 30,
            "MAX_VALIDATION_CHUNK_SIZE": 16285,
        }
    }
)


def get_validation_config(network: str = None):
    """
    Returns the validation config for the given network.
    If network is None, returns the config for the network specified in the environment variable OD_CHAIN_NETWORK, defaulting to "satori".
    :param network: The network to get the validation config for
    :return: The validation config for the given network
    """
    if not network:
        network = os.environ.get("OD_CHAIN_NETWORK", "satori")

    # If the network is not in the validation config, default to the testnet config
    if network not in validation_config:
        network = "satori"

    return validation_config[network]


def check_config(cls, config: vana.Config):
    r"""Checks/validates the config namespace object."""
    vana.logging.check_config(config)


def add_args(cls, parser):
    """
    Adds relevant arguments to the parser for operation.
    """

    parser.add_argument("--dlpuid", type=int, help="The ID of the DLP", default=1)

    parser.add_argument("--dlp.contract", type=str, help="The contract address of the DLP", default=None)

    parser.add_argument("--dlp.token_contract", type=str, help="The contract address of the DLP Token", default=None)

    parser.add_argument("--dlp.tempo",
                        type=int,
                        help="The frequency (in number of blocks) to save data on-chain",
                        default=10)  # Every 60 seconds on the testnet
    # default=360)

    dlp_implementation_abi_path = os.path.join(os.path.dirname(__file__), "../dlp-implementation-abi.json")
    dlp_token_implementation_abi_path = os.path.join(os.path.dirname(__file__), "../dlp-token-implementation-abi.json")
    parser.add_argument("--dlp.abi_path",
                        type=str,
                        help="The full path to the DLP Smart Contract ABI JSON file",
                        default=dlp_implementation_abi_path)

    parser.add_argument("--dlp.token_abi_path",
                        type=str,
                        help="The full path to the DLP Token Smart Contract ABI JSON file",
                        default=dlp_token_implementation_abi_path)

    parser.add_argument(
        "--node.epoch_length",
        type=int,
        help="The default epoch length (how often we set weights, measured in 12 second blocks).",
        default=10,
    )


def add_validator_args(cls, parser):
    """Add validator specific arguments to the parser."""

    parser.add_argument(
        "--node.name",
        type=str,
        help="The name of this node. ",
        default="validator",
    )

    parser.add_argument(
        "--node.timeout",
        type=float,
        help="The timeout for each forward call in seconds.",
        default=10,
    )

    parser.add_argument(
        "--node.num_concurrent_forwards",
        type=int,
        help="The number of concurrent forwards running at any time.",
        default=1,
    )

    parser.add_argument(
        "--node.max_wait_blocks",
        type=int,
        help="The maximum number of blocks to wait for a validator to respond.",
        default=100,
    )


def config(cls):
    """
    Returns the configuration object specific to this miner or validator after adding relevant arguments.
    """
    parser = argparse.ArgumentParser()
    vana.Wallet.add_args(parser)
    vana.ChainManager.add_args(parser)
    vana.logging.add_args(parser)
    vana.NodeServer.add_args(parser)
    cls.add_args(parser)
    return vana.Config(parser)
