#!/bin/sh
set -eu

fail() {
    printf 'release: %s\n' "$1" >&2
    exit 1
}

if [ "$#" -ne 1 ] || [ -z "$1" ]; then
    fail "usage: mate release VERSION"
fi

version=$1
tag="v${version}"

printf '%s\n' "$version" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+((a|b|rc)[0-9]+)?$' ||
    fail "VERSION must be X.Y.Z, X.Y.ZaN, X.Y.ZbN, or X.Y.ZrcN"

[ "$(git branch --show-current)" = "main" ] || fail "release must run on the main branch"
[ -z "$(git status --porcelain)" ] || fail "working tree must be clean"

if git rev-parse --verify --quiet "refs/tags/${tag}" >/dev/null; then
    fail "tag ${tag} already exists locally"
fi

git fetch --no-tags origin
start_head=$(git rev-parse HEAD)
remote_head=$(git rev-parse refs/remotes/origin/main)
[ "$start_head" = "$remote_head" ] || fail "main must match origin/main before release"

current_version=$(uv version --short)

set +e
git ls-remote --exit-code --tags origin "refs/tags/${tag}" >/dev/null 2>&1
remote_tag_status=$?
set -e
case "$remote_tag_status" in
    0) fail "tag ${tag} already exists on origin" ;;
    2) ;;
    *) fail "could not check tag ${tag} on origin" ;;
esac

rollback_needed=true
rollback() {
    status=$?
    if [ "$status" -ne 0 ] && [ "$rollback_needed" = true ]; then
        printf 'release: rolling back local release state\n' >&2
        git tag --delete "$tag" >/dev/null 2>&1 || true
        git reset --hard "$start_head" >/dev/null
    fi
    exit "$status"
}
trap rollback EXIT

if [ "$version" != "$current_version" ]; then
    uv version "$version"
    [ "$(uv version --short)" = "$version" ] ||
        fail "uv normalized VERSION; use the normalized version"

    for changed_path in $(git status --porcelain | cut -c4-); do
        case "$changed_path" in
            pyproject.toml|uv.lock) ;;
            *) fail "version update unexpectedly changed ${changed_path}" ;;
        esac
    done

    git diff --quiet -- pyproject.toml && fail "version update did not change pyproject.toml"
fi

make compatibility
make smoke

git add pyproject.toml uv.lock
git commit --allow-empty -m "Release ${tag}"
git tag --annotate "$tag" --message "Release ${tag}"
git push --atomic origin main "$tag"

rollback_needed=false
printf 'release: pushed %s\n' "$tag"
