package config

import (
	"fmt"
	"log"
	"os"
	"strconv"
	"strings"

	"github.com/joho/godotenv"
)

type Config struct {
	Port                string
	DBHost              string
	DBPort              string
	DBUser              string
	DBPassword          string
	DBName              string
	AWSAccessKeyID      string
	AWSSecretAccessKey  string
	AWSRegion           string
	AWSRoleARN          string
	BucketName          string
	WebhookURLs         []string
	WebhookToken        string
	PollIntervalMinutes int
	SlackWebhookURL     string
}

var AppConfig *Config

func LoadConfig() {
	err := godotenv.Load()
	if err != nil {
		fmt.Printf("Warning: Error loading .env file: %v", err)
	}

	pollInterval, err := strconv.Atoi(getEnv("POLL_INTERVAL_MINUTES", "5"))
	if err != nil {
		log.Fatalf("Invalid POLL_INTERVAL_MINUTES: %v", err)
	}

	webhookURLsEnv := getEnv("WEBHOOK_URLS", "")
	webhookURLs := strings.Split(webhookURLsEnv, ",")

	AppConfig = &Config{
		Port:                getEnv("PORT", ""),
		DBHost:              getEnv("DB_HOST", ""),
		DBPort:              getEnv("DB_PORT", ""),
		DBUser:              getEnv("DB_USER", ""),
		DBPassword:          getEnv("DB_PASSWORD", ""),
		DBName:              getEnv("DB_NAME", ""),
		AWSAccessKeyID:      getEnv("AWS_ACCESS_KEY_ID", ""),
		AWSSecretAccessKey:  getEnv("AWS_SECRET_ACCESS_KEY", ""),
		AWSRegion:           getEnv("AWS_REGION", ""),
		AWSRoleARN:          getEnv("AWS_ROLE_ARN", ""),
		BucketName:          getEnv("BUCKET_NAME", ""),
		SlackWebhookURL:     getEnv("SLACK_WEBHOOK_URL", ""),
		WebhookToken:        getEnv("WEBHOOK_SECRET_TOKEN", ""),
		PollIntervalMinutes: pollInterval,
		WebhookURLs:         webhookURLs,
	}

}

func getEnv(key, defaultValue string) string {
	value, exists := os.LookupEnv(key)
	if !exists {
		return defaultValue
	}
	return value
}
