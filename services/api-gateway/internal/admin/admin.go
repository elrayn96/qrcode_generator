package admin

import (
	"context"
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"github.com/elrayn96/qrcode_generator/services/api-gateway/internal/auth"
	"io"
	"net/http"
	"strings"
	"time"
)

// Store serializes changes to a single owner's state. Implementations must commit atomically.
type Store interface {
	Update(context.Context, string, func(*State) error) error
}
type Project struct {
	ID   string `json:"id"`
	Name string `json:"name"`
}
type Application struct {
	ID           string              `json:"id"`
	ProjectID    string              `json:"projectId"`
	Name         string              `json:"name"`
	Type         string              `json:"type"`
	Enabled      bool                `json:"enabled"`
	Permissions  []string            `json:"permissions,omitempty"`
	Restrictions map[string][]string `json:"-"`
}
type Key struct {
	ID            string `json:"id"`
	Name          string `json:"name"`
	Kind          string `json:"kind"`
	Prefix        string `json:"prefix"`
	Revoked       bool   `json:"revoked"`
	ApplicationID string `json:"-"`
	Hash          string `json:"-"`
}
type State struct {
	Projects     map[string]Project
	Applications map[string]Application
	Keys         map[string]Key
}

func (s *State) Init() {
	if s.Projects == nil {
		s.Projects = map[string]Project{}
	}
	if s.Applications == nil {
		s.Applications = map[string]Application{}
	}
	if s.Keys == nil {
		s.Keys = map[string]Key{}
	}
}

var missing = errors.New("not_found")
var invalid = errors.New("invalid_request")
var conflict = errors.New("conflict")

func id() string {
	var b [24]byte
	if _, e := rand.Read(b[:]); e != nil {
		panic(e)
	}
	return hex.EncodeToString(b[:])
}
func validName(s string) bool { return strings.TrimSpace(s) != "" && len([]rune(s)) <= 100 }

type input struct {
	Name        string   `json:"name"`
	Type        string   `json:"type,omitempty"`
	Enabled     *bool    `json:"enabled,omitempty"`
	Permissions []string `json:"permissions,omitempty"`
}

