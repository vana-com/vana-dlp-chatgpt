import time
import random
from web3.exceptions import Web3Exception, ContractLogicError
from eth_abi import decode
import vana


def rpc_call_with_retry(func, max_retries=3, initial_delay=1, max_delay=60):
    """
    Wrapper function to make RPC calls with retry logic.

    :param func: The RPC function to call
    :param max_retries: Maximum number of retry attempts
    :param initial_delay: Initial delay between retries (in seconds)
    :param max_delay: Maximum delay between retries (in seconds)
    :return: Result of the RPC call
    """
    retries = 0
    delay = initial_delay

    while retries < max_retries:
        try:
            return func()
        except Web3Exception as e:
            retries += 1
            if retries == max_retries:
                raise e

            vana.logging.warning(f"RPC call failed. Retrying in {delay} seconds. Error: {str(e)}")
            time.sleep(delay)
            delay = min(delay * 2, max_delay)  # Exponential backoff

    raise Exception("Max retries reached. RPC call failed.")


def safe_rpc_call(chain_manager, contract_function, *args, **kwargs):
    """
    Safely make an RPC call using the chain manager.

    :param chain_manager: The chain manager instance
    :param contract_function: The contract function to call
    :param args: Positional arguments for the contract function
    :param kwargs: Keyword arguments for the contract function
    :return: Result of the RPC call or None if decoding fails
    """
    def rpc_call():
        try:
            vana.logging.debug(f"Calling contract function '{contract_function}' with args: {args}, kwargs: {kwargs}")
            result = chain_manager.read_contract_fn(contract_function(*args, **kwargs))
            vana.logging.debug(f"Raw result from contract for calling '{contract_function}': '{result}'")
            return result
        except ContractLogicError as e:
            vana.logging.warning(f"Contract logic error: {str(e)}")
            return None
        except Exception as e:
            vana.logging.error(f"Failed to read from contract function: {str(e)}")

            # Attempt to decode raw return data
            try:
                raw_return_data = e.args[0]['data']
                vana.logging.debug(f"Raw return data: {raw_return_data}")

                # Get the output types from the contract function
                output_types = contract_function.abi['outputs']
                type_strings = [output['type'] for output in output_types]

                # Attempt to decode
                decoded = decode(type_strings, raw_return_data)
                vana.logging.debug(f"Decoded data: {decoded}")
                return decoded
            except Exception as decode_error:
                vana.logging.error(f"Failed to decode raw return data: {str(decode_error)}")

            return None

    return rpc_call_with_retry(rpc_call)


def safe_send_transaction(chain_manager, transaction_function, wallet, *args, **kwargs):
    """
    Safely send a transaction using the chain manager.

    :param chain_manager: The chain manager instance
    :param transaction_function: The transaction function to call
    :param wallet: The wallet to use for the transaction
    :param args: Positional arguments for the transaction function
    :param kwargs: Keyword arguments for the transaction function
    :return: Transaction receipt
    """
    def send_transaction():
        return chain_manager.send_transaction(transaction_function(*args, **kwargs), wallet)

    return rpc_call_with_retry(send_transaction)