#!/bin/sh
# Runs a real WikkaWiki 1.4.2 with MariaDB in Docker. It runs the Wikka
# installer, adds the action line to the theme's header.php and the settings
# to wikka.config.php, then checks the tag on the home page.
# Usage: ./scripts/verify-docker.sh [wikka-version]   (default 1.4.2)
set -e
VERSION="${1:-1.4.2}"
PORT="${PORT:-8090}"
NET=pa-wikka-test
cd "$(dirname "$0")/.."
WORK=$(mktemp -d)
cleanup() { docker rm -f pa-wikka-web pa-wikka-db >/dev/null 2>&1 || true; docker network rm $NET >/dev/null 2>&1 || true; rm -rf "$WORK"; }
trap cleanup EXIT
docker rm -f pa-wikka-web pa-wikka-db >/dev/null 2>&1 || true; docker network rm $NET >/dev/null 2>&1 || true

curl -fsSL -o "$WORK/wikka.tar.gz" "https://github.com/bakoontz/WikkaWiki/archive/refs/tags/$VERSION.tar.gz"
mkdir "$WORK/site" && tar -xzf "$WORK/wikka.tar.gz" -C "$WORK/site" --strip-components=1
mkdir -p "$WORK/site/plugins/actions/privatusanalytics"
cp plugins/actions/privatusanalytics/privatusanalytics.php "$WORK/site/plugins/actions/privatusanalytics/"

cat > "$WORK/Dockerfile" <<'DOCKER'
FROM php:7.4-apache
RUN docker-php-ext-install -j4 mysqli pdo_mysql >/dev/null && a2enmod rewrite >/dev/null
DOCKER
docker build -q -t pa-wikka-php "$WORK" >/dev/null

docker network create $NET >/dev/null
docker run -d --name pa-wikka-db --network $NET -e MARIADB_RANDOM_ROOT_PASSWORD=1 -e MARIADB_DATABASE=wikka \
  -e MARIADB_USER=wikka -e MARIADB_PASSWORD=wikkapw mariadb:10.6 >/dev/null
docker run -d --name pa-wikka-web --network $NET -p "$PORT:80" -v "$WORK/site":/src:ro pa-wikka-php \
  sh -c 'cp -a /src/. /var/www/html/ && touch /var/www/html/wikka.config.php && chown -R www-data:www-data /var/www/html && apache2-foreground' >/dev/null

for i in $(seq 1 60); do
  docker exec pa-wikka-db mariadb -uwikka -pwikkapw -e 'select 1' wikka >/dev/null 2>&1 && curl -fs -o /dev/null "http://localhost:$PORT/" && break
  sleep 1
done

python3 scripts/verify_wikka.py "http://localhost:$PORT"

if docker logs pa-wikka-web 2>&1 | grep -i privatus | grep -qiE "warning|fatal|deprecated|notice"; then
  docker logs pa-wikka-web 2>&1 | grep -i privatus
  echo "FAIL PHP messages from the action"; exit 1
fi
echo "ok   no PHP messages from the action (WikkaWiki $VERSION)"
