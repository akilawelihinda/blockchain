#!/usr/bin/env bash

# Kill any running Flask apps
kill $(ps aux | grep python3 | awk '{print $2}')

# Hardcoded Test App Ports (keep in sync with blockchainTests.py)
PORT_ONE=5000
PORT_TWO=5004

python3 blockchain.py $PORT_ONE &
python3 blockchain.py $PORT_TWO &
python3 blockchainTests.py
