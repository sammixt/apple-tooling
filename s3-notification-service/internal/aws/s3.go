package aws

import (
	"S3-notification-service/config"
	"context"
	"encoding/json"
	"fmt"
	"hash/fnv"
	"strings"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/credentials"
	"github.com/aws/aws-sdk-go-v2/service/s3"
	"github.com/aws/aws-sdk-go-v2/service/sts"
)

func GetS3Client() (*s3.Client, error) {
	cfg := config.AppConfig

	// Use static credentials
	creds := credentials.NewStaticCredentialsProvider(cfg.AWSAccessKeyID, cfg.AWSSecretAccessKey, "")

	// Create STS client
	stsClient := sts.New(sts.Options{
		Credentials: creds,
		Region:      cfg.AWSRegion,
	})

	// Assume role
	input := &sts.AssumeRoleInput{
		RoleArn:         aws.String(cfg.AWSRoleARN),
		RoleSessionName: aws.String("AssumeRoleSession"),
	}

	result, err := stsClient.AssumeRole(context.Background(), input)
	if err != nil {
		return nil, fmt.Errorf("failed to assume role: %v", err)
	}

	// Create S3 client with assumed role credentials
	s3Client := s3.New(s3.Options{
		Credentials: credentials.NewStaticCredentialsProvider(
			*result.Credentials.AccessKeyId,
			*result.Credentials.SecretAccessKey,
			*result.Credentials.SessionToken,
		),
		Region: cfg.AWSRegion,
	})

	return s3Client, nil
}

type S3ObjectInfo struct {
	Key          string    `json:"key"`
	ETag         string    `json:"etag"`
	LastModified time.Time `json:"last_modified"`
}

func ListS3Objects(s3Client *s3.Client, bucketName string) ([]S3ObjectInfo, error) {
	var objects []S3ObjectInfo

	paginator := s3.NewListObjectsV2Paginator(s3Client, &s3.ListObjectsV2Input{
		Bucket: aws.String(bucketName),
	})

	for paginator.HasMorePages() {
		output, err := paginator.NextPage(context.Background())
		if err != nil {
			return nil, fmt.Errorf("failed to list objects: %v", err)
		}

		for _, item := range output.Contents {
			key := aws.ToString(item.Key)
			if strings.HasSuffix(key, ".json") {
				if strings.Contains(key, "assets") {
					fmt.Println("Skipping JSON file with 'assets' in pathname: ", key)
				} else {
					objInfo := S3ObjectInfo{
						Key:          key,
						ETag:         aws.ToString(item.ETag),
						LastModified: aws.ToTime(item.LastModified),
					}
					objects = append(objects, objInfo)
				}
			}
		}
	}

	return objects, nil
}

func ComputeHash(objects []S3ObjectInfo) (string, error) {
	data, err := json.Marshal(objects)
	if err != nil {
		return "", fmt.Errorf("failed to marshal objects: %v", err)
	}

	h := fnv.New64a()
	_, err = h.Write(data)
	if err != nil {
		return "", fmt.Errorf("failed to compute hash: %v", err)
	}

	return fmt.Sprintf("%x", h.Sum64()), nil
}
