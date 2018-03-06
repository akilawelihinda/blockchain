import hashlib
import json
import sys
from time import time
from uuid import uuid4
from textwrap import dedent
from urllib.parse import urlparse
import requests

from flask import Flask, jsonify, request

class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.new_block(proof=369, previous_hash=0xdeadbeef)
        self.nodes = set()

    def register_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    # Creates a new block and adds it to the chain
    # Only specify previous hash if creating genesis block
    def new_block(self, proof, previous_hash = None):
        block = {
            'index': len(self.chain) + 1,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
            'timestamp': time(),
            'transactions': self.current_transactions,
        }

        self.current_transactions = []
        self.chain.append(block)
        return block

    # Adds a new transaction to the list of transactions
    # Returns index of block which will contain the new transaction
    def new_transaction(self, sender, recipient, amount):
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        })
        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, last_proof):
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def valid_chain(self, chain):
        current_index = 1
        while(current_index < len(chain)):
            current_block = chain[current_index]
            previous_block = chain[current_index-1]
            if not self.valid_proof(previous_block['proof'], current_block['proof']):
                return False
            if (self.hash(previous_block) != current_block['previous_hash']):
                return False
            current_index += 1
        return True

    # Consensus algorithm: Pick longest valid chain from neighboring nodes
    def resolve_conflicts(self):
        neighbors = self.nodes
        new_chain = None
        max_len = len(self.chain)

        for neighbor in neighbors:
             response = requests.get(f'http://{neighbor}/chain')
             if response.status_code == 200:
                 length = response.json()['length']
                 chain = response.json()['chain']
                 if length > max_len and self.valid_chain(chain):
                     new_chain = chain
                     max_len = length

        if new_chain:
            self.chain = new_chain
            return True

        return False

# Flask logic
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = Blockchain()


@app.route('/mine', methods=['GET'])
def mine():
    blockchain.new_transaction("coinbase", node_identifier, 1)
    last_proof = blockchain.last_block['proof']
    current_proof = blockchain.proof_of_work(last_proof)
    block = blockchain.new_block(current_proof)
    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json(force=True)
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400
    index = blockchain.new_transaction(values.get('sender'), values.get('recipient'), values.get('amount'))
    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json(force=True)
    nodes = values.get("nodes")
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()
    if replaced:
        response = {
            'message': 'This node\'s chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'This node\'s chain is authoritative',
            'chain': blockchain.chain
        }

    return jsonify(response), 200

if __name__ == '__main__':
    if(len(sys.argv) < 2):
        sys.exit("Invalid number of arguements")
    chosen_port = int(sys.argv[1])
    app.run(host='127.0.0.1', port=chosen_port)
