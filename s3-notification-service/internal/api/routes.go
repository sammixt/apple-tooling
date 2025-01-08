package api

import (
	"github.com/gin-gonic/gin"
)

func SetupRouter() *gin.Engine {
	router := gin.Default()

	router.GET("/health", HealthCheck)
	router.POST("/check", CheckForUpdates)

	return router
}
