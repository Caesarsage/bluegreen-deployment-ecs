-- Initial database schema (V1)
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample data
INSERT INTO
    customers (name, email, address)
VALUES (
        'John Doe',
        'john@example.com',
        '123 Main St, New York, NY, 10001'
    ),
    (
        'Jane Smith',
        'jane@example.com',
        '456 Oak Ave, Los Angeles, CA, 90001'
    ),
    (
        'Bob Johnson',
        'bob@example.com',
        '789 Pine Rd, Chicago, IL, 60601'
    ),
    (
        'Alice Williams',
        'alice@example.com',
        '321 Elm St, Houston, TX, 77001'
    ),
    (
        'Charlie Brown',
        'charlie@example.com',
        '654 Maple Dr, Phoenix, AZ, 85001'
    );

-- Create index
CREATE INDEX idx_customers_email ON customers (email);
