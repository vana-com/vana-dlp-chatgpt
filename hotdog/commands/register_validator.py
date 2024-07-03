import argparse
import json

import vana
from hotdog.nodes.base_node import BaseNode
from rich.prompt import Prompt
from vana.commands.base_command import BaseCommand


class RegisterValidatorCommand(BaseCommand):
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

        ./vanacli dlp register_validator --wallet.name="my_wallet" --wallet.hotkey="my_hotkey" --stake_amount=100
    """

    def run(cli: "vana.cli"):
        """
        Creates a new hotkey under this wallet
        :arg cli: The CLI object
        """
        config = BaseNode.config()
        config.dlp.contract = BaseNode.setup_config(config)
        config.dlp.token_contract = BaseNode.setup_config_token(config)
        chain_manager = vana.ChainManager(config=config)
        wallet = vana.Wallet(config=cli.config)

        with open(config.dlp.abi_path) as f:
            dlp_contract = chain_manager.web3.eth.contract(address=config.dlp.contract, abi=json.load(f))

        with open(config.dlp.token_abi_path) as f:
            token_contract = chain_manager.web3.eth.contract(address=config.dlp.token_contract, abi=json.load(f))

        validator_address = wallet.hotkey.address
        validator_owner_address = wallet.coldkeypub.to_checksum_address()
        stake_amount = cli.config.stake_amount
        stake_amount_wad = int(cli.config.stake_amount * 1e18)

        # Step 1: Approve DLP contract to spend validator owner's DLPTokens
        approval_fn = token_contract.functions.approve(dlp_contract.address, stake_amount_wad)
        chain_manager.send_transaction(approval_fn, wallet.coldkey)
        vana.logging.info(f"Approved DLP contract at {dlp_contract.address} to spend {stake_amount} DLPTokens")

        # Step 2: Register the validator
        registration_fn = dlp_contract.functions.registerValidator(validator_address, validator_owner_address, stake_amount_wad)

        chain_manager.send_transaction(registration_fn, wallet.coldkey)
        vana.logging.info(f"Registered validator {validator_address} with owner {validator_owner_address} and staked {stake_amount} DLPTokens")

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
        register_validator_parser = parser.add_parser(
            "register_validator", help="""Registers a validator to this DLP"""
        )
        register_validator_parser.add_argument(
            "--stake_amount",
            type=float,
            required=False,
            default=100,
            help="""The amount of tokens to stake for this validator.""",
        )
        vana.Wallet.add_args(register_validator_parser)
