package server

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestHealth(t *testing.T) {
	router := NewRouter()

	request := httptest.NewRequest(
		http.MethodGet,
		"/healthz",
		nil,
	)

	response := httptest.NewRecorder()

	router.ServeHTTP(response, request)

	if response.Code != http.StatusOK {
		t.Fatalf(
			"Esperado HTTP 200, recebido %d",
			response.Code,
		)
	}

	var body map[string]string

	if err := json.Unmarshal(response.Body.Bytes(), &body); err != nil {
		t.Fatalf("Resposta JSON inválida: %v", err)
	}

	if body["status"] != "ok" {
		t.Fatalf("Estado inesperado: %s", body["status"])
	}

	if body["service"] != "api-gateway" {
		t.Fatalf("Serviço inesperado: %s", body["service"])
	}
}
