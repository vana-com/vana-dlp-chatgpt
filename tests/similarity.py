import os
import tempfile
import zipfile

from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize


def get_file_contents_as_string(directory):
    """
    Returns the contents of all files in a directory as a single, deterministic string
    """
    contents = []

    for root, dirs, files in sorted(os.walk(directory)):
        dirs.sort()
        files.sort()

        for file in files:
            file_path = os.path.join(root, file)
            with open(file_path, 'rb') as f:
                contents.append(f.read())

    return b"".join(contents).decode('utf-8', errors='ignore')


def feature_hash_string(s, n_features=128):
    """
    Hashes a string into a fixed-size feature vector
    :param s: String to hash
    :param n_features: Higher number captures more details but increases the hash size.
    :return:
    """
    vectorizer = HashingVectorizer(n_features=n_features, norm=None, alternate_sign=False)
    hashed = vectorizer.transform([s])
    hashed_normalized = normalize(hashed, norm='l2')
    return hashed_normalized.toarray()[0]


def calculate_similarity(hash1, hash2):
    # Reshape hashes to 2D arrays and calculate cosine similarity
    hash1 = hash1.reshape(1, -1)
    hash2 = hash2.reshape(1, -1)
    similarity = cosine_similarity(hash1, hash2)[0][0]

    similarity_percentage = (similarity + 1) / 2 * 100
    return similarity_percentage


def generate_feature_hash(zip_relative_path):
    zip_path = os.path.join(os.getcwd(), zip_relative_path)

    with tempfile.TemporaryDirectory() as tmpdirname:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmpdirname)

        file_contents = get_file_contents_as_string(tmpdirname)
        hash = feature_hash_string(file_contents)
        return hash


if __name__ == "__main__":
    # Uses feature vectors to fingerprint a zip file and calculate similarity between two zip files
    # Usage: poetry run python tests/similarity.py

    # ChatGPT export file with 1 conversation
    feature_hash_1 = generate_feature_hash('tests/data/chatgpt_1_conversation.zip')

    # Same zip file as before, but the user email has been modified
    feature_hash_2 = generate_feature_hash('tests/data/chatgpt_1_conversation_similar.zip')

    # ChatGPT export file with 5 conversations
    feature_hash_3 = generate_feature_hash('tests/data/chatgpt_5_conversations.zip')

    similarity_between_1_2 = calculate_similarity(feature_hash_1, feature_hash_2)
    similarity_between_1_3 = calculate_similarity(feature_hash_1, feature_hash_3)
    print(f"Similarity between files 1 and 2: {similarity_between_1_2:.5f}%")
    print(f"Similarity between files 1 and 3: {similarity_between_1_3:.5f}%")
