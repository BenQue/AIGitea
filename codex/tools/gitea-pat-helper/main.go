package main

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"os"
	"os/exec"
	osuser "os/user"
	"path/filepath"
	"regexp"
	"runtime"
	"runtime/debug"
	"strconv"
	"strings"
	"syscall"
	"time"

	"code.gitea.io/gitea/models/db"
	"code.gitea.io/gitea/modules/log"
	"code.gitea.io/gitea/modules/setting"
)

const governancePath = "/usr/local/share/aisoft/gitea-governance.json"
const accessPath = "/usr/local/share/aisoft/host-access-broker.json"
const giteaConfigPath = "/etc/gitea/app.ini"
const giteaBinaryPath = "/usr/local/bin/gitea"
const moduleSum = "h1:VDA00oYg16VrQf3sES0NuS/oiDLAIVng/7jKHsBMP/w="

func main() {
	if len(os.Args) == 2 && os.Args[1] == "--version" {
		_ = json.NewEncoder(os.Stdout).Encode(map[string]string{"helper_version": "1", "gitea_model_version": modelVersion, "toolchain": runtime.Version()})
		return
	}
	if len(os.Args) != 1 {
		writeReceipt(os.Stdout, Receipt{}, "REQUEST_INVALID")
		os.Exit(2)
	}
	os.Clearenv()
	// Upstream fatal/config/SQL logs must not expose DSNs or token error values.
	log.GetManager().GetLogger(log.DEFAULT).ReplaceAllWriters()
	log.OsExiter = func(int) { panic(failure("CONFIG_INVALID")) }
	receipt, code := run()
	writeReceipt(os.Stdout, receipt, code)
	if code != "" {
		os.Exit(2)
	}
}

func run() (receipt Receipt, code string) {
	defer func() {
		if recover() != nil {
			receipt = Receipt{}
			code = "INTERNAL_ERROR"
		}
	}()
	if runtime.GOOS != "linux" {
		return Receipt{}, "HOST_UNSUPPORTED"
	}
	build, ok := debug.ReadBuildInfo()
	if !ok || !validBuild(build) {
		return Receipt{}, "BUILD_PIN_MISMATCH"
	}
	service, err := osuser.Lookup("git")
	if err != nil || service.Uid != strconv.Itoa(os.Geteuid()) || os.Geteuid() == 0 {
		return Receipt{}, "SERVICE_IDENTITY_REQUIRED"
	}
	r, code := decodeRequest(os.Stdin)
	if code != "" {
		return Receipt{}, code
	}
	target, code := resolveTarget(r, governancePath, accessPath)
	if code != "" {
		return Receipt{}, code
	}
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	// No configurable executable, flags, config path or server endpoint.
	command := exec.CommandContext(ctx, giteaBinaryPath, "--version")
	command.Env = []string{"LANG=C", "PATH=/usr/bin:/bin"}
	var version bytes.Buffer
	command.Stdout = &version
	command.Stderr = io.Discard
	if command.Run() != nil || !regexp.MustCompile(`^Gitea version 1\.26\.4 built with go[^\r\n]+$`).MatchString(strings.TrimSpace(version.String())) {
		return Receipt{}, "VERSION_MISMATCH"
	}
	if code = initDatabase(ctx, giteaConfigPath); code != "" {
		return Receipt{}, code
	}
	defer db.UnsetDefaultEngine()
	return execute(ctx, r, target, modelVersion)
}

func validBuild(info *debug.BuildInfo) bool {
	if info.GoVersion != "go1.26.3" {
		return false
	}
	for _, dep := range info.Deps {
		if dep.Path == "code.gitea.io/gitea" {
			return dep.Version == "v1.26.4" && dep.Sum == moduleSum && dep.Replace == nil
		}
	}
	return false
}

func decodeRequest(reader io.Reader) (r Request, code string) {
	raw, err := io.ReadAll(io.LimitReader(reader, 4097))
	if err != nil || len(raw) > 4096 {
		return Request{}, "REQUEST_INVALID"
	}
	// Reject duplicate/unknown fields and extra documents rather than last-key-wins.
	d := json.NewDecoder(bytes.NewReader(raw))
	first, err := d.Token()
	if err != nil || first != json.Delim('{') {
		return Request{}, "REQUEST_INVALID"
	}
	fields := map[string]json.RawMessage{}
	allowed := map[string]bool{"action": true, "project_id": true, "token_kind": true, "token": true, "expected_token_name": true, "expected_token_id": true, "expected_user_id": true}
	for d.More() {
		key, err := d.Token()
		if err != nil {
			return Request{}, "REQUEST_INVALID"
		}
		name, ok := key.(string)
		if !ok || !allowed[name] || fields[name] != nil {
			return Request{}, "REQUEST_INVALID"
		}
		var value json.RawMessage
		if d.Decode(&value) != nil || string(value) == "null" {
			return Request{}, "REQUEST_INVALID"
		}
		fields[name] = value
	}
	if _, err = d.Token(); err != nil {
		return Request{}, "REQUEST_INVALID"
	}
	if _, err = d.Token(); err != io.EOF {
		return Request{}, "REQUEST_INVALID"
	}
	canonical, _ := json.Marshal(fields)
	if json.Unmarshal(canonical, &r) != nil || (r.Action != "inspect" && r.Action != "revoke") || len(r.Token) == 0 || len(r.Token) > 128 || !regexp.MustCompile(`^[a-z][a-z0-9-]{0,63}$`).MatchString(r.ProjectID) {
		return Request{}, "REQUEST_INVALID"
	}
	return r, ""
}

