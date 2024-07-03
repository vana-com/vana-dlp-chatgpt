<div align="center">

# **Hot Dog Data Liquidity Pool** <!-- omit in toc -->
[![Discord Chat](https://img.shields.io/discord/308323056592486420.svg)](https://discord.gg/xx98TSE8)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

### The first decentralized network for user-owned data <!-- omit in toc -->

[Discord](https://discord.gg/xx98TSE8) • [Network](https://satori.vanascan.io)

</div>

We believe in an open internet where users own their data and the AI models they contribute to.

AI models should be created more like open source software: iteratively by a community. To make this possible, researchers need access to the world's best datasets that are held captive across walled gardens. Users can break down these walled gardens by exporting their own data.

We are building towards a user-owned foundation model, trained by 100M users who contribute their data and compute.

## Getting Started

> <b>Minimum hardware requirements:</b>  
Local: 1 CPU, 8GB RAM, 10GB free disk space  
AWS: t3.large, m5.large or better  
GCP: n1-standard-2 or better  

To get started with the Hot Dog DLP, follow these steps:

1. Clone the repository:
```shell
git clone https://github.com/vana-com/vana-dlp-hotdog.git
```

2. Install the required dependencies using poetry:
```shell
poetry install
poetry run setup
```
3. Configure the environment variables by copying and modifying the `.env.example` file:

4. Run the application:
```shell
poetry run python -m hotdog.nodes.validator
```

## Generate validator encryption keys

To generate the encryption keypair for DLP validators:

1. Run the keygen script:
    ```bash
    ./keygen.sh
    ```

2. Follow the prompts to enter your name, email, and key expiration.

3. The script generates four files:
    - `public_key.asc` and `public_key_base64.asc` (for UI)
    - `private_key.asc` and `private_key_base64.asc` (for validators)

4. Copy the contents of `private_key_base64.asc` to `vana-dlp-hotdog/.env` under `PRIVATE_FILE_ENCRYPTION_PUBLIC_KEY_BASE64`.

5. Paste the public key into the [DLP Demo UI](https://dlp-ui.vercel.vana.com/claim/upload) (settings icon on the top right)

## Using the CLI
The Vana command line interface (`vanacli`) is the primary command line tool for interacting with the Vana network.
It can be used to deploy nodes, manage wallets, stake/unstake, nominate, transfer tokens, and more.

### (Optional) Setup vanacli
To install vanacli system-wide, run the following command:

```shell
pip install vana
```

## Run Tests
To run the tests, you can use the following command. This is especially useful for local development.

```bash
pytest
```

### Basic Usage

To get the list of all the available commands and their descriptions, you can use:

```bash
vanacli <command> <command args>

vana cli v0.0.1

positional arguments:
  {root,r,roots,wallet,w,wallets,stake,st,stakes,sudo,su,sudos,info,i}
    root (r, roots)     Commands for managing and viewing the root network.
    wallet (w, wallets)
                        Commands for managing and viewing wallets.
    stake (st, stakes)  Commands for staking and removing stake from hotkey accounts.
    sudo (su, sudos)    Commands for DLP management
    info (i)            Instructions for enabling autocompletion for the CLI.

options:
  -h, --help            show this help message and exit
  --print-completion {bash,zsh,tcsh}
                         Print shell tab completion script
```

# Wallets

Wallets are the core ownership and identity technology around which all functions on Vana are carried out.
Vana wallets consists of a coldkey and hotkey where the coldkey may contain many hotkeys, while each hotkey can only belong to a single coldkey.
Coldkeys store funds securely, and operate functions such as transfers and staking, while hotkeys are used for all online operations such as signing queries, running miners and validating.


```bash
$ vanacli wallet --help

usage: vanacli <command> <command args> wallet [-h] {balance,create,new_hotkey,new_coldkey,regen_coldkey,regen_coldkeypub,regen_hotkey,update,history} ...

positional arguments:
  {balance,create,new_hotkey,new_coldkey,regen_coldkey,regen_coldkeypub,regen_hotkey,update,history}
                        Commands for managing and viewing wallets.
    balance             Checks the balance of the wallet.
    create              Creates a new coldkey (for containing balance) under the specified path.
    new_hotkey          Creates a new hotkey (for running a miner) under the specified path.
    new_coldkey         Creates a new coldkey (for containing balance) under the specified path.
    regen_coldkey       Regenerates a coldkey from a passed value
    regen_coldkeypub    Regenerates a coldkeypub from the public part of the coldkey.
    regen_hotkey        Regenerates a hotkey from a passed mnemonic
    update              Updates the wallet security using NaCL instead of ansible vault.
    history             Fetch transfer history associated with the provided wallet

options:
  -h, --help            show this help message and exit
```

You should be able to view your keys by navigating to ~/.vana/wallets or viewed by running ```vanacli wallet list```
```bash
$ tree ~/.vana/
    .vana/                      # Root directory.
        wallets/                # The folder containing all vana wallets.
            default/            # The name of your wallet, "default"
                coldkey         # You encrypted coldkey.
                coldkeypub.txt  # Your coldkey public address
                hotkeys/        # The folder containing all of your hotkeys.
                    default     # You unencrypted hotkey information.
```
Your default wallet ```Wallet (default, default, ~/.vana/wallets/)``` is always used unless you specify otherwise.
Be sure to store your mnemonics safely.
If you lose your password to your wallet, or the access to the machine where the wallet is stored, you can always regenerate the coldkey using the mnemonic you saved from above.
```bash
$ vanacli wallet regen_coldkey --mnemonic **** *** **** **** ***** **** *** **** **** **** ***** *****
```

## License
The MIT License (MIT)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
