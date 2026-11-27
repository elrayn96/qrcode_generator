package firebase

import (
	"cloud.google.com/go/firestore"
	"context"
	"errors"
	sdk "firebase.google.com/go/v4"
	"firebase.google.com/go/v4/auth"
	"google.golang.org/api/option"
)

type Client struct {
	Auth *auth.Client
	DB   *firestore.Client
}

func Open(ctx context.Context, project, credentials string) (*Client, error) {
	if project == "" {
		return nil, errors.New("Firebase project ID required")
	}
	var opts []option.ClientOption
	if credentials != "" {
		opts = append(opts, option.WithCredentialsFile(credentials))
	}
	app, err := sdk.NewApp(ctx, &sdk.Config{ProjectID: project}, opts...)
	if err != nil {
		return nil, err
	}
	a, err := app.Auth(ctx)
	if err != nil {
		return nil, err
	}
	db, err := app.Firestore(ctx)
	if err != nil {
		return nil, err
	}
	return &Client{a, db}, nil
}
func (c *Client) Verify(ctx context.Context, token string) (string, error) {
	t, e := c.Auth.VerifyIDTokenAndCheckRevoked(ctx, token)
	if e != nil {
		return "", e
	}
	return t.UID, nil
}
func (c *Client) Close() error { return c.DB.Close() }
