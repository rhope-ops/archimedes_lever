# Tool retirement R4, group W-B: scanner trials (skeleton, in progress)

Evidence only. No verdict is decided here. Written 2026-11-23 by a worker session of "Kit · Tool retirement · 2026-11-23".

## Versions and commits

| Item | Value |
|---|---|
| gitleaks | v8.30.1 (module github.com/zricethezav/gitleaks/v8), built with Go 1.26.11 |
| trufflehog | v3.100.1 source (module github.com/trufflesecurity/trufflehog/v3), built with Go 1.26.0; the binary reports "dev" |
| detect-secrets | 1.5.0 (PyPI) |
| Vale | v3.28.1 (module github.com/vale-cli/vale/v3), built with Go 1.27.4 |
| Repos (HEAD short SHA) | kit 641023e, RADE a99ba73, 90-161.Z 91ccb0c, 33-332.Z 6cbc517, ICF-Source 02a7ed2d |
| History depth (commits reachable from HEAD) | kit 570, RADE 709, 90-161.Z 1371, 33-332.Z 252, ICF-Source 2548 (all complete) |

Install deviation: GitHub release downloads returned HTTP 403 from the agent proxy, so the three Go tools were built from
the Go module proxy (proxy.golang.org) with auto-downloaded Go toolchains. The repos' own CI pins gitleaks 8.30.1: same version.

The full report follows in the next commit.
