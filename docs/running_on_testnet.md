# Running the ChatGPT DLP on Testnet

This tutorial introduces the concept of data liquidity pools (DLPs) and proof of contribution. You can choose to either create your own DLP or join an existing one as a validator.

If you're creating a new DLP, you will:
- Deploy a data liquidity pool smart contract
- Register validators to run proof of contribution, ensuring ChatGPT data quality
- Submit ChatGPT data to test that proof of contribution is working

If you're joining an existing DLP as a validator, you will:
- Set up your environment to connect to an existing DLP
- Register as a validator for the DLP
- Run a validator node to participate in proof of contribution

Whether you're creating a new DLP or joining an existing one, this tutorial will guide you through the process step by step. The setup process typically takes about 1 hour to complete.

## Disclaimer

By continuing in this tutorial, you agree to the following:
- The testnet is provided solely on an "as is" and "as available" basis for experimental purposes. The functionality of the testnet remains experimental and has not undergone comprehensive testing.
- Vana expressly disclaims any representations or warranties regarding the operability, accuracy, or reliability of the testnet.
- Participation in the testnet neither constitutes an investment nor implies an expectation of profit. There is no promise or implication of future value or potential return on any contributions of resources, time, or effort.
- I confirm that I am not a citizen of the United States or Canada, nor am I a citizen or resident of any nation or region subjected to comprehensive sanctions, including but not limited to Cuba, North Korea, Russia, Belarus, Crimea, Donetsk, Luhansk, Iran, or Syria.

### Testnet Disclaimers

Incentive mechanisms running on the testnet are open to anyone. Although these mechanisms on testnet do not emit real VANA, they cost you test VANA which you must get from a faucet. Testnet tokens, including testnet VANA and dataset-specific tokens like testnet GPTDAT, have no value.

### Words of Wisdom

- Do not expose your private keys or mnemonic phrases.
- Do not reuse the password of your mainnet wallet.

## Setup

Follow these steps to set up your environment, whether you're creating a new DLP or joining an existing one as a validator.

### Prerequisites

