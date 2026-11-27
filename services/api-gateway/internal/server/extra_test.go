package server

import (
	"github.com/elrayn96/qrcode_generator/services/api-gateway/internal/config"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

func TestRejections(t *testing.T) {
	engine := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(503) }))
	defer engine.Close()
	g := New(config.Config{QREngineURL: engine.URL, WorkerCount: 1, QueueCapacity: 1, RequestTimeout: time.Second})
	for _, c := range []struct {
		path, body, key string
		status          int
	}{{"/readyz", "", "", 503}, {"/v1/qr/generate", "{}", "key", 401}, {"/v1/qr/generate", strings.Repeat("x", (1<<20)+1), "", 413}, {"/v1/qr/generate", `{"type":"text","data":{"text":"hello"}}`, "", 503}} {
		method := "POST"
		if c.path == "/readyz" {
			method = "GET"
		}
		r := httptest.NewRequest(method, c.path, strings.NewReader(c.body))
		r.Header.Set("Content-Type", "application/json")
		r.Header.Set("X-API-Key", c.key)
		w := httptest.NewRecorder()
		g.ServeHTTP(w, r)
		if w.Code != c.status {
			t.Fatal(w.Code, c.status)
		}
	}
	for i := 0; i < 61; i++ {
		r := httptest.NewRequest("POST", "/v1/qr/generate", strings.NewReader("{}"))
		r.RemoteAddr = "192.0.2.5:123"
		r.Header.Set("Content-Type", "application/json")
		w := httptest.NewRecorder()
		g.ServeHTTP(w, r)
		if i == 60 && w.Code != 429 {
			t.Fatal(w.Code)
		}
	}
}
