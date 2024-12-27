from app import session, get_db_connection
from blockchain import Block, Blockchain


def sql_raw(query, params=None):
    """Executes a raw SQL query with optional parameters."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            conn.commit()


class InvalidTransactionException(Exception):
    pass


class InsufficientFundsException(Exception):
    pass


class Table:
    """
    Encapsulates logic of database.
    Example initialization for blockchain table:
        Table("blockchain", "number", "hash", "previous", "data", "nonce")
    """
    def __init__(self, table_name, *args):
        self.table = table_name
        self.columns = f'({",".join(args)})'
        self.columns_list = args

        # Create the table if it doesn't exist
        if is_new_table(table_name):
            create_data = ", ".join([f"{column} VARCHAR(100)" for column in self.columns_list])
            sql_raw(f"CREATE TABLE IF NOT EXISTS {self.table} ({create_data});")

    def get_all(self):
        """Retrieve all rows from the table."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT * FROM {self.table};")
                return cur.fetchall()

    def get_one(self, search, value):
        """Retrieve a single row based on a condition."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT * FROM {self.table} WHERE {search} = %s;", (value,))
                return cur.fetchone()

    def delete_one(self, search, value):
        """Delete a single row based on a condition."""
        sql_raw(f"DELETE FROM {self.table} WHERE {search} = %s;", (value,))

    def delete_all(self):
        """Delete all rows from the table."""
        self.drop()
        self.__init__(self.table, *self.columns_list)

    def drop(self):
        """Drop the table."""
        sql_raw(f"DROP TABLE IF EXISTS {self.table};")

    def insert(self, *args):
        """Insert a row into the table."""
        placeholders = ', '.join(['%s'] * len(args))
        sql_raw(f"INSERT INTO {self.table} {self.columns} VALUES ({placeholders});", args)


def is_new_table(table_name):
    """Check if a table exists."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s);",
                (table_name,)
            )
            return not cur.fetchone()[0]


def is_new_user(username):
    """Check if a user exists."""
    users = Table("users", "name", "email", "username", "password")
    data = users.get_all()
    usernames = [user['username'] for user in data]
    return username not in usernames


def send_money(sender, recipient, amount):
    """Handle sending money between users."""
    try:
        amount = float(amount)
    except ValueError:
        raise InvalidTransactionException("Invalid transaction.")

    if amount > get_balance(sender) and sender != "BANK":
        raise InsufficientFundsException("Insufficient funds.")

    if sender == recipient or amount <= 0.00:
        raise InvalidTransactionException("Invalid transaction.")

    if is_new_user(recipient):
        raise InvalidTransactionException("User does not exist.")

    # Add transaction and sync to database
    blockchain = get_blockchain()
    number = len(blockchain.chain) + 1
    data = f"{sender}-->{recipient}-->{amount}"
    blockchain.mine(Block(number, data=data))
    sync_blockchain(blockchain)


def get_balance(username):
    """Get the balance of a user."""
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
    """Retrieve the blockchain from the database."""
    blockchain = Blockchain()
    blockchain_sql = Table("blockchain", "number", "hash", "previous", "data", "nonce")
    for b in blockchain_sql.get_all():
        blockchain.add(Block(int(b['number']), b['previous'], b['data'], int(b['nonce'])))

    return blockchain


def sync_blockchain(blockchain):
    """Sync the blockchain to the database."""
    blockchain_sql = Table("blockchain", "number", "hash", "previous", "data", "nonce")
    blockchain_sql.delete_all()

    for block in blockchain.chain:
        blockchain_sql.insert(block.number, block.hash(), block.previous_hash, block.data, block.nonce)
