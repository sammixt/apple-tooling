package job

import (
	"S3-notification-service/config"
	awsUtils "S3-notification-service/internal/aws"
	"S3-notification-service/internal/db"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"strings"
	"time"

	"golang.org/x/text/cases"
	"golang.org/x/text/language"
)

func StartScheduler() *time.Ticker {
	interval := time.Duration(config.AppConfig.PollIntervalMinutes) * time.Minute
	ticker := time.NewTicker(interval)

	go func() {
		for range ticker.C {
			err := ExecuteJob()
			if err != nil {
				log.Printf("Error executing job: %v", err)
			}
		}
	}()

	return ticker
}

func ExecuteJob() error {
	fmt.Println("Executing job to check for S3 updates...")
	s3Client, err := awsUtils.GetS3Client()
	if err != nil {
		return fmt.Errorf("failed to get S3 client: %v", err)
	}

	objects, err := awsUtils.ListS3Objects(s3Client, config.AppConfig.BucketName)
	if err != nil {
		return fmt.Errorf("failed to list S3 objects: %v", err)
	}

	currentHash, err := awsUtils.ComputeHash(objects)
	if err != nil {
		return fmt.Errorf("failed to compute hash: %v", err)
	}

	// Serialize current objects
	currentObjectsData, err := json.Marshal(objects)
	if err != nil {
		return fmt.Errorf("failed to serialize current objects: %v", err)
	}

	// Retrieve previous state
	var state db.State
	result := db.DB.First(&state)
	if result.Error != nil {
		state = db.State{
			LastRunTime: time.Now(),
			StateHash:   currentHash,
			Objects:     currentObjectsData,
		}
		db.DB.Create(&state)
		fmt.Println("Initial state saved.")
		return nil
	}

	// Deserialize previous objects
	var previousObjects []awsUtils.S3ObjectInfo
	err = json.Unmarshal(state.Objects, &previousObjects)
	if err != nil {
		return fmt.Errorf("failed to deserialize previous objects: %v", err)
	}

	// Detect changes
	changes := detectChanges(previousObjects, objects)

	if len(changes) > 0 {
		fmt.Printf("Detected %d changes in S3 bucket.", len(changes))
		go sendNotification(changes)

		// Prepare Slack message
		slackMessage := createSlackMessage(changes)

		// Send Slack notification
		go func() {
			err := sendSlackNotification(slackMessage)
			if err != nil {
				log.Printf("Error sending Slack notification: %v", err)
			}
		}()
	} else {
		fmt.Println("No changes detected.")
	}

	// Update state
	state.LastRunTime = time.Now()
	state.StateHash = currentHash
	state.Objects = currentObjectsData
	db.DB.Save(&state)

	return nil
}

type ChangeType string

const (
	Created ChangeType = "created"
	Updated ChangeType = "updated"
	Deleted ChangeType = "deleted"
)

type Change struct {
	Key    string     `json:"key"`
	Action ChangeType `json:"action"`
	Time   time.Time  `json:"time"`
	S3URI  string     `json:"s3_uri"`
}

type NotificationChange struct {
	Key        string     `json:"s3key"`
	Action     ChangeType `json:"action"`
	WorkStream string     `json:"workstream"`
	S3URI      string     `json:"file_url"`
}

func detectChanges(previousObjects, currentObjects []awsUtils.S3ObjectInfo) []Change {
	changes := []Change{}

	prevMap := make(map[string]awsUtils.S3ObjectInfo)
	currMap := make(map[string]awsUtils.S3ObjectInfo)

	bucketName := config.AppConfig.BucketName

	for _, obj := range previousObjects {
		prevMap[obj.Key] = obj
	}

	for _, obj := range currentObjects {
		currMap[obj.Key] = obj
	}

	// Detect deleted and updated files
	for key, prevObj := range prevMap {
		currObj, exists := currMap[key]
		s3URI := fmt.Sprintf("s3://%s/%s", bucketName, key)
		if !exists {
			// File was deleted
			changes = append(changes, Change{
				Key:    key,
				Action: Deleted,
				Time:   time.Now(),
				S3URI:  s3URI,
			})
		} else if prevObj.ETag != currObj.ETag || !prevObj.LastModified.Equal(currObj.LastModified) {
			// File was updated
			changes = append(changes, Change{
				Key:    key,
				Action: Updated,
				Time:   currObj.LastModified,
				S3URI:  s3URI,
			})
		}
	}

	// Detect new files
	for key, currObj := range currMap {
		_, exists := prevMap[key]
		if !exists {
			s3URI := fmt.Sprintf("s3://%s/%s", bucketName, key)
			// File was created
			changes = append(changes, Change{
				Key:    key,
				Action: Created,
				Time:   currObj.LastModified,
				S3URI:  s3URI,
			})
		}
	}

	return changes
}

