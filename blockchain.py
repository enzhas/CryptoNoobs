from hashlib import sha256

def gethash(*args):
    plaintext = ''.join(str(x) for x in args).encode('utf-8')
    return sha256(plaintext).hexdigest()


class Block():
    def __init__(self,number=0, previous_hash="0"*64, data=None, nonce=0):
        self.data = data
        self.number = number
        self.previous_hash = previous_hash
        self.nonce = nonce

    def hash(self):
        return gethash(self.number, self.previous_hash, self.data, self.nonce)

    def __str__(self):
        return f"Block#: {self.number}\nHash: {self.hash()}\nPrevious: {self.previous_hash}\nData: {self.data}\nNonce: {self.nonce}\n"



class Blockchain():
    difficulty = 4

    def __init__(self):
        self.chain = []

    def add(self, block):
        self.chain.append(block)

    def remove(self, block):
        self.chain.remove(block)

    def mine(self, block):
        try: 
            block.previous_hash = self.chain[-1].hash()
        except IndexError: 
            pass

        while True:
            if block.hash()[:self.difficulty] == "0" * self.difficulty:
                self.add(block)
                break
            block.nonce += 1

    def isValid(self):
        for i in range(1, len(self.chain)):
            previous = self.chain[i].previous_hash
            current = self.chain[i-1].hash()
            if previous != current or current[:self.difficulty] != "0"*self.difficulty:
                return False
        return True
