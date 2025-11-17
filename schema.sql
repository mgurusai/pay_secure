-- Drop tables if they already exist
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS users;

-- User table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Transactions table
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    user_id INTEGER NOT NULL,
    encrypted_card TEXT NOT NULL,
    amount REAL NOT NULL,
    region VARCHAR(100) NOT NULL,
    risk_score REAL NOT NULL,
    status VARCHAR(50) NOT NULL, -- e.g., 'pending', 'success', 'failed'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);