import psycopg2
from psycopg2.extras import RealDictCursor

from config import config
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.conn = None
        self.connect()

    def connect(self):
        try:
            self.conn = psycopg2.connect(
                config.DATABASE_URI,
                cursor_factory=RealDictCursor
            )
            logger.info(f"Connected to database: {config.DB_HOST}")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def execute(self, query, params=None):
        cursor = self.conn.cursor()
        try:
            cursor.execute(query, params)
            self.conn.commit()
            return cursor
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Query failed: {e}")
            raise

    def query(self, query, params=None):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    def query_one(self, query, params=None):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()

    def close(self):
        if self.conn:
            self.conn.close()

db = Database()

class Customer:
    """
    Customer model supporting both V1 (single address field)
    and V2 (structured address fields)
    """

    def __init__(self, id=None, name=None, email=None,
                 address=None, street_address=None, city=None,
                 state=None, zip_code=None, created_at=None, updated_at=None):
        self.id = id
        self.name = name
        self.email = email

        # V1 fields
        self.address = address

        # V2 fields
        self.street_address = street_address
        self.city = city
        self.state = state
        self.zip_code = zip_code
        
        # Timestamp fields
        self.created_at = created_at
        self.updated_at = updated_at

    def save(self):
        """Save customer - handles both V1 and V2 schema"""
        if config.APP_VERSION == 'blue':
            # V1: Only use address field
            if self.id:
                db.execute("""
                    UPDATE customers
                    SET name = %s, email = %s, address = %s
                    WHERE id = %s
                """, (self.name, self.email, self.address, self.id))
            else:
                cursor = db.execute("""
                    INSERT INTO customers (name, email, address)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (self.name, self.email, self.address))
                self.id = cursor.fetchone()['id']

        elif config.APP_VERSION == 'green':
            # V2: Use structured fields but also write to address for compatibility
            full_address = f"{self.street_address}, {self.city}, {self.state}, {self.zip_code}"

            if self.id:
                db.execute("""
                    UPDATE customers
                    SET name = %s, email = %s,
                        street_address = %s, city = %s,
                        state = %s, zip_code = %s,
                        address = %s
                    WHERE id = %s
                """, (self.name, self.email, self.street_address,
                      self.city, self.state, self.zip_code,
                      full_address, self.id))
            else:
                cursor = db.execute("""
                    INSERT INTO customers
                    (name, email, street_address, city, state, zip_code, address)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (self.name, self.email, self.street_address,
                      self.city, self.state, self.zip_code, full_address))
                self.id = cursor.fetchone()['id']

        return self

    @classmethod
    def find(cls, customer_id):
        """Find customer by ID"""
        result = db.query_one("""
            SELECT * FROM customers WHERE id = %s
        """, (customer_id,))

        if result:
            return cls(**result)
        return None

    @classmethod
    def all(cls, limit=50):
        """Get all customers"""
        results = db.query("""
            SELECT * FROM customers
            ORDER BY id DESC
            LIMIT %s
        """, (limit,))

        return [cls(**row) for row in results]

    def to_dict(self):
        """Convert to dictionary based on version"""
        if config.APP_VERSION == 'blue':
            return {
                'id': self.id,
                'name': self.name,
                'email': self.email,
                'address': self.address
            }
        else:  # green
            return {
                'id': self.id,
                'name': self.name,
                'email': self.email,
                'address': {
                    'street': self.street_address,
                    'city': self.city,
                    'state': self.state,
                    'zip': self.zip_code
                }
            }