func sendNotification(changes []Change) {
	if len(changes) == 0 {
		fmt.Println("No changes to notify.")
		return
	}

	// Transform changes into notificationChanges without the Time field
	notificationChanges := make([]NotificationChange, len(changes))
	for i, change := range changes {
		workstream := getWorkstream(change.Key)
		notificationChanges[i] = NotificationChange{
			Key:        change.Key,
			Action:     change.Action,
			WorkStream: workstream,
			S3URI:      change.S3URI,
		}
	}

	payload := map[string]interface{}{
		"bucket":  config.AppConfig.BucketName,
		"changes": notificationChanges,
	}

	data, err := json.Marshal(payload)
	if err != nil {
		log.Printf("Failed to marshal payload: %v", err)
		return
	}

	for _, url := range config.AppConfig.WebhookURLs {
		go func(webhookURL string) {
			ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
			defer cancel()

			req, err := http.NewRequestWithContext(ctx, http.MethodPost, webhookURL, bytes.NewBuffer(data))
			if err != nil {
				log.Printf("Failed to create HTTP request for %s: %v", webhookURL, err)
				return
			}

			req.Header.Set("Content-Type", "application/json")
			req.Header.Set("x-webhook-token", config.AppConfig.WebhookToken)

			client := &http.Client{}
			resp, err := client.Do(req)
			if err != nil {
				log.Printf("Failed to send HTTP request to %s: %v", webhookURL, err)
				return
			}
			defer resp.Body.Close()

			if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusCreated {
				log.Printf("Received non-OK response from %s: %v", webhookURL, resp.Status)
				return
			}

			fmt.Printf("Notification sent successfully to %s.", webhookURL)
		}(url)
	}
}

func getWorkstream(key string) string {
	parts := strings.SplitN(key, "/", 2)
	if len(parts) > 0 {
		return parts[0]
	}
	return ""
}

func createSlackMessage(changes []Change) interface{} {
	// Create an array of blocks
	blocks := []map[string]interface{}{
		{
			"type": "section",
			"text": map[string]string{
				"type": "mrkdwn",
				"text": fmt.Sprintf("*Detected %d changes in S3 bucket `%s`*", len(changes), config.AppConfig.BucketName),
			},
		},
	}

	// Create a Title Casing Transformer
	titleCaser := cases.Title(language.English)

	// Load the Pacific Time Zone (handles PST and PDT)
	loc, err := time.LoadLocation("America/Los_Angeles")
	if err != nil {
		// Handle the error, perhaps default to UTC
		fmt.Printf("Error loading location: %v", err)
		loc = time.UTC
	}

	// Add a section for each change, including Key and Time
	for _, change := range changes {
		actionTitle := titleCaser.String(string(change.Action))
		changeTime := change.Time.In(loc).Format("2006-01-02 15:04:05 MST")
		changeText := fmt.Sprintf("*Action:* `%s`\n*Key:* `%s`\n*S3 URI:* `%s`\n*Time:* %s",
			actionTitle, change.Key, change.S3URI, changeTime)

		blocks = append(blocks, map[string]interface{}{
			"type": "section",
			"text": map[string]string{
				"type": "mrkdwn",
				"text": changeText,
			},
		})
	}

	slackMessage := map[string]interface{}{
		"blocks": blocks,
	}

	return slackMessage
}

func sendSlackNotification(message interface{}) error {
	webhookURL := config.AppConfig.SlackWebhookURL
	if webhookURL == "" {
		fmt.Println("Slack webhook URL not configured.")
		return nil
	}

	// Marshal the message payload to JSON
	payloadBytes, err := json.Marshal(message)
	if err != nil {
		return fmt.Errorf("failed to marshal Slack message: %v", err)
	}

	// Create a new HTTP request
	req, err := http.NewRequest("POST", webhookURL, bytes.NewBuffer(payloadBytes))
	if err != nil {
		return fmt.Errorf("failed to create HTTP request: %v", err)
	}

	req.Header.Set("Content-Type", "application/json")

	// Send the HTTP request
	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("failed to send Slack notification: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		bodyString := string(bodyBytes)
		return fmt.Errorf("slack notification failed with status %d: %s", resp.StatusCode, bodyString)
	}

	fmt.Println("Slack notification sent successfully.")
	return nil
}
