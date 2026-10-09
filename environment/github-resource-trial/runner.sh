#!/usr/bin/env bash
set -euo pipefail

# Run on a fresh ubuntu-24.04 GitHub-hosted runner.  All substantial setup and
# verification work runs in one persistent cgroup v2 slice.
official_repo=josusanmartin/riemann
official_commit=6664d243005e12e155c19775b83f53721757414b
proof_name=r_arun_chandru_proof.lean
proof_sha=f7ef331e72e8c34804e196a4cc0c6fdd69bb1c6947a51dfbf60b88a6343aad9d
proof_bytes=1858713
slice="riemanntrial${GITHUB_RUN_ID:?}${GITHUB_RUN_ATTEMPT:?}.slice"
holder="riemanntrial${GITHUB_RUN_ID}${GITHUB_RUN_ATTEMPT}holder.service"
setup_unit="riemanntrial${GITHUB_RUN_ID}${GITHUB_RUN_ATTEMPT}setup.service"
probe_unit="riemanntrial${GITHUB_RUN_ID}${GITHUB_RUN_ATTEMPT}probe.service"
verify_unit="riemanntrial${GITHUB_RUN_ID}${GITHUB_RUN_ATTEMPT}verify.service"
root=/opt/riemann
work=/home/riemann/verification
cg="/sys/fs/cgroup/$slice"

metrics() {
  local label=$1
  printf '\n[%s] slice %s (memory.peak cumulative across phases)\n' "$label" "$slice"
  for name in memory.current memory.peak memory.events memory.swap.current memory.max memory.swap.max cpu.max cpu.stat; do
    if [[ -r "$cg/$name" ]]; then
      printf '%s: ' "$name"
      tr '\n' ' ' < "$cg/$name"
      printf '\n'
    fi
  done
  if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
    {
      printf '### %s\n\n' "$label"
      printf 'Slice: `%s`; `memory.peak` is cumulative across phases.\n\n```text\n' "$slice"
      for name in memory.current memory.peak memory.events memory.swap.current memory.max memory.swap.max cpu.max cpu.stat; do
        if [[ -r "$cg/$name" ]]; then
          printf '\n%s\n' "$name"
          sed -n '1,30p' "$cg/$name"
        fi
      done
      printf '```\n\n'
    } >> "$GITHUB_STEP_SUMMARY"
  fi
}

assert_limits() {
  local bytes=$1 quota period
  [[ "$(<"$cg/memory.max")" == "$bytes" ]] || { echo 'Slice memory.max did not take effect' >&2; exit 92; }
  [[ "$(<"$cg/memory.swap.max")" == 0 ]] || { echo 'Slice memory.swap.max did not take effect' >&2; exit 92; }
  read -r quota period < "$cg/cpu.max"
  [[ "$quota" != max ]] && (( quota <= 4 * period )) || { echo 'Slice CPU quota did not take effect' >&2; exit 92; }
}

