CREATE TABLE available_drivers (
    id SERIAL PRIMARY KEY,
    driver_id INTEGER NOT NULL,
    available_date DATE NOT NULL,
    status VARCHAR(32) NOT NULL -- np. 'available', 'day off'
);