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

import vana


def check_config(cls, config: vana.Config):
    r"""Checks/validates the config namespace object."""
    vana.logging.check_config(config)


def add_args(cls, parser):
    """
    Adds relevant arguments to the parser for operation.
    """

    parser.add_argument("--dlpuid", type=int, help="The ID of the DLP", default=1)

    parser.add_argument("--dlp.contract", type=str, help="The contract address of the DLP", default=None)

    parser.add_argument("--dlp.tempo",
                        type=int,
                        help="The frequency (in number of blocks) to save data on-chain",
                        default=10)  # Every 60 seconds on the testnet
    # default=360)

    parser.add_argument(
        "--node.epoch_length",
        type=int,
        help="The default epoch length (how often we set weights, measured in 12 second blocks).",
        default=10,
    )


def add_validator_args(cls, parser):
    """Add validator specific arguments to the parser."""

    parser.add_argument("--dlp.register", type=float,
                        help="Register this validator to the DLP, specifying the amount of stake to post to the DLP",
                        default=None)

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