preflight() {
  [[ "$(id -u)" -eq 0 ]] || { echo 'Root required for systemd resource trial' >&2; exit 90; }
  [[ "$(uname -m)" == x86_64 ]] || { echo 'Linux x86_64 required' >&2; exit 90; }
  [[ "$(stat -fc %T /sys/fs/cgroup)" == cgroup2fs ]] || { echo 'cgroup v2 required' >&2; exit 90; }
  [[ -d /run/systemd/system ]] || { echo 'System systemd required' >&2; exit 90; }
  systemctl show -p ControlGroup system.slice | grep -q '^ControlGroup=/' || { echo 'systemd cgroup unavailable' >&2; exit 90; }
  python3 -c 'import ctypes; c=ctypes.CDLL(None, use_errno=True); assert c.syscall(444, 0, 0, 1) > 0' || { echo 'Landlock syscall unavailable' >&2; exit 90; }
  id runner >/dev/null || { echo 'GitHub runner account unavailable' >&2; exit 90; }
  [[ "${GITHUB_REPOSITORY:-}" == arun-chandru/riemann_zeros ]] || { echo 'Unexpected repository' >&2; exit 90; }
  [[ "${GITHUB_REF:-}" == refs/heads/codex/resource-check-2026-10-09 ]] || { echo 'Unexpected ref' >&2; exit 90; }
  [[ -f "$GITHUB_WORKSPACE/$proof_name" ]] || { echo 'Proof file missing' >&2; exit 90; }
  [[ "$(stat -c %s "$GITHUB_WORKSPACE/$proof_name")" == "$proof_bytes" ]] || { echo 'Proof byte count changed' >&2; exit 90; }
  printf '%s  %s\n' "$proof_sha" "$GITHUB_WORKSPACE/$proof_name" | sha256sum -c --status || { echo 'Proof digest changed' >&2; exit 90; }
  node_bin="$(find /opt/hostedtoolcache/node -path '/opt/hostedtoolcache/node/22.*/x64/bin/node' -type f 2>/dev/null | sort -V | tail -1)"
  [[ -n "$node_bin" && -x "$node_bin" ]] || { echo 'Preinstalled Node 22 toolcache required' >&2; exit 90; }
  [[ "$("$node_bin" --version)" == v22.* ]] || { echo 'Node major version mismatch' >&2; exit 90; }
  export PATH="$(dirname "$node_bin"):$PATH"
  command -v npm >/dev/null || { echo 'npm unavailable in Node 22 toolcache' >&2; exit 90; }
  command -v systemd-run >/dev/null || { echo 'systemd-run unavailable' >&2; exit 90; }
}

setup() {
  # This function is the systemd setup service, already inside the slice.
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    bash build-essential ca-certificates coreutils curl git jq libssl-dev \
    pkg-config python3 util-linux xz-utils
  apt-get clean
  runuser -u runner -- env -i HOME=/home/riemann ELAN_HOME=/home/riemann/.elan PATH="$PATH" \
    git clone --quiet "https://github.com/$official_repo.git" "$root"
  runuser -u runner -- git -C "$root" checkout --quiet --detach "$official_commit"
  [[ "$(runuser -u runner -- git -C "$root" rev-parse HEAD)" == "$official_commit" ]] || { echo 'Official source pin mismatch' >&2; exit 91; }
  # Match the official E2B build layout: lightweight runtime dependencies first.
  cp "$root/e2b/runtime/package.json" "$root/package.json"
  cp "$root/e2b/runtime/package-lock.json" "$root/package-lock.json"
  runuser -u runner -- env -i HOME=/home/riemann ELAN_HOME=/home/riemann/.elan PATH="$PATH" \
    npm --prefix "$root" ci --no-audit --no-fund
  runuser -u runner -- env -i HOME=/home/riemann ELAN_HOME=/home/riemann/.elan PATH="$PATH" \
    bash "$root/scripts/prepare-e2b-template.sh"
  # Match the official template's precompiled candidate preparer; tsx can use
  # an IPC socket and must never be run under the no-network syscall filter.
  install -d -o runner -g runner -m 0755 "$root/.runtime"
  runuser -u runner -- env -i HOME=/home/riemann PATH="$PATH" \
    "$root/node_modules/@esbuild/linux-x64/bin/esbuild" \
      "$root/scripts/prepare-candidate.ts" --bundle --platform=node \
      --format=esm --outdir="$root/.runtime" --out-extension:.js=.mjs
  git -c safe.directory="$root" -C "$root" show "$official_commit:package.json" > "$root/package.json"
  git -c safe.directory="$root" -C "$root" show "$official_commit:package-lock.json" > "$root/package-lock.json"
  [[ -s "$root/.runtime/prepare-candidate.mjs" ]] || { echo 'Precompiled candidate preparer missing' >&2; exit 91; }
  # The official runtime wrapper uses /opt/riemann and /home/riemann exactly.
  [[ -s "$root/zeta23/.lake/build/lib/lean/Zeta23/Unconditional.olean" ]] || { echo 'Trusted Zeta build incomplete' >&2; exit 91; }
  for tool in comparator lean4export landrun nanoda_bin lake; do
    [[ -x "$root/tools/bin/$tool" ]] || { echo "Missing verifier tool: $tool" >&2; exit 91; }
  done
  # Seal trusted source and binaries before processing the proof.
  git config --system --add safe.directory "$root/zeta23"
  while IFS= read -r repo; do git config --system --add safe.directory "$repo"; done < <(
    find "$root/zeta23/.lake/packages" -mindepth 2 -maxdepth 2 -type d -name .git -exec dirname {} + | LC_ALL=C sort
  )
  chown -R root:root "$root" /home/riemann/.elan
  find "$root" /home/riemann/.elan -type d -exec chmod a+rx,a-w {} +
  find "$root" /home/riemann/.elan -type f -exec chmod a+r,a-w {} +
  printf 'Pinned official verifier setup complete at %s\n' "$official_commit"
}

