package main

import (
	"S3-notification-service/config"
	"S3-notification-service/internal/api"
	"S3-notification-service/internal/db"
	"S3-notification-service/internal/job"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"
)

func main() {
	// Load configuration
	config.LoadConfig()

	// Connect to database
	db.Connect()

	// Start job scheduler
	job.StartScheduler()

	// Setup router
	router := api.SetupRouter()

	// Start server
	go func() {
		if err := router.Run(":" + config.AppConfig.Port); err != nil {
			log.Fatalf("Failed to run server: %v", err)
		}
	}()

	// Wait for interrupt signal to gracefully shutdown the server
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, os.Interrupt, syscall.SIGTERM)
	<-quit
	fmt.Println("Shutting down server...")
}
