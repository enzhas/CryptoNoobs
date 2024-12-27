import psycopg2
from psycopg2.extras import DictCursor

DATABASE_URL = "postgres://neondb_owner:qYeDo92VtPAI@ep-sparkling-surf-a5683xkm-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=DictCursor)
