package auth

import (
	"context"
	"errors"
	"net/http/httptest"
	"testing"
)

type fake struct{}

func (fake) Verify(_ context.Context, t string) (string, error) {
	if t == "valid" {
		return "uid", nil
	}
	return "", errors.New("invalid")
}
func TestAuthenticate(t *testing.T) {
	for _, x := range []struct {
		header, key string
		ok          bool
	}{{"Bearer valid", "", true}, {"bearer valid", "", true}, {"Bearer invalid", "", false}, {"", "", false}, {"Basic valid", "", false}, {"Bearer valid", "key", false}, {"Bearer valid extra", "", false}} {
		r := httptest.NewRequest("GET", "/", nil)
		r.Header.Set("Authorization", x.header)
		if x.key != "" {
			r.Header.Set("X-API-Key", x.key)
		}
		u, e := Authenticate(r, fake{})
		if (e == nil) != x.ok || (x.ok && u != "uid") {
			t.Fatal(x)
		}
	}
}
