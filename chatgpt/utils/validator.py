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
import os
import random
import zipfile
from typing import List, Dict, Any, Iterable

from openai import OpenAI

from chatgpt.models.chatgpt import ChatGPTData
import vana as opendata
import tiktoken

# Max token size for LLM validation
MAX_VALIDATION_CHUNK_SIZE = 16285


def validate_chatgpt_zip(zip_file_path):
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

    # Perform random sampling and LLM validation
    sample_size = 10
    threshold_score = 80
    validation_response = validate_sample(parsed_data, sample_size, threshold_score)

    return {
        'is_valid': validation_response["is_valid"],
        'score': validation_response["score"],
        'metadata': metadata,
    }


def analyze_data(data: List[ChatGPTData]) -> Dict[str, Any]:
    """
    Analyze the structure and content of ChatGPT data.
    :param data: List of ChatGPTData objects
    :return: Dictionary containing metadata analysis
    """
    num_conversations = len(data)
    total_messages = sum(len(conv.mapping) for conv in data)
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

    avg_message_length = round(sum(
        get_message_length(node) for conv in data for node in conv.mapping.values()
    ) / total_messages, 2)

    # Additional metadata analysis
    max_messages_per_conversation = max(len(conv.mapping) for conv in data)
    min_messages_per_conversation = min(len(conv.mapping) for conv in data)
    total_characters = sum(
        get_message_length(node) for conv in data for node in conv.mapping.values()
    )

    return {
        'num_conversations': num_conversations,
        'avg_messages_per_conversation': avg_messages_per_conversation,
        'avg_message_length': avg_message_length,
        'max_messages_per_conversation': max_messages_per_conversation,
        'min_messages_per_conversation': min_messages_per_conversation,
        'total_characters': total_characters
    }


def validate_sample(data: List[ChatGPTData], sample_size: int, threshold_score: int) -> bool | dict[str, float | bool]:
    """
    Validate a sample of ChatGPT data using a language model evaluation.
    :param data:
    :param sample_size:
    :param threshold_score:
    :return:
    """
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    sample = random.sample(data, sample_size)
    scores = []

    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    system_message = "You are an AI language model that evaluates the coherence and relevance of a conversation."
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
        max_chunk_size = MAX_VALIDATION_CHUNK_SIZE - len(system_message_tokens)  # Adjust chunk size based on system message tokens
        context_chunks = [context_tokens[i:i+max_chunk_size] for i in range(0, len(context_tokens), max_chunk_size)]

        chunk_scores = []
        for chunk in context_chunks:
            chunk_text = encoding.decode(chunk)
            content = "Please evaluate the following conversation and provide a score from 1 to 100 indicating the degree of consistency and appropriateness of the responses within the given context. Your entire response/output should consist of a single JSON object {}, and you should NOT wrap it within JSON markdown markers:\n\n" + chunk_text
            max_retries = 3
            retry_count = 0
            while retry_count < max_retries:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": content}
                    ],
                )

                score_json = response.choices[0].message.content
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
                        return False

        avg_conversation_score = sum(chunk_scores) / len(chunk_scores)
        scores.append(avg_conversation_score)

    avg_score = sum(scores) / len(scores)
    opendata.logging.info(f"Average LLM validation score: {avg_score}")

    return {
        'is_valid': avg_score >= threshold_score,
        'score': avg_score / 100
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
    return int(num * 1e18)


def from_wad(num: int = 0) -> float:
    return num / 1e18