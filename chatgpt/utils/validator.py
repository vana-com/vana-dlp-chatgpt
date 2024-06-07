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

import json
import math
import os
import random
import zipfile
from typing import List, Dict, Any, Iterable
from openai import OpenAI
from chatgpt.models.chatgpt import ChatGPTData
import vana as opendata
import tiktoken
from chatgpt.utils.config import get_validation_config


def evaluate_chatgpt_zip(zip_file_path):
    """
    Validate a ChatGPT data zip file.
    :param zip_file_path:  Path to the zip file containing ChatGPT data
    :return: Object containing metadata, validation result and a score
    """
    required_files = ['chat.html', 'conversations.json', 'message_feedback.json', 'model_comparisons.json', 'user.json']

    # Load data from zip file and validate that it contains the required files
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        file_names = zip_ref.namelist()
        if not all(file in file_names for file in required_files):
            raise ValueError(f"Zip file does not contain all required files: {required_files}")

        with zip_ref.open('conversations.json') as file:
            data = json.load(file)

        # Validate other files
        if not validate_file_structure(zip_ref, required_files):
            raise ValueError("Validation failed for one or more files")

    # Load and parse the data
    parsed_data = load_chatgpt_data(data)

    # Analyze the structure and content of conversations.json
    metadata = analyze_data(parsed_data)

    # Perform validation and scoring
    # Check file metadata using the validation config thresholds
    validation_response = calculate_score_from_metadata(metadata)

    # If optional LLM check is enabled and the API key is set, perform LLM validation
    if "OPENAI_API_KEY" in os.environ and validation_response["is_valid"]:
        opendata.logging.info("OPENAI_API_KEY is set. Performing LLM validation.")
        validation_response = validate_sample(parsed_data)

    return {
        'is_valid': validation_response["is_valid"],
        'score': validation_response["score"] / 100,
        'metadata': metadata,
    }


def analyze_data(data: List[ChatGPTData]) -> Dict[str, Any]:
    """
    Analyze the structure and content of ChatGPT data.
    :param data: List of ChatGPTData objects
    :return: Dictionary containing metadata analysis
    """
    num_conversations = len(data)
    total_messages = 0

    for conv in data:
        for node in conv.mapping.values():
            if node.message and node.message.content.parts:
                message_text = ' '.join(str(part) for part in node.message.content.parts)
                if len(message_text) > 0:
                    total_messages += 1

    avg_messages_per_conversation = round(total_messages / num_conversations, 2)

    def get_message_length(node):
        if node.message and isinstance(node.message.content.parts, Iterable):
            length = 0
            for part in node.message.content.parts:
                if isinstance(part, str):
                    length += len(part)
                elif isinstance(part, dict):
                    length += len(str(part))
            return length
        return 0

    total_message_length = sum(
        get_message_length(node)
        for conv in data
        for node in conv.mapping.values()
        if node.message and node.message.content.parts
    )
    avg_message_length = round(total_message_length / total_messages, 2) if total_messages > 0 else 0

    # Additional metadata analysis
    max_messages_per_conversation = max(
        sum(
            1 for node in conv.mapping.values()
            if node.message and node.message.content.parts
        )
        for conv in data
    )
    min_messages_per_conversation = min(
        sum(
            1 for node in conv.mapping.values()
            if node.message and node.message.content.parts
        )
        for conv in data
    )
    total_characters = total_message_length

    return {
        'num_conversations': num_conversations,
        'avg_messages_per_conversation': avg_messages_per_conversation,
        'avg_message_length': avg_message_length,
        'max_messages_per_conversation': max_messages_per_conversation,
        'min_messages_per_conversation': min_messages_per_conversation,
        'total_characters': total_characters
    }


