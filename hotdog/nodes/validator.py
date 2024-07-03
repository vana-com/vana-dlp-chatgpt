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
import traceback
import vana
from hotdog.nodes.base_node import BaseNode
from hotdog.utils.config import add_validator_args
from hotdog.utils.proof_of_contribution import proof_of_contribution
from hotdog.utils.validator import as_wad
from dataclasses import dataclass, field
from traceback import print_exception
from typing import Dict, List, Any, Tuple


@dataclass
class PeerScoringTask:
    file_id: int
    active_validators: List[str]
    own_submission: Dict[str, Any]
    added_at_block: int
    processed_validators: List[str] = field(default_factory=list)


def transform_tuple(data_tuple: Tuple[Any, ...], field_specs: List[Tuple[str, bool]]) -> Dict[str, Any]:
    """
    Transforms a tuple of data into a dictionary with field names as keys.
    Divides WAD fields by 1e18.

    :param data_tuple: tuple of data
    :param field_specs: list of tuples (field_name, is_wad)
    :return: dictionary of data
    """
    data_dict = {}
    for (name, is_wad), value in zip(field_specs, data_tuple):
        if is_wad and isinstance(value, (int, float)):
            data_dict[name] = value / 1e18
        else:
            data_dict[name] = value
    return data_dict

def transform_file_data(file_data_tuple: Tuple[Any, ...]) -> Dict[str, Any]:
    """
    Transforms a tuple of file data into a dictionary with field names as keys.
    Converts WAD fields from wei.

    :param file_data_tuple: tuple of file data
    :return: dictionary of file data
    """
    field_specs = [
        ("fileId", False),
        ("ownerAddress", False),
        ("url", False),
        ("encryptedKey", False),
        ("addedTimestamp", False),
        ("addedAtBlock", False),
        ("valid", False),
        ("score", True),
        ("authenticity", True),
        ("ownership", True),
        ("quality", True),
        ("uniqueness", True),
        ("reward", True),
        ("rewardWithdrawn", False),
        ("verificationsCount", False)
    ]
    return transform_tuple(file_data_tuple, field_specs)

def transform_file_score(file_score_tuple: Tuple[Any, ...]) -> Dict[str, Any]:
    """
    Transforms a tuple of file score data into a dictionary with field names as keys.
    Converts WAD fields from wei.

    :param file_score_tuple: tuple of file score data
    :return: dictionary of file score data
    """
    field_specs = [
        ("valid", False),
        ("score", True),
        ("reportedAtBlock", False),
        ("authenticity", True),
        ("ownership", True),
        ("quality", True),
        ("uniqueness", True)
    ]
    return transform_tuple(file_score_tuple, field_specs)


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
            # Init sync with the network. Updates the state.
            self.sync()

            # Create asyncio event loop to manage async tasks.
            self.loop = asyncio.get_event_loop()

            # Instantiate runners
            self.should_exit: bool = False
            self.is_running: bool = False
            self.thread: threading.Thread = None
            self.lock = asyncio.Lock()

            vana.logging.info(
                f"Running validator on network: {self.config.chain.chain_endpoint} with dlpuid: {self.config.dlpuid}"
            )

            if not hasattr(self.state, 'needs_peer_scoring'):
                setattr(self.state, 'needs_peer_scoring', [])

    def record_file_score(self, file_id: int, score_data: Dict[str, Any]):
        active_validators = self.get_active_validators()
        current_block = self.chain_manager.get_current_block()

        task = PeerScoringTask(
            file_id=file_id,
            active_validators=active_validators,
            own_submission=score_data,
            added_at_block=current_block
        )

        self.state.needs_peer_scoring.append(task)
        self.state.save()

    def get_active_validators(self) -> List[str]:
        validator_count = self.chain_manager.read_contract_fn(self.dlp_contract.functions.activeValidatorsListsCount())
        return self.chain_manager.read_contract_fn(self.dlp_contract.functions.activeValidatorsLists(validator_count))

    async def process_peer_scoring_queue(self):
        validator_scores = {}
        current_block = self.chain_manager.get_current_block()

        for task in self.state.needs_peer_scoring[:]:
            file_data_tuple = self.chain_manager.read_contract_fn(self.dlp_contract.functions.files(task.file_id))

            if not file_data_tuple:
                continue

            file_data = transform_file_data(file_data_tuple)

            for validator in task.active_validators[:]:
                if validator in task.processed_validators:
                    continue

                file_score_tuple = self.chain_manager.read_contract_fn(
                    self.dlp_contract.functions.fileScores(task.file_id, validator)
                )
                validator_score = transform_file_score(file_score_tuple)

                if validator_score:
                    performance_score = self.score_validator_performance(task.own_submission, validator_score,
                                                                         file_data)
                    if validator not in validator_scores:
                        validator_scores[validator] = []
                    validator_scores[validator].append(performance_score)
                    task.active_validators.remove(validator)
                    task.processed_validators.append(validator)
                elif current_block - task.added_at_block >= self.config.node.max_wait_blocks:
                    vana.logging.info(
                        f"Validator {validator} did not respond in time for file {task.file_id}. Scoring 0.")
                    if validator not in validator_scores:
                        validator_scores[validator] = []
                    validator_scores[validator].append(0)
                    task.active_validators.remove(validator)
                    task.processed_validators.append(validator)

            if not task.active_validators:
                self.state.needs_peer_scoring.remove(task)

        self.update_validator_weights(validator_scores)
        self.state.save()

    def score_validator_performance(self, own_submission: Dict[str, Any], validator_score: Dict[str, Any],
                                    file_data: Dict[str, Any]) -> float:
        initial_weights = {
            'score': 50,
            'authenticity': 10,
            'ownership': 10,
            'quality': 10,
            'uniqueness': 10,
            'speed': 10
        }

        weights = {k: v for k, v in initial_weights.items() if k in own_submission or k == 'speed'}
        total_weight = sum(weights.values())
        weights = {k: v / total_weight for k, v in weights.items()}

        scores = {}

        for dimension in ['score', 'authenticity', 'ownership', 'quality', 'uniqueness']:
            if dimension in own_submission and dimension in validator_score:
                scores[dimension] = 1 - abs(own_submission[dimension] - validator_score[dimension])
            else:
                scores[dimension] = 0 if dimension in own_submission else 1

        if 'addedAtBlock' in file_data and 'reportedAtBlock' in validator_score:
            file_added_block = file_data['addedAtBlock']
            reported_block = validator_score['reportedAtBlock']
            max_block_difference = self.config.node.max_wait_blocks
            scores['speed'] = 0

            if reported_block >= file_added_block:
                block_difference = reported_block - file_added_block
                scores['speed'] = max(0, 1 - (block_difference / max_block_difference))

        return sum(weights[k] * scores[k] for k in weights)

    def update_validator_weights(self, validator_scores: Dict[str, List[float]]):
        # Calculate new weights based on the accumulated scores
        new_weights = {}
        for validator, scores in validator_scores.items():
            avg_score = sum(scores) / len(scores)
            new_weights[validator] = avg_score

        # Update weights in the state
        for validator, weight in new_weights.items():
            self.state.add_weight(validator, weight)

    async def forward(self):
        """
        The forward function is called by the validator every time step.
        It is responsible for querying the network and scoring the responses.
        """
        validator_hotkey = self.wallet.get_hotkey()
        validator_address = validator_hotkey.address

        try:
            # Get the next file to verify
            get_next_file_to_verify_fn = self.dlp_contract.functions.getNextFileToVerify(validator_address)
            next_file = self.chain_manager.read_contract_fn(get_next_file_to_verify_fn)
            if not next_file or next_file[0] == 0:
                vana.logging.info("No files to verify. Sleeping for 5 seconds.")
                await asyncio.sleep(5)
                return

            # Unpack all values from next_file
            (
                file_id, owner_address, url, encrypted_key, added_timestamp,
                added_at_block, valid, finalized, score, authenticity, ownership,
                quality, uniqueness, reward, reward_withdrawn, verifications_count
            ) = next_file

            vana.logging.debug(
                f"Received file_id: {file_id}, owner_address: {owner_address}, url: {url}, "
                f"encrypted_key: {encrypted_key}, added_timestamp: {added_timestamp}, "
                f"added_at_block: {added_at_block}, valid: {valid}, finalized: {finalized}, score: {score}, "
                f"authenticity: {authenticity}, ownership: {ownership}, quality: {quality}, "
                f"uniqueness: {uniqueness}, reward: {reward}, reward_withdrawn: {reward_withdrawn}, "
                f"verifications_count: {verifications_count}"
            )

            contribution = await proof_of_contribution(file_id, url, encrypted_key)
            vana.logging.info(f"File is valid: {contribution.is_valid}, file score: {contribution.score()}")

            # Call verifyFile function on the DLP contract to set the file's scores
            verify_file_fn = self.dlp_contract.functions.verifyFile(
                file_id,
                contribution.is_valid,
                as_wad(contribution.score()),
                as_wad(contribution.scores.authenticity),
                as_wad(contribution.scores.ownership),
                as_wad(contribution.scores.quality),
                as_wad(contribution.scores.uniqueness))
            self.chain_manager.send_transaction(verify_file_fn, self.wallet.hotkey)

            # Add this file to the peer scoring queue
            self.record_file_score(file_id, {
                "score": contribution.score(),
                "is_valid": contribution.is_valid,
                "authenticity": contribution.scores.authenticity,
                "ownership": contribution.scores.ownership,
                "quality": contribution.scores.quality,
                "uniqueness": contribution.scores.uniqueness
            })

        except Exception as e:
            vana.logging.error(f"Error during forward process: {e}")
            vana.logging.error(traceback.format_exc())
            await asyncio.sleep(5)

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
                vana.logging.info(f"step({self.step}) block({self.block})")

                # Run multiple forwards concurrently.
                self.loop.run_until_complete(self.concurrent_forward())

                # Process peer scoring queue every tempo period
                current_block = self.chain_manager.get_current_block()
                if current_block % self.config.dlp.tempo == 0:
                    self.loop.run_until_complete(self.process_peer_scoring_queue())

                # Check if we should exit.
                if self.should_exit:
                    break

                # Sync state and potentially set weights.
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
