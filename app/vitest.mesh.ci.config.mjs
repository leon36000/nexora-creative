import path from 'node:path';

const root = process.env.DIRECTOR_CI_ROOT;
const cache = process.env.DIRECTOR_CI_CACHE;
const coverage = process.env.MESH_CI_COVERAGE;
if (!root || !cache || !coverage) {
  throw new Error('DIRECTOR_CI_ROOT, DIRECTOR_CI_CACHE et MESH_CI_COVERAGE requis');
}

export default {
  root,
  envFile: false,
  envDir: false,
  cacheDir: path.join(cache, 'mesh-vitest'),
  esbuild: { jsx: 'automatic' },
  resolve: {
    alias: [
      { find: /^vitest$/, replacement: `${root}/app/node_modules/vitest/dist/index.js` },
      { find: /^@vitest\/coverage-v8$/, replacement: `${root}/app/node_modules/@vitest/coverage-v8/dist/index.js` },
    ],
  },
  test: {
    pool: 'threads',
    maxWorkers: 1,
    minWorkers: 1,
    include: [
      'app/mcp/mesh.test.ts', 'app/mcp/mesh-init.test.ts', 'app/mcp/mesh-multivue.test.ts',
      'app/src/ModelView.test.tsx',
      'app/src/SourcePick.test.tsx',
      'app/src/SourcePickRace.contract.test.tsx',
      'app/src/ViewerActions.test.tsx',
      'app/src/meshCopy.test.ts',
      'app/src/store.test.ts',
      'app/src/pages/MeshLanguageSwitch.test.tsx',
      'app/src/pages/Object.test.tsx',
      'app/src/pages/ObjectTextPolling.test.tsx',
      'app/src/pages/ObjectPolling.test.ts',
      'app/src/pages/ReliefOutils.test.tsx',
      'app/src/pages/ReliefUsdz.test.tsx',
      'app/src/planCle3d.test.ts',
      'app/src/productNames.test.ts',
      'app/src/ui.test.tsx',
      'app/server/nexora/relief.test.ts',
      'app/server/nexora/usdz.test.ts',
    ],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov', 'json-summary'],
      reportsDirectory: coverage,
      include: [
        'app/mcp/server.ts', 'app/mcp/client.ts',
        'app/src/ModelView.tsx',
        'app/src/SourcePick.tsx',
        'app/src/Viewer.tsx',
        'app/src/meshCopy.ts',
        'app/src/store.ts',
        'app/src/pages/MeshLanguageSwitch.tsx',
        'app/src/pages/Object.tsx',
        'app/src/pages/ReliefOutils.tsx',
        'app/src/planCle3d.ts',
        'app/src/ui.tsx',
        'app/shared/productNames.ts',
        'app/server/nexora/relief.ts',
        'app/server/nexora/usdz.ts',
      ],
    },
  },
};
