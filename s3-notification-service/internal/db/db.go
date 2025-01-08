package db

import (
	"fmt"
	"log"
	"time"

	"S3-notification-service/config"

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

var DB *gorm.DB

func Connect() {
	cfg := config.AppConfig
	dsn := fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=disable",
		cfg.DBHost, cfg.DBPort, cfg.DBUser, cfg.DBPassword, cfg.DBName)

	var db *gorm.DB
	var err error
	maxRetries := 5
	for retries := 0; retries < maxRetries; retries++ {
		db, err = gorm.Open(postgres.Open(dsn), &gorm.Config{})
		if err == nil {
			break
		}
		log.Printf("Failed to connect to database: %v. Retrying... (%d/%d)", err, retries+1, maxRetries)
		time.Sleep(5 * time.Second)
	}

	if err != nil {
		log.Fatalf("Failed to connect to database after retries: %v", err)
	}

	DB = db

	// Run Migrations
	err = DB.AutoMigrate(&State{})
	if err != nil {
		log.Fatalf("Failed to migrate database: %v", err)
	}
}
