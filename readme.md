<p align="left">
  <img src="https://csfloat.com/assets/n-mini-logo.png" width="150">
</p>

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Integration: CSFloat.com](https://img.shields.io/badge/Integration-CSFloat.com-blue.svg)](https://csfloat.com/assets/n-mini-logo.png)

this script fetches trade data from the csfloat api and exports it to csv files. it creates two csv files:

- `csfloat_purchases.csv`: contains purchases (buyer role)
- `csfloat_sales.csv`: contains sales (seller role)

each csv contains the following columns:

- item name
- price
- float
- type
- date bought/sold
- csfloat transaction id

## the output!

<img width="916" alt="csfloat csv output" src="https://github.com/user-attachments/assets/1aa60422-0a77-4d15-8f2e-29ebe5741169" />

## getting started

### prerequisites

- python 3.7 or higher
- required python packages (listed in `requirements.txt`)

### installation

1. download the repo

2. install the required packages using pip:

   ```bash
   pip install -r requirements.txt
   ```

3. add your csfloat api key and steam id to the `.env` file:

   ```
   API_KEY=your_csfloat_api_key
   STEAM_ID=your_steam_id
   ```

### obtaining your csfloat api key

follow these steps to get your csfloat api key:

1. navigate to [csfloat profile](https://csfloat.com/profile).
2. go to the **developer** tab.
3. click **new api key** and save it.

### usage

run the script - it will fetch your trades and export them to the specified csv files.

## license

this project is licensed under the [mit license](LICENSE).

## acknowledgments

- created by loz
- csfloat team for allowing api usage and creating a great marketplace :)
