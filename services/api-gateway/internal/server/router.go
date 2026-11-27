package server

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"github.com/elrayn96/qrcode_generator/services/api-gateway/internal/config"
	"github.com/elrayn96/qrcode_generator/services/api-gateway/internal/handlers"
	"github.com/elrayn96/qrcode_generator/services/api-gateway/internal/qrengine"
	"io"
	"log/slog"
	"mime"
	"net"
	"net/http"
	"strings"
	"sync"
	"time"
)

type gateway struct {
	cfg              config.Config
	engine           *qrengine.Client
	slots, admission chan struct{}
	mu               sync.Mutex
	window           time.Time
	counts           map[string]int
}

func NewRouter() http.Handler {
	return New(config.Config{QREngineURL: "http://127.0.0.1:8001", WorkerCount: 2, QueueCapacity: 8, RequestTimeout: 15 * time.Second})
}
func New(cfg config.Config) http.Handler {
	g := &gateway{cfg: cfg, engine: qrengine.New(cfg.QREngineURL), slots: make(chan struct{}, cfg.WorkerCount), admission: make(chan struct{}, cfg.WorkerCount+cfg.QueueCapacity), counts: make(map[string]int)}
	m := http.NewServeMux()
	m.HandleFunc("GET /healthz", health)
	m.HandleFunc("GET /readyz", g.ready)
	m.HandleFunc("POST /v1/qr/generate", g.render)
	m.HandleFunc("POST /v1/qr/preview", g.render)
	m.HandleFunc("GET /v1/templates", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		io.WriteString(w, "[]")
	})
	return m
}
func health(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "ok", "service": "api-gateway"})
}
func problem(w http.ResponseWriter, status int, code, id string) {
	w.Header().Set("Content-Type", "application/problem+json")
	w.Header().Set("Cache-Control", "no-store")
	w.Header().Set("X-Request-ID", id)
	if status == 429 || status == 503 {
		w.Header().Set("Retry-After", "1")
	}
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(map[string]any{"type": "about:blank", "title": http.StatusText(status), "status": status, "code": code, "requestId": id})
}
func requestID() string {
	var b [16]byte
	if _, err := rand.Read(b[:]); err != nil {
		panic(err)
	}
	return hex.EncodeToString(b[:])
}
func (g *gateway) ready(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 2*time.Second)
	defer cancel()
	if !g.engine.Ready(ctx) {
		problem(w, 503, "engine_unavailable", requestID())
		return
	}
	health(w, r)
}
func (g *gateway) allow(addr string) bool {
	host, _, err := net.SplitHostPort(addr)
	if err != nil {
		host = addr
	}
	g.mu.Lock()
	defer g.mu.Unlock()
	now := time.Now()
	if now.Sub(g.window) >= time.Minute {
		g.window = now
		clear(g.counts)
	}
	if g.counts[host] >= 60 {
		return false
	}
	if _, ok := g.counts[host]; !ok && len(g.counts) >= 10000 {
		return false
	}
	g.counts[host]++
	return true
}
func (g *gateway) render(w http.ResponseWriter, r *http.Request) {
	id := requestID()
	start := time.Now()
	defer func() { slog.Info("render", "request_id", id, "duration_ms", time.Since(start).Milliseconds()) }()
	if r.Header.Get("X-API-Key") != "" || r.Header.Get("Authorization") != "" {
		problem(w, 401, "credentials_not_supported", id)
		return
	}
	if !g.allow(r.RemoteAddr) {
		problem(w, 429, "rate_limit", id)
		return
	}
	mt, _, err := mime.ParseMediaType(r.Header.Get("Content-Type"))
	if err != nil || mt != "application/json" {
		problem(w, 415, "unsupported_media_type", id)
		return
	}
	select {
	case g.admission <- struct{}{}:
		defer func() { <-g.admission }()
	default:
		problem(w, 503, "queue_full", id)
		return
	}
	r.Body = http.MaxBytesReader(w, r.Body, 1<<20)
	body, err := io.ReadAll(r.Body)
	if err != nil {
		problem(w, 413, "body_too_large", id)
		return
	}
	if !json.Valid(body) {
		problem(w, 400, "invalid_json", id)
		return
	}
	canonical, err := handlers.Canonical(body, strings.HasSuffix(r.URL.Path, "/preview"))
	if err != nil {
		problem(w, 422, "invalid_request", id)
		return
	}
	ctx, cancel := context.WithTimeout(r.Context(), g.cfg.RequestTimeout)
	defer cancel()
	select {
	case g.slots <- struct{}{}:
		defer func() { <-g.slots }()
	case <-ctx.Done():
		problem(w, 504, "timeout", id)
		return
	}
	data, media, status := g.engine.Render(ctx, canonical)
	if status != 200 {
		problem(w, status, "render_failed", id)
		return
	}
	w.Header().Set("Content-Type", media)
	w.Header().Set("Cache-Control", "no-store")
	w.Header().Set("X-Content-Type-Options", "nosniff")
	w.Header().Set("X-Request-ID", id)
	w.Write(data)
}
