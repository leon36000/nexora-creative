#!/bin/sh
set -eu
: "${DIRECTOR_CI_ROOT:?}" "${DIRECTOR_CI_CACHE:?}" "${HOME:?}" "${TMPDIR:?}"
cd "$DIRECTOR_CI_ROOT"
run_logged() {
  name=$1
  shift
  if "$@" > ".ci-director/$name.log" 2>&1; then
    cat ".ci-director/$name.log"
  else
    cat ".ci-director/$name.log"
    return 1
  fi
}
run_logged npm-ci npm ci --prefix app --ignore-scripts --no-audit --no-fund
node -e "for (const [p,v] of [['better-sqlite3','11.10.0'],['vitest','3.2.7'],['@vitest/coverage-v8','3.2.7']]) {const x=require('./app/node_modules/'+p+'/package.json').version;if(x!==v) throw Error(p+': '+x)}"
run_logged sqlite-build npm rebuild --prefix app better-sqlite3 --ignore-scripts=false --build-from-source
run_logged tsc-server node app/node_modules/typescript/bin/tsc -p app/server/tsconfig.json --noEmit
run_logged tsc-client node app/node_modules/typescript/bin/tsc -p app/tsconfig.json --noEmit
run_logged vitest node app/node_modules/vitest/vitest.mjs run --config app/vitest.director.ci.config.mjs --coverage
run_logged vitest-mesh node app/node_modules/vitest/vitest.mjs run --config app/vitest.mesh.ci.config.mjs --coverage
mkdir -p .ci-director/coverage-storm-frame
run_logged mesh-storm-frame node --test --experimental-test-coverage --test-reporter=spec --test-reporter-destination=stdout --test-reporter=lcov --test-reporter-destination=.ci-director/coverage-storm-frame/lcov.info outils/labo/mesh-storm-frame/reproject.test.mjs outils/labo/mesh-storm-normal-bake/*.test.mjs outils/labo/mesh-hunyuan-paint-20261108/*.test.cjs
