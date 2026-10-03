package main

import (
	"context"
	"crypto/subtle"
	"encoding/json"
	"io"
	"regexp"
	"slices"
	"strings"

	auth "code.gitea.io/gitea/models/auth"
	"code.gitea.io/gitea/models/db"
	user "code.gitea.io/gitea/models/user"
)

const modelVersion = "1.26.4"

type Request struct {
	Action            string `json:"action"`
	ProjectID         string `json:"project_id"`
	Kind              string `json:"token_kind"`
	Token             string `json:"token"`
	ExpectedTokenName string `json:"expected_token_name"`
	ExpectedTokenID   int64  `json:"expected_token_id"`
	ExpectedUserID    int64  `json:"expected_user_id"`
}
type Target struct{ ProjectID, Kind, Username, Version string }
type Receipt struct {
	Result    string   `json:"result"`
	TokenID   int64    `json:"token_id,omitempty"`
	UserID    int64    `json:"user_id,omitempty"`
	TokenName string   `json:"token_name,omitempty"`
	Scopes    []string `json:"scopes,omitempty"`
}
type failure string

func (f failure) Error() string { return string(f) }

// No upstream error value, panic value, hash, salt or raw token leaves this boundary.
func execute(ctx context.Context, r Request, target Target, serverVersion string) (receipt Receipt, code string) {
	defer func() {
		if recover() != nil {
			receipt = Receipt{}
			code = "INTERNAL_ERROR"
		}
	}()
	if serverVersion != modelVersion || target.Version != modelVersion {
		return Receipt{}, "VERSION_MISMATCH"
	}
	if r.ProjectID != target.ProjectID || r.Kind != target.Kind || target.Username == "" {
		return Receipt{}, "TARGET_MISMATCH"
	}
	if r.Action != "inspect" && r.Action != "revoke" {
		return Receipt{}, "REQUEST_INVALID"
	}
	if r.Action == "revoke" && (r.ExpectedTokenID <= 0 || r.ExpectedUserID <= 0 || r.ExpectedTokenName == "") {
		return Receipt{}, "TOKEN_BINDING_REQUIRED"
	}
	err := db.WithTx(ctx, func(tx context.Context) error {
		token, err := auth.GetAccessTokenBySHA(tx, r.Token)
		if auth.IsErrAccessTokenNotExist(err) || auth.IsErrAccessTokenEmpty(err) {
			return failure("TOKEN_UNKNOWN")
		}
		if err != nil {
			return failure("DB_ERROR")
		}
		account, err := user.GetUserByID(tx, token.UID)
		if err != nil {
			return failure("DB_ERROR")
		}
		if account.Name != target.Username || account.LowerName != strings.ToLower(target.Username) || account.IsAdmin || account.IsOrganization() || !account.IsActive {
			return failure("IDENTITY_UNSAFE")
		}
		if (r.ExpectedTokenID != 0 && r.ExpectedTokenID != token.ID) || (r.ExpectedUserID != 0 && r.ExpectedUserID != token.UID) || (r.ExpectedTokenName != "" && r.ExpectedTokenName != token.Name) {
			return failure("TOKEN_BINDING_MISMATCH")
		}
		// Inspect must not turn arbitrary DB strings into public receipts.
		namePattern := `^issue-[1-9][0-9]*-` + regexp.QuoteMeta(target.Kind) + `(-rotation-[0-9a-f]{12})?$`
		if !regexp.MustCompile(namePattern).MatchString(token.Name) {
			return failure("TOKEN_NAME_UNOWNED")
		}
		// GetAccessTokenBySHA returns the first salt/hash match. Reject ambiguity,
		// even if a second salted row contains the same raw token under another UID.
		var candidates []auth.AccessToken
		if err = db.GetEngine(tx).Where("token_last_eight = ?", token.TokenLastEight).Find(&candidates); err != nil {
			return failure("DB_ERROR")
		}
		matches := 0
		for _, candidate := range candidates {
			if subtle.ConstantTimeCompare([]byte(candidate.TokenHash), []byte(auth.HashToken(r.Token, candidate.TokenSalt))) == 1 {
				matches++
			}
		}
		if matches != 1 {
			return failure("TOKEN_AMBIGUOUS")
		}
		normalized, err := token.Scope.Normalize()
		if err != nil || !normalized.HasPermissionScope() {
			return failure("SCOPE_INVALID")
		}
		scopes := strings.Split(string(normalized), ",")
		slices.Sort(scopes)
		receipt = Receipt{Result: "verified", TokenID: token.ID, UserID: token.UID, TokenName: token.Name, Scopes: scopes}
		if r.Action == "inspect" {
			return nil
		}
		if err = auth.DeleteAccessTokenByID(tx, token.ID, token.UID); err != nil {
			return failure("REVOKE_FAILED")
		}
		exists, err := db.ExistByID[auth.AccessToken](tx, token.ID)
		if err != nil || exists {
			return failure("REVOKE_POSTCHECK_FAILED")
		}
		return nil
	})
	if err != nil {
		if f, ok := err.(failure); ok {
			return Receipt{}, string(f)
		}
		return Receipt{}, "DB_TRANSACTION_FAILED"
	}
	if r.Action == "revoke" {
		// Fresh read after commit; a failed confirmation never becomes success.
		exists, err := db.ExistByID[auth.AccessToken](ctx, receipt.TokenID)
		if err != nil || exists {
			return Receipt{}, "REVOKE_UNCONFIRMED"
		}
		receipt.Result = "revoked"
	}
	return receipt, ""
}

func writeReceipt(w io.Writer, r Receipt, code string) {
	if code != "" {
		_ = json.NewEncoder(w).Encode(struct {
			Result string `json:"result"`
			Code   string `json:"code"`
		}{"BLOCKED", code})
		return
	}
	_ = json.NewEncoder(w).Encode(r)
}
