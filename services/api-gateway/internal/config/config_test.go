package config

import (
	"strings"
	"testing"
	"time"
)

func clearEnvironment(t *testing.T) {
	t.Helper()

	keys := []string{
		"API_HOST",
		"API_PORT",
		"QR_ENGINE_URL",
		"APP_ENV",
		"LOG_LEVEL",
		"WORKER_COUNT",
		"QUEUE_CAPACITY",
		"REQUEST_TIMEOUT_SECONDS",
		"CACHE_TTL_SECONDS",
		"FIREBASE_PROJECT_ID",
		"GOOGLE_APPLICATION_CREDENTIALS",
	}

	for _, key := range keys {
		t.Setenv(key, "")
	}
}

func TestLoadDefaults(t *testing.T) {
	clearEnvironment(t)

	cfg, err := Load()
	if err != nil {
		t.Fatalf("Erro inesperado: %v", err)
	}

	expected := Config{
		Host:           "127.0.0.1",
		Port:           8080,
		QREngineURL:    "http://127.0.0.1:8001",
		Environment:    "development",
		LogLevel:       "INFO",
		WorkerCount:    2,
		QueueCapacity:  8,
		RequestTimeout: 15 * time.Second,
		CacheTTL:       60 * time.Second,
	}

	if cfg != expected {
		t.Errorf("Configuração predefinida incorrecta")
	}

	if cfg.Address() != "127.0.0.1:8080" {
		t.Errorf("Endereço incorrecto: %s", cfg.Address())
	}
}

func TestLoadCustomEnvironment(t *testing.T) {
	clearEnvironment(t)

	values := map[string]string{
		"API_HOST":                       "0.0.0.0",
		"API_PORT":                       "9090",
		"QR_ENGINE_URL":                  "http://qr-engine:8001",
		"APP_ENV":                        "production",
		"LOG_LEVEL":                      "debug",
		"WORKER_COUNT":                   "4",
		"QUEUE_CAPACITY":                 "32",
		"REQUEST_TIMEOUT_SECONDS":        "30",
		"CACHE_TTL_SECONDS":              "120",
		"FIREBASE_PROJECT_ID":            "gqr-test",
		"GOOGLE_APPLICATION_CREDENTIALS": "credentials.json",
	}

	for key, value := range values {
		t.Setenv(key, value)
	}

	cfg, err := Load()
	if err != nil {
		t.Fatalf("Erro inesperado: %v", err)
	}

	expected := Config{
		Host:              "0.0.0.0",
		Port:              9090,
		QREngineURL:       "http://qr-engine:8001",
		Environment:       "production",
		LogLevel:          "DEBUG",
		WorkerCount:       4,
		QueueCapacity:     32,
		RequestTimeout:    30 * time.Second,
		CacheTTL:          120 * time.Second,
		FirebaseProjectID: "gqr-test",
		GoogleCredentials: "credentials.json",
	}

	if cfg != expected {
		t.Error("Configuração personalizada incorrecta")
	}
}

func TestLoadInvalidEnvironment(t *testing.T) {
	cases := []struct {
		name  string
		key   string
		value string
	}{
		{"host inválido", "API_HOST", "invalid host"},
		{"porta não numérica", "API_PORT", "abc"},
		{"porta zero", "API_PORT", "0"},
		{"porta negativa", "API_PORT", "-1"},
		{"porta demasiado elevada", "API_PORT", "65536"},
		{"URL inválida", "QR_ENGINE_URL", "invalid"},
		{"URL malformada", "QR_ENGINE_URL", "http://%"},
		{"protocolo inválido", "QR_ENGINE_URL", "ftp://localhost"},
		{"URL sem host", "QR_ENGINE_URL", "http://"},
		{"URL com credenciais", "QR_ENGINE_URL", "http://user:pass@localhost"},
		{"URL com query", "QR_ENGINE_URL", "http://localhost?x=1"},
		{"URL com fragmento", "QR_ENGINE_URL", "http://localhost#test"},
		{"URL com caminho", "QR_ENGINE_URL", "http://localhost/render"},
		{"URL com porta inválida", "QR_ENGINE_URL", "http://localhost:65536"},
		{"ambiente inválido", "APP_ENV", "unknown"},
		{"log inválido", "LOG_LEVEL", "INVALID"},
		{"workers não numéricos", "WORKER_COUNT", "abc"},
		{"workers zero", "WORKER_COUNT", "0"},
		{"workers negativos", "WORKER_COUNT", "-1"},
		{"workers excessivos", "WORKER_COUNT", "257"},
		{"fila não numérica", "QUEUE_CAPACITY", "abc"},
		{"fila vazia", "QUEUE_CAPACITY", "0"},
		{"fila excessiva", "QUEUE_CAPACITY", "100001"},
		{"timeout não numérico", "REQUEST_TIMEOUT_SECONDS", "abc"},
		{"timeout zero", "REQUEST_TIMEOUT_SECONDS", "0"},
		{"timeout excessivo", "REQUEST_TIMEOUT_SECONDS", "301"},
		{"cache não numérica", "CACHE_TTL_SECONDS", "abc"},
		{"cache negativa", "CACHE_TTL_SECONDS", "-1"},
		{"cache excessiva", "CACHE_TTL_SECONDS", "86401"},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			clearEnvironment(t)
			t.Setenv(tc.key, tc.value)

			_, err := Load()
			if err == nil {
				t.Fatalf("Esperado erro para %s", tc.key)
			}

			if !strings.Contains(err.Error(), tc.key) {
				t.Errorf("Erro inesperado: %v", err)
			}
		})
	}
}

func TestAddressIPv6(t *testing.T) {
	clearEnvironment(t)
	t.Setenv("API_HOST", "::1")

	cfg, err := Load()
	if err != nil {
		t.Fatal(err)
	}

	if cfg.Address() != "[::1]:8080" {
		t.Errorf("Endereço IPv6 incorrecto: %s", cfg.Address())
	}
}

func TestCacheDisabled(t *testing.T) {
	clearEnvironment(t)
	t.Setenv("CACHE_TTL_SECONDS", "0")

	cfg, err := Load()
	if err != nil {
		t.Fatal(err)
	}

	if cfg.CacheTTL != 0 {
		t.Error("A cache deveria estar desactivada")
	}
}

func TestValidateInvalidConfig(t *testing.T) {
	cases := []struct {
		name   string
		key    string
		change func(*Config)
	}{
		{"porta", "API_PORT", func(c *Config) { c.Port = 0 }},
		{"workers", "WORKER_COUNT", func(c *Config) { c.WorkerCount = 0 }},
		{"fila", "QUEUE_CAPACITY", func(c *Config) { c.QueueCapacity = 0 }},
		{"timeout", "REQUEST_TIMEOUT_SECONDS", func(c *Config) { c.RequestTimeout = 0 }},
		{"cache", "CACHE_TTL_SECONDS", func(c *Config) { c.CacheTTL = -time.Second }},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			clearEnvironment(t)

			cfg, err := Load()
			if err != nil {
				t.Fatal(err)
			}

			tc.change(&cfg)

			err = cfg.Validate()
			if err == nil || !strings.Contains(err.Error(), tc.key) {
				t.Errorf("Esperado erro de validação para %s", tc.key)
			}
		})
	}
}
