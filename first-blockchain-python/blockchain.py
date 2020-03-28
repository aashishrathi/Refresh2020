import hashlib
import json
from time import time


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

        #Genesis
        self.new_block(previous_hash=1, proof=100)

    def new_block(self, previous_hash=None, proof):
        """
        Create a new Block in the Blockchain
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
        #Returns the hash of a block
        pass

    @property #makes it an attribute with a getter and setter
    def last_block(self):
        #Returns the last block in a chain
        pass