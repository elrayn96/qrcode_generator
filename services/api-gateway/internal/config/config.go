package config

import (
	"fmt"
	"net"
	"net/url"
	"os"
	"strconv"
	"strings"
	"time"
)

type Config struct {
	Host              string
	Port              int
	QREngineURL       string
	Environment       string
	LogLevel          string
	WorkerCount       int
	QueueCapacity     int
	RequestTimeout    time.Duration
	CacheTTL          time.Duration
	FirebaseProjectID string
	GoogleCredentials string
}

// Load carrega e valida as configurações do ambiente.
func Load() (Config, error) {
	cfg := Config{
		Host:              envString("API_HOST", "127.0.0.1"),
		QREngineURL:       envString("QR_ENGINE_URL", "http://127.0.0.1:8001"),
		Environment:       envString("APP_ENV", "development"),
		LogLevel:          strings.ToUpper(envString("LOG_LEVEL", "INFO")),
		FirebaseProjectID: envString("FIREBASE_PROJECT_ID", ""),
		GoogleCredentials: envString("GOOGLE_APPLICATION_CREDENTIALS", ""),
	}

	var err error

	cfg.Port, err = envInt("API_PORT", 8080, 1, 65535)
	if err != nil {
		return Config{}, err
	}

	cfg.WorkerCount, err = envInt("WORKER_COUNT", 2, 1, 256)
	if err != nil {
		return Config{}, err
	}

	cfg.QueueCapacity, err = envInt("QUEUE_CAPACITY", 8, 1, 100000)
	if err != nil {
		return Config{}, err
	}

	timeout, err := envInt("REQUEST_TIMEOUT_SECONDS", 15, 1, 300)
	if err != nil {
		return Config{}, err
	}
	cfg.RequestTimeout = time.Duration(timeout) * time.Second

	cacheTTL, err := envInt("CACHE_TTL_SECONDS", 60, 0, 86400)
	if err != nil {
		return Config{}, err
	}
	cfg.CacheTTL = time.Duration(cacheTTL) * time.Second

	if err := cfg.Validate(); err != nil {
		return Config{}, err
	}

	return cfg, nil
}

// Address devolve o endereço de escuta do servidor HTTP.
func (c Config) Address() string {
	return net.JoinHostPort(c.Host, strconv.Itoa(c.Port))
}

// Validate verifica a consistência das configurações.
func (c Config) Validate() error {
	if net.ParseIP(c.Host) == nil && c.Host != "localhost" {
		return fmt.Errorf("API_HOST inválido: utilize um endereço IP ou localhost")
	}

	if c.Port < 1 || c.Port > 65535 {
		return fmt.Errorf("API_PORT fora do intervalo permitido")
	}

	engineURL, err := url.Parse(c.QREngineURL)
	if err != nil {
		return fmt.Errorf("QR_ENGINE_URL inválido")
	}

	if (engineURL.Scheme != "http" && engineURL.Scheme != "https") ||
		engineURL.Hostname() == "" ||
		engineURL.User != nil ||
		engineURL.RawQuery != "" ||
		engineURL.ForceQuery ||
		engineURL.Fragment != "" ||
		(engineURL.Path != "" && engineURL.Path != "/") {
		return fmt.Errorf("QR_ENGINE_URL deve ser uma URL base HTTP ou HTTPS válida")
	}

	if port := engineURL.Port(); port != "" {
		number, err := strconv.Atoi(port)
		if err != nil || number < 1 || number > 65535 {
			return fmt.Errorf("QR_ENGINE_URL contém uma porta inválida")
		}
	}

	switch c.Environment {
	case "development", "test", "production":
	default:
		return fmt.Errorf("APP_ENV inválido")
	}

	switch c.LogLevel {
	case "DEBUG", "INFO", "WARN", "ERROR":
	default:
		return fmt.Errorf("LOG_LEVEL inválido")
	}

	if c.WorkerCount < 1 || c.WorkerCount > 256 {
		return fmt.Errorf("WORKER_COUNT fora do intervalo permitido")
	}

	if c.QueueCapacity < 1 || c.QueueCapacity > 100000 {
		return fmt.Errorf("QUEUE_CAPACITY fora do intervalo permitido")
	}

	if c.RequestTimeout < time.Second ||
		c.RequestTimeout > 300*time.Second {
		return fmt.Errorf("REQUEST_TIMEOUT_SECONDS fora do intervalo permitido")
	}

	if c.CacheTTL < 0 || c.CacheTTL > 24*time.Hour {
		return fmt.Errorf("CACHE_TTL_SECONDS fora do intervalo permitido")
	}

	return nil
}

func envString(key, fallback string) string {
	value := strings.TrimSpace(os.Getenv(key))
	if value == "" {
		return fallback
	}

	return value
}

func envInt(key string, fallback, minimum, maximum int) (int, error) {
	value := strings.TrimSpace(os.Getenv(key))
	if value == "" {
		return fallback, nil
	}

	number, err := strconv.Atoi(value)
	if err != nil {
		return 0, fmt.Errorf("%s deve ser um número inteiro", key)
	}

	if number < minimum || number > maximum {
		return 0, fmt.Errorf(
			"%s deve estar entre %d e %d",
			key,
			minimum,
			maximum,
		)
	}

	return number, nil
}
