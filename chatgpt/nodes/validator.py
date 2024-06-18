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

    async def validate(self,
                       message: chatgpt.protocol.ValidationMessage) -> chatgpt.protocol.ValidationMessage:
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
        It is responsible for querying the network and scoring the responses.
        """
        validator_hotkey = self.wallet.get_hotkey()
        validator_address = validator_hotkey.address

        # TODO: this try-catch block was added mindlessly to prevent crashes and may need to be refactored
        try:
            # Get the next file to verify
            get_next_file_to_verify_output = self.dlp_contract.functions.getNextFileToVerify(validator_address).call()
            if get_next_file_to_verify_output is None:
                vana.logging.error("No files to verify.")
                return

            file_id, input_url, input_encryption_key, added_time, assigned_validator = get_next_file_to_verify_output
            if file_id == 0:
                vana.logging.info("Received file_id 0. No files to verify. Sleeping for 5 seconds.")
                time.sleep(5)
                return

            vana.logging.debug(
                f"Received file_id: {file_id}, input_url: {input_url}, input_encryption_key: {input_encryption_key}, added_time: {added_time}, assigned_validator: {assigned_validator}")

            # TODO: Define how the validator selects a which other validators to query, how often, etc.
            node_servers = self.chain_manager.get_active_node_servers()
            responses = await self.node_client.forward(
                node_servers=node_servers,
                message=chatgpt.protocol.ValidationMessage(
                    input_url=input_url,
                    input_encryption_key=input_encryption_key
                ),
                deserialize=False,
            )

            # TODO: Define how the validator scores responses, calculates rewards and updates the scores
            vana.logging.info(f"Received responses: {responses}")

            def majority_is_valid(results: list[chatgpt.protocol.ValidationMessage]) -> bool:
                true_count = sum(1 for result in results if result.output_is_valid)
                false_count = len(results) - true_count
                return true_count > false_count

            valid_scores = [output.output_file_score for output in responses if output.is_success]
            mean_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0
            is_file_valid = majority_is_valid(responses)

            def calculate_validator_score(output: chatgpt.protocol.ValidationMessage):
                file_weight = 0.8
                process_time_weight = 0.2

                # TODO: use this validator's score as the reference instead of mean_score
                file_score_part = 1 - abs(output.output_file_score - mean_score)
                process_time_part = 1 - (
                        output.node_client.process_time / output.timeout) if output.node_client.process_time else 0
                process_time_part = max(0, min(1, process_time_part))
                return file_weight * file_score_part + process_time_weight * process_time_part

            metadata = {}
            for response in responses:
                metadata[response.node_server.hotkey] = {
                    "output_is_valid": response.output_is_valid,
                    "output_file_score": response.output_file_score
                }
                self.state.add_weight(response.node_server.hotkey, calculate_validator_score(response))

            vana.logging.info(f"File is valid: {is_file_valid}, mean score: {mean_score}")

            # Call verifyFile function on the DLP contract to set the file's score and metadata
            verify_file_fn = self.dlp_contract.functions.verifyFile(file_id, as_wad(mean_score), f"{metadata}")
            self.chain_manager.send_transaction(verify_file_fn, self.wallet.hotkey)

        except Exception as e:
            vana.logging.error(f"Error during forward process: {e}")
            vana.logging.error(traceback.format_exc())
            time.sleep(5)

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
