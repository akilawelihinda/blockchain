import unittest
import blockchain
from flask import json
import tempfile
import requests
import os
import sys

# Hardcoded Test App Ports (keep in sync with test_script.sh)
PORT_ONE = 5000
PORT_TWO = 5004

serverOne = "http://localhost:" + str(PORT_ONE)
serverTwo = "http://localhost:" + str(PORT_TWO)

def add_new_transaction(server):
    response = requests.post(server + '/transactions/new',
        data=json.dumps(dict(
            sender= 'sender_id',
            recipient= 'recipient_id',
            amount= 10
        ))
    )
    assert(response.status_code == 201)
    requests.get(server + '/mine')
    return requests.get(server + '/chain').json()


class TestBlockChainBasic(unittest.TestCase):
    def setUp(self):
        requests.get(serverOne + '/reset').json()
        requests.get(serverTwo + '/reset').json()

    def test_initial_chain(self):
        response = requests.get(serverOne + '/chain').json()
        self.assertEqual(response['length'], 1)

    def test_new_transaction(self):
        response = add_new_transaction(serverOne)
        response = add_new_transaction(serverOne)
        self.assertEqual(response['length'], 3)

    def test_register_new_node(self):
        response = requests.post(serverOne + '/nodes/register',
            data=json.dumps(dict(
                nodes=['localhost:5000']
            ))
        )
        total_nodes = response.json()['total_nodes']
        self.assertEqual(len(total_nodes), 1)

    def test_consensus_algorithm(self):
        response = add_new_transaction(serverOne)
        self.assertEqual(response['length'], 2)
        response = requests.get(serverTwo + '/chain').json()
        self.assertEqual(response['length'], 1)
        response = requests.get(serverOne + '/nodes/resolve').json()
        self.assertEqual(len(response['chain']), 2)


if __name__ == '__main__':
    unittest.main()
