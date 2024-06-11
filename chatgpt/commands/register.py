import argparse
import json

import vana
from chatgpt.nodes.base_node import BaseNode
from rich.prompt import Prompt
from vana.commands.base_command import BaseCommand


class RegisterCommand(BaseCommand):
    """
    Registers a validator with the DLP smart contract using the stake amount.

    A node must be registered to participate in the network.

    Usage:
        The command creates a new hotkey with an optional word count for the mnemonic and supports password protection.
        It also allows overwriting an existing hotkey.

    Optional arguments:
        - ``--wallet.name`` (str): The name of the wallet owned by the validator, used to get the validator owner address.
        - ``--wallet.hotkey`` (str): The validator address to register.
        - ``--stake_amount`` (int): The amount this validator will stake.

    Example usage::

        ./vanacli dlp register --wallet.name="my_wallet" --wallet.hotkey="my_hotkey" --stake_amount=100
    """

    def run(cli: "vana.cli"):
        """Creates a new hotkey under this wallet."""

        config = BaseNode.config()
        config.dlp.contract = BaseNode.setup_config(config)
        chain_manager = vana.ChainManager(config=config)
        wallet = vana.Wallet(config=config)

        with open(config.dlp.abi_path) as f:
            dlp_contract = chain_manager.web3.eth.contract(address=config.dlp.contract, abi=json.load(f))
            validator_address = wallet.hotkey.address
            validator_owner_address = wallet.coldkeypub.to_checksum_address()
            stake_amount = cli.config.stake_amount

            registration_fn = dlp_contract.functions.registerValidator(validator_address, validator_owner_address)
            chain_manager.send_transaction(registration_fn, wallet.hotkey)

    @staticmethod
    def check_config(config: "vana.Config"):
        if not config.is_set("wallet.name") and not config.no_prompt:
            wallet_name = Prompt.ask("Enter wallet name", default=vana.defaults.wallet.name)
            config.wallet.name = str(wallet_name)

        if not config.is_set("wallet.hotkey") and not config.no_prompt:
            hotkey = Prompt.ask("Enter hotkey name", default=vana.defaults.wallet.hotkey)
            config.wallet.hotkey = str(hotkey)

    @staticmethod
    def add_args(parser: argparse.ArgumentParser):
        register_parser = parser.add_parser(
            "register", help="""Registers a validator to this DLP"""
        )
        register_parser.add_argument(
            "--stake_amount",
            type=int,
            required=False,
            default=100,
            help="""The amount of tokens to stake for this validator.""",
        )
        vana.Wallet.add_args(register_parser)
