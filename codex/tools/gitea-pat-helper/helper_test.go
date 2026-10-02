package main

import (
	"bytes"
	"context"
	"encoding/json"
	"os"
	"path/filepath"
	"runtime/debug"
	"strings"
	"testing"

	auth "code.gitea.io/gitea/models/auth"
	"code.gitea.io/gitea/models/db"
	user "code.gitea.io/gitea/models/user"
	"code.gitea.io/gitea/modules/setting"
	_ "github.com/mattn/go-sqlite3"
	"xorm.io/xorm"
	"xorm.io/xorm/names"
)

// Only synthetic PATs generated in an isolated database are used here.
func fixture(t *testing.T) (context.Context, *auth.AccessToken, *auth.AccessToken, *auth.AccessToken, Target) {
	t.Helper()
	setting.IsProd = true
	e, err := xorm.NewEngine("sqlite3", "file:"+filepath.Join(t.TempDir(), "test.db")+"?mode=rwc&_txlock=immediate")
	if err != nil {
		t.Fatal("test engine init failed")
	}
	e.SetMapper(names.GonicMapper{})
	db.SetDefaultEngine(context.Background(), e)
	t.Cleanup(db.UnsetDefaultEngine)
	if err = e.Sync(new(user.User), new(auth.AccessToken)); err != nil {
		t.Fatal("test schema init failed")
	}
	u := &user.User{ID: 11, Name: "newemaint-routine-merger", LowerName: "newemaint-routine-merger", IsActive: true}
	other := &user.User{ID: 12, Name: "other-agent", LowerName: "other-agent", IsActive: true}
	if _, err = e.Insert(u, other); err != nil {
		t.Fatal("fixture users failed")
	}
	ctx := context.Background()
	ts := []*auth.AccessToken{
		{UID: u.ID, Name: "issue-208-routine-merge-agent", Scope: "write:repository"},
		{UID: u.ID, Name: "unrelated", Scope: "read:user"},
		{UID: other.ID, Name: "other-token", Scope: "read:user"},
	}
	for _, token := range ts {
		if auth.NewAccessToken(ctx, token) != nil {
			t.Fatal("fixture token failed")
		}
	}
	target := Target{ProjectID: "newemaint", Kind: "routine-merge-agent", Username: u.Name, Version: "1.26.4"}
	return ctx, ts[0], ts[1], ts[2], target
}
func assertPresent(t *testing.T, ctx context.Context, ids ...int64) {
	t.Helper()
	for _, id := range ids {
		ok, err := db.ExistByID[auth.AccessToken](ctx, id)
		if err != nil || !ok {
			t.Fatal("unrelated token changed")
		}
	}
}
func req(token *auth.AccessToken) Request {
	return Request{Action: "revoke", ProjectID: "newemaint", Kind: "routine-merge-agent", Token: token.Token, ExpectedTokenID: token.ID, ExpectedUserID: token.UID, ExpectedTokenName: token.Name}
}
func TestExactRevokeAndFreshReadback(t *testing.T) {
	ctx, old, same, other, target := fixture(t)
	// Upstream lookup is exercised before and after deletion.
	if _, err := auth.GetAccessTokenBySHA(ctx, old.Token); err != nil {
		t.Fatal("fixture lookup failed")
	}
	receipt, code := execute(ctx, req(old), target, "1.26.4")
	if code != "" || receipt.Result != "revoked" || receipt.TokenID != old.ID {
		t.Fatal("exact revoke failed", code)
	}
	if _, err := auth.GetAccessTokenBySHA(ctx, old.Token); !auth.IsErrAccessTokenNotExist(err) {
		t.Fatal("revoked token still found")
	}
	assertPresent(t, ctx, same.ID, other.ID)
}
func TestInspectIsReadOnlyAndReturnsOldScopes(t *testing.T) {
	ctx, old, same, other, target := fixture(t)
	r := req(old)
	r.Action = "inspect"
	r.ExpectedTokenID = 0
	r.ExpectedUserID = 0
	r.ExpectedTokenName = ""
	receipt, code := execute(ctx, r, target, "1.26.4")
	if code != "" || receipt.Result != "verified" || receipt.UserID != old.UID || strings.Join(receipt.Scopes, ",") != "write:repository" {
		t.Fatal("inspect failed", code)
	}
	assertPresent(t, ctx, old.ID, same.ID, other.ID)
}
func TestRejectedTargetsHaveZeroDeletion(t *testing.T) {
	for _, name := range []string{"wrong-user", "unknown", "admin", "version", "id", "uid", "name", "project", "kind", "org", "inactive", "ambiguous"} {
		t.Run(name, func(t *testing.T) {
			ctx, old, same, other, target := fixture(t)
			r := req(old)
			version := "1.26.4"
			switch name {
			case "wrong-user":
				r.Token = other.Token
			case "unknown":
				r.Token = strings.Repeat("a", 40)
			case "admin":
				_, _ = db.GetEngine(ctx).ID(old.UID).Cols("is_admin").Update(&user.User{IsAdmin: true})
			case "version":
				version = "1.26.5"
			case "id":
				r.ExpectedTokenID++
			case "uid":
				r.ExpectedUserID++
			case "name":
				r.ExpectedTokenName = "different"
			case "project":
				r.ProjectID = "other"
			case "kind":
				r.Kind = "project-agent"
			case "org":
				_, _ = db.GetEngine(ctx).ID(old.UID).Cols("type").Update(&user.User{Type: user.UserTypeOrganization})
			case "inactive":
				_, _ = db.GetEngine(ctx).ID(old.UID).Cols("is_active").Update(&user.User{IsActive: false})
			case "ambiguous":
				salt := "different-salt"
				dupe := &auth.AccessToken{UID: other.UID, Name: "dup", TokenSalt: salt, TokenHash: auth.HashToken(old.Token, salt), TokenLastEight: old.Token[len(old.Token)-8:], Scope: "read:user"}
				if _, err := db.GetEngine(ctx).Insert(dupe); err != nil {
					t.Fatal("ambiguous fixture failed")
				}
			}
			_, code := execute(ctx, r, target, version)
			if code == "" {
				t.Fatal("unsafe target accepted")
			}
			assertPresent(t, ctx, old.ID, same.ID, other.ID)
		})
	}
}
func TestSecretErrorsAreFixedCodes(t *testing.T) {
	ctx, old, same, other, target := fixture(t)
	canary := "synthetic-secret-canary-must-never-appear"
	r := req(old)
	r.Token = canary
	result, code := execute(ctx, r, target, "1.26.4")
	var output bytes.Buffer
	writeReceipt(&output, result, code)
	if strings.Contains(output.String(), canary) || strings.Contains(output.String(), old.Token) {
		t.Fatal("secret leaked")
	}
	var receipt map[string]any
	if json.Unmarshal(output.Bytes(), &receipt) != nil || receipt["code"] != "TOKEN_UNKNOWN" {
		t.Fatal("fixed error receipt missing")
	}
	assertPresent(t, ctx, old.ID, same.ID, other.ID)
}

