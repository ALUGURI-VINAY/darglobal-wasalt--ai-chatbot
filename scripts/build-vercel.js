const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const rootDir = path.resolve(__dirname, '..');
const frontendDir = path.join(rootDir, 'frontend');

console.log('=== Vercel Automated Monorepo Build Triggered ===');
console.log('Root Directory:    ', rootDir);
console.log('Frontend Directory:', frontendDir);

// 1. Install frontend dependencies
console.log('\n[1/3] Installing frontend dependencies...');
execSync('npm install --prefer-offline --no-audit --no-fund', {
  cwd: frontendDir,
  stdio: 'inherit'
});

// 2. Build frontend
console.log('\n[2/3] Building frontend with Vite / TanStack Start...');
const env = { ...process.env, VERCEL: '1' };
execSync('npm run build', {
  cwd: frontendDir,
  env,
  stdio: 'inherit'
});

// 3. Ensure Build Output API v3 exists at root
const frontendVercel = path.join(frontendDir, '.vercel', 'output');
const rootVercelDir = path.join(rootDir, '.vercel');
const rootVercelOutput = path.join(rootVercelDir, 'output');

console.log('\n[3/3] Inspecting build outputs for Vercel deployment...');
if (fs.existsSync(frontendVercel)) {
  console.log('Found frontend Build Output at: ' + frontendVercel);
  fs.mkdirSync(rootVercelDir, { recursive: true });
  if (fs.existsSync(rootVercelOutput)) {
    fs.rmSync(rootVercelOutput, { recursive: true, force: true });
  }
  fs.cpSync(frontendVercel, rootVercelOutput, { recursive: true });
  console.log('Successfully prepared root .vercel/output for Vercel deployment!');
} else {
  const staticOutput = path.join(frontendDir, '.output', 'public');
  if (fs.existsSync(staticOutput)) {
    console.log('Fallback: Static output found at ' + staticOutput);
    const rootStatic = path.join(rootVercelOutput, 'static');
    fs.mkdirSync(rootStatic, { recursive: true });
    fs.cpSync(staticOutput, rootStatic, { recursive: true });
    fs.writeFileSync(
      path.join(rootVercelOutput, 'config.json'),
      JSON.stringify({ version: 3 }, null, 2)
    );
    console.log('Prepared fallback root .vercel/output from static files.');
  } else {
    console.warn('Warning: Neither .vercel/output nor .output/public was found in frontend.');
  }
}

console.log('\n=== Monorepo Build Completed Successfully! ===\n');