copy_workspace_tree() {
  local source=$1 destination=$2
  [[ -d "$source" && -d "$destination" && ! -L "$destination" ]] || return 94
  [[ -z "$(find "$destination" -mindepth 1 -maxdepth 1 -print -quit)" ]] || return 94
  # rsync uses socketpair even for local copies. GNU cp needs no socket IPC.
  # Select top-level entries so nested .lake directories and dotfiles survive.
  find "$source" -mindepth 1 -maxdepth 1 ! -name .lake \
    -exec cp -a --no-preserve=ownership --target-directory="$destination" -- {} +
  # Default find traversal never follows symlinks into the trusted source.
  find "$destination" \( -type d -o -type f \) -exec chmod u+w -- {} +
}

probe() (
  python3 -c 'import socket' || exit 93
  printf 'Python socket baseline ready\n'
  set +e
  python3 -c 'import socket; socket.socket(socket.AF_INET, socket.SOCK_STREAM)' >/dev/null 2>&1
  local inet_status=$?
  python3 -c 'import socket; socket.socketpair()' >/dev/null 2>&1
  local unix_status=$?
  set -e
  printf 'Network probe exit statuses: inet=%s unix=%s\n' "$inet_status" "$unix_status"
  [[ "$inet_status" -ne 0 && "$unix_status" -ne 0 ]]

  probe_dir="$(mktemp -d /home/riemann/riemann-preflight.XXXXXX)"
  [[ "$probe_dir" == /home/riemann/riemann-preflight.* && -d "$probe_dir" && ! -L "$probe_dir" ]] || exit 94
  trap 'chmod -R u+w -- "$probe_dir"; rm -rf -- "$probe_dir"' EXIT
  mkdir -p "$probe_dir/source/.lake" "$probe_dir/source/.git" \
    "$probe_dir/source/nested/.lake" "$probe_dir/source/dir with space" "$probe_dir/copy"
  printf 'hidden\n' > "$probe_dir/source/.hidden"
  printf 'git\n' > "$probe_dir/source/.git/config"
  printf 'excluded\n' > "$probe_dir/source/.lake/excluded"
  printf 'retained\n' > "$probe_dir/source/nested/.lake/retained"
  printf '#!/bin/sh\nexit 0\n' > "$probe_dir/source/dir with space/executable"
  printf 'trusted\n' > "$probe_dir/trusted"
  chmod 0755 "$probe_dir/source/dir with space/executable"
  chmod 0444 "$probe_dir/trusted"
  ln -s .hidden "$probe_dir/source/file-link"
  ln -s nested "$probe_dir/source/dir-link"
  ln -s missing "$probe_dir/source/dangling-link"
  ln -s ../trusted "$probe_dir/source/trusted-link"
  chmod -R a-w -- "$probe_dir/source"
  copy_workspace_tree "$probe_dir/source" "$probe_dir/copy"
  [[ ! -e "$probe_dir/copy/.lake" && -f "$probe_dir/copy/.git/config" ]]
  [[ -f "$probe_dir/copy/nested/.lake/retained" && -x "$probe_dir/copy/dir with space/executable" ]]
  [[ -L "$probe_dir/copy/file-link" && -L "$probe_dir/copy/dir-link" && -L "$probe_dir/copy/dangling-link" ]]
  [[ "$(readlink "$probe_dir/copy/file-link")" == .hidden && "$(readlink "$probe_dir/copy/dir-link")" == nested ]]
  [[ "$(readlink "$probe_dir/copy/trusted-link")" == ../trusted ]]
  [[ "$(stat -c %a "$probe_dir/source/.hidden")" == 444 && "$(stat -c %a "$probe_dir/trusted")" == 444 ]]
  [[ "$(stat -c %a "$probe_dir/source/nested")" == 555 ]]
  [[ -w "$probe_dir/copy/.hidden" && -w "$probe_dir/copy/nested" ]]
  printf 'Workspace copy fixture passed\n'
  node --input-type=module - "$probe_dir" <<'JS'
import assert from 'node:assert/strict';
import { appendFile, cp, mkdir, readFile, readdir, stat, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
assert.match(process.version, /^v22\./);
const workspace = join(process.argv[2], 'copy');
assert.equal(await readFile(join(workspace, '.hidden'), 'utf8'), 'hidden\n');
assert.ok((await readdir(workspace, { withFileTypes: true })).some(entry => entry.name === '.git'));
assert.equal((await stat(join(workspace, '.hidden'))).size, 7);
await mkdir(join(workspace, 'comparator', 'Solution'), { recursive: true });
await writeFile(join(workspace, 'comparator', 'Solution', 'Candidate.lean'), 'fixture\n');
await appendFile(join(workspace, '.hidden'), 'writable\n');
assert.equal(await readFile(join(process.argv[2], 'source', '.hidden'), 'utf8'), 'hidden\n');
await cp(join(workspace, '.git'), join(workspace, 'Candidate'), { recursive: true, errorOnExist: true });
await writeFile(join(workspace, 'config.json'), JSON.stringify({ enable_nanoda: true }));
assert.equal(JSON.parse(await readFile(join(workspace, 'config.json'), 'utf8')).enable_nanoda, true);
console.log(`Node ${process.version} candidate-preparation filesystem fixture passed`);
JS
  chmod -R u+w -- "$probe_dir"
  rm -rf -- "$probe_dir"
  trap - EXIT
)

verify() {
  # RuntimeMaxSec on this unit covers copying, candidate preparation and Comparator.
  install -d -m 0700 "$work" "$work/submission" "$work/submission/proof" "$work/zeta23"
  install -m 0444 "$GITHUB_WORKSPACE/$proof_name" "$work/submission/proof/Solution.lean"
  cp "$GITHUB_WORKSPACE/environment/github-resource-trial/submission.json" "$work/submission/submission.json"
  copy_workspace_tree "$root/zeta23" "$work/zeta23"
  mkdir -p "$work/zeta23/.lake/build/lib/lean" "$work/zeta23/.lake/build/ir"
  ln -s "$root/zeta23/.lake/packages" "$work/zeta23/.lake/packages"
  local part base
  for part in lib/lean ir; do
    while IFS= read -r -d '' source; do
      base="$(basename "$source")"
      ln -s "$source" "$work/zeta23/.lake/build/$part/$base"
    done < <(find "$root/zeta23/.lake/build/$part" -mindepth 1 -maxdepth 1 -name 'Zeta23*' -print0)
  done
  cd "$root"
  RIEMANN_RECORDS_PATH="$root/data/records.json" \
    node "$root/.runtime/prepare-candidate.mjs" \
    "$work/submission" "$work/zeta23"
  cd "$work/zeta23"
  export PATH="$root/tools/bin:/home/riemann/.elan/bin:$PATH"
  export ELAN_HOME=/home/riemann/.elan
  export COMPARATOR_LANDRUN="$root/tools/bin/landrun"
  export COMPARATOR_LEAN4EXPORT="$root/tools/bin/lean4export"
  export COMPARATOR_NANODA="$root/tools/bin/nanoda_bin"
  # This official, unchanged script probes syscall-network isolation and Landlock,
  # then invokes Comparator (which builds/exports/compares and replays with NanoDa).
  bash "$root/scripts/run-comparator-sandbox.sh" \
    "$root/tools/bin/comparator" comparator/config-candidate.json
}

main() {
  preflight
  install -d -o runner -g runner -m 0700 /home/riemann
  install -d -o runner -g runner -m 0755 "$root"
  install -d -o runner -g runner -m 0700 /home/riemann/verification
  systemd-run --quiet --unit="$holder" --slice="$slice" \
    --property=User=runner --property=Restart=no /usr/bin/sleep infinity
  cleanup() {
    metrics final || true
    systemctl stop "$holder" || true
    systemctl stop "$slice" || true
  }
  trap cleanup EXIT
  systemctl set-property --runtime "$slice" CPUQuota=400% MemoryMax=12G MemorySwapMax=0
  assert_limits 12884901888
  metrics initial
  # Prove that the intended systemd sandbox properties are available before
  # downloading or building trusted tools, and before touching the proof.
  # Deny the same network syscalls as the official wrapper, but return EPERM
  # rather than SIGSYS so incidental libc/NSS socket attempts can fall back.
  systemd-run --unit="$probe_unit" --slice="$slice" --wait --pipe --collect \
    --property=User=runner --property=PrivateNetwork=yes \
    --property=SystemCallArchitectures=native \
    --property=SystemCallFilter=~@network-io \
    --property=SystemCallErrorNumber=EPERM \
    --property=RestrictAddressFamilies=AF_UNIX \
    --property=NoNewPrivileges=yes --property=TasksMax=512 \
    --property=LimitCORE=0 \
    --setenv="PATH=$PATH" --setenv="HOME=/home/riemann" \
    --setenv="GITHUB_RUN_ID=$GITHUB_RUN_ID" \
    --setenv="GITHUB_RUN_ATTEMPT=$GITHUB_RUN_ATTEMPT" \
    -- /usr/bin/bash "$GITHUB_WORKSPACE/environment/github-resource-trial/runner.sh" probe
  systemd-run --unit="$setup_unit" --slice="$slice" --wait --pipe --collect \
    --property=RuntimeMaxSec=5400 --setenv="PATH=$PATH" \
    --setenv="GITHUB_RUN_ID=$GITHUB_RUN_ID" \
    --setenv="GITHUB_RUN_ATTEMPT=$GITHUB_RUN_ATTEMPT" \
    -- bash "$GITHUB_WORKSPACE/environment/github-resource-trial/runner.sh" setup
  metrics after-setup
  # Retain the slice across phases so setup page-cache charges remain visible.
  # Reclaim what the kernel can before enforcing the tighter verifier cap.
  if [[ -w "$cg/memory.reclaim" ]]; then
    printf '%s' 4294967296 > "$cg/memory.reclaim" || true
  fi
  if (( $(<"$cg/memory.current") > 7*1024*1024*1024 )); then
    echo 'Setup cache could not be reclaimed below the 7 GiB verifier limit' >&2
    exit 92
  fi
  systemctl set-property --runtime "$slice" MemoryMax=7G MemorySwapMax=0
  assert_limits 7516192768
  metrics before-verification
  systemd-run --unit="$verify_unit" --slice="$slice" --wait --pipe --collect \
    --property=User=runner --property=WorkingDirectory=/home/riemann \
    --property=PrivateNetwork=yes --property=SystemCallFilter=~@network-io \
    --property=SystemCallErrorNumber=EPERM \
    --property=SystemCallArchitectures=native \
    --property=RestrictAddressFamilies=AF_UNIX \
    --property=NoNewPrivileges=yes --property=TasksMax=512 \
    --property=LimitFSIZE=8589934592 --property=RuntimeMaxSec=3200 \
    --property=TimeoutStopSec=15 \
    --setenv="PATH=$PATH" --setenv="HOME=/home/riemann" \
    --setenv="GITHUB_WORKSPACE=$GITHUB_WORKSPACE" \
    --setenv="GITHUB_RUN_ID=$GITHUB_RUN_ID" \
    --setenv="GITHUB_RUN_ATTEMPT=$GITHUB_RUN_ATTEMPT" \
    -- bash "$GITHUB_WORKSPACE/environment/github-resource-trial/runner.sh" verify
  metrics after-verification
}

case "${1:-}" in
  setup) setup ;;
  probe) probe ;;
  verify) verify ;;
  '') main ;;
  *) echo 'Usage: runner.sh [setup|probe|verify]' >&2; exit 2 ;;
esac
