package main

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"

	auth "code.gitea.io/gitea/models/auth"
	"code.gitea.io/gitea/models/db"
	user "code.gitea.io/gitea/models/user"
	"xorm.io/xorm"
	"xorm.io/xorm/names"
)

// Test-only export for the real binary's disposable-container test. The
// production helper never sees this environment variable and never creates schema.
func TestExportProcessFixture(t *testing.T) {
	path := os.Getenv("AISOFT_HELPER_PROCESS_FIXTURE")
	if path == "" {
		t.Skip("explicit synthetic process fixture export not requested")
	}
	if !filepath.IsAbs(path) {
		t.Fatal("fixture path must be absolute")
	}
	f, err := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if err != nil {
		t.Fatal("fixture path is not fresh")
	}
	_ = f.Close()
	e, err := xorm.NewEngine("sqlite3", path)
	if err != nil {
		t.Fatal("fixture engine failed")
	}
	e.SetMapper(names.GonicMapper{})
	db.SetDefaultEngine(context.Background(), e)
	defer db.UnsetDefaultEngine()
	if e.Sync(new(user.User), new(auth.AccessToken)) != nil {
		t.Fatal("fixture schema failed")
	}
	if _, err = e.Insert(&user.User{ID: 11, Name: "newemaint-routine-merger", LowerName: "newemaint-routine-merger", IsActive: true},
		&user.User{ID: 12, Name: "other-agent", LowerName: "other-agent", IsActive: true}); err != nil {
		t.Fatal("fixture account insert failed")
	}
	for i, raw := range []string{strings.Repeat("c316", 10), strings.Repeat("d316", 10), strings.Repeat("e316", 10)} {
		uid, name := int64(11), "unrelated"
		if i == 0 {
			name = "issue-208-routine-merge-agent"
		} else if i == 2 {
			uid, name = 12, "other"
		}
		token := &auth.AccessToken{ID: int64(i + 1), UID: uid, Name: name, TokenHash: auth.HashToken(raw, "synthetic-salt-316"),
			TokenSalt: "synthetic-salt-316", TokenLastEight: raw[len(raw)-8:], Scope: "write:repository"}
		if _, err = e.Insert(token); err != nil {
			t.Fatal("fixture token insert failed")
		}
	}
}
