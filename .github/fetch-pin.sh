#!/usr/bin/env bash
# Gets one thing pins.conf names, and checks it is exactly that before anything uses it.
#
#   .github/fetch-pin.sh <name> <folder>
#
# A release file: downloaded into <folder> and checked against pins.conf's SHA-256; prints
# its path. pi-gen: cloned into <folder> at the tag and checked against pins.conf's commit.
set -euo pipefail
cd "$(dirname "$0")/.."
want="${1:?usage: fetch-pin.sh <name> <folder>}"; dir="${2:?folder}"
line=$(grep -Ev '^[[:space:]]*(#|$)' pins.conf | awk -v n="$want" '$1 == n') || true
[[ -n "$line" ]] || { echo "::error::$want is not in pins.conf" >&2; exit 1; }
read -r name repo rel file sum <<<"$line"
if [[ "$file" == - ]]; then
  git clone -q --depth 1 --branch "$rel" "https://github.com/$repo.git" "$dir"
  got=$(git -C "$dir" rev-parse HEAD)
  [[ "$got" == "$sum" ]] || { echo "::error::$name $rel is at $got, pins.conf says $sum" >&2; exit 1; }
  echo "::notice title=$name::$rel ($sum)" >&2
  echo "$dir"
else
  mkdir -p "$dir"
  curl -fsSL --retry 3 -o "$dir/$file" "https://github.com/$repo/releases/download/$rel/$file"
  echo "$sum  $dir/$file" | sha256sum -c - >&2
  echo "::notice title=$name::$file from $rel (SHA-256 $sum)" >&2
  echo "$dir/$file"
fi
