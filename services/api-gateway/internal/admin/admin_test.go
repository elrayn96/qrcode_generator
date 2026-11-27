package admin

import (
	"context"
	"encoding/json"
	"net/http/httptest"
	"strings"
	"sync"
	"testing"
)

type memory struct {
	mu   sync.Mutex
	data map[string]*State
}

func (m *memory) Update(_ context.Context, u string, f func(*State) error) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	if m.data[u] == nil {
		m.data[u] = &State{}
	}
	return f(m.data[u])
}

type verify struct{}

func (verify) Verify(_ context.Context, t string) (string, error) { return t, nil }
func TestAdmin(t *testing.T) {
	m := &memory{data: map[string]*State{}}
	h := Handler(m, verify{})
	call := func(method, path, body, user string, want int) *httptest.ResponseRecorder {
		r := httptest.NewRequest(method, path, strings.NewReader(body))
		if user != "" {
			r.Header.Set("Authorization", "Bearer "+user)
		}
		w := httptest.NewRecorder()
		h.ServeHTTP(w, r)
		if w.Code != want {
			t.Fatalf("%s %s: %d != %d: %s", method, path, w.Code, want, w.Body.String())
		}
		return w
	}
	call("GET", "/v1/projects", "", "", 401)
	w := call("POST", "/v1/projects", `{"name":"P"}`, "alice", 201)
	var p Project
	json.Unmarshal(w.Body.Bytes(), &p)
	path := "/v1/projects/" + p.ID
	call("GET", path, "", "bob", 404)
	call("PATCH", path, `{"name":"P2"}`, "alice", 200)
	w = call("POST", path+"/applications", `{"name":"A","type":"backend","permissions":["generate"]}`, "alice", 201)
	var a Application
	json.Unmarshal(w.Body.Bytes(), &a)
	ap := "/v1/applications/" + a.ID
	w = call("POST", ap+"/keys", `{"name":"K"}`, "alice", 201)
	var k map[string]string
	json.Unmarshal(w.Body.Bytes(), &k)
	if !strings.HasPrefix(k["key"], "qr_sk_") {
		t.Fatal(k)
	}
	w = call("GET", ap+"/keys", "", "alice", 200)
	if strings.Contains(w.Body.String(), k["key"]) {
		t.Fatal("secret leaked")
	}
	call("DELETE", "/v1/keys/"+k["id"], "", "bob", 404)
	call("DELETE", "/v1/keys/"+k["id"], "", "alice", 204)
	call("DELETE", path, "", "alice", 409)
	call("DELETE", ap, "", "alice", 204)
	call("DELETE", path, "", "alice", 204)
}
