# Vana

![Vana Image](https://i.imgur.com/tvAuEGr.png)

---

## Community Links

- [Vana Discord](https://discord.gg/withvana)
- [Vana Twitter](https://x.com/withvana)
- [Vana Website](https://www.vana.org/)
- [Vana Blog](https://www.vana.org/post)
- [Vana github](https://github.com/vana-com)
- [Vana Explorer](https://satori.vanascan.io/)

---

## 💻 System Requirements

| Components  | Minimum Requirements |
|-------------|----------------------|
| CPU         | 2 Cores               |
| RAM         | 4+ GB                 |
| Storage     | 50++ GB SSD            |
| Ubuntu      | 22.04         |



## Setup Steps

### 1. Update and Upgrade System Packages

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Install Essential Packages

```bash
sudo apt install -y curl gnupg
```

### 3. Install Node.js and npm

Add the NodeSource repository and install Node.js:

```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

Update npm to the latest version:

```bash
sudo npm install -g npm@10.8.3
```

### 5. Clone the Repository

Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/vana-com/vana-dlp-chatgpt.git
cd vana-dlp-chatgpt
```

### 6. Configure Python Version for Poetry

Set Python 3.11 as the interpreter for Poetry:

```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev

```

```bash
poetry env use python3.11
```

```bash
poetry install
```

```bash
poetry run python --version
poetry check
poetry --version
```


![Version check](https://i.imgur.com/MI6TYQT.png)


### 8. Create Your `.env` File

Copy the example environment configuration file:

```bash
cp .env.example .env
```
**We will change that .env file informations after deploying contract**

```bash
nano .env
```

```bash                                                                                        
# The network to use, currently Vana Satori testnet
OD_CHAIN_NETWORK=satori
OD_CHAIN_NETWORK_ENDPOINT=https://rpc.satori.vana.org

# Optional: OpenAI API key for additional data quality check
OPENAI_API_KEY="sk-nXXXXX"

# Optional: Your own DLP smart contract address once deployed to the network, useful for local testing
DLP_CONTRACT_ADDRESS=0xa0519f5ADc4e82729b21Ef1586d397260D9B9E45
DLP_MOKSHA_CONTRACT=0xee4e3Fd107BE4097718B8aACFA3a8d2d9349C9a5
DLP_SATORI_CONTRACT=0xa0519f5ADc4e82729b21Ef1586d397260D9B9E45

# Optional: Your own DLP token contract address once deployed to the network, useful for local testing
DLP_TOKEN_VANA_CONTRACT=0x3db29b7ED68Ca561794039B4D675f68fb64D6ac3
DLP_TOKEN_MOKSHA_CONTRACT=0xF1925473bA6aa147EeB2529197C2704454D66b43
DLP_TOKEN_SATORI_CONTRACT=0x3db29b7ED68Ca561794039B4D675f68fb64D6ac3

# The private key for the DLP, follow "Generate validator encryption keys" section in the README
PRIVATE_FILE_ENCRYPTION_PUBLIC_KEY_BASE64=XXXXX
```


CTRL + X + Y




### 9. Install Vana CLI

To install `vanacli` system-wide:

```bash
pip install vana
```

** If you will get error here follow these steps otherwise jump to step 10** 
It seems you're encountering issues with broken package dependencies. To fix this, try the following steps:

a. **Fix Broken Packages:**

   Run the following command to correct any broken package dependencies:

   ```bash
   sudo apt --fix-broken install
   ```

b. **Update and Upgrade Packages:**

   After fixing broken packages, update and upgrade your packages to ensure everything is up to date:

   ```bash
   sudo apt update
   sudo apt upgrade
   ```

c. **Once the broken packages are fixed, install the `python3.10-venv` package:**

   ```bash
   sudo apt install python3.10-venv
   ```

d. **Create and Activate Virtual Environment:**

   After successfully installing `python3.10-venv`, create and activate your virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

e. **Install Vana:**

   With the virtual environment activated, install Vana:

   ```bash
   pip install vana
   ```

![Output](https://i.imgur.com/TGBz6g1.png)

Let me know if you encounter any more issues!

### 10. Create a Wallet

Create a wallet using the Vana CLI:

```bash
vanacli wallet create --wallet.name default --wallet.hotkey default
```

This will create two key pairs:

- **Coldkey**: For human-managed transactions (e.g., staking).
- **Hotkey**: For validator-managed transactions (e.g., submitting scores).

Follow the prompts to set a secure password. Save the mnemonic phrases securely; you'll need these to recover your wallet if needed.

### 11. Add Satori Testnet to MetaMask

Configure MetaMask with the following details:

- **Network Name**: Satori Testnet
- **RPC URL**: https://rpc.satori.vana.org
- **Chain ID**: 14801
- **Currency**: VANA
- **Explorer**: https://satori.vanascan.io/

### 12. Export Your Private Keys

Export private keys using the Vana CLI:
Follow the prompts to export both the coldkey and hotkey private keys.

**a. Coldkey**
```bash
vanacli wallet export_private_key
```

OUTPUT:**Save in safe place.**

```bash
Enter wallet name (default):
Enter key type [coldkey/hotkey] (coldkey): coldkey
Enter your coldkey password:
Your coldkey private key:
```

**b. Hotkey**

**Don't forget to write hotkey when it asks you. If you will not write anything you will get key of coldkey**
```bash
vanacli wallet export_private_key
```

OUTPUT:**Save in safe place.**
```bash
Enter wallet name (default):
Enter key type [coldkey/hotkey] (coldkey): coldkey
Enter your coldkey password:
Your coldkey private key:
```

### 13. Import Keys to MetaMask

- Click your account icon in MetaMask and select "Import Account."
- Select "Private Key" as the import method.
- Paste the private key for your coldkey and repeat the process for your hotkey.

### 14. Fund Both Addresses with Testnet VANA

Visit [https://faucet.vana.org](https://faucet.vana.org), connect your MetaMask wallet, and request VANA for both your coldkey and hotkey addresses.

**Note**: The faucet can be used once per day. If needed, ask a VANA holder to send you some test VANA tokens.

### 15. Creating a DLP

**If you're joining an existing DLP as a validator, skip to the Validator Setup section.**

#### Generate Encryption Keys

Run the key generation script:

```bash
./keygen.sh
```

This script generates RSA key pairs for file encryption/decryption in the DLP. Follow the prompts to enter your name, email, and key expiration.

The script generates four files:

- `public_key.asc` and `public_key_base64.asc` (for UI)
- `private_key.asc` and `private_key_base64.asc` (for validators)

#### Deploy DLP Smart Contracts

Clone the DLP Smart Contract repository:

```bash
cd
git clone https://github.com/vana-com/vana-dlp-smart-contracts.git
cd vana-dlp-smart-contracts
```

Install dependencies:


```bash
nvm install 18.8.0 && nvm use 18.8.0
```

```bash
yarn install
```

**upgrade**
```bash
yarn upgrade
```

```bash
npm install --save-dev hardhat
```

```bash
cat ~/.vana/wallets/default/hotkeys/default
```

**Save the output**
Example: {"address": "0x0XXXXXXXXXXXXXXXXXXXA", "publicKey": "0xa08b00caXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX86", "privateKey": "0xXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX1"}(venv)

Edit the `.env` file in the `vana-dlp-smart-contracts` directory:

```bash
nano .env
```

```bash
DEPLOYER_PRIVATE_KEY=0x... (your coldkey private key)
OWNER_ADDRESS=0x... (your coldkey address)
SATORI_RPC_URL=https://rpc.satori.vana.org
DLP_NAME=... (your DLP name)
DLP_TOKEN_NAME=... (your DLP token name)
DLP_TOKEN_SYMBOL=... (your DLP token symbol)
```

Deploy contracts:

```bash
npx hardhat deploy --network satori --tags DLPDeploy
```

EXAMPLE OUTPUT:
Successfully generated 162 typings!
Compiled 52 Solidity files successfully (evm target: paris).
DataLiquidityPoolToken deployed at: 0xXXXXXXXXXXXXXXXXXXXXXXXXa45 (DataLiquidityPoolToken)
DataLiquidityPool "sunkriptodlp" deployed at: 0xXXXXXXXXXXXXXXXXXXXXXXXXas4 (DataLiquidityPool address)

**Note the deployed addresses for DataLiquidityPool and DataLiquidityPoolToken.**

**Optional**: Verify the contracts if you made changes to the code:

```bash
npx hardhat verify --network satori <DataLiquidityPool address>
npx hardhat verify --network satori <DataLiquidityPoolToken address> "<DLP_TOKEN_NAME>" <DLP_TOKEN_SYMBOL> <OWNER_ADDRESS>
```

If no changes were made, contracts should be verified automatically.

#### Configure the DLP Contract

Visit [https://satori.vanascan.io/address/](https://satori.vanascan.io/address/):

- Go to the "Contract" tab and after "Write proxy" tab
- Connect your wallet
- Make sure you added to '' Satori Network '' to Metamask
- Refresh the page
- Find `updateFileRewardDelay` and set it to 0
- Find `addRewardsForContributors` with 1000000000000000000000 (1 million tokens)

Update the `.env` file in the `vana-dlp-chatgpt` directory:

```bash
DLP_SATORI_CONTRACT=0x... (DataLiquidityPool address)
DLP_TOKEN_SATORI_CONTRACT=0x... (DataLiquidityPoolToken address)
PRIVATE_FILE_ENCRYPTION_PUBLIC_KEY_BASE64=... (content of public_key_base64.asc)
```

### 16. Validator Setup

Follow these steps whether you're a DLP creator or joining an existing DLP. Ensure you have completed the Setup section.

**Required Information**:

For non-DLP creators, request the following from the DLP creator:

- DLP contract address (DataLiquidityPool)
- DLP token contract address (DataLiquidityPoolToken)
- Public key for the DLP validator network (`public_key.asc`)
- Base64-encoded private key for the DLP validator network (`private_key_base64.asc`)

**Setup**:

Ensure you're in the `vana-dlp-chatgpt` directory:

```bash
cd
cd vana-dlp-chatgpt
```

```bash
cat public_key_base64.asc
```
**Save output**

If you're a non-DLP creator, edit the `.env` file with the information provided by the DLP creator:

```bash
nano .env
```
If you've deployed your own DLP contract, make sure to update the following 5 fields:

DLP_CONTRACT_ADDRESS=0xaYOURDLPADDRESS
DLP_SATORI_CONTRACT=0xaYOURDLPADDRESS
DLP_TOKEN_VANA_CONTRACT=0x6381YOURDLPTOKEN-ADDRESS
DLP_TOKEN_SATORI_CONTRACT=0x6381YOURDLPTOKEN-ADDRESS
PRIVATE_FILE_ENCRYPTION_PUBLIC_KEY_BASE64=LS0tLS1CR

```bash                                                                   
# The network to use, currently Vana Satori testnet
OD_CHAIN_NETWORK=satori
OD_CHAIN_NETWORK_ENDPOINT=https://rpc.satori.vana.org

# Optional: OpenAI API key for additional data quality check
OPENAI_API_KEY="sk-nXXXXX"

# Optional: Your own DLP smart contract address once deployed to the network, useful for local testing
DLP_CONTRACT_ADDRESS=0xaYOURDLPADRESS
DLP_MOKSHA_CONTRACT=0xee4e3Fd107BE4097718B8aACFA3a8d2d9349C9a5
DLP_SATORI_CONTRACT=0xaYOURDLPADRESS

# Optional: Your own DLP token contract address once deployed to the network, useful for local testing
DLP_TOKEN_VANA_CONTRACT=0x6381YOURDLPTOKEN-ADRES
DLP_TOKEN_MOKSHA_CONTRACT=0xF1925473bA6aa147EeB2529197C2704454D66b43
DLP_TOKEN_SATORI_CONTRACT=0x6381YOURDLPTOKEN-ADRES

# The private key for the DLP, follow "Generate validator encryption keys" section in the README
PRIVATE_FILE_ENCRYPTION_PUBLIC_KEY_BASE64=LS0tLS1CR
```

**Fund Validator with DLP Tokens**:

- **For DLP creators**: Import the DLP token to MetaMask using `<DataLiquidityPoolToken address>` and send 10 tokens to your coldkey address.

- **For non-DLP creators**: Request DLP tokens from the DLP creator and ensure they are in your coldkey address.

**Register as a Validator**:

Register your validator:

```bash
./vanacli dlp register_validator --stake_amount 10
```

For non-DLP creators, ask the DLP owner to accept your registration.

**For DLP creators**: Approve validators with:

```bash
./vanacli dlp approve_validator --validator_address=<your hotkey address from MetaMask>
```

**Run Validator Node**:

Start the validator node:

```bash
screen -S vana
```

```bash
poetry run python -m chatgpt.nodes.validator
```

Monitor the logs for any errors. If set up correctly, you'll see the validator waiting for new files to verify.
Logs:
![Vana Image](https://i.imgur.com/XYSQYwR.png)

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

