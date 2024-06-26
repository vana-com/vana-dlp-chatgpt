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
import asyncio
import threading
import time
import traceback
from traceback import print_exception

import chatgpt.protocol
import vana
from chatgpt.nodes.base_node import BaseNode
from chatgpt.utils.config import add_validator_args
from chatgpt.utils.proof_of_contribution import proof_of_contribution
from chatgpt.utils.validator import as_wad


class Validator(BaseNode):
    """
    Base class for the Vana validators. Your validator should inherit from this class.
    """

    node_type: str = "ValidatorNode"

    @classmethod
    def add_args(cls, parser: argparse.ArgumentParser):
        super().add_args(parser)
        add_validator_args(cls, parser)

    def __init__(self, config=None):
        super().__init__(config=config)
        self.files_verified = []

        if self.wallet:
            self.node_client = vana.NodeClient(wallet=self.wallet)

            # Init sync with the network. Updates the state.
            self.sync()

            # Serve NodeServer to enable external connections.
            self.node_server = ((vana.NodeServer(wallet=self.wallet, config=self.config)
                                 .attach(self.validate)
                                 .serve(dlp_uid=self.config.dlpuid, chain_manager=self.chain_manager))
                                .start())

            # Create asyncio event loop to manage async tasks.
            self.loop = asyncio.get_event_loop()

            # Instantiate runners
            self.should_exit: bool = False
            self.is_running: bool = False
            self.thread: threading.Thread = None
            self.lock = asyncio.Lock()

            vana.logging.info(
                f"Running validator {self.node_server} on network: {self.config.chain.chain_endpoint} with dlpuid: {self.config.dlpuid}"
            )

    async def validate(self, message: chatgpt.protocol.ValidationMessage) -> chatgpt.protocol.ValidationMessage:
        """
        Proof of Contribution: Processes a validation request
        :param message: The validation message
        :return: The validation message with the output fields filled
        """
        vana.logging.info(f"Received {message.input_url} and encrypted key: {message.input_encryption_key}")
        return await proof_of_contribution(message)

    async def forward(self):
        """
        The forward function is called by the validator every time step.
        It is responsible for verifying files and reporting the results on-chain.
        """
        validator_hotkey = self.wallet.get_hotkey()
        validator_address = validator_hotkey.address

        try:
            # Get the next file to verify
            get_next_file_to_verify_output = self.dlp_contract.functions.getNextFileToVerify().call()
            if get_next_file_to_verify_output is None or get_next_file_to_verify_output[0] == 0:
                vana.logging.info("No files to verify. Sleeping for 5 seconds.")
                time.sleep(5)
                return

            file_id, input_url, input_encryption_key, added_time = get_next_file_to_verify_output

            # Validate the file
            validation_result = await self.validate(chatgpt.protocol.ValidationMessage(
                input_url=input_url,
                input_encryption_key=input_encryption_key
            ))

            # Report the score to the smart contract
            verify_file_fn = self.dlp_contract.functions.verifyFile(
                file_id,
                as_wad(validation_result.output_file_score),
                as_wad(validation_result.output_authenticity),
                as_wad(validation_result.output_ownership),
                as_wad(validation_result.output_quality),
                as_wad(validation_result.output_uniqueness),
                validation_result.metadata if hasattr(validation_result, 'metadata') else ""
            )
            tx_receipt = self.chain_manager.send_transaction(verify_file_fn, self.wallet.hotkey)
            block_number = tx_receipt[1].blockNumber

            vana.logging.info(f"Verified file {file_id} with score {validation_result.output_file_score}, "
                              f"authenticity {validation_result.output_authenticity}, "
                              f"ownership {validation_result.output_ownership}, "
                              f"quality {validation_result.output_quality}, "
                              f"uniqueness {validation_result.output_uniqueness}")

        except Exception as e:
            vana.logging.error(f"Error during forward process: {e}")
            vana.logging.error(traceback.format_exc())

    async def concurrent_forward(self):
        coroutines = [
            self.forward()
            for _ in range(self.config.node.num_concurrent_forwards)
        ]
        await asyncio.gather(*coroutines)

    def run(self):
        """
        Initiates and manages the main loop for the validator on the network.
        """
        # Check that validator is registered on the network.
        self.sync()

        vana.logging.info(f"Validator starting at block: {self.block}")

        # This loop maintains the validator's operations until intentionally stopped.
        try:
            while True:
                # TODO: this conditional was added mindlessly to prevent crashes and may need to be refactored
                if self.chain_manager:
                    vana.logging.info(f"step({self.step}) block({self.block})")

                    # Run multiple forwards concurrently.
                    self.loop.run_until_complete(self.concurrent_forward())

                    # Check if we should exit.
                    if self.should_exit:
                        break

                    # Sync metagraph and potentially set weights.
                    self.sync()

                self.step += 1

        # If someone intentionally stops the validator, it'll safely terminate operations.
        except KeyboardInterrupt:
            if hasattr(self, 'node_server') and self.node_server:
                self.node_server.stop()
                self.node_server.unserve(dlp_uid=self.config.dlpuid, chain_manager=self.chain_manager)
            vana.logging.success("Validator killed by keyboard interrupt.")
            exit()

        # In case of unforeseen errors, the validator will log the error and continue operations.
        except Exception as err:
            vana.logging.error("Error during validation", str(err))
            vana.logging.debug(
                print_exception(type(err), err, err.__traceback__)
            )

    def run_in_background_thread(self):
        """
        Starts the validator's operations in a background thread upon entering the context.
        This method facilitates the use of the validator in a 'with' statement.
        """
        if not self.is_running:
            vana.logging.debug("Starting validator in background thread.")
            self.should_exit = False
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()
            self.is_running = True
            vana.logging.debug("Started")

    def stop_run_thread(self):
        """
        Stops the validator's operations that are running in the background thread.
        """
        if self.is_running:
            vana.logging.debug("Stopping validator in background thread.")
            self.should_exit = True
            self.thread.join(5)
            self.is_running = False
            vana.logging.debug("Stopped")

    def __enter__(self):
        self.run_in_background_thread()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Stops the validator's background operations upon exiting the context.
        This method facilitates the use of the validator in a 'with' statement.

        Args:
            exc_type: The type of the exception that caused the context to be exited.
                      None if the context was exited without an exception.
            exc_value: The instance of the exception that caused the context to be exited.
                       None if the context was exited without an exception.
            traceback: A traceback object encoding the stack trace.
                       None if the context was exited without an exception.
        """
        if self.is_running:
            vana.logging.debug("Stopping validator in background thread.")
            self.should_exit = True
            self.thread.join(5)
            self.is_running = False
            vana.logging.debug("Stopped")

    def resync_state(self):
        self.state.sync(chain_manager=self.chain_manager)


if __name__ == "__main__":
    vana.trace()
    Validator().run()
