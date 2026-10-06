#!/usr/bin/env bash
set -euo pipefail

review_date=""
source_app="codex"
space="default"
chunk_size=200

usage() {
  echo "Usage: $0 --date YYYY-MM-DD [--source codex] [--space default]" >&2
}

while (($#)); do
  case "$1" in
    --date) review_date="${2:-}"; shift 2 ;;
    --source) source_app="${2:-}"; shift 2 ;;
    --space) space="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) usage; exit 2 ;;
  esac
done

if [[ ! "$review_date" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
  usage
  exit 2
fi

for command in nmem jq date; do
  command -v "$command" >/dev/null || {
    echo "Missing required command: $command" >&2
    exit 1
  }
done

start_epoch=$(TZ=Asia/Shanghai date -d "$review_date 00:00:00" +%s)
end_epoch=$(TZ=Asia/Shanghai date -d "$review_date tomorrow" +%s)
start_utc=$(date -u -d "@$start_epoch" +%Y-%m-%dT%H:%M:%SZ)
end_utc=$(date -u -d "@$end_epoch" +%Y-%m-%dT%H:%M:%SZ)

threads_json=$(nmem --json fs ls "/threads/$source_app")
work_dir=$(mktemp -d)
trap 'rm -rf "$work_dir"' EXIT
threads_out="$work_dir/threads.jsonl"
: >"$threads_out"

while IFS=$'\t' read -r thread_path title updated_at; do
  [[ -n "$thread_path" ]] || continue
  messages_path="$thread_path/messages.jsonl"
  first_page=$(nmem --json fs cat "$messages_path" --line 1 --lines "$chunk_size")
  total_lines=$(jq -r '.range.total_lines // 0' <<<"$first_page")
  selected="$work_dir/selected.jsonl"
  : >"$selected"

  line=1
  while ((line <= total_lines)); do
    if ((line == 1)); then
      page="$first_page"
    else
      page=$(nmem --json fs cat "$messages_path" --line "$line" --lines "$chunk_size")
    fi
    jq -r '.body // ""' <<<"$page" |
      jq -c --argjson start "$start_epoch" --argjson end "$end_epoch" '
        select(.role == "user" or .role == "assistant")
        | select(.timestamp | type == "string")
        | (.timestamp | sub("\\+00:00$"; "Z") | sub("\\.[0-9]+Z$"; "Z") | fromdateiso8601) as $ts
        | select($ts >= $start and $ts < $end)
        | {id, role, content, order_index, timestamp}
      ' >>"$selected"
    line=$((line + chunk_size))
  done

  if [[ -s "$selected" ]]; then
    jq -n \
      --arg path "$thread_path" \
      --arg title "$title" \
      --arg updated_at "$updated_at" \
      --slurpfile messages "$selected" \
      '{path: $path, title: $title, updated_at: $updated_at, messages: $messages}' \
      >>"$threads_out"
  fi
done < <(
  jq -r --arg start "$start_utc" '
    .entries[]
    | select(.updated_at != null and .updated_at >= $start)
    | [.path, (.title // .name), .updated_at]
    | @tsv
  ' <<<"$threads_json"
)

jq -n \
  --arg review_date "$review_date" \
  --arg timezone "Asia/Shanghai" \
  --arg start_utc "$start_utc" \
  --arg end_utc "$end_utc" \
  --arg source "$source_app" \
  --arg space "$space" \
  --slurpfile threads "$threads_out" \
  '{
    review_date: $review_date,
    timezone: $timezone,
    window: {start_utc: $start_utc, end_utc: $end_utc},
    source: $source,
    space: $space,
    thread_count: ($threads | length),
    message_count: ([$threads[].messages | length] | add // 0),
    threads: $threads
  }'
