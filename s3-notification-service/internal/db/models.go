package db

import (
	"time"

	"gorm.io/gorm"
)

type State struct {
	ID          uint `gorm:"primaryKey"`
	LastRunTime time.Time
	StateHash   string
	Objects     []byte `gorm:"type:jsonb"`
	CreatedAt   time.Time
	UpdatedAt   time.Time
	DeletedAt   gorm.DeletedAt `gorm:"index"`
}
