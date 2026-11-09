#!/bin/sh
# Offline contract test: fake apk and sleep only; never invokes the package manager.
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
HELPER="$SCRIPT_DIR/retry-director-alpine-deps.sh"
nexora_test_tmp=$(mktemp -d)
trap 'rm -rf "$nexora_test_tmp"' EXIT HUP INT TERM
mkdir -p "$nexora_test_tmp/bin"

cat > "$nexora_test_tmp/bin/apk" <<'STUB_APK'
#!/bin/sh
printf '%s\n' "$*" >> "$APK_CALLS"
[ "$#" -eq 5 ] && [ "$1" = add ] && [ "$2" = --no-cache ] && \
    [ "$3" = python3 ] && [ "$4" = make ] && [ "$5" = g++ ] || exit 97
call_no=$(wc -l < "$APK_CALLS" | tr -d ' ')
line_no=0
while IFS= read -r code; do
    line_no=$((line_no + 1))
    if [ "$line_no" -eq "$call_no" ]; then
        exit "$code"
    fi
done < "$APK_RESULTS"
exit 98
STUB_APK

cat > "$nexora_test_tmp/bin/sleep" <<'STUB_SLEEP'
#!/bin/sh
[ "$#" -eq 1 ] || exit 96
case "$1" in 2|4) ;; *) exit 95 ;; esac
printf '%s\n' "$1" >> "$SLEEP_CALLS"
exit 0
STUB_SLEEP
chmod 700 "$nexora_test_tmp/bin/apk" "$nexora_test_tmp/bin/sleep"

fail() { printf 'FAIL: %s\n' "$1" >&2; exit 1; }
run_case() {
    name=$1 results=$2 expected_status=$3 expected_apk=$4 sleep_spec=$5
    expected_sleeps=$(printf '%b' "$sleep_spec")
    case_dir="$nexora_test_tmp/$name"
    mkdir -m 700 "$case_dir"
    printf '%b\n' "$results" > "$case_dir/results"
    : > "$case_dir/apk.calls"
    : > "$case_dir/sleep.calls"
    if APK_CALLS="$case_dir/apk.calls" APK_RESULTS="$case_dir/results" \
        SLEEP_CALLS="$case_dir/sleep.calls" PATH="$nexora_test_tmp/bin:/usr/bin:/bin" \
        sh "$HELPER" > "$case_dir/stdout" 2> "$case_dir/stderr"; then
        status=0
    else
        status=$?
    fi
    [ "$status" -eq "$expected_status" ] || fail "$name: exit $status, expected $expected_status"
    calls=$(wc -l < "$case_dir/apk.calls" | tr -d ' ')
    [ "$calls" -eq "$expected_apk" ] || fail "$name: $calls apk calls, expected $expected_apk"
    actual_sleeps=$(cat "$case_dir/sleep.calls")
    [ "$actual_sleeps" = "$expected_sleeps" ] || fail "$name: sleep trace '$actual_sleeps', expected '$expected_sleeps'"
    if ! awk '$0 != "add --no-cache python3 make g++" { exit 1 }' "$case_dir/apk.calls"; then
        fail "$name: package command changed"
    fi
    printf 'PASS %s (apk=%s sleeps=%s exit=%s)\n' "$name" "$expected_apk" "${expected_sleeps:-none}" "$status"
}

run_case success-first '0' 0 1 ''
run_case failure-then-success '17\n0' 0 2 '2'
run_case two-failures-then-success '17\n18\n0' 0 3 '2\n4'
run_case three-failures '17\n18\n19' 19 3 '2\n4'
run_case stop-after-success '17\n0\n23' 0 2 '2'
