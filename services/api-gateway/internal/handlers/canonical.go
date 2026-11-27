package handlers

import (
	"encoding/json"
	"errors"
	"fmt"
	"net/mail"
	"net/url"
	"strings"
	"unicode/utf8"
)

func Canonical(body []byte, preview bool) ([]byte, error) {
	bad := errors.New("invalid request")
	var m map[string]json.RawMessage
	if json.Unmarshal(body, &m) != nil || m == nil {
		return nil, bad
	}
	for k := range m {
		switch k {
		case "type", "data", "output", "options", "style":
		default:
			return nil, bad
		}
	}
	var kind string
	var d map[string]json.RawMessage
	if json.Unmarshal(m["type"], &kind) != nil || json.Unmarshal(m["data"], &d) != nil || d == nil {
		return nil, bad
	}
	used := map[string]bool{}
	valid := true
	get := func(k string, max int, required bool) string {
		used[k] = true
		raw, ok := d[k]
		if !ok && !required {
			return ""
		}
		var s string
		if json.Unmarshal(raw, &s) != nil || s == "" || utf8.RuneCountInString(s) > max {
			valid = false
		}
		return s
	}
	email := func(s string) string {
		a, e := mail.ParseAddress(s)
		if e != nil || a.Address != s {
			valid = false
		}
		return s
	}
	esc := strings.NewReplacer("\\", "\\\\", ";", "\\;", ",", "\\,", ":", "\\:", "\n", "\\n", "\r", "")
	var content string
	switch kind {
	case "text":
		content = get("text", 2048, true)
	case "url":
		content = get("url", 2048, true)
		u, e := url.Parse(content)
		if e != nil || u.Hostname() == "" || (u.Scheme != "http" && u.Scheme != "https") || strings.ContainsAny(content, " \t\r\n") {
			valid = false
		}
	case "phone":
		content = "tel:" + get("phone", 40, true)
	case "sms":
		content = "SMSTO:" + get("phone", 40, true) + ":" + get("message", 1024, false)
	case "email":
		a := email(get("address", 254, true))
		q := url.Values{}
		if s := get("subject", 256, false); s != "" {
			q.Set("subject", s)
		}
		if s := get("body", 2048, false); s != "" {
			q.Set("body", s)
		}
		content = "mailto:" + a
		if len(q) > 0 {
			content += "?" + strings.ReplaceAll(q.Encode(), "+", "%20")
		}
	case "wifi":
		s := get("security", 6, true)
		ssid := get("ssid", 32, true)
		p := get("password", 128, s != "nopass")
		if s != "WPA" && s != "WEP" && s != "nopass" {
			valid = false
		}
		if s == "nopass" && p != "" {
			valid = false
		}
		used["hidden"] = true
		var h bool
		if raw, ok := d["hidden"]; ok && (string(raw) == "null" || json.Unmarshal(raw, &h) != nil) {
			valid = false
		}
		content = fmt.Sprintf("WIFI:T:%s;S:%s;P:%s;H:%t;;", s, esc.Replace(ssid), esc.Replace(p), h)
	case "vcard":
		n := get("name", 256, true)
		content = "BEGIN:VCARD\r\nVERSION:3.0\r\nFN:" + esc.Replace(n) + "\r\nN:" + esc.Replace(n) + ";;;;\r\n"
		for _, f := range []struct {
			k, label string
			max      int
		}{{"phone", "TEL", 40}, {"email", "EMAIL", 254}, {"organization", "ORG", 256}} {
			s := get(f.k, f.max, false)
			if s != "" {
				if f.k == "email" {
					email(s)
				}
				content += f.label + ":" + esc.Replace(s) + "\r\n"
			}
		}
		content += "END:VCARD\r\n"
	case "geo":
		var lat, lon float64
		used["latitude"] = true
		used["longitude"] = true
		if json.Unmarshal(d["latitude"], &lat) != nil || json.Unmarshal(d["longitude"], &lon) != nil || string(d["latitude"]) == "null" || string(d["longitude"]) == "null" || lat < -90 || lat > 90 || lon < -180 || lon > 180 {
			valid = false
		}
		content = fmt.Sprintf("geo:%g,%g", lat, lon)
	default:
		return nil, bad
	}
	for k := range d {
		if !used[k] {
			valid = false
		}
	}
	if !valid || utf8.RuneCountInString(content) > 4096 {
		return nil, bad
	}
	delete(m, "type")
	delete(m, "data")
	m["content"], _ = json.Marshal(content)
	for _, k := range []string{"output", "options", "style"} {
		if raw, ok := m[k]; ok {
			var obj map[string]json.RawMessage
			if json.Unmarshal(raw, &obj) != nil || obj == nil {
				return nil, bad
			}
		}
	}
	if preview {
		var o map[string]json.RawMessage
		if raw, ok := m["output"]; ok {
			json.Unmarshal(raw, &o)
		} else {
			o = map[string]json.RawMessage{}
		}
		if raw, ok := o["size"]; ok {
			var n int
			if json.Unmarshal(raw, &n) != nil || n < 128 || n > 512 {
				return nil, bad
			}
		} else {
			o["size"] = json.RawMessage("512")
		}
		m["output"], _ = json.Marshal(o)
	}
	return json.Marshal(m)
}