func TestStrictRequestAndBuildPins(t *testing.T) {
	valid := `{"action":"inspect","project_id":"newemaint","token_kind":"routine-merge-agent","token":"synthetic"}`
	if _, code := decodeRequest(strings.NewReader(valid)); code != "" {
		t.Fatal(code)
	}
	for _, input := range []string{valid + `{}`, `{"action":"inspect","action":"revoke"}`, `{"sql":"DELETE"}`, `{"username":"admin"}`, `{"token":null}`, strings.Repeat("x", 4097)} {
		if _, code := decodeRequest(strings.NewReader(input)); code != "REQUEST_INVALID" {
			t.Fatal("unsafe schema accepted")
		}
	}
	info := &debug.BuildInfo{GoVersion: "go1.26.3", Deps: []*debug.Module{{Path: "code.gitea.io/gitea", Version: "v1.26.4", Sum: moduleSum}}}
	if !validBuild(info) {
		t.Fatal("pin rejected")
	}
	info.Deps[0].Replace = &debug.Module{Path: "alternate"}
	if validBuild(info) {
		t.Fatal("replacement accepted")
	}
	info.Deps[0].Replace = nil
	info.GoVersion = "go1.26.4"
	if validBuild(info) {
		t.Fatal("different toolchain accepted")
	}
}
func TestCanonicalManifestBindings(t *testing.T) {
	g, err := os.ReadFile("../../config/gitea-governance.json")
	if err != nil {
		t.Fatal(err)
	}
	a, err := os.ReadFile("../../config/host-access-broker.json")
	if err != nil {
		t.Fatal(err)
	}
	for _, kind := range []string{"project-agent", "routine-merge-agent", "manager-audit", "manager-mutation"} {
		target, code := bindTarget(Request{ProjectID: "newemaint", Kind: kind}, g, a)
		if code != "" || target.Username == "" {
			t.Fatal("canonical binding failed", kind, code)
		}
	}
	for _, r := range []Request{{ProjectID: "unknown", Kind: "project-agent"}, {ProjectID: "aisoft-platform", Kind: "routine-merge-agent"}, {ProjectID: "newemaint", Kind: "admin"}} {
		if _, code := bindTarget(r, g, a); code != "TARGET_UNMANAGED" {
			t.Fatal("unmanaged target accepted")
		}
	}
}
func TestDatabaseErrorsNeverPrintUpstreamError(t *testing.T) {
	ctx, old, _, _, target := fixture(t)
	// Real driver error, not a mocked successful revoke transport.
	if err := db.GetXORMEngineForTesting().Close(); err != nil {
		t.Fatal("close failed")
	}
	receipt, code := execute(ctx, req(old), target, "1.26.4")
	var out bytes.Buffer
	writeReceipt(&out, receipt, code)
	if code == "" || strings.Contains(out.String(), old.Token) || strings.Contains(out.String(), "sql:") {
		t.Fatal("unsafe DB error receipt")
	}
}

func TestRevokeFailureRollsBackAndRedactsDriverMessage(t *testing.T) {
	ctx, old, same, other, target := fixture(t)
	// Test-only SQLite trigger injects a real failure containing a synthetic canary.
	// No generic SQL is exposed by the helper runtime.
	canary := "synthetic-driver-secret-canary"
	_, err := db.GetEngine(ctx).Exec("CREATE TRIGGER deny_revoke BEFORE DELETE ON access_token BEGIN SELECT RAISE(ABORT, '" + canary + "'); END")
	if err != nil {
		t.Fatal("trigger fixture failed")
	}
	receipt, code := execute(ctx, req(old), target, "1.26.4")
	var out bytes.Buffer
	writeReceipt(&out, receipt, code)
	if code != "REVOKE_FAILED" || strings.Contains(out.String(), canary) || strings.Contains(out.String(), old.Token) {
		t.Fatal("revoke failure was unsafe")
	}
	assertPresent(t, ctx, old.ID, same.ID, other.ID)
}
