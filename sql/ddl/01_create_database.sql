-- Stage 2: Create MySQL database for fraud intelligence platform
-- This script creates the database if it doesn't exist.

CREATE DATABASE IF NOT EXISTS fraud_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE fraud_db;

