package qrengine

import (
	"context"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestClient(t *testing.T) {
	for _, status := range []int{200, 400, 413, 415, 422, 500, 503, 504, 302, 404} {
		t.Run(fmt.Sprint(status), func(t *testing.T) {
			s := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				if r.URL.Path == "/readyz" {
					return
				}
				if r.Method != "POST" || r.URL.Path != "/internal/v1/render" || r.Header.Get("Content-Type") != "application/json" {
					t.Error("bad request")
				}
				w.Header().Set("Content-Type", "image/png")
				w.WriteHeader(status)
				w.Write([]byte("image"))
			}))
			defer s.Close()
			c := New(s.URL + "/")
			if !c.Ready(context.Background()) {
				t.Fatal("not ready")
			}
			d, m, got := c.Render(context.Background(), []byte("{}"))
			want := status
			if status == 302 || status == 404 {
				want = 503
			}
			if got != want {
				t.Fatal(got, want)
			}
			if got == 200 && (string(d) != "image" || m != "image/png") {
				t.Fatal(d, m)
			}
		})
	}
}
func TestFailures(t *testing.T) {
	for _, media := range []string{"text/plain", "image/png"} {
		s := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { w.Header().Set("Content-Type", media) }))
		c := New(s.URL)
		if _, _, status := c.Render(context.Background(), nil); status != 503 {
			t.Fatal(status)
		}
		s.Close()
		if c.Ready(context.Background()) {
			t.Fatal("closed")
		}
		if _, _, status := c.Render(context.Background(), nil); status != 503 {
			t.Fatal(status)
		}
	}
	c := New(":bad")
	if c.Ready(context.Background()) {
		t.Fatal("bad url")
	}
	if _, _, status := c.Render(context.Background(), nil); status != 500 {
		t.Fatal(status)
	}
	s := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { <-r.Context().Done() }))
	defer s.Close()
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Millisecond)
	defer cancel()
	if _, _, status := New(s.URL).Render(ctx, nil); status != 504 {
		t.Fatal(status)
	}
}
