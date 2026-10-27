-- ========================================================
-- 餐廳預約與點餐系統 — 資料庫 Schema (MySQL)
-- 依據 SPEC.md 第 7 節 資料庫規格
-- ========================================================

CREATE DATABASE IF NOT EXISTS `restaurant_db` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `restaurant_db`;

-- --------------------------------------------------------
-- 1. Users (會員及管理員帳號)
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS `users` (
    `user_id` BIGINT NOT NULL AUTO_INCREMENT,
    `email` VARCHAR(255) NOT NULL,
    `password_hash` VARCHAR(255) NOT NULL,
    `display_name` VARCHAR(100) NOT NULL,
    `role` VARCHAR(20) NOT NULL DEFAULT 'MEMBER' COMMENT 'MEMBER, ADMIN, STAFF',
    `status` VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' COMMENT 'ACTIVE, SUSPENDED, DELETED',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`user_id`),
    UNIQUE KEY `uk_users_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 2. DiningTables (餐廳桌位)
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS `dining_tables` (
    `table_id` BIGINT NOT NULL AUTO_INCREMENT,
    `table_name` VARCHAR(50) NOT NULL,
    `capacity` INT NOT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' COMMENT 'ACTIVE, MAINTENANCE, DISABLED',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`table_id`),
    KEY `idx_tables_capacity_status` (`capacity`, `status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 3. Reservations (預約主檔)
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS `reservations` (
    `reservation_id` BIGINT NOT NULL AUTO_INCREMENT,
    `reservation_code` VARCHAR(32) NOT NULL,
    `user_id` BIGINT NULL,
    `party_size` INT NOT NULL,
    `start_at` DATETIME NOT NULL,
    `end_at` DATETIME NOT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'CONFIRMED' COMMENT 'PENDING, CONFIRMED, COMPLETED, CANCELLED',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`reservation_id`),
    UNIQUE KEY `uk_reservation_code` (`reservation_code`),
    KEY `idx_reservations_user` (`user_id`),
    KEY `idx_reservations_time_status` (`start_at`, `end_at`, `status`),
    CONSTRAINT `fk_reservations_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 4. ReservationGuests (訪客預約聯絡資料)
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS `reservation_guests` (
    `reservation_id` BIGINT NOT NULL,
    `guest_name` VARCHAR(100) NOT NULL,
    `guest_phone` VARCHAR(30) NOT NULL,
    PRIMARY KEY (`reservation_id`),
    KEY `idx_guest_phone` (`guest_phone`),
    CONSTRAINT `fk_reservation_guests_reservation` FOREIGN KEY (`reservation_id`) REFERENCES `reservations` (`reservation_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 5. ReservationTables (預約與桌位關聯)
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS `reservation_tables` (
    `reservation_id` BIGINT NOT NULL,
    `table_id` BIGINT NOT NULL,
    PRIMARY KEY (`reservation_id`, `table_id`),
    KEY `idx_res_tables_table` (`table_id`),
    CONSTRAINT `fk_res_tables_reservation` FOREIGN KEY (`reservation_id`) REFERENCES `reservations` (`reservation_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_res_tables_table` FOREIGN KEY (`table_id`) REFERENCES `dining_tables` (`table_id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 6. MenuCategories (餐點分類)
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS `menu_categories` (
    `category_id` BIGINT NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' COMMENT 'ACTIVE, HIDDEN',
    `sort_order` INT NOT NULL DEFAULT 0,
    PRIMARY KEY (`category_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 7. MenuItems (餐點資料)
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS `menu_items` (
    `item_id` BIGINT NOT NULL AUTO_INCREMENT,
    `category_id` BIGINT NOT NULL,
    `name` VARCHAR(150) NOT NULL,
    `description` TEXT NULL,
    `price` DECIMAL(10, 2) NOT NULL,
    `is_available` TINYINT(1) NOT NULL DEFAULT 1,
    `image_url` VARCHAR(255) NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`item_id`),
    KEY `idx_menu_items_category` (`category_id`),
    KEY `idx_menu_items_available` (`is_available`),
    CONSTRAINT `fk_menu_items_category` FOREIGN KEY (`category_id`) REFERENCES `menu_categories` (`category_id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 8. Orders (訂單主檔)
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS `orders` (
    `order_id` BIGINT NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT NULL,
    `reservation_id` BIGINT NULL,
    `table_id` BIGINT NULL,
    `order_type` VARCHAR(20) NOT NULL DEFAULT 'DINE_IN' COMMENT 'PRE_ORDER, DINE_IN',
    `status` VARCHAR(20) NOT NULL DEFAULT 'PENDING' COMMENT 'PENDING, CONFIRMED, PREPARING, READY, COMPLETED, CANCELLED',
    `total_amount` DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`order_id`),
    KEY `idx_orders_user` (`user_id`),
    KEY `idx_orders_reservation` (`reservation_id`),
    KEY `idx_orders_table` (`table_id`),
    KEY `idx_orders_status` (`status`),
    CONSTRAINT `fk_orders_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE SET NULL,
    CONSTRAINT `fk_orders_reservation` FOREIGN KEY (`reservation_id`) REFERENCES `reservations` (`reservation_id`) ON DELETE SET NULL,
    CONSTRAINT `fk_orders_table` FOREIGN KEY (`table_id`) REFERENCES `dining_tables` (`table_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 9. OrderItems (訂單明細)
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS `order_items` (
    `order_item_id` BIGINT NOT NULL AUTO_INCREMENT,
    `order_id` BIGINT NOT NULL,
    `item_id` BIGINT NOT NULL,
    `item_name_snapshot` VARCHAR(150) NOT NULL,
    `quantity` INT NOT NULL,
    `unit_price` DECIMAL(10, 2) NOT NULL,
    `subtotal` DECIMAL(10, 2) NOT NULL,
    `note` VARCHAR(255) NULL,
    PRIMARY KEY (`order_item_id`),
    KEY `idx_order_items_order` (`order_id`),
    KEY `idx_order_items_item` (`item_id`),
    CONSTRAINT `fk_order_items_order` FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_order_items_item` FOREIGN KEY (`item_id`) REFERENCES `menu_items` (`item_id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
