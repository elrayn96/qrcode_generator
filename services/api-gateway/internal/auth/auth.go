package auth

import (
	"context"
	"errors"
	"net/http"
	"strings"
)

var ErrUnauthorized = errors.New("unauthorized")

type Verifier interface {
	Verify(context.Context, string) (string, error)
}

func Authenticate(r *http.Request, v Verifier) (string, error) {
	values := r.Header.Values("Authorization")
	if v == nil || len(values) != 1 || len(r.Header.Values("X-API-Key")) != 0 {
		return "", ErrUnauthorized
	}
	parts := strings.Fields(values[0])
	if len(parts) != 2 || !strings.EqualFold(parts[0], "Bearer") || len(parts[1]) > 8192 {
		return "", ErrUnauthorized
	}
	uid, err := v.Verify(r.Context(), parts[1])
	if err != nil || uid == "" {
		return "", ErrUnauthorized
	}
	return uid, nil
}
