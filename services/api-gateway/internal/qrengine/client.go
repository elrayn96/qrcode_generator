package qrengine

import (
	"bytes"
	"context"
	"io"
	"mime"
	"net/http"
	"strings"
)

type Client struct {
	base string
	http *http.Client
}

func New(base string) *Client {
	return &Client{strings.TrimRight(base, "/"), &http.Client{CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}}
}
func (c *Client) Ready(ctx context.Context) bool {
	r, e := http.NewRequestWithContext(ctx, "GET", c.base+"/readyz", nil)
	if e != nil {
		return false
	}
	s, e := c.http.Do(r)
	if e != nil {
		return false
	}
	defer s.Body.Close()
	return s.StatusCode == 200
}
func (c *Client) Render(ctx context.Context, b []byte) ([]byte, string, int) {
	r, e := http.NewRequestWithContext(ctx, "POST", c.base+"/internal/v1/render", bytes.NewReader(b))
	if e != nil {
		return nil, "", 500
	}
	r.Header.Set("Content-Type", "application/json")
	s, e := c.http.Do(r)
	if e != nil {
		if ctx.Err() != nil {
			return nil, "", 504
		}
		return nil, "", 503
	}
	defer s.Body.Close()
	switch s.StatusCode {
	case 200:
	case 400, 413, 415, 422, 500, 503, 504:
		return nil, "", s.StatusCode
	default:
		return nil, "", 503
	}
	mt, _, e := mime.ParseMediaType(s.Header.Get("Content-Type"))
	if e != nil || (mt != "image/png" && mt != "image/svg+xml") {
		return nil, "", 503
	}
	data, e := io.ReadAll(io.LimitReader(s.Body, 32<<20+1))
	if e != nil || len(data) > 32<<20 || len(data) == 0 {
		if ctx.Err() != nil {
			return nil, "", 504
		}
		return nil, "", 503
	}
	return data, mt, 200
}
