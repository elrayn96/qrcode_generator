package cache

import (
	"crypto/sha256"
	"sync"
	"testing"
	"time"
)

func TestCache(t *testing.T) {
	c := New(time.Minute, 4)
	k := []byte("a")

	if _, _, ok := c.Get(k); ok {
		t.Fatal("unexpected hit")
	}

	d := []byte("abc")
	c.Put(k, d, "png")
	d[0] = 'z'

	v, m, ok := c.Get(k)
	if !ok || m != "png" || string(v) != "abc" {
		t.Fatal(v, m, ok)
	}

	v[0] = 'z'
	v, _, _ = c.Get(k)
	if string(v) != "abc" {
		t.Fatal("alias")
	}

	c.Put(k, []byte("d"), "svg")
	c.Put([]byte("b"), []byte("1234"), "png")

	if _, _, ok = c.Get(k); ok {
		t.Fatal("not evicted")
	}

	c.Put(k, []byte("12345"), "png")
	if _, _, ok = c.Get(k); ok {
		t.Fatal("oversize")
	}

	c = New(0, 4)
	c.Put(k, d, "png")

	if _, _, ok = c.Get(k); ok {
		t.Fatal("disabled")
	}
}

func TestExpiration(t *testing.T) {
	c := New(time.Minute, 1024)
	key := []byte("expiration")

	c.Put(key, []byte("data"), "png")

	if _, _, ok := c.Get(key); !ok {
		t.Fatal("expected valid entry")
	}

	hash := sha256.Sum256(key)

	c.mu.Lock()
	e := c.entries[hash]
	e.expires = time.Now().Add(-time.Minute)
	c.entries[hash] = e
	c.mu.Unlock()

	if _, _, ok := c.Get(key); ok {
		t.Fatal("expired entry returned")
	}

	c.mu.Lock()
	defer c.mu.Unlock()

	if _, ok := c.entries[hash]; ok {
		t.Fatal("expired entry not removed")
	}

	if c.bytes != 0 {
		t.Fatal("incorrect memory accounting")
	}
}

func TestConcurrent(t *testing.T) {
	c := New(time.Minute, 1024)

	var wg sync.WaitGroup

	for i := 0; i < 50; i++ {
		wg.Add(1)

		go func() {
			defer wg.Done()

			c.Put([]byte("key"), []byte("data"), "png")
			c.Get([]byte("key"))
		}()
	}

	wg.Wait()
}
