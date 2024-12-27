from blockchain import Block, Blockchain

def test_blockchain():
    bc = Blockchain()
    data_to_add = ["Genesis", "first test", "second test", "goodbye!"]
    for i, data in enumerate(data_to_add):
        bc.mine(Block(i, data=data))
        assert bc.isValid()
        
    bc.chain[2].data = "third test"
    assert not bc.isValid()

    bc.chain[2].data = "second test"
    assert bc.isValid()