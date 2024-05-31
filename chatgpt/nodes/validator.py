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
import base64
import os
import tempfile
import threading
import time
import traceback
from traceback import print_exception

import gnupg
import requests
import vana

import chatgpt.protocol
from chatgpt.nodes.base_node import BaseNode
from chatgpt.utils.config import add_validator_args
from chatgpt.utils.validator import validate_chatgpt_zip, as_wad


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
            self.sync(skip_registration_check=True)

            # Serve NodeServer to enable external connections.
            self.node_server = ((vana.NodeServer(wallet=self.wallet, config=self.config)
                                 .attach(self.proof_of_contribution)
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

    async def proof_of_contribution(self,
                                    message: chatgpt.protocol.ValidationMessage) -> chatgpt.protocol.ValidationMessage:
        """
        Proof of Contribution: Processes a validation request
        :param message: The validation message
        :return: The validation message with the output fields filled
        """
        vana.logging.info(f"Received {message.input_url} and encrypted key: {message.input_encryption_key}")

        # Download the file
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, "data.zip")
        response = requests.get(message.input_url)

        if response.status_code != 200:
            vana.logging.error(f"Failed to download file from {message.input_url}")
            message.output_is_valid = False
            message.output_file_score = 0
        else:
            with open(file_path, 'wb') as f:
                f.write(response.content)

            # Decode symmetric key from base64 and decrypt it using private key
            encrypted_symmetric_key = base64.b64decode(message.input_encryption_key)
            private_key_base64 = os.environ["PRIVATE_FILE_ENCRYPTION_PUBLIC_KEY_BASE64"]
            private_key_bytes = base64.b64decode(private_key_base64)

            # Import the private key into the gnupg keyring
            gpg = gnupg.GPG()
            import_result = gpg.import_keys(private_key_bytes)
            vana.logging.info(f"Private key import result: {import_result}")

            # Decrypt the symmetric key using the private key and gnupg library
            decrypted_symmetric_key = gpg.decrypt(encrypted_symmetric_key)

            # Print decrypted symmetric key
            vana.logging.info(f"Decrypted symmetric key: {decrypted_symmetric_key.data}")

            # Decrypt the file using the symmetric key
            decrypted_file_path = os.path.join(temp_dir, "decrypted_data.zip")
            with open(file_path, 'rb') as encrypted_file, open(decrypted_file_path, 'wb') as decrypted_file:
                # Decrypt the file using the decrypted symmetric key bytes and gnupg library
                decrypted_data = gpg.decrypt_file(encrypted_file,
                                                  passphrase=decrypted_symmetric_key.data.decode('utf-8'))
                vana.logging.info(f"Decryption status: {decrypted_data.status}")
                # Write decrypted data to the decrypted file
                decrypted_file.write(decrypted_data.data)

            try:
                # Validate the decrypted file
                validation_result = validate_chatgpt_zip(decrypted_file_path)

                vana.logging.info(f"Validation result: {validation_result}")

                message.output_is_valid = validation_result["is_valid"]
                message.output_file_score = validation_result["score"]

                # TODO: Implement ownership check via sharing a chat with the user's wallet address,
                #  and scraping it to ensure the wallet owner owns the Zip file

                # TODO: Implement a similarity check to ensure the file is not a duplicate
                #  (or very similar) to a previously validated file

                return message
            except Exception as e:
                vana.logging.error(f"Error during validation, assuming file is invalid: {e}")
                vana.logging.error(traceback.format_exc())
                message.output_is_valid = False
                message.output_file_score = 0
            finally:
                # Clean up
                os.remove(file_path)  # Remove the downloaded file
                os.remove(decrypted_file_path)  # Remove the decrypted file
                vana.logging.info(f"Encrypted and decrypted data removed from the node")

        return message

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

            file_id, input_url, input_encryption_key, _ = get_next_file_to_verify_output
            if file_id == 0:
                vana.logging.info("Received file_id 0. No files to verify. Sleeping for 5 seconds.")
                time.sleep(5)
                return

            vana.logging.debug(
                f"Received file_id: {file_id}, input_url: {input_url}, input_encryption_key: {input_encryption_key}")

            # TODO: Define how the validator selects a which other validators to query, how often, etc.
            node_servers = self.chain_manager.get_active_node_servers(omit=[self.node_server.info()])
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

    async def register_validator(self, stake_amount):
        # TODO: Consider transferring funds automatically to the hotkey when they are staked.
        # Currently, the user must transfer funds to the hotkey manually before staking.

        validator_address = self.wallet.hotkey.address
        validator_owner_address = self.wallet.coldkeypub.to_checksum_address()
        registration_fn = self.dlp_contract.functions.registerAsValidator(validator_address, validator_owner_address)
        self.chain_manager.send_transaction(registration_fn, self.wallet.hotkey)

    def run(self):
        """
        Initiates and manages the main loop for the validator on the network.
        """
        if self.config.dlp.register:
            vana.logging.info(f"Registering, staking {self.config.dlp.register} tokens.")
            self.loop.run_until_complete(self.register_validator(self.config.dlp.register))
            vana.logging.success(f"Staked {self.config.dlp.register} tokens.")
            exit()

        # TODO: this conditional was added mindlessly to prevent crashes and may need to be refactored
        if self.chain_manager:
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
