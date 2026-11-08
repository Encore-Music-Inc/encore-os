#!/usr/bin/env bash
# Checks pins.conf, the one list of what ENCORE. OS is built from:
# - each release is published (not a draft) and has the file attached;
# - the SHA-256 in pins.conf is the one that release published (its .sha256 file);
# - pi-gen: the Raspberry Pi OS tag points to the commit in pins.conf;
# - the README's Pinned releases table says the same as pins.conf.
#
#   .github/pins/check.sh           check (CI runs this on every build)
#   .github/pins/check.sh --table   print the README table for pins.conf
set -euo pipefail
cd "$(dirname "$0")/../.."

pins() { grep -Ev '^[[:space:]]*(#|$)' pins.conf; }
table() {
  echo "| What | Repository | Release | Exactly |"
  echo "|---|---|---|---|"
  while read -r name repo rel file sum; do
    if [[ "$file" == - ]]; then what="the tag, at commit \`${sum:0:7}\`"
    else what="\`$file\`, SHA-256 \`${sum:0:12}\`"; fi
    echo "| $name | [$repo](https://github.com/$repo) | \`$rel\` | $what |"
  done < <(pins)
}
[[ "${1:-}" == --table ]] && { table; exit 0; }

api() { curl -fsSL --retry 3 ${GH_TOKEN:+-H "Authorization: Bearer $GH_TOKEN"} -H "Accept: application/vnd.github+json" "https://api.github.com/$1"; }
bad=0
fail() { echo "::error file=pins.conf::$*"; bad=1; }
while read -r name repo rel file sum; do
  if [[ "$file" == - ]]; then
    got=$(git ls-remote "https://github.com/$repo.git" "refs/tags/$rel" "refs/tags/$rel^{}" | awk '{ c = $1 } END { print c }')
    if [[ -z "$got" ]]; then fail "$name: no tag $rel in $repo"
    elif [[ "$got" != "$sum" ]]; then fail "$name: tag $rel is at ${got:0:12}, pins.conf says ${sum:0:12}"
    else echo "ok   $name  $rel  (commit ${sum:0:12})"; fi
    continue
  fi
  json=$(api "repos/$repo/releases/tags/$rel") || { fail "$name: $rel is not a published release of $repo"; continue; }
  read -r draft has_file sha_url < <(python3 -c '
import json, sys
r = json.load(sys.stdin); f = sys.argv[1]
names = {a["name"]: a["browser_download_url"] for a in r.get("assets", [])}
print(str(r.get("draft")).lower(), str(f in names).lower(), names.get(f + ".sha256", "-"))' "$file" <<<"$json")
  [[ "$draft" == false ]] || { fail "$name: $rel is a draft, not a published release"; continue; }
  [[ "$has_file" == true ]] || { fail "$name: $rel has no $file"; continue; }
  [[ "$sha_url" != - ]] || { fail "$name: $rel has no $file.sha256"; continue; }
  published=$(curl -fsSL --retry 3 "$sha_url" | awk '{ print $1 }')
  if [[ "$published" != "$sum" ]]; then fail "$name: $rel published SHA-256 ${published:0:12} for $file, pins.conf says ${sum:0:12}"
  else echo "ok   $name  $rel  $file  (SHA-256 ${sum:0:12})"; fi
done < <(pins)

readme=$(awk '/<!-- pinned-releases:start -->/{on=1; next} /<!-- pinned-releases:end -->/{on=0} on' README.md)
if [[ "$readme" != "$(table)" ]]; then
  echo "::error file=README.md::The Pinned releases table doesn't match pins.conf. It should be:"
  table
  bad=1
else
  echo "ok   README Pinned releases table matches pins.conf"
fi
exit "$bad"
