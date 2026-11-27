// Package cache stores bounded, short-lived render results in memory.
package cache

import (
	"crypto/sha256"
	"sync"
	"time"
)

type entry struct {
	data    []byte
	media   string
	expires time.Time
}
type Cache struct {
	mu      sync.Mutex
	entries map[[32]byte]entry
	ttl     time.Duration
	bytes   int
	limit   int
}

func New(ttl time.Duration, limit int) *Cache {
	return &Cache{entries: make(map[[32]byte]entry), ttl: ttl, limit: limit}
}
func (c *Cache) Get(key []byte) ([]byte, string, bool) {
	c.mu.Lock()
	defer c.mu.Unlock()
	k := sha256.Sum256(key)
	e, ok := c.entries[k]
	if !ok {
		return nil, "", false
	}
	if !time.Now().Before(e.expires) {
		delete(c.entries, k)
		c.bytes -= len(e.data)
		return nil, "", false
	}
	return append([]byte(nil), e.data...), e.media, true
}
func (c *Cache) Put(key, data []byte, media string) {
	if c.ttl <= 0 || len(data) == 0 || len(data) > c.limit {
		return
	}
	c.mu.Lock()
	defer c.mu.Unlock()
	now := time.Now()
	for k, e := range c.entries {
		if !now.Before(e.expires) {
			delete(c.entries, k)
			c.bytes -= len(e.data)
		}
	}
	k := sha256.Sum256(key)
	if e, ok := c.entries[k]; ok {
		c.bytes -= len(e.data)
		delete(c.entries, k)
	}
	for k, e := range c.entries {
		if c.bytes+len(data) <= c.limit && len(c.entries) < 256 {
			break
		}
		delete(c.entries, k)
		c.bytes -= len(e.data)
	}
	c.entries[k] = entry{append([]byte(nil), data...), media, now.Add(c.ttl)}
	c.bytes += len(data)
}
