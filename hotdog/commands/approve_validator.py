import argparse
import json

import vana
from hotdog.nodes.base_node import BaseNode
from rich.prompt import Prompt
from vana.commands.base_command import BaseCommand


class ApproveValidatorCommand(BaseCommand):
    """
    Approves a validator in the DLP smart contract.

    Validators need to be approved by the contract owner before they can start participating in the network.

    Usage:
        The command approves a validator using their validator address.

    Required arguments:
        - ``--validator_address`` (str): The address of the validator to approve.

    Example usage::

        ./vanacli dlp approve_validator --validator_address="0x1234567890123456789012345678901234567890"
    """

    def run(cli: "vana.cli"):
        """
        Approves a validator in the DLP contract
        :arg cli: The CLI object
        """
        config = BaseNode.config()
        config.dlp.contract = BaseNode.setup_config(config)
        chain_manager = vana.ChainManager(config=config)
        wallet = vana.Wallet(config=cli.config)

        with open(config.dlp.abi_path) as f:
            dlp_contract = chain_manager.web3.eth.contract(address=config.dlp.contract, abi=json.load(f))

        validator_address = cli.config.validator_address

        # Approve the validator
        approval_fn = dlp_contract.functions.approveValidator(validator_address)
        chain_manager.send_transaction(approval_fn, wallet.coldkey)
        vana.logging.info(f"Approved validator {validator_address}")

    @staticmethod
    def check_config(config: "vana.Config"):
        if not config.is_set("wallet.name") and not config.no_prompt:
            wallet_name = Prompt.ask("Enter wallet name", default=vana.defaults.wallet.name)
            config.wallet.name = str(wallet_name)

        if not config.is_set("validator_address") and not config.no_prompt:
            validator_address = Prompt.ask("Enter validator address")
            config.validator_address = str(validator_address)

    @staticmethod
    def add_args(parser: argparse.ArgumentParser):
        approve_validator_parser = parser.add_parser(
            "approve_validator", help="""Approves a validator in the DLP contract"""
        )
        approve_validator_parser.add_argument(
            "--validator_address",
            type=str,
            required=False,
            help="""The address of the validator to approve.""",
        )
        vana.Wallet.add_args(approve_validator_parser)
