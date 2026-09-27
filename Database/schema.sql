CREATE DATABASE IF NOT EXISTS parksmart CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE parksmart;

CREATE TABLE IF NOT EXISTS users (
  id int NOT NULL AUTO_INCREMENT,
  name varchar(100) DEFAULT NULL,
  phone varchar(15) DEFAULT NULL,
  email varchar(100) DEFAULT NULL,
  password varchar(100) DEFAULT NULL,
  role varchar(20) DEFAULT NULL,
  created_at timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS admins (
  id int NOT NULL AUTO_INCREMENT,
  name varchar(100) DEFAULT NULL,
  phone varchar(15) DEFAULT NULL,
  email varchar(100) DEFAULT NULL,
  password varchar(100) DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS parking (
  parking_id int NOT NULL AUTO_INCREMENT,
  parking_name varchar(100) DEFAULT NULL,
  location varchar(100) DEFAULT NULL,
  total_slots int DEFAULT NULL,
  created_at timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (parking_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS slots (
  slot_id int NOT NULL AUTO_INCREMENT,
  parking_id int DEFAULT NULL,
  slot_name varchar(20) DEFAULT NULL,
  status varchar(30) NOT NULL DEFAULT 'available',
  price int DEFAULT 50,
  PRIMARY KEY (slot_id),
  KEY parking_id (parking_id),
  CONSTRAINT slots_ibfk_1 FOREIGN KEY (parking_id) REFERENCES parking (parking_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS bookings (
  booking_id int NOT NULL AUTO_INCREMENT,
  user_id int DEFAULT NULL,
  slot_id int DEFAULT NULL,
  vehicle_type varchar(50) DEFAULT NULL,
  vehicle_number varchar(50) DEFAULT NULL,
  booking_date date DEFAULT NULL,
  start_time time DEFAULT NULL,
  end_time time DEFAULT NULL,
  status varchar(30) NOT NULL DEFAULT 'booked',
  created_at timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (booking_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS payments (
  payment_id int NOT NULL AUTO_INCREMENT,
  order_id varchar(100) DEFAULT NULL,
  user_id int NOT NULL,
  booking_id int NOT NULL,
  slot_id int NOT NULL,
  razorpay_order_id varchar(150) DEFAULT NULL,
  razorpay_payment_id varchar(150) DEFAULT NULL,
  razorpay_signature varchar(255) DEFAULT NULL,
  amount decimal(10,2) NOT NULL,
  currency varchar(10) NOT NULL DEFAULT 'INR',
  status varchar(50) NOT NULL DEFAULT 'pending',
  payment_method varchar(50) DEFAULT NULL,
  created_at timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (payment_id),
  KEY user_id (user_id),
  KEY booking_id (booking_id),
  KEY slot_id (slot_id),
  CONSTRAINT payments_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (id),
  CONSTRAINT payments_ibfk_2 FOREIGN KEY (booking_id) REFERENCES bookings (booking_id),
  CONSTRAINT payments_ibfk_3 FOREIGN KEY (slot_id) REFERENCES slots (slot_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS contact_messages (
  id int NOT NULL AUTO_INCREMENT,
  name varchar(100) DEFAULT NULL,
  email varchar(100) DEFAULT NULL,
  message text,
  created_at timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS password_resets (
  id int NOT NULL AUTO_INCREMENT,
  email varchar(100) DEFAULT NULL,
  new_password varchar(100) DEFAULT NULL,
  created_at timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS vehicles (
  vehicle_id int NOT NULL AUTO_INCREMENT,
  user_id int DEFAULT NULL,
  vehicle_number varchar(20) DEFAULT NULL,
  vehicle_type varchar(20) DEFAULT NULL,
  PRIMARY KEY (vehicle_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
