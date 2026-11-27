package handlers

import (
	"encoding/json"
	"testing"
)

func TestInvalidCanonical(t *testing.T) {
	for _, s := range []string{`null`, `[]`, `{}`, `{"extra":1}`, `{"type":"bad","data":{}}`, `{"type":"text","data":{"text":""}}`, `{"type":"text","data":{"text":1}}`, `{"type":"text","data":{"text":"x","extra":1}}`, `{"type":"url","data":{"url":"ftp://x"}}`, `{"type":"email","data":{"address":"bad"}}`, `{"type":"wifi","data":{"ssid":"a","security":"bad"}}`, `{"type":"wifi","data":{"ssid":"a","security":"WPA"}}`, `{"type":"wifi","data":{"ssid":"a","security":"nopass","password":"x"}}`, `{"type":"wifi","data":{"ssid":"a","security":"nopass","hidden":null}}`, `{"type":"geo","data":{"latitude":91,"longitude":0}}`, `{"type":"geo","data":{"latitude":null,"longitude":0}}`, `{"type":"text","data":{"text":"x"},"style":null}`, `{"type":"text","data":{"text":"x"},"output":{"size":1024}}`} {
		if _, e := Canonical([]byte(s), true); e == nil {
			t.Errorf("accepted %s", s)
		}
	}
}
func TestAdditionalCanonical(t *testing.T) {
	for _, s := range []string{`{"type":"vcard","data":{"name":"A","phone":"123","email":"a@example.com","organization":"B"}}`, `{"type":"email","data":{"address":"a@example.com","subject":"hello world","body":"text"}}`, `{"type":"wifi","data":{"ssid":"a;b","security":"WPA","password":"secret","hidden":true}}`} {
		b, e := Canonical([]byte(s), true)
		if e != nil {
			t.Fatal(e)
		}
		var m struct{ Output struct{ Size int } }
		if json.Unmarshal(b, &m) != nil || m.Output.Size != 512 {
			t.Fatal(string(b))
		}
	}
}
