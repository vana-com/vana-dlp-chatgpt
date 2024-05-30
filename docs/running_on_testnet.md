# Running the ChatGPT DLP on Testnet

This tutorial shows how to use the Vana Satori Testnet to get started with the ChatGPT Data Liquidity Pool.

Incentive mechanisms running on the testnet are open to anyone, and although these mechanisms on testnet do not emit
real DAT, they cost you test DAT which you must create.

### Words of Wisdom

- Do not expose your private keys.
- Only use your testnet wallet.
- Do not reuse the password of your mainnet wallet.

## Prerequisites

Before proceeding further, make sure that you have installed the project dependencies:

```bash
poetry install
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

Wallets must be funded for registering and validating on the testnet. To fund your wallets, you can use the testnet
faucet available at https://faucet.vana.com, or ask a DAT holder to send you some test DAT tokens. The hotkey must be
funded, but funding the coldkey is optional.

## Deploy a copy of the ChatGPT DLP smart contracts on Testnet

To ensure your validators do not interfere with other ChatGPT validators, you must deploy a copy of the ChatGPT DLP
smart contracts on the testnet and register your validators through that smart contract.

1. Install hardhat: https://hardhat.org/hardhat-runner/docs/getting-started#installation
2. Clone the DLP Smart Contract Repo: https://github.com/vana-com/dlp-smart-contracts/
3. Install dependencies

```bash
yarn install
```

4. Create an `.env` file
```.env
DEPLOYER_PRIVATE_KEY=8...7
OWNER_ADDRESS=0x3....1
BACKEND_WALLET_ADDRESS=0x06...5
VANA_TESTNET_URL=http://34.172.243.254:8545
VANA_TESTNET_API_URL=http://vanascan.io/api
VANA_TESTNET_BROWSER_URL=http://vanascan.io/
```
5. Deploy smart contract

```bash
npx hardhat deploy --network vanaTestnet --tags DLPDeploy
```

6. Copy the deployed smart contract address

## Register Validators

Before validators can begin participating in the DLP, they must be registered. Run the following command to register the
validators.

```bash
poetry run python -m chatgpt.nodes.validator --wallet.name=validator_4000 --dlp.register 0.001
poetry run python -m chatgpt.nodes.validator --wallet.name=validator_4001 --dlp.register 0.001
```

Afterwards, the transaction must be accepted by calling the acceptValidator function in the deployed smart contract, which can be done like so:

- Visit: https://satori.vanascan.io/address/<deployed_contract_address>?tab=write_contract
- Connect owner wallet created earlier
- Write contract tab
- acceptValidator(newValidatorAddress)
- Repeat for as many validators

## Run validator nodes
Now that validators are registered, you can run the validator nodes.

```bash
# Terminal 1 for validator_4000
poetry run python -m chatgpt.nodes.validator --node_server.external_ip=127.0.0.1 --node_server.port=4000 --wallet.name=validator_4000

# Terminal 2 for validator_4001
poetry run python -m chatgpt.nodes.validator --node_server.external_ip=127.0.0.1 --node_server.port=4001 --wallet.name=validator_4001
```

## Send addFile transaction
- Visit [GPT Data DAO](https://www.gptdatadao.org/claim/upload), connect a wallet and upload a file. In the console logs, we will see the uploaded file URL and the encryption key. 
- Paste the URL and encryption key in the `addFile` function in the deployed smart contract: https://satori.vanascan.io/address/<deployed_contract_address>?tab=write_contract
- Your validator should pick up the files, and write the file scores back on chain