def validate_sample(data: List[ChatGPTData]) -> bool | dict[str, float | bool]:
    """
    Validate a sample of ChatGPT data using a language model evaluation.
    :param data:
    :return:
    """
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    validation_config = get_validation_config()

    sample_size = validation_config["SAMPLE_SIZE"]
    threshold_score = validation_config["THRESHOLD_SCORE"]
    max_validation_chunk_size = validation_config["MAX_VALIDATION_CHUNK_SIZE"]

    sample = random.sample(data, sample_size)
    scores = []

    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    system_message = ("You are an AI language model that evaluates the coherence and relevance of a conversation. "
                      "Please evaluate the following conversation and provide a score from 1 to 100 indicating the "
                      "degree of consistency and appropriateness of the responses within the given context. Your "
                      "entire response/output should consist of a single JSON object with a score key-value, "
                      "and you should NOT wrap it within JSON markdown markers.")
    system_message_tokens = encoding.encode(system_message)

    for conversation in sample:
        context = []
        for node in conversation.mapping.values():
            if node.message:
                parts = node.message.content.parts if isinstance(node.message.content.parts, (list, tuple)) else [node.message.content.parts]
                parts = [part for part in parts if part is not None]
                if parts:
                    context.append(' '.join(str(part) for part in parts))

        # Use tiktoken to calculate the actual token count of the context
        context_tokens = encoding.encode(' '.join(context))

        # Adjust chunk size based on system message tokens
        max_chunk_size = max_validation_chunk_size - len(system_message_tokens)
        context_chunks = [context_tokens[i:i+max_chunk_size] for i in range(0, len(context_tokens), max_chunk_size)]

        chunk_scores = []
        for chunk in context_chunks:
            chunk_text = encoding.decode(chunk)
            max_retries = 3
            retry_count = 0
            while retry_count < max_retries:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": f"# Conversation to evaluate:\n\n{chunk_text}"}
                    ],
                )

                score_json = response.choices[0].message.content
                opendata.logging.info(f"LLM validation response: {score_json}")

                try:
                    score_data = json.loads(score_json)
                    score = int(score_data["score"])
                    chunk_scores.append(score)
                    # Exit the retry loop if a valid JSON response is received
                    break
                except (json.JSONDecodeError, KeyError, ValueError):
                    retry_count += 1
                    if retry_count == max_retries:
                        opendata.logging.info(f"Failed to get a valid JSON response after {max_retries} retries.")
                        return {
                            'is_valid': False,
                            'score': 0
                        }

        avg_conversation_score = sum(chunk_scores) / len(chunk_scores)
        scores.append(avg_conversation_score)

    avg_score = sum(scores) / len(scores)
    opendata.logging.info(f"Average LLM validation score: {avg_score}")

    return {
        'is_valid': avg_score >= threshold_score,
        'score': avg_score
    }


def validate_file_structure(zip_ref, required_files):
    """
    Validate the structure and content of files in a zip archive.
    :param zip_ref: ZipFile object
    :param required_files: List of required file names
    :return: True if all files are valid, False otherwise
    """
    for file in required_files:
        if file == 'conversations.json':
            continue  # Skip conversations.json as it's validated separately
        try:
            with zip_ref.open(file) as f:
                # Perform validation logic for each file
                if file == 'chat.html':
                    # Validate chat.html
                    content = f.read().decode('utf-8')
                    if '<html>' not in content or '</html>' not in content:
                        raise ValueError(f"Invalid chat.html file: missing <html> tags")
                elif file == 'message_feedback.json':
                    # Validate message_feedback.json
                    feedback_data = json.load(f)
                    if not isinstance(feedback_data, list):
                        raise ValueError(f"Invalid message_feedback.json: expected a list")
                elif file == 'model_comparisons.json':
                    # Validate model_comparisons.json
                    comparisons_data = json.load(f)
                    if not isinstance(comparisons_data, list):
                        raise ValueError(f"Invalid model_comparisons.json: expected a list")
                elif file == 'user.json':
                    # Validate user.json
                    user_data = json.load(f)
                    if 'id' not in user_data or 'email' not in user_data:
                        raise ValueError(f"Invalid user.json: missing required fields")
        except (KeyError, ValueError) as e:
            opendata.logging.info(f"Validation failed for {file}: {str(e)}")
            return False
    return True


def load_chatgpt_data(data: dict) -> List[ChatGPTData]:
    """
    Load ChatGPT data from a JSON object.
    :param data:
    :return:
    """
    return [ChatGPTData(**item) for item in data]


def as_wad(num: float = 0) -> int:
    """
    Convert a number to its equivalent in wei.
    :param num:
    :return:
    """
    return int(num * 1e18)


def from_wad(num: int = 0) -> float:
    """
    Convert a number from wei to its equivalent.
    :param num:
    :return:
    """
    return num / 1e18


def calculate_score_from_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate a score based on metadata and thresholds.
    :param metadata: Dictionary containing metadata analysis
    :return: Dictionary containing the score and a boolean indicating if the data is valid
    """
    # Get the validation thresholds
    validation_config = get_validation_config()

    # Extract the validation thresholds from the configuration
    min_conversations = validation_config["MIN_CONVERSATIONS"]
    min_avg_messages = validation_config["MIN_AVG_MESSAGES"]
    min_avg_message_length = validation_config["MIN_AVG_MESSAGE_LENGTH"]
    threshold_score = validation_config["THRESHOLD_SCORE"]

    # Initialize the score and validity status
    score = 0
    is_valid = True

    # Check if the minimum thresholds are met
    if metadata["num_conversations"] < min_conversations:
        is_valid = False
    if metadata["avg_messages_per_conversation"] < min_avg_messages:
        is_valid = False
    if metadata["avg_message_length"] < min_avg_message_length:
        is_valid = False

    # Calculate the score proportionally based on the metadata and thresholds if the conversation is valid
    if is_valid:
        if min_conversations > 0:
            score += min(metadata["num_conversations"] / min_conversations, 1) * 30
        if min_avg_messages > 0:
            score += min(metadata["avg_messages_per_conversation"] / min_avg_messages, 1) * 30
        if min_avg_message_length > 0:
            score += min(metadata["avg_message_length"] / min_avg_message_length, 1) * 40

        # Ensure the score is between 0 and 100
        score = max(0, min(score, 100))
    else:
        score = 0

    # Return a dictionary with the score and validity status
    return {
        'is_valid': is_valid and score >= threshold_score,
        'score': score
    }
