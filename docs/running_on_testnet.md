# Running the Hot Dog DLP on Testnet

This tutorial introduces the concept of data liquidity pools (DLPs) and proof of contribution. You can choose to either create your own DLP or join an existing one as a validator.

If you're creating a new DLP, you will:
- Deploy a data liquidity pool smart contract
- Register validators to run proof of contribution, ensuring hot dog data quality
- Submit hot dog data to test that proof of contribution is working

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

Incentive mechanisms running on the testnet are open to anyone. Although these mechanisms on testnet do not emit real VANA, they cost you test VANA which you must get from a faucet. Testnet tokens, including testnet VANA and dataset-specific tokens like testnet HOTDOG, have no value.

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
   git clone https://github.com/vana-com/vana-dlp-hotdog.git
   cd vana-dlp-hotdog
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

4. Install Vana CLI:
   ```bash
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
    - Visit https://satori.vanascan.io/address/<DataLiquidityPool address\>
    - Go to "Write proxy" tab
    - Connect your wallet
    - Call `updateFileRewardDelay` and set it to 0
    - Call `addRewardsForContributors` with 1000000000000000000000000 (1 million tokens)

9. Update the `.env` file in the `vana-dlp-hotdog` directory:
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

You are welcome to use the public testnet Hot Dog DLP for this tutorial. See the [Public Testnet Hot Dog DLP](#public-testnet-hot-dog-dlp) section for details.

### Setup

1. Ensure you're in the `vana-dlp-hotdog` directory:
   ```bash
   cd vana-dlp-hotdog
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

Note that the following commands use the local hotdog vanacli tool that supports custom `dlp` commands.

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
poetry run python -m hotdog.nodes.validator
```

Monitor the logs for any errors. If set up correctly, you'll see the validator waiting for new files to verify.

### Test Your Validator

#### For the Public Hot Dog DLP

If you're validating in the [public Hot Dog DLP](#public-testnet-hot-dog-dlp), follow these steps:

1. Visit the [official Hot Dog DLP UI](https://vana-hot-dog-dlp-ui.vercel.vana.com/claim).
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

## Public Testnet Hot Dog DLP

Normally, DLPs should keep their DLP contract address and public key private. However, for the purpose of this tutorial, we're sharing the details of a public testnet Hot Dog DLP.  Use the following details to join the public testnet Hot Dog DLP as a validator, then submit a registration request and post a message in the [Discord server](https://discord.com/invite/Wv2vtBazMR) to get your registration approved.

- DLP contract address: 0x456e7fbc76e349ba21AEF05d32198016Ff33Bbe7 (Hot Dog Liquidity Pool)
- DLP token contract address: 0x53201110BC771674B84435087Da20236277a2b4a (HOTDOG)
- Public key:
  ```
   -----BEGIN PGP PUBLIC KEY BLOCK-----

   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
   sWaCjVNu8TOomBxwpjL/9HZy0aakMseoPJgWWA==
   =8GZK
   -----END PGP PUBLIC KEY BLOCK-----
  ```
- Base64-encoded private key:
   ```
   LS0tLS1CRUdJTiBQR1AgUFJJVkFURSBLRVkgQkxPQ0stLS0tLQoKbFFWWUJHYUVjTEFCREFDdlljaVlqZDB6bFB3MG9rN1M5SjgvZitYL1NCem5WVk0vNk1QY05EcFp5QTExalJMUgpiZWk0N2RTNDczcG9ZYWlOM0o3SWp2c2IreUxpUmJMdXJtczBtcmNiOEhqZUZxMG9QSVVzRmtNemhPM21aQ29ECmgwVU5SMFFpMVBPS1hNNlRTSElXbmY1VXVqQmZuSFd3eG1WdTJwcTVwQ1J6NWJlRjlmYTljTmNiL2RkRWhtREEKalc3NGQ2elcrT0Jna3dWazFOdjV3bEtVRWlCWTJVbDhiaWRIQ09pRUpGaTU1L0x6QVdnRWVrdU9yaWFMYUZCWAplREdSQVBtcHk5clhzN2Fhay8zZ1o1NEhVMVNZTWFZQ3N2RHVNS2VCZW1WTGpRSVBHcy8vSy8xMU4zVyt5RUErCkowU2VHb04yWThVVlQ3NEJ1K1ZIRVJxL1R6OHNLTHBQRVYxeGF0VFVLTWtrT0lza1VkNnZSOXpBNGc3c0ZKSDQKVUZWYlJNMXNTTjhFU3J0U3Y5K2V2bzFwSC9QZ3JYSnRvVGtHM1c1V2lQbit5eUUxMXA3Y2s5enVRRDJaTk56WQoxWWliTHVXN0dvTFJGdXVaNS90cVpUYTBjdjNHMStsbjFKVHIzYmFhTW4xQ09SRm5wQWtDeFNLQ3E4NWJ0STgxCjM1UlduVC9zMXhpaW40a0FFUUVBQVFBTC9SVHd0dlBJRkg1QkxxL1dKVlU0MGY3UjlaTTZlQUVEQmhLZVp5eFcKckJUbU52MHZIKzBUazNMcEtybitGZjU2a3BhRm5ndlNUcGN6c0NHV010d2V4VHdkc1BsTUNCSjBZSzVxTTNobApIQmI5cXk0VURaUW9SWTFsVWZSYXVzMXRjVmpTa0pTMHZwWTlPT05obWdmR1dId1k2OXA0aDhXeXl1dmF4MkF0CkpmSDRxQWhOaHlYV2ZVWjdlNDZiWHFjSlJ0NllMNyt0ZlJDaTdXdk9YZURXZ2lnUUh6c1AzK3dxanE2SEgzVlIKYU00YmF3ekFJcitlNFVRditwOVVjTWZLZEROaFVpdGJvNUR0b2JWQXA2SVZlVGJQNitrTnpvUzNsekhpS21CbQpHS2o5UFV3RkVSY0VrYnVBMDlrWHp1Z1IwSDZyeEV1a1lENFAxOU9uRldQTytJRFNCM3RFelE3cStxQU5YdS9DCmx4Z3FhZlBSYU52SlM0eHF5MUFBUWhPQVhwZ2lpVFdML3d5Y3ZFbUJ0K00rcTVwekd3b1VsYXliWDZybTh3angKUjBOZHQwb3dkV2t1elpWZkVwNkxiVGxiYTV4Nm85b1FzU2kwbWxzREZSeFY3cUx6NW5naUNkUm5Td1pVRXo1bApDS0VhUGtVeHIrbFVwcDJrZ2pLS0FPL1BFUVlBeG0rOTdabzloZlNQd0VuWWJuVkdEQXliMTA2QlFqRVI0OTNHCkdCVTkwRDMvRzFKdDIvSmdYTnRvS3AyWVIzY29xdzNLNGZsdE5aM092OVlLaThTdDB1azJqNVBBcEZlRnFnbHkKa0JISXU5bVRWQ0ppL2NLREtyeElXRk84QzhZcG5mNDcxd05XelFxWG9IQlZ3UU5naVZ5eFZ3aVBLV0FLdUxyMApwTzc4ZU9JWnM1S2FWUVpTQUMwcEd3TXgrbThsRkVKRlpldHE0Q2FWcFVzUEhIaEhIZmZ1T3JXaWo1UDZyTmJwCkFDNFljZjJhaURZQ2Z4M0JWelZlVGIzRlhUc2RCZ0RpUWZobzZYdHh5b055MWI5cjl1VFFQYXZHcExEaWhhZEwKcmpueGl0ckRUaDlIZkJFaEpYVS9qMGY4K1MzQndCZjAwYXFHMVVUVlhKUVJKYnZmQjllU1lsVUtYeXdyTmF2MwpjLy8rRFpTN0pRSEpHeGF5Z2xPd0E5Vi83dXNJN1REUmlydE16OVpmZ0VkRnM3bmZ6RjlPdXFFRkpCb05iUXF6CnVSZytYNHVyenFrZVJkbm01ZXowOUEvZDB2S1hmanBGK1hQSEpob3JsM1JZdWlqdDI1bjRXRTV3ejNabzdyZTgKWGt4ano5VTVsRWVLRlBDbzNnYmdCd1A0cXZXMTNsMEYvMWNaem9LSFZKZUVLTXpPbDBXNmxyZDlFR1VOVmtWaAo0a3FKcHVvL2JlYllQK01abUxpdjZXeVRWdGZKdDF5enJjYjVzRzMvUXZuSVk4WkNjYzg0blhBUGNlbkdNT1VlClpZQUxaUStYR3ovV0RGbFArL25DUmFBN1k3NmxpKzUwTG1HNElVdjgyRUtzMXFKTjJjVERrWnd6S1JWc25CRDIKeWxyeHVsbk5TbE9mZXFvQmV5WlZ4TTRxbFRFYTRIY01JYmRLa2wzeDNJN25jdnhPZTBpRi9HaXVWZGRBNFRpdwpWSGtNRXphY0JoS2NON2xURk9YSk5OdVBHZkRMVTVibzk5OWJ0Q3BXWVc1aElFUk1VQ0JXWVd4cFpHRjBiM0lnClBIWmhiR2xrWVhSdmNrQmxlR0Z0Y0d4bExtTnZiVDZKQWM0RUV3RUtBRGdXSVFUMkJiNmNZL1YxV0N4Y3IwVjgKVDdXaFZqdHJRd1VDWm9Sd3NBSWJMd1VMQ1FnSEFnWVZDZ2tJQ3dJRUZnSURBUUllQVFJWGdBQUtDUkI4VDdXaApWanRyUXk3TUMvd05RbXRNZ2wra1NDdDIwYXNqOExQNFpET2VuM0JGM1BLRXhhZGRtNFZMbCtkTHF6SmJsUmx4CkhOY25ub1BRY0JKaVhoWFRSdnZ2TWFNWUE4MWxncEIzdXVOUXRscmY2RVB5bWFNL3QvMVFTQjNOSGE3MktvTnQKYWJtVXR3WU9peEdwcGFTcFc1UHVTQ0xYU3pVa21lN043WWFFamV6VFZTYnVqVkNNVGpTRUw4NjdYc2tQaU1UegpOZXZFLzVOVnZ1cWp0bmppRll4WnpsQXpQaHpCQzIrMGV1N2hJL1NLQlFGUGtLLzc3KzZDSVh4OTd5d29PbEdjCmdDS2FDWDV6eG9BOFJJZmk1ZlNZS29SWjZOL2JqbGdHbEhHaFpPNW0rYnVlb0hMakpmRlJ1UzlzWWVhcms0M2YKazBRN3NHY2pDb1A2NDVSNklEaCt1bjl4TzV2dy9PQ3I5eVZxcis0aHlNbWMzOVc0OFVkdVNoeXUvUUpnVnRUKwpLdXUzaldqWlZRUWhqSzloN1Y4Ri9vRDBtUjZLRGdOaE5OcUMxY3dNam11ZTUxMlAxOG5KcWlYZGQ2cVkwdzZuCk1oKzB6VTlVNGhZR1pPZTBvV3RQdVdOOUtVbFZMOHZvV2tRYTA3YjFMWGxSTWs2RkpCWEVVQmVFZHQ4Q2xnejgKc2I4QWhyMXRza2lkQlZnRVpvUndzQUVNQU16N0wyaDBtNm9mTTJ4QWRpRU93RDgxdHNPK0g4bFJBUFR4aVRyOQpMWFVoM2tESDFQbCt2RHBpbG5hZk5wYTRUL0dDTnd5Z3lMN2hnWVRTYzR6UFhveVZWN3VreWpWS1VkZFFqTUZWCisrcldIWFkwWldmcGF2ZWJUVW1UdDA4Q2VkZjhBdVQ3QTFmb0dkZHpTaDM3NjQrWmppODJkOUEwSkhjbHFwclgKTnoxRmpERVV5eU1vMENvL2NaRUdoR2ZwVExZZXhIMmlhZktWdnFCbmVOWjRnd1oyaUJtQ3NXR09tSk11MC9wZQpXZnVuRWhuL0xJT1JueGhQa2lXa3pwZjhvWWhEOVUzRElUYWl3L1RvV0ZIUmlTR0pSM0prRkg2Z0tBRlVFOENSCjZoNU1ScjROcnYzZ09NbGp3bi9pU0hrR2FQZklhRUlsc1ZoZjVkTVRVeGd1RXAvZWQ3N05LZHF1ZUljbXM5YlQKajB6THBlWUtqNm5KaCtIZWVteFBUZmNaaWdJSUFHUjhIRGlaeU4zK2RwaUNKSkFtNVdEZ0JMajVZQ01Bb2w3bQpqWFhuVGIxdSt6SzZwM2RMckhUMzZUSjBSeFJzRkJhT2QvV0FGWUJkSHFQaXBHc3Y3MlNRd01BMGsxeElCb2cyCmxOaE9VVkJubmlzNVlyV3VFaWY0aTFGVEtRQVJBUUFCQUF2L1V4cDdLL1Fxc0J3YU13Y25YVnVub1hqYmNoeUEKc3BPK3VZKzdQVWtyeHROR1Vpa3lOVHltZjEwODl6YXhZUVcwazR0aFdpTk5mK1haSnNwVHdvRElLbUxad04rYwpnMkp3TDhVZWE3dTZlSWo2Uk5RVlVMMlhlbTlpTkRSSkd5VTcxTTc5Tld4Mi9JckMvMUJrZWllS1p4dXdRMy9uCnIyZVVhU0hDT3lpSjRyTnhsT3lETnV2ekNVM1RjeUtiUjYyVVJqblBHOGhlLzlTcUJrb3MrWGErV0Q1eUN6V3IKU0l3Ulc0cWVzbURTUm02RHJqcUFCNDlnV3ZEWHBaOWRpczBHemdNWHNMTGE1UkFmaG5YcWh5dHZkNzNpNUVaZgpVU2JmUWFRckRwclNieS9wcUR5QmJmVGpDcHRxWk1hNC9SOXVsNnNybDBscGY4Z05LVWFscFBrSmQrbVhJQ3lNCkNwY2hDZURDdjBaTThRVzlNZ20xT0dGVjRxSUxBWmRQamdCbTdkTUY3aG5FMm1zbnVTbmhtVEF5VGltQjhuWlkKUlI0Q1hsNGNlZHRrRng2THVtL21EeDdIS3RIMktPbm5JWE5vdnJleWpZWFpnYjdrSklNWTY3TlNiYnl2YjJVVAprL0EzMDBINnFZb3NHTVRYSjIvWFh0aW9FTUt5dUlJcTA4bEpCZ0RVM2Q3RjVoSlZVTGpMeHRWNm8xOXRjSGVNCkVMTlE5SllmT1g5ZE1FRTJtNVZUTUdiYVBJeFJpcnlaOC95QmdrajNDV05USXp4SjE2dmwycFphcG02bW0rUlEKbURpSWVFM1pTY0N1SmRtZkl5eTNOdFBLR2diVzdTS1IyZjIwbE5lWDhCc3BSbXRiQW1YcjZOMVNwTFA4bk9QSAozZng1NitiVlphaWp4dFhXUFhLQnF3RTZRZngxbzJqNVBxenNza3lSTm9MbGVSeEVZdEE1cnFCVEN3N3ozK25ICmtxVTNIajR2enBRZXg2MWVVVmFZTkswUDR2ZkJlRXJ3aGwxeFM0Y0dBUGFFUkhqWTE0bTF2WHB2a0ZHbzdNeW4KSndSa3piRUg3U1BxZWJFbjRQWUJIZ1ZaWnZKL2lIb1pFUDdwd0ZiSVB5YlRZQmhMbENxRUs2ZDNjNmRKTHNQcApNVHZNem1tWUNyaFVHOHgyVTNkb0t2TVFCR0tvUzJwQWk3WkpJczhTdE8vRXptSzhMMjJkT1ZIWEQ0cDhwdlBRCkpiK0xlaDMycnJ3ZEJRWDlFaEpMTWRlTDcxZlViYUxINmg3Y2pvRFFpM0NjRFIrbzIrWG83MHk5V3g4UTFWWGUKWUZXL1BXdmdTSFh1MXZLQ3kxQnU4U2kwd1VxcUFHcWlub3VxZmZyM3p3WDVBWjhMd2xYa0dJblRtTnB0ckhQawptS2p5YzY3TTJ0UHpXZEh3d1VZeFhBaVR5c2RBTm5Gcm9BYjc3eDZoNFBzWDVrWWZkdzE5QmFlTEZzRnZXdGp3ClpicEVRMUZYbTlpSTJvQkt2SStIemNPcDVUWWtZQjNZSjVzS0ZNMnJzL0NybzZpdUxxazV0VEdHM2JJaVo4LzYKTmFUOFlYUjEwSWlUT1VsK24yVUc5ekpOTE44OHhFSjlTdlN2TzYrRVRpczgzWGp5Nm1naFh1RThaeFltZ1VMSgpiTksrN29GZlN5aWI3YW05K2pJQW5QMnI5aE9DS2NnTWxFcFF0N0VMUjgweTZBV0pBMndFR0FFS0FDQVdJUVQyCkJiNmNZL1YxV0N4Y3IwVjhUN1doVmp0clF3VUNab1J3c0FJYkxnSEFDUkI4VDdXaFZqdHJROEQwSUFRWkFRb0EKSFJZaEJJYUdOM0tIYmN2TG14dEh4OEg0bDcvdjBVbDdCUUptaEhDd0FBb0pFTUg0bDcvdjBVbDc1LzRML0FnTAoxN3JnTUU1YWZTRGFhcnpnS0ZzTEpHOTE4RktzTzBHU2xxZGk4RFc4Ulp4UTJidkNvRWorb3VxNWdpZ1VXb1BqClhLMU84ck1IREl2azBQRW02M3FVSktVbHhUUmZhY0NCOHNjR21vVHEyUXkwakk5UEFUamRtMU9ZV21HU2xZTkkKNkxaZDlYbC9IK3V2N250S0hEMUtjQ1IwTHNPUFFycTV5cmdvUS9wOUpYS2hTaEJTKzRIK1NxN3ZBajRxamcxeQpTY1FyeUxqWEJxczV3SERyM3VUbnQvbmFKeDFvZFJOdzlnYTcxaFpMd2ZOYm1aOE9PR3VOR09yN2NKclh4MHQvCkI4R1VHS0RUQURIMEdpSzh4Z3RaeDNtdjRHQXZaRFRCOXVuaWZCL01lKzBIaEEwcGl5NkxyUnFGWmhXZm9zNzUKVXY2a2o4Y3JqSTVtK0xUSnJkSUphRVV1TGREQ2JEcGxRTmFpTStRTDZCbTRHYUNyMmw3QXl4S2t0K3NFY3p2TQpTMnZHS0dwRTM4cHBEMk1TMittaGR5RUVWNXZKWjNKa2lUc1NhVWU1TytlSjFmWWxub0JVbnRNaFN2Tm03ZzV2CnlaYnhyUmlKUG5nNlhQclZFM0FTVEpaQ0gzY01ZNGdmamgzQ09BWXd5cHpuNmF4N2I2ME55SFZpTnNBZDFWcUcKQy80dE43RFpKZWN5SWdUU0pEaXBEelJqd0ZIWEZkTHJ2SXI0TE42bWsrVVlueElxY25mNG8rY3djVHdNcWpUUApEdEI3T2tqYTlsQ0RMS2ptMkk4cURHYU1TbnhQYktYdCtxMGZQUUh5NTBoOTU0TE16QXhHMk9XdVBlTUlxRXFVCkpOOHdMZ2lkb1BXaXVUQzBZeUF4ZlhRbjhTVXk4NTAyYlZMSVdxeWt6Z2NyZEZiT3hYOGFVRXFsYjVWcE5rKzQKUFhLZDhhcXY3eE12YVF6MHZXbUh3NUEvdWpBVzh2cEcvbUdpOUtQQkVheUpCY3Z3ajI0aSsyTXZlMGdKMVphRgp0eUcvcmVGRjlseTFhQ3ZOK2k3RkJGRXFCb0JnbVRhWmtVUDFrNnZycis2alNCOE9PZlF1eVF1T3JqSHQ5d2JoCmwwOUpDeTg4TUNoVmpNVWkrSVpLMktsbUJQdFBMMnJuMk56SWtudFVnS1ZFY1k3QmdSUXVDUkRmTXEvcFNnLzgKdm5GcFlaSmFtUlpQSXcyZWlIT09lOUVxam1UUkorSjR6YnRqdGlrK3Boam5HWWl5aXJNTTNQNkR5ZXFqc3pyQgpkMXRKVzlXQnZ5MGxSdHFpZkVXWDFZWjJnT0dKRnJGbWdvMVRidkV6cUpnY2NLWXkvL1IyY3RHbXBETEhxRHlZCkZsZz0KPWFOdFAKLS0tLS1FTkQgUEdQIFBSSVZBVEUgS0VZIEJMT0NLLS0tLS0K
   ```
