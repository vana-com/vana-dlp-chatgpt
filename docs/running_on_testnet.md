# Running the ChatGPT DLP on Testnet

This tutorial introduces the concept of data liquidity pools and proof of contribution by having you create your own data liquidity pool and validators. It is based on the standard [smart contract template](https://github.com/vana-com/vana-dlp-smart-contracts/tree/2ada9aac3a54dc193903fb4d0e0886bfe7c92e1f) and [validator template](https://github.com/vana-com/vana-dlp-chatgpt), and will take about 1 hour to get setup. You will:
- Deploy a data liquidity pool smart contract
- Register validators to run proof of contribution, ensuring chatGPT data quality
- Submit chatGPT data to test that proof of contribution is working

Note that you will not be rewarded in GPTDAT - this testnet tutorial just writes scores onchain, but does not yet support claiming GPTDAT. 

By continuing in this tutorial, you agree to the following
- The testnet is provided solely on an “as is” and “as available” basis for experimental purposes. The functionality of the testnet remains experimental and has not undergone comprehensive testing.
- Vana expressly disclaims any representations or warranties regarding the operability, accuracy, or reliability of the testnet.
- Participation in the testnet neither constitutes an investment nor implies an expectation of profit. There is no promise or implication of future value or potential return on any contributions of resources, time, or effort.
- I confirm that I am not a citizen of the United States or Canada, nor am I a citizen or resident of any nation or region subjected to comprehensive sanctions, including but not limited to Cuba, North Korea, Russia, Belarus, Crimea, Donetsk, Luhansk, Iran, or Syria.

### Testnet disclaimers

Incentive mechanisms running on the testnet are open to anyone, and although these mechanisms on testnet do not emit
real DAT, they cost you test DAT which you must get from a faucet. Testnet tokens, including testnet DAT and dataset-specific tokens like testnet GPTDAT, have no value. 

### Words of Wisdom

- Do not expose your private keys or mnemonic phrase.
- Do not reuse the password of your mainnet wallet. 

## Get started

Make sure to install the project dependencies:

```bash
git clone https://github.com/vana-com/vana-dlp-chatgpt.git
cd vana-dlp-chatgpt
poetry install
```

Configure the environment variables by copying and modifying the `.env.example` file, to a `.env` file in the root of the project. 

## (Optional) Setup vanacli
To install vanacli system-wide, run the following command:

```shell
pip install vana
```

## Create a Wallet

Now we need to create wallets for the DLP owner and validators running on the DLP. Let's create two wallets for running 2 validators on two
different ports.

The owner will create and control the DLP.

```bash
# Create a wallet for a the DLP owner
vanacli wallet create
> wallet name: owner
> hotkey name: default
> password: <password>
```

It may take a moment to generate the wallet. Remember to save your mnemonic phrase.

Generate wallets for two validators you will run, too:

```bash
# Create a wallet for a validator running on port 4000
vanacli wallet create
> wallet name: validator_4000
> hotkey name: default
> password: <password>

# Create a wallet for a validator running on port 4001
vanacli wallet create
> wallet name: validator_4001
> hotkey name: default
> password: <password>
```

## Fund Wallets

First, fund your metamask or other evm-compatible wallet from the faucet so you have some funds to work with. 

Add the Satori Testnet to your metamask wallet: 
```bash
Network name: Satori Testnet
RPC URL: https://rpc.satori.vana.org
Chain ID: 14801
Currency: DAT
```
Note you can only use the faucet once per day. Use the testnet faucet available at https://faucet.vana.org to fund your wallets, or ask a DAT holder to send you some test DAT tokens.

Get your wallet private keys for all three accounts and import them into metamask or another wallet of your choice.
```bash
jq -r '.privateKey' ~/.vana/wallets/owner/coldkey
jq -r '.privateKey' ~/.vana/wallets/validator_4000/coldkey
jq -r '.privateKey' ~/.vana/wallets/validator_4001/coldkey
```
Now, send DAT from your metamask wallet to these three wallets. 
You are funding the coldkey wallets for use on the network.

## Deploy your own DLP smart contracts on Testnet

You're now ready to deploy a DLP smart contract, creating your own data DAO. You will then register two validators through the smart contract. The validators will be running proof of contribution. 

1. Install hardhat: https://hardhat.org/hardhat-runner/docs/getting-started#installation
2. Clone the DLP Smart Contract Repo: https://github.com/vana-com/vana-dlp-smart-contracts/tree/acdae3f4cf5b60426e779f5a3d220486d2a58b5a (this version is compatible with the latest vana-dlp-chatgpt)
3. Install dependencies

```bash
yarn install
```

4. Create an `.env` file for the smart contract repo. You will need the owner address and private key. 

```bash
jq -r '.address' ~/.vana/wallets/owner/coldkey
jq -r '.privateKey' ~/.vana/wallets/owner/coldkey
```
Copy the address and private key over to the .env file: 
```.env
DEPLOYER_PRIVATE_KEY=0x8...7
OWNER_ADDRESS=0x3....1
SATORI_RPC_URL=https://rpc.satori.vana.org
```

5. Deploy DataLiquidityPool and Token smart contracts. Make a note of:
   1. The DLP contract address. 
   2. The token contract address.
```bash
npx hardhat deploy --network satori --tags DLPDeploy
```

You will get output that looks like this:
```bash
...
DataLiquidityPoolToken deployed at: 0x...
DataLiquidityPool deployed at: 0x...
```

6. Congratulations, you've deployed the DLP smart contracts! You can confirm they're up by searching the address for each on the block explorer: https://satori.vanascan.io/address/<address\>.

7. In `vana-dlp-chatgpt/.env`, add an environment variable `DLP_SATORI_CONTRACT=0x...` and `DLP_TOKEN_SATORI_CONTRACT=0x` (replace with the deployed contract addresses for `DataLiquidityPool` and `DataLiquidityPoolToken` respectively).

8. Optional: If you made any changes to smart contracts code, verify the contracts, so you can interact with them directly in the block explorer:

```bash
npx hardhat verify --network satori <data_liquidity_pool_address>
npx hardhat verify --network satori <data_liquidity_pool_token_address> <owner_address>
```
If you didn't make changes, contracts should be verified automatically. You may need to wait a few minutes / refresh the page to see the verification status.

## Fund Validators with DLP specific token

In order to register validators, they must have some of your DLP tokens to stake. You can import your owner wallet into metamask and send tokens to the validator wallets. 
Use `DataLiquidityPoolToken` address to import your data liquidity pool tokens into metamask for your DLP owner hotkey.

Now transfer some DLP tokens from DLP owner hotkey to the validators coldkeys via metamask. 
For the purpose of this tutorial, you can transfer 10 tokens to each validator.
You can get validator coldkey addresses by running the following commands:
```bash
jq -r '.address' ~/.vana/wallets/validator_4000/coldkey
jq -r '.address' ~/.vana/wallets/validator_4001/coldkey
```

## Register Validators

Before validators can begin participating in the DLP, they must be registered. Run the following command to register the
validators.

```bash
# Note: we are using vanacli from this repo, and not the global vanacli to ensure DLP specific commands are available
./vanacli dlp register_validator --wallet.name=validator_4000 --wallet.hotkey=default --stake_amount=10
./vanacli dlp register_validator --wallet.name=validator_4001 --wallet.hotkey=default --stake_amount=10
```
These transactions must be accepted by calling the approveValidator function in the deployed smart contract.

## Approve Validators

To approve the validators:
```bash
./vanacli dlp approve_validator --wallet.name=owner --validator_address=$(jq -r '.address' ~/.vana/wallets/validator_4000/hotkeys/default)
./vanacli dlp approve_validator --wallet.name=owner --validator_address=$(jq -r '.address' ~/.vana/wallets/validator_4001/hotkeys/default)
```

Alternatively, you can approve validators through the explorer:

- Visit: https://satori.vanascan.io/address/<deployed_contract_address>?tab=write_contract
- Connect owner wallet created earlier
- Write contract tab
- approveValidator(newValidatorAddress)
- Repeat for as many validators as you have

## Run validator nodes
Now that validators are registered, you can run the validator nodes.

```bash
# Terminal 1 for validator_4000
poetry run python -m chatgpt.nodes.validator --node_server.external_ip=127.0.0.1 --node_server.port=4000 --wallet.name=validator_4000

# Terminal 2 for validator_4001
poetry run python -m chatgpt.nodes.validator --node_server.external_ip=127.0.0.1 --node_server.port=4001 --wallet.name=validator_4001
```

## Send addFile transaction
- Visit [the demo DLP UI](https://dlp-ui.vercel.vana.com/claim/upload), connect a wallet and upload a file.
    - Click on the gear icon to edit the DLP contract address and public part of the encryption key in the UI to match the deployed contract address and public key.
    - In the console logs, we will see the uploaded file URL and the encryption key.
- Paste the URL and encryption key in the `addFile` function in the deployed smart contract: https://satori.vanascan.io/address/<deployed_contract_address>?tab=write_contract
- Your validator should pick up the files, and write the file scores back on chain

# Running a validator on an existing DLP

In order to run a validator for an existing DLP, you will need to request a few things from the DLP owner:

* The private Redis credentials for the DLP validator network
* The private decryption key for the DLP validator network

Once you have these, you can set up your validator node. Get started with [the above instructions for DLP creators](#get-started), skipping the steps for deploying the smart contract.

The basic steps are:

1. Install the Vana CLI with `pip install vana`
2. Create one wallet with `vanacli wallet create`.
3. Fund the **hotkey** address of your wallet with some of the DLP's tokens. You can ask the DLP creator to send you some tokens.
4. Submit a validator registration transaction: `./vanacli dlp register_validator --wallet.name=validator_4000 --stake_amount 10`.
5. Ask the DLP owner to accept your registration request.
6. Run your validator node: `poetry run python -m chatgpt.nodes.validator --node_server.external_ip=127.0.0.1 --node_server.port=4000 --wallet.name=validator_4000`
7. Add a file to the DLP and watch your validator node score it! ([instructions above](#send-addfile-transaction))

> Note: if the DLP has been heavily modified from the starter template, you may not be able to register a validator with the CLI. In this case, you can register it through the [Satori explorer](https://satori.vanascan.io/).
> 1. Import your hotkey into a browser-compatible wallet like MetaMask.
> 2. Navigate to the Write proxy tab for the verified contract for the DLP in the Satori explorer. You can get this URL from the DLP owner. [Here is an example](https://satori.vanascan.io/address/0x4eFF0E1E2D6A5F549A1d3a8AAb5a175E4AD19a14?tab=write_proxy#76980d93).
> 3. Connect to your hotkey with the button at the bottom of the page.
> 4. Submit a validator registration transaction with the **public** addresses of your hotkey and coldkey as the validator and validator owner addresses, along with an amount of the required tokens to stake. Ensure you stake at least the minimum of the specific token required by the DLP.
