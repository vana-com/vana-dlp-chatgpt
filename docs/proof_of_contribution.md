# Proof of Contribution

Vana uses a Proof-of-Contribution (PoC) system to validate data submitted to the network. The PoC system functions to
ensure the integrity and quality of data within Data Liquidity Pools (DLPs). Everyone's data is different, so to enable
data liquidity, data must be mapped to some fungible asset.

Each DLP implements their own proof of contribution function based on their particular dataset. Specifically for the
ChatGPT DLP, we break up Proof of Contribution into four categories below.

## Proof of authenticity

Proof of authenticity aims to prove that the data submitted is authentic and not tampered with. The attack vector this
aims to mitigate is submitting altered data to the DLP. For example, a malicious data contributor may add synthetically
generated conversation history to their chats, making the data seem more valuable than it actually is. They may also
alter their personal information, such as their birthday or when the account was created.

### How it works in the ChatGPT DLP

In the ChatGPT LDP, we rely on the email from OpenAI linking the user to their export to verify the authenticity of the
data.

1. User requests a data export of their ChatGPT data.
2. Once they receive the "Your export is ready email", they download the zip file and copy the download link from the
   email.
3. In gptdatadao.org, along with uploading their zip file, they are asked to provide the download link. Both are
   encrypted such that only a DLP validator can see them.
4. The DLP validator receives the encrypted file and download link. They download and decrypt the file from the user's
   storage, as well as the one provided in the link. They calculate a checksum of both files and ensure they match,
   ensuring the zip that's uploaded to the user's storage has not been tampered with.

## Proof of ownership

Proof of ownership aims to prove that the data contributor indeed owns the data they are submitting. The attack vector
this prevents is a data contributor contributing someone else's data.

### How it works in the ChatGPT DLP

Specifically for the ChatGPT DLP, proof of ownership is covered by the proof of authenticity, because it's difficult
fake a unique link to download a ChatGPT export.

## Proof of quality

Proof of quality aims to prove that the data submitted is of high quality. If a data contributor submits a data export
for a newly created account, the data will still be authentic and rightfully owned by the contributor, however, it is
probably not very useful.

### How it works in the ChatGPT DLP

We leverage an LLM and sample conversations to determine the quality of the data.

1. When data is submitted to a validator, they take a few randomly sampled conversations and sends them to an LLM (
   OpenAI in this case) and is prompted to determine the coherence and relevance of the conversation and score it from
   0-100.
2. The scores from different conversations are then averaged, giving an idea of the quality of the data.

## Proof of uniqueness

Proof of uniqueness aims to prove that the data submitted is unique. Similar to the authenticity check, this proof aims
to thwart malicious data contributors who may submit the same data multiple times to the DLP.

### How it works in the ChatGPT DLP

We implement a model influence function that fingerprints a data point and compares it to other data points on the
network.

1. The validator calculates a feature vector of the zip file by first getting a deterministic string representation
   of the file, and converting it to a feature vector. This is the fingerprint of that data point. If a slightly altered
   file is ran through this same process, it will produce a very similar fingerprint, unlike a hash, which will be
   vastly different even if 1 bit of the underlying data is changed.
2. The validator then records this on-chain so other validators are aware of the fingerprints of other data points in
   the network. They then build a local vector store of all existing data points.
3. After the fingerprint is calculated, it inserts the fingerprint into the local vector store and checks how similar it
   is to other fingerprints in the store. If it is too similar, it will reject the data point.

This method offers an efficient way to check similarity against all other files in the network. A proof-of-concept of
how this works is provided in `/tests/similarity.py`.

## Conclusion

While Proof-of-contribution is different for different DLPs, some ideas outlined here can be applied to other DLPs.
Combined with the proof of authenticity, ownership, quality and uniqueness, we can be sure that the network rewards
high-quality, meaningful data while preventing attackers who submit low-quality data.
