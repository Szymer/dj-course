CREATE TABLE available_vehicles (
    id SERIAL PRIMARY KEY,
    vehicle_id INTEGER NOT NULL,
    available_date DATE NOT NULL,
    status VARCHAR(32) NOT NULL -- np. 'available', 'service'
);