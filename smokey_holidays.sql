CREATE TABLE IF NOT EXISTS `smokey_holiday_leaderboard` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `holiday` VARCHAR(50) NOT NULL,
    `identifier` VARCHAR(80) NOT NULL,
    `player_name` VARCHAR(100) NOT NULL DEFAULT 'Unknown',
    `normal_eggs` INT NOT NULL DEFAULT 0,
    `rare_eggs` INT NOT NULL DEFAULT 0,
    `total_points` INT NOT NULL DEFAULT 0,
    `last_collect` TIMESTAMP NULL DEFAULT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uniq_holiday_identifier` (`holiday`, `identifier`)
);