func trustedRead(path string, max int64) ([]byte, string) {
	// Every ancestor is root-owned and cannot be changed by an unprivileged caller.
	for dir := filepath.Dir(path); ; dir = filepath.Dir(dir) {
		st, err := os.Lstat(dir)
		if err != nil || !st.IsDir() || st.Mode().Perm()&0022 != 0 || st.Sys().(*syscall.Stat_t).Uid != 0 {
			return nil, "TRUSTED_PATH_UNSAFE"
		}
		if dir == "/" {
			break
		}
	}
	fd, err := syscall.Open(path, syscall.O_RDONLY|syscall.O_NOFOLLOW, 0)
	if err != nil {
		return nil, "TRUSTED_FILE_UNAVAILABLE"
	}
	f := os.NewFile(uintptr(fd), path)
	defer f.Close()
	st, err := f.Stat()
	if err != nil || !st.Mode().IsRegular() || st.Mode().Perm()&0022 != 0 || st.Sys().(*syscall.Stat_t).Uid != 0 || st.Size() > max {
		return nil, "TRUSTED_FILE_UNSAFE"
	}
	raw, err := io.ReadAll(io.LimitReader(f, max+1))
	if err != nil || int64(len(raw)) > max {
		return nil, "TRUSTED_FILE_UNAVAILABLE"
	}
	return raw, ""
}

type governance struct {
	Version string `json:"gitea_version"`
	Manager struct {
		Username  string `json:"username"`
		SiteAdmin bool   `json:"site_admin"`
	} `json:"platform_manager"`
	Repositories []struct {
		Name    string  `json:"name"`
		Agent   string  `json:"project_agent"`
		Routine *string `json:"routine_merge_agent"`
	} `json:"repositories"`
}
type access struct {
	Projects []struct {
		ID         string  `json:"project_id"`
		Repository string  `json:"repository"`
		Agent      string  `json:"project_agent"`
		Routine    *string `json:"routine_merge_agent"`
	} `json:"projects"`
}

func resolveTarget(r Request, governanceFile, accessFile string) (Target, string) {
	graw, code := trustedRead(governanceFile, 2<<20)
	if code != "" {
		return Target{}, code
	}
	araw, code := trustedRead(accessFile, 2<<20)
	if code != "" {
		return Target{}, code
	}
	return bindTarget(r, graw, araw)
}

func bindTarget(r Request, graw, araw []byte) (Target, string) {
	var g governance
	var a access
	if json.Unmarshal(graw, &g) != nil || json.Unmarshal(araw, &a) != nil || g.Version != modelVersion || g.Manager.SiteAdmin {
		return Target{}, "MANIFEST_INVALID"
	}
	target := Target{ProjectID: r.ProjectID, Kind: r.Kind, Version: g.Version}
	projectCount := 0
	repoCount := 0
	for _, project := range a.Projects {
		if project.ID != r.ProjectID {
			continue
		}
		projectCount++
		for _, repo := range g.Repositories {
			if repo.Name != project.Repository {
				continue
			}
			repoCount++
			switch r.Kind {
			case "manager-audit", "manager-mutation":
				target.Username = g.Manager.Username
			case "project-agent":
				if repo.Agent == project.Agent {
					target.Username = repo.Agent
				}
			case "routine-merge-agent":
				if repo.Routine != nil && project.Routine != nil && *repo.Routine == *project.Routine {
					target.Username = *repo.Routine
				}
			}
		}
	}
	if projectCount != 1 || repoCount != 1 || !regexp.MustCompile(`^[a-z][a-z0-9-]{1,63}$`).MatchString(target.Username) || target.Username == "admin" || target.Username == "ci-bot" {
		return Target{}, "TARGET_UNMANAGED"
	}
	return target, ""
}

func initDatabase(ctx context.Context, path string) string {
	raw, code := trustedRead(path, 2<<20)
	if code != "" {
		return code
	}
	cfg, err := setting.NewConfigProviderFromData(string(raw))
	if err != nil {
		return "CONFIG_INVALID"
	}
	cfg.DisableSaving()
	setting.CfgProvider = cfg
	setting.LoadDBSetting()
	setting.IsProd = true
	setting.Database.AutoMigration = false
	setting.Database.LogSQL = false
	setting.Database.SlowQueryThreshold = 0
	// SQLite mode=rwc must never create a new DB on an erroneous configuration.
	if setting.Database.Type.IsSQLite3() {
		p := setting.Database.Path
		resolved, err := filepath.EvalSymlinks(p)
		if err != nil || !filepath.IsAbs(p) || resolved != filepath.Clean(p) {
			return "DB_PATH_UNSAFE"
		}
		st, err := os.Lstat(p)
		if err != nil || !st.Mode().IsRegular() || int(st.Sys().(*syscall.Stat_t).Uid) != os.Geteuid() || st.Mode().Perm()&0022 != 0 {
			return "DB_PATH_UNSAFE"
		}
	}
	// InitEngine only connects. NEVER InitEngineWithMigration, Sync, or migrations.
	if db.InitEngine(ctx) != nil {
		return "DB_INIT_FAILED"
	}
	if db.GetEngine(ctx).Ping() != nil {
		db.UnsetDefaultEngine()
		return "DB_INIT_FAILED"
	}
	return ""
}
