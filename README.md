# Grail Program 2024 Analytics Dashboard

This project is a web-based analytics dashboard for the Grail Program 2024, which aims to visualize and analyze the on-chain bridging activity on the NEAR blockchain. The dashboard is built using Dash and Plotly, providing an interactive and user-friendly interface for exploring various metrics and insights.

## Features

- **Overview Tab**: Displays total bridged volume, daily bridging volume, and capital flow (inbound vs. outbound) during the program period. Also shows the top source chains and top bridged tokens.
- **User Behavior Tab**: Shows user retention rates and holding period length distribution. Includes a cohort analysis of weekly bridging volume during the program.
- **Grail Program Impact Tab**: Compares bridging volume before, during, and after the program, normalized to weekly volume. Highlights significant changes and includes an anomaly detection chart.

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/JupyterNoteFiend/Flipside-Challenge.git
    cd Flipside-Challenge
    ```

2. Create and activate a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate   # On Windows, use `venv\Scripts\activate`
    ```

3. Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

4. Ensure the data file `NEAR_01012024_07282024_data.xlsx` is in the project directory.

## Running the Dashboard

Run the following command to start the Dash server:
```bash
python NearBridgeChallenge.py
