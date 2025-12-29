DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS order_timeline_events;
DROP TABLE IF EXISTS transportation_orders;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS drivers;
DROP TABLE IF EXISTS vehicles;

CREATE TABLE vehicles (
    id INT PRIMARY KEY,
    make VARCHAR(50),
    model VARCHAR(50),
    year INT,
    fuel_tank_capacity DECIMAL(5,1)
);

CREATE TABLE drivers (
    id INT PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100),
    phone VARCHAR(20),
    contract_type VARCHAR(20),
    status VARCHAR(20)
);

CREATE TABLE customers (
    id INT PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100),
    phone VARCHAR(20),
    customer_type VARCHAR(20),
    address VARCHAR(255)
);

CREATE TABLE transportation_orders (
    id INT PRIMARY KEY,
    order_number VARCHAR(20) UNIQUE NOT NULL,
    customer_id INT NOT NULL,
    driver_id INT,
    vehicle_id INT,
    status VARCHAR(20) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    order_date TIMESTAMP NOT NULL,
    expected_delivery DATE,
    shipping_address VARCHAR(255),
    shipping_city VARCHAR(100),
    shipping_state VARCHAR(50),
    shipping_zip_code VARCHAR(20),
    shipping_method VARCHAR(50),
    tracking_number VARCHAR(50),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (driver_id) REFERENCES drivers(id),
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
);

-- Table for daily driver availability
CREATE TABLE available_drivers (
    id INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    driver_id INT NOT NULL,
    available_date DATE NOT NULL,
    is_day_off BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (driver_id) REFERENCES drivers(id)
);

-- Table for daily vehicle availability
CREATE TABLE available_vehicles (
    id INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    vehicle_id INT NOT NULL,
    available_date DATE NOT NULL,
    is_service_day BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
);

CREATE TABLE order_timeline_events (
    id INT PRIMARY KEY,
    order_id INT NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_timestamp TIMESTAMP NOT NULL,
    title VARCHAR(100),
    description TEXT,
    executed_by VARCHAR(100),
    FOREIGN KEY (order_id) REFERENCES transportation_orders(id)
);

CREATE TABLE order_items (
    id INT PRIMARY KEY,
    order_id INT NOT NULL,
    product_name VARCHAR(100) NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    item_type VARCHAR(20) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES transportation_orders(id)
);

CREATE INDEX idx_timeline_order ON order_timeline_events(order_id);
CREATE INDEX idx_items_order ON order_items(order_id);
CREATE INDEX idx_orders_customer ON transportation_orders(customer_id);
CREATE INDEX idx_orders_status ON transportation_orders(status);
