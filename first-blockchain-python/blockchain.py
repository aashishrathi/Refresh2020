import hashlib
import json
from textwrap import dedent
from time import time
from uuid import uuid4
from urllib.parse import urlparse
import requests

from flask import Flask, jsonify, request


"""
Pseudocode
==========

Blockchain = {list(Block), list(Transaction)}
Block = {idx, timestamp, list(Transaction), proof, hash(prevBlock)}
Transaction = {sender, recipient, amount}}

"""


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()

        #Genesis
        self.new_block(previous_hash=1, proof=100)

    def register_node(self, address):
        """
        Add a new node to the set
        :param address: <str> URL
        :return: None
        """
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain):
        """
        Determine if a chain is valid
        :param chain: <list> A blockchain
        :return: <bool> True if valid
        """

        last_block = chain[0]
        idx = 1

        while idx < len(chain):
            block = chain[idx]
            #Confirm hash
            if block['previous_hash'] != self.hash(last_block):
                return False
            #Confirm POW
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            idx += 1

        return True

    def resolve_conflicts(self):
        """
        Consensus Algorithm, longest valid one wins
        :return: <bool> True if chain replaces, False if not
        """

        neighbours = self.nodes
        new_chain = None

        max_length = len(self.chain)

        for node in neighbours:
            response = request.get(f'http://{node}/chain')

            if response.states_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        if new_chain:
            self.chain = new_chain
            return True

        return False


    def new_block(self, proof, previous_hash=None):
        """
        Create a new Block in the blockchain
        :param proof: <int> The proof given by the Proof of Work algorithm
        :param previous_hash: (Optional) <str> Hash of previous Block
        :return: <dict> New Block
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        #Reset current transactions list
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Create new transaction and add to new mined block in the chain
        :param sender: <str> Address of the Sender
        :param recipient: <str> Address of the Recipient
        :param amount: <int> Amount
        :return: <int> The index of the Block that will hold this transaction
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        })

        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        #Returns the SHA256 hash of a block
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property #makes it an attribute with a getter and setter
    def last_block(self):
        #Returns the last block in a chain
        return self.chain[-1]

    def proof_of_work(self, last_proof):
        """
        Find number p which when hashed with the previous proof generates a number with 4 leading 0s
        :param last_proof: <int>
        :return: <int> next_proof
        """
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Check if hash(pp') contains 4 leading 0s
        :param last_proof: <int> p'
        :param proof: <int> p
        :return: <bool>
        """
        test_string = f'{last_proof}{proof}'.encode()
        test_hash = hashlib.sha256(test_string).hexdigest()
        return test_hash[:4] == "0000"



#Create Node
app = Flask(__name__)

#Unique Global ID
node_id = str(uuid4()).replace('-','')

#Create the blockchain
blockchain = Blockchain()

@app.route('/mine', methods=["GET"])
def mine():
    # We run the proof of work algorithm to get the next proof...
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # We must receive a reward for finding the proof.
    # NOTE: The correct way would be to put this in the list of current_transactions,
    # mine on those, and then publish that block with the proof
    # The sender is "0" to signify that this node has mined a new coin.
    blockchain.new_transaction(
        sender="0",
        recipient=node_id,
        amount=1,
    )

    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200

@app.route('/transactions/new', methods=["POST"])
def new_transactions():
    values = request.get_json()

    #Checking that required fields are in the POST data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing Values', 400

    #Create a new transaction
    index = blockchain.new_transaction(values['sender'],
                                       values['recipient'],
                                       values['amount'])

    response = {'message': f'Transaction will be added to Block{index}'}
    return jsonify(response), 201

@app.route('/chain', methods=["GET"])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)