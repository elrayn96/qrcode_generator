package main

import (
	"log"
	"net/http"

	"github.com/elrayn96/qrcode_generator/services/api-gateway/internal/config"
	"github.com/elrayn96/qrcode_generator/services/api-gateway/internal/server"
)

func main() {
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Configuração inválida: %v", err)
	}

	log.Printf(
		"GQR API Gateway iniciado em %s (ambiente: %s)",
		cfg.Address(),
		cfg.Environment,
	)

	if err := http.ListenAndServe(
		cfg.Address(),
		server.NewRouter(),
	); err != nil {
		log.Fatal(err)
	}
}
