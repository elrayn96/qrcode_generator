package handlers

import (
	"encoding/json"
	"testing"
)

func TestCanonical(t *testing.T) {
	for _, c := range []struct{ body, want string }{{`{"type":"text","data":{"text":"hello"}}`, "hello"}, {`{"type":"url","data":{"url":"https://example.com"}}`, "https://example.com"}, {`{"type":"phone","data":{"phone":"123"}}`, "tel:123"}, {`{"type":"sms","data":{"phone":"123"}}`, "SMSTO:123:"}, {`{"type":"email","data":{"address":"a@example.com"}}`, "mailto:a@example.com"}, {`{"type":"wifi","data":{"ssid":"abc","security":"nopass"}}`, "WIFI:T:nopass;S:abc;P:;H:false;;"}, {`{"type":"geo","data":{"latitude":1,"longitude":2}}`, "geo:1,2"}} {
		b, e := Canonical([]byte(c.body), false)
		var m map[string]any
		json.Unmarshal(b, &m)
		if e != nil || m["content"] != c.want {
			t.Errorf("%s: %s %v", c.body, b, e)
		}
	}
}
