package firebase

import (
	"cloud.google.com/go/firestore"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"github.com/elrayn96/qrcode_generator/services/api-gateway/internal/admin"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

func (c *Client) Update(ctx context.Context, uid string, fn func(*admin.State) error) error {
	h := sha256.Sum256([]byte(uid))
	ref := c.DB.Collection("gateway_owners").Doc(hex.EncodeToString(h[:]))
	return c.DB.RunTransaction(ctx, func(ctx context.Context, tx *firestore.Transaction) error {
		var s admin.State
		snap, e := tx.Get(ref)
		if e == nil {
			if e = snap.DataTo(&s); e != nil {
				return e
			}
		} else if status.Code(e) != codes.NotFound {
			return e
		}
		if e = fn(&s); e != nil {
			return e
		}
		return tx.Set(ref, s)
	})
}
