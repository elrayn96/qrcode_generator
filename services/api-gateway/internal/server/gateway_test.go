package server

import (
	"encoding/json"
	"github.com/elrayn96/qrcode_generator/services/api-gateway/internal/config"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

func TestGateway(t *testing.T) {
	engine := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/readyz" {
			return
		}
		var m map[string]any
		if json.NewDecoder(r.Body).Decode(&m) != nil || m["content"] != "hello" {
			t.Error("canonical")
			w.WriteHeader(422)
			return
		}
		w.Header().Set("Content-Type", "image/png")
		w.Write([]byte("mock"))
	}))
	defer engine.Close()
	g := New(config.Config{QREngineURL: engine.URL, WorkerCount: 1, QueueCapacity: 1, RequestTimeout: time.Second})
	for _, c := range []struct {
		method, path, body, media string
		status                    int
	}{{"GET", "/healthz", "", "", 200}, {"GET", "/readyz", "", "", 200}, {"GET", "/v1/templates", "", "", 200}, {"POST", "/v1/qr/generate", `{"type":"text","data":{"text":"hello"}}`, "application/json", 200}, {"POST", "/v1/qr/preview", `{"type":"text","data":{"text":"hello"},"output":{"size":1024}}`, "application/json", 422}, {"POST", "/v1/qr/generate", `{`, "application/json", 400}, {"POST", "/v1/qr/generate", `{}`, "text/plain", 415}} {
		r := httptest.NewRequest(c.method, c.path, strings.NewReader(c.body))
		r.Header.Set("Content-Type", c.media)
		w := httptest.NewRecorder()
		g.ServeHTTP(w, r)
		if w.Code != c.status {
			t.Errorf("%s: %d != %d", c.path, w.Code, c.status)
		}
	}
}
func BenchmarkGateway(b *testing.B) {
	g := NewRouter()
	for i := 0; i < b.N; i++ {
		g.ServeHTTP(httptest.NewRecorder(), httptest.NewRequest("GET", "/healthz", nil))
	}
}
