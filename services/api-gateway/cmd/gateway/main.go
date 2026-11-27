package main

import (
	"context"
	"errors"
	"github.com/elrayn96/qrcode_generator/services/api-gateway/internal/admin"
	"github.com/elrayn96/qrcode_generator/services/api-gateway/internal/config"
	"github.com/elrayn96/qrcode_generator/services/api-gateway/internal/firebase"
	"github.com/elrayn96/qrcode_generator/services/api-gateway/internal/server"
	"log"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"
)

func main() {
	cfg, err := config.Load()
	if err != nil {
		log.Fatal(err)
	}
	var level slog.Level
	if err = level.UnmarshalText([]byte(cfg.LogLevel)); err != nil {
		log.Fatal(err)
	}
	slog.SetDefault(slog.New(slog.NewJSONHandler(os.Stderr, &slog.HandlerOptions{Level: level})))
	var handler http.Handler = server.New(cfg)
	if cfg.FirebaseProjectID != "" {
		ctx, cancel := context.WithTimeout(context.Background(), cfg.RequestTimeout)
		client, e := firebase.Open(ctx, cfg.FirebaseProjectID, cfg.GoogleCredentials)
		cancel()
		if e != nil {
			log.Fatal("Firebase initialization failed")
		}
		defer client.Close()
		mux := http.NewServeMux()
		mux.Handle("/", handler)
		a := admin.Handler(client, client)
		for _, p := range []string{"/v1/projects", "/v1/projects/", "/v1/applications/", "/v1/keys/"} {
			mux.Handle(p, a)
		}
		handler = mux
	}
	s := &http.Server{Addr: cfg.Address(), Handler: handler, ReadHeaderTimeout: 5 * time.Second, ReadTimeout: 15 * time.Second, WriteTimeout: cfg.RequestTimeout + 20*time.Second, IdleTimeout: 60 * time.Second, MaxHeaderBytes: 32 << 10}
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	done := make(chan error, 1)
	go func() { done <- s.ListenAndServe() }()
	log.Printf("GQR API Gateway iniciado em %s", cfg.Address())
	select {
	case err = <-done:
		if !errors.Is(err, http.ErrServerClosed) {
			log.Fatal(err)
		}
	case <-ctx.Done():
		c, cancel := context.WithTimeout(context.Background(), cfg.RequestTimeout+time.Second)
		defer cancel()
		if err = s.Shutdown(c); err != nil {
			s.Close()
			log.Print(err)
		}
	}
}