For all users:
- [Git](https://git-scm.com/downloads)
- [Python 3.11+](https://www.python.org/downloads)
- [Poetry](https://python-poetry.org/docs/#installation)
- [Metamask](https://metamask.io/download) or another EVM-compatible wallet

Additional for DLP creators:
- [Node.js and npm](https://nodejs.org/en/download/package-manager)

### Setup Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/vana-com/vana-dlp-chatgpt.git
   cd vana-dlp-chatgpt
   ```

2. Create your `.env` file:
   ```bash
   cp .env.example .env
   ```
   We'll populate this file later with DLP-specific information.

3. Install dependencies:
   ```bash
   poetry install
   ```

4. (Optional) Install Vana CLI:
   ```bash
   # To install vanacli system-wide, run the following command:
   pip install vana
   ```

5. Create a wallet:
   ```bash
   vanacli wallet create --wallet.name default --wallet.hotkey default
   ```
   This creates two key pairs:
   - Coldkey: for human-managed transactions (like staking)
   - Hotkey: for validator-managed transactions (like submitting scores)

   Follow the prompts to set a secure password. Save the mnemonic phrases securely; you'll need these to recover your wallet if needed.

6. Add Satori Testnet to Metamask:
   - Network name: Satori Testnet
   - RPC URL: https://rpc.satori.vana.org
   - Chain ID: 14801
   - Currency: VANA

7. Export your private keys. Follow the prompts and securely save the displayed private keys:
   ```bash
   vanacli wallet export_private_key
   Enter wallet name (default):
   Enter key type [coldkey/hotkey] (coldkey): coldkey
   Enter your coldkey password:
   Your coldkey private key:
   ```
   ```bash
   vanacli wallet export_private_key
   Enter wallet name (default):
   Enter key type [coldkey/hotkey] (coldkey): hotkey
   Your hotkey private key:
   ```

8. Import your coldkey and hotkey addresses to Metamask:
   - Click your account icon in MetaMask and select "Import Account"
   - Select "Private Key" as the import method
   - Paste the private key for your coldkey
   - Repeat the process for your hotkey

9. Fund both addresses with testnet VANA:
   - Visit https://faucet.vana.org
   - Connect your Metamask wallet
   - Request VANA for both your coldkey and hotkey addresses

   Note: you can only use the faucet once per day. Use the testnet faucet available at https://faucet.vana.org to fund your wallets, or ask a VANA holder to send you some test VANA tokens.

Always keep your private keys and mnemonic phrases secure. Never share them with anyone.

## Creating a DLP

If you're joining an existing DLP as a validator, skip to the [Validator Setup](#validator-setup) section.

Before you start, ensure you have gone through the [Setup](#setup) section.

### Generate Encryption Keys

1. Run the key generation script:
   ```bash
   ./keygen.sh
   ```
   This script generates RSA key pairs for file encryption/decryption in the DLP.

2. Follow the prompts to enter your name, email, and key expiration.

3. The script generates four files:
    - `public_key.asc` and `public_key_base64.asc` (for UI)
    - `private_key.asc` and `private_key_base64.asc` (for validators)

### Deploy DLP Smart Contracts

1. Clone the DLP Smart Contract repo:
   ```bash
   cd ..
   git clone https://github.com/vana-com/vana-dlp-smart-contracts.git
   cd vana-dlp-smart-contracts
   ```

2. Install dependencies:
   ```bash
   yarn install
   ```

3. Export your private key from Metamask (see [official instructions](https://support.metamask.io/managing-my-wallet/secret-recovery-phrase-and-private-keys/how-to-export-an-accounts-private-key)).

4. Edit the `.env` file in the `vana-dlp-smart-contracts` directory:
   ```
   DEPLOYER_PRIVATE_KEY=0x... (your coldkey private key)
   OWNER_ADDRESS=0x... (your coldkey address)
   SATORI_RPC_URL=https://rpc.satori.vana.org
   DLP_NAME=... (your DLP name)
   DLP_TOKEN_NAME=... (your DLP token name)
   DLP_TOKEN_SYMBOL=... (your DLP token symbol)
   ```

5. Deploy contracts:
   ```bash
   npx hardhat deploy --network satori --tags DLPDeploy
   ```
   Note the deployed addresses for DataLiquidityPool and DataLiquidityPoolToken.

6. Congratulations, you've deployed the DLP smart contracts! You can confirm they're up by searching the address for each on the block explorer: https://satori.vanascan.io/address/<DataLiquidityPool\>.

7. Optional: If you made any changes to smart contracts code, verify the contracts, so you can interact with them directly in the block explorer:

   ```bash
   npx hardhat verify --network satori <DataLiquidityPool address>
   npx hardhat verify --network satori <DataLiquidityPoolToken address> "<DLP_TOKEN_NAME>" <DLP_TOKEN_SYMBOL> <OWNER_ADDRESS>
   ```
   If you didn't make changes, contracts should be verified automatically. You may need to wait a few minutes / refresh the page to see the verification status. If you get an error, it may be because the block explorer has already verified matching bytecode. Check your contract in the block explorer. If it is verified, you can ignore the error.

8. Configure the DLP contract:
    - Visit https://satori.vanascan.io/address/<DataLiquidityPool address>
    - Go to "Write proxy" tab
    - Connect your wallet
    - Call `updateFileRewardDelay` and set it to 0
    - Call `addRewardsForContributors` with 1000000000000000000000000 (1 million tokens)

9. Update the `.env` file in the `vana-dlp-chatgpt` directory:
   ```
   DLP_SATORI_CONTRACT=0x... (DataLiquidityPool address)
   DLP_TOKEN_SATORI_CONTRACT=0x... (DataLiquidityPoolToken address)
   PRIVATE_FILE_ENCRYPTION_PUBLIC_KEY_BASE64=... (content of public_key_base64.asc)
   ```

After completing these steps, proceed to the [Validator Setup](#validator-setup) section.

## Validator Setup

Follow these steps whether you're a DLP creator or joining an existing DLP.

Before you start, ensure you have gone through the [Setup](#setup) section.

### Required Information

For non-DLP creators, request from the DLP creator:
- DLP contract address (DataLiquidityPool)
- DLP token contract address (DataLiquidityPoolToken)
- Public key for the DLP validator network (`public_key.asc`)
- Base64-encoded private key for the DLP validator network (`private_key_base64.asc`)

### Setup

1. Ensure you're in the `vana-dlp-chatgpt` directory:
   ```bash
   cd vana-dlp-chatgpt
   ```

2. If you're a non-DLP creator, edit the `.env` file with the information provided by the DLP creator:
   ```
   DLP_SATORI_CONTRACT=0x... (DataLiquidityPool address)
   DLP_TOKEN_SATORI_CONTRACT=0x... (DataLiquidityPoolToken address)
   PRIVATE_FILE_ENCRYPTION_PUBLIC_KEY_BASE64=... (base64-encoded private key--yes, PUBLIC is a misnomer)
   ```

### Fund Validator with DLP Tokens

For DLP creators:
1. Import DLP token to Metamask using `<DataLiquidityPoolToken address>`
2. Send 10 tokens to your coldkey address

For non-DLP creators:
1. Request DLP tokens from the DLP creator
2. Once received, ensure they are in your coldkey address

### Register as a Validator

Note that the following commands use the local chatgpt vanacli tool that supports custom `dlp` commands.

1. Register your validator:
   ```bash
   ./vanacli dlp register_validator --stake_amount 10
   ```

2. For non-DLP creators, ask the DLP owner to accept your registration.

   DLP creators can approve validators with:
   ```bash
   ./vanacli dlp approve_validator --validator_address=<your hotkey address from Metamask>
   ```

### Run Validator Node

Start the validator node:

```bash
poetry run python -m chatgpt.nodes.validator
```

Monitor the logs for any errors. If set up correctly, you'll see the validator waiting for new files to verify.

### Test Your Validator

#### For the Public ChatGPT DLP

If you're validating in the [Public ChatGPT DLP](gptdatadao.org), follow these steps:

1. Visit the [official ChatGPT DLP UI](https://gptdatadao.org/claim).
2. Connect your wallet (must hold some VANA).
3. Follow the instructions on the UI to upload a file (to submit the `addFile` transaction).
4. Wait for your validator to process the file and write scores on-chain (`verifyFile` transaction).
5. Check the UI for a reward claiming dialog and test claiming rewards.

#### For Custom DLPs

If you're validating with your own or a custom DLP, follow these steps:

1. Visit [the demo DLP UI](https://dlp-ui.vercel.vana.com/claim/upload).
2. Connect your wallet (must hold some VANA).
3. Use the gear icon to set the DLP contract address and public encryption key.
4. Upload a file (to submit the `addFile` transaction).
5. In the console logs, note the uploaded file URL and encryption key (you can also add files manually via https://satori.vanascan.io/address/<DataLiquidityPool address>?tab=write_contract).
6. Wait for your validator to process the file and write scores on-chain (`verifyFile` transaction).
7. Check the UI for a reward claiming dialog and test claiming rewards.

> Note: For heavily modified DLPs, you may need to register through the Satori explorer using your wallet's browser extension:
> 1. Import your hotkey into a browser-compatible wallet like MetaMask.
> 2. Navigate to the Write proxy tab for the verified contract for the DLP in the Satori explorer. You can get this URL from the DLP owner.
> 3. Connect to your hotkey with the button at the bottom of the page.
> 4. Submit a validator registration transaction with the addresses of your hotkey and coldkey as the validator and validator owner addresses, along with an amount of the required tokens to stake. Ensure you stake at least the minimum of the specific token required by the DLP.

## Troubleshooting

If you encounter issues:
- Ensure all prerequisites are correctly installed
- Double-check your `.env` file contents in both repositories
- Verify your wallet has sufficient VANA and DLP tokens in both coldkey and hotkey addresses
- Check the validator logs for specific error messages

For further assistance, please join our [Discord community](https://discord.com/invite/Wv2vtBazMR).

