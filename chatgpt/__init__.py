# The MIT License (MIT)
# Copyright © 2024 Corsali, Inc. dba Vana
import os

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

from dotenv import load_dotenv

load_dotenv()

__dlp_vana_contract__ = os.environ.get("DLP_CONTRACT_ADDRESS", "0xa0519f5ADc4e82729b21Ef1586d397260D9B9E45")
__dlp_moksha_contract__ = os.environ.get("DLP_MOKSHA_CONTRACT", "0xee4e3Fd107BE4097718B8aACFA3a8d2d9349C9a5")
__dlp_satori_contract__ = os.environ.get("DLP_SATORI_CONTRACT", "0x456e7fbc76e349ba21AEF05d32198016Ff33Bbe7")

__dlp_token_vana_contract__ = os.environ.get("DLP_TOKEN_VANA_CONTRACT", "0x3db29b7ED68Ca561794039B4D675f68fb64D6ac3")
__dlp_token_moksha_contract__ = os.environ.get("DLP_TOKEN_MOKSHA_CONTRACT", "0xF1925473bA6aa147EeB2529197C2704454D66b43")
__dlp_token_satori_contract__ = os.environ.get("DLP_TOKEN_SATORI_CONTRACT", "0x53201110BC771674B84435087Da20236277a2b4a")
