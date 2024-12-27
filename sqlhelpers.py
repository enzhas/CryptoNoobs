from app import mysql, session
from blockchain import Block, Blockchain


def sql_raw(query):
    cur = mysql.connection.cursor()
    cur.execute(query)
    mysql.connection.commit()
    cur.close()


class InvalidTransactionException(Exception): 
    pass


class InsufficientFundsException(Exception): 
    pass


class Table():
    """
        Incapsulates logic of database
        Example initialization for blockchain table:
            Table("blockchain", "number", "hash", "previous", "data", "nonce")

    """
    def __init__(self, table_name, *args):
        self.table = table_name
        self.columns = f'({",".join(args)})'
        self.columnsList = args

        #if table does not already exist, create it.
        if isnewtable(table_name):
            create_data = ""
            for column in self.columnsList:
                create_data += f"{column} varchar(100),"

            sql_raw(f"CREATE TABLE {self.table}({create_data[:len(create_data)-1]})")

    def getall(self):
        cur = mysql.connection.cursor()
        result = cur.execute(f"SELECT * FROM {self.table}")
        data = cur.fetchall(); 
        return data

    def getone(self, search, value):
        data = {}
        cur = mysql.connection.cursor()
        result = cur.execute(f"SELECT * FROM {self.table} WHERE {search} = \"{value}\"")
        if result > 0: 
            data = cur.fetchone()
        cur.close()
        return data

    def deleteone(self, search, value):
        sql_raw(f"DELETE from {self.table} where {search} = \"{value}\"")

    def deleteall(self):
        self.drop()
        self.__init__(self.table, *self.columnsList)

    def drop(self):
        sql_raw(f"DROP TABLE {self.table}")

    def insert(self, *args):
        data = ""
        for arg in args:
            data += f"\"{str(arg)}\","

        sql_raw(f"INSERT INTO {self.table}{self.columns} VALUES({data[:len(data)-1]})")

def isnewtable(tableName):
    try:
        sql_raw(f"SELECT * from {tableName}")
    except:
        return True
    else:
        return False

def isnewuser(username):
    users = Table("users", "name", "email", "username", "password")
    data = users.getall()
    usernames = [user.get('username') for user in data]

    return False if username in usernames else True

def send_money(sender, recipient, amount):
    try: 
        amount = float(amount)
    except ValueError:
        raise InvalidTransactionException("Invalid Transaction.")

    if amount > get_balance(sender) and sender != "BANK":
        raise InsufficientFundsException("Insufficient Funds.")
    
    if sender == recipient or amount <= 0.00:
        raise InvalidTransactionException("Invalid Transaction.")

    if isnewuser(recipient):
        raise InvalidTransactionException("User Does Not Exist.")

    # add transaction and sync to database
    blockchain = get_blockchain()
    number = len(blockchain.chain) + 1
    data = f"{sender}-->{recipient}-->{amount}"
    blockchain.mine(Block(number, data=data))
    sync_blockchain(blockchain)

def get_balance(username):
    balance = 0.00
    blockchain = get_blockchain()

    for block in blockchain.chain:
        data = block.data.split("-->")
        if username == data[0]:
            balance -= float(data[2])
        elif username == data[1]:
            balance += float(data[2])
    return balance

def get_blockchain():
    """
        Get the existing blocks from database and return as Blockchain object
    """
    blockchain = Blockchain()
    blockchain_sql = Table("blockchain", "number", "hash", "previous", "data", "nonce")
    for b in blockchain_sql.getall():
        blockchain.add(Block(int(b.get('number')), b.get('previous'), b.get('data'), int(b.get('nonce'))))

    return blockchain

def sync_blockchain(blockchain):
    """
        Update blocks in database
    """
    blockchain_sql = Table("blockchain", "number", "hash", "previous", "data", "nonce")
    blockchain_sql.deleteall()

    for block in blockchain.chain:
        blockchain_sql.insert(str(block.number), block.hash(), block.previous_hash, block.data, block.nonce)