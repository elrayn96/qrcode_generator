package main

import (
	"log"
	"net/http"
	"os"

	"github.com/elrayn96/qrcode_generator/services/api-gateway/internal/server"
)

func main() {
	host := os.Getenv("API_HOST")
	if host == "" {
		host = "127.0.0.1"
	}

	port := os.Getenv("API_PORT")
	if port == "" {
		port = "8080"
	}

	address := host + ":" + port

	log.Printf("GQR API Gateway iniciado em %s", address)

	if err := http.ListenAndServe(address, server.NewRouter()); err != nil {
		log.Fatal(err)
	}
}
