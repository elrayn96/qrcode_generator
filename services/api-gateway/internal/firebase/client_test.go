package firebase

import (
	"context"
	"os"
	"testing"
	"time"
)

func TestMissingProject(t *testing.T) {
	if _, e := Open(context.Background(), "", ""); e == nil {
		t.Fatal("expected error")
	}
}
func TestIntegration(t *testing.T) {
	if os.Getenv("GQR_FIREBASE_INTEGRATION") != "1" {
		t.Skip("opt-in integration")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	c, e := Open(ctx, os.Getenv("FIREBASE_PROJECT_ID"), os.Getenv("GOOGLE_APPLICATION_CREDENTIALS"))
	if e != nil {
		t.Fatal("initialization failed")
	}
	defer c.Close()
	if _, e = c.Auth.GetUser(ctx, os.Getenv("GQR_TEST_UID")); e != nil {
		t.Fatal("auth lookup failed")
	}
	if _, e = c.DB.Collection("projects").Limit(1).Documents(ctx).GetAll(); e != nil {
		t.Fatal("Firestore read failed")
	}
}