func read(w http.ResponseWriter, r *http.Request) (input, error) {
	var v input
	d := json.NewDecoder(http.MaxBytesReader(w, r.Body, 16384))
	d.DisallowUnknownFields()
	if e := d.Decode(&v); e != nil {
		return v, invalid
	}
	if d.Decode(new(any)) != io.EOF {
		return v, invalid
	}
	return v, nil
}
func Handler(store Store, verifier auth.Verifier) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Cache-Control", "no-store")
		w.Header().Set("X-Content-Type-Options", "nosniff")
		rid := id()
		w.Header().Set("X-Request-ID", rid)
		fail := func(status int, code string) {
			w.Header().Set("Content-Type", "application/problem+json")
			if status == 503 || status == 429 {
				w.Header().Set("Retry-After", "1")
			}
			w.WriteHeader(status)
			json.NewEncoder(w).Encode(map[string]any{"type": "about:blank", "title": http.StatusText(status), "status": status, "code": code, "requestId": rid})
		}
		uid, e := auth.Authenticate(r, verifier)
		if e != nil {
			fail(401, "unauthorized")
			return
		}
		if store == nil {
			fail(503, "storage_unavailable")
			return
		}
		p := strings.Split(strings.Trim(r.URL.Path, "/"), "/")
		if len(p) < 2 || p[0] != "v1" {
			fail(404, "not_found")
			return
		}
		var v input
		if r.Method == "POST" || r.Method == "PATCH" {
			v, e = read(w, r)
			if e != nil {
				fail(422, "invalid_request")
				return
			}
		}
		var out any
		status := 200
		ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
		defer cancel()
		e = store.Update(ctx, uid, func(s *State) error {
			s.Init()
			out = nil
			status = 200
			switch p[1] {
			case "projects":
				if len(p) == 2 {
					switch r.Method {
					case "GET":
						a := []Project{}
						for _, x := range s.Projects {
							a = append(a, x)
						}
						out = a
					case "POST":
						if !validName(v.Name) || v.Type != "" || v.Enabled != nil || v.Permissions != nil {
							return invalid
						}
						if len(s.Projects) >= 100 {
							return conflict
						}
						x := Project{id(), v.Name}
						s.Projects[x.ID] = x
						out = x
						status = 201
					default:
						return missing
					}
					return nil
				}
				x, ok := s.Projects[p[2]]
				if !ok {
					return missing
				}
				if len(p) == 3 {
					switch r.Method {
					case "GET":
						out = x
					case "PATCH":
						if !validName(v.Name) || v.Type != "" || v.Enabled != nil || v.Permissions != nil {
							return invalid
						}
						x.Name = v.Name
						s.Projects[x.ID] = x
						out = x
					case "DELETE":
						for _, a := range s.Applications {
							if a.ProjectID == x.ID {
								return conflict
							}
						}
						delete(s.Projects, x.ID)
						status = 204
					default:
						return missing
					}
					return nil
				}
				if len(p) == 4 && p[3] == "applications" {
					switch r.Method {
					case "GET":
						a := []Application{}
						for _, y := range s.Applications {
							if y.ProjectID == x.ID {
								a = append(a, y)
							}
						}
						out = a
					case "POST":
						if !validName(v.Name) || (v.Type != "web" && v.Type != "android" && v.Type != "backend") || v.Enabled != nil || !permissions(v.Permissions) {
							return invalid
						}
						if len(s.Applications) >= 100 {
							return conflict
						}
						a := Application{ID: id(), ProjectID: x.ID, Name: v.Name, Type: v.Type, Enabled: true, Permissions: v.Permissions}
						s.Applications[a.ID] = a
						out = a
						status = 201
					default:
						return missing
					}
					return nil
				}
			case "applications":
				if len(p) < 3 {
					return missing
				}
				a, ok := s.Applications[p[2]]
				if !ok {
					return missing
				}
				if len(p) == 3 {
					switch r.Method {
					case "GET":
						out = a
					case "PATCH":
						if v.Type != "" || !permissions(v.Permissions) {
							return invalid
						}
						if v.Name != "" {
							if !validName(v.Name) {
								return invalid
							}
							a.Name = v.Name
						}
						if v.Enabled != nil {
							a.Enabled = *v.Enabled
						}
						if v.Permissions != nil {
							a.Permissions = v.Permissions
						}
						s.Applications[a.ID] = a
						out = a
					case "DELETE":
						for k, x := range s.Keys {
							if x.ApplicationID == a.ID {
								delete(s.Keys, k)
							}
						}
						delete(s.Applications, a.ID)
						status = 204
					default:
						return missing
					}
					return nil
				}
				if len(p) == 4 && p[3] == "keys" {
					switch r.Method {
					case "GET":
						keys := []Key{}
						for _, k := range s.Keys {
							if k.ApplicationID == a.ID {
								keys = append(keys, k)
							}
						}
						out = keys
					case "POST":
						if !validName(v.Name) || v.Type != "" || v.Enabled != nil || v.Permissions != nil {
							return invalid
						}
						if len(s.Keys) >= 200 {
							return conflict
						}
						kind, prefix := "public", "qr_pk_"
						if a.Type == "backend" {
							kind, prefix = "private", "qr_sk_"
						}
						secret := prefix + id()
						hash := sha256.Sum256([]byte(secret))
						k := Key{ID: id(), Name: v.Name, Kind: kind, Prefix: secret[:12], ApplicationID: a.ID, Hash: hex.EncodeToString(hash[:])}
						s.Keys[k.ID] = k
						out = map[string]string{"id": k.ID, "key": secret, "kind": kind}
						status = 201
					default:
						return missing
					}
					return nil
				}
			case "keys":
				if len(p) == 3 && r.Method == "DELETE" {
					k, ok := s.Keys[p[2]]
					if !ok {
						return missing
					}
					k.Revoked = true
					s.Keys[k.ID] = k
					status = 204
					return nil
				}
			}
			return missing
		})
		if e != nil {
			switch {
			case errors.Is(e, missing):
				fail(404, "not_found")
			case errors.Is(e, invalid):
				fail(422, "invalid_request")
			case errors.Is(e, conflict):
				fail(409, "conflict")
			default:
				fail(503, "storage_unavailable")
			}
			return
		}
		if status == 204 {
			w.WriteHeader(status)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(status)
		json.NewEncoder(w).Encode(out)
	})
}
func permissions(p []string) bool {
	if len(p) > 100 {
		return false
	}
	for _, x := range p {
		if x != "generate" && x != "preview" && x != "templates" {
			return false
		}
	}
	return true
}
