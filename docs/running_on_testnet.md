# Running the ChatGPT DLP on Testnet

This tutorial shows how to use the Vana Satori Testnet to get started with the ChatGPT Data Liquidity Pool. You will: 
- Deploy a data liquidity pool smart contract to create your own data DAO
- Register validators to run proof of contribution, ensuring chatGPT data quality
- Submit chatGPT data to test that proof of contribution is working

Note that you will not be rewarded in GPTDAT - this testnet tutorial just writes scores onchain, but does not yet support claiming GPTDAT. 

By continuing in this tutorial, you agree to the following
- The participant acknowledges that the testnet is provided solely on an “as is” and “as available” basis for experimental purposes. The functionality of the testnet remains experimental and has not undergone comprehensive testing.
- VANA expressly disclaims any representations or warranties regarding the operability, accuracy, or reliability of the testnet.
- The participant agrees that participation in the testnet neither constitutes an investment nor implies an expectation of profit. There is no promise or implication of future value or potential return on any contributions of resources, time, or effort.
- I confirm that I am not a citizen of the United States or Canada, nor am I a citizen or resident of any nation or region subjected to comprehensive sanctions, including but not limited to Cuba, North Korea, Crimea, Donetsk, Luhansk, Iran, or Syria.

### Testnet disclaimers

Incentive mechanisms running on the testnet are open to anyone, and although these mechanisms on testnet do not emit
real DAT, they cost you test DAT which you must get from a faucet. Testnet tokens, including testnet DAT and dataset-specific tokens like testnet GPTDAT, have no value. 

### Words of Wisdom

- Do not expose your private keys or mnemonic phrase.
- Do not reuse the password of your mainnet wallet. 

## Prerequisites

Make sure to install the project dependencies:

```bash
poetry install
```

## Setup vanacli
Clone and set up the [vana-framework](https://github.com/vana-com/vana-framework) repository to access the `vanacli`

```bash
git clone https://github.com/vana-com/vana-framework.git
cd vana-framework
poetry install
python setup_vanacli.py
> vanacli command set up successfully!
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

Get your wallet address for all three accounts
```bash
> jq -r '.address' ~/.vana/wallets/owner/hotkeys/default
> jq -r '.address' ~/.vana/wallets/validator_4000/hotkeys/default
> jq -r '.address' ~/.vana/wallets/validator_4001/hotkeys/default
```

Use the testnet faucet available at https://faucet.vana.com to fund your wallets, or ask a DAT holder to send you some test DAT tokens.

For convenience, you may want to get testnet DAT sent over to your metamask wallet, then send DAT from your metamask wallet to these three wallets. 

You are funding the hotkey wallets for use on the network.

## Deploy your own DLP smart contracts on Testnet

You're now ready to deploy a DLP smart contract, creating your own data DAO. You will then register two validators through the smart contract. The validators will be running proof of contribution. 

1. Install hardhat: https://hardhat.org/hardhat-runner/docs/getting-started#installation
2. Clone the DLP Smart Contract Repo: https://github.com/vana-com/vana-dlp-smart-contracts
3. Install dependencies

```bash
yarn install
```

4. Create an `.env` file for the smart contract repo. You will need the owner address and private key. 

```bash
cat ~/.vana/wallets/owner/hotkeys/default
```
Copy the address and private key over to the .env file: 
```.env
DEPLOYER_PRIVATE_KEY=0x8...7
OWNER_ADDRESS=0x3....1
VANA_TESTNET_URL=http://rpc.satori.vana.com
```
5. Deploy smart contract

```bash
npx hardhat deploy --network vanaTestnet --tags DLPDeploy
```

6. Congratulations, you've deployed the DLP smart contract. You can confirm it's up by searching the address on the block explorer: https://satori.vanascan.io/ . Copy the deployed smart contract address. 

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
