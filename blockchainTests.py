import unittest
import blockchain
from flask import json, jsonify

class TestBlockChain(unittest.TestCase):
    def setUp(self):
        blockchain.app.testing = True
        self.app = blockchain.app.test_client()

    def test_initial_chain(self):
        response = json.loads(self.app.get('/chain').data)
        self.assertEqual(response['length'], 1)

    def test_new_transaction(self):
        self.app.post('/transactions/new',
            data=dict(
                sender= 'sender_id',
                recipient= 'recipient_id',
                amount= 10
            )
        )
        self.app.get('/mine')
        response = json.loads(self.app.get('/chain').data)
        self.assertEqual(response['length'], 2)

if __name__ == '__main__':
    unittest.main()
