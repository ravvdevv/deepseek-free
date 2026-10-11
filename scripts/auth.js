#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const readline = require('readline');
const { spawnSync } = require('child_process');

const { loadDotEnv } = require('../lib/env');
const { defaultAuthOutputPath } = require('./auth_import');

const ROOT = path.resolve(__dirname, '..');
loadDotEnv(path.join(ROOT, '.env'));
const AUTH_PATH = defaultAuthOutputPath(process.env, ROOT);
const PROFILE_DIR = process.env.DEEPSEEK_CHROME_PROFILE || path.join(ROOT, '.chrome-for-testing-profile-deepseek');

function prompt(question) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  return new Promise(resolve => rl.question(question, ans => { rl.close(); resolve(ans); }));
}
function divider() { console.log('======================================================'); }
function loadAuth() {
  try { return JSON.parse(fs.readFileSync(AUTH_PATH, 'utf8')); }
  catch { return null; }
}
function status() {
  const auth = loadAuth();
  console.log('\nDeepSeek account:');
  if (!auth) {
    console.log('  ❌ deepseek-auth.json not found');
  } else {
    console.log(`  ✅ auth file: ${AUTH_PATH}`);
    console.log(`  token: ${auth.token ? 'OK (' + String(auth.token).length + ' chars)' : 'MISSING'}`);
    console.log(`  cookies: ${auth.cookie ? 'OK' : 'MISSING'}`);
    console.log(`  Chrome profile: ${fs.existsSync(PROFILE_DIR) ? PROFILE_DIR : 'not found'}`);
  }
}
function runDirectAuth() {
  const script = path.join(__dirname, 'deepseek_chrome_auth.js');
  return spawnSync(process.execPath, [script], { stdio: 'inherit', env: process.env }).status === 0;
}
function runImportAuth() {
  const script = path.join(__dirname, 'auth_import.js');
  return spawnSync(process.execPath, [script], { stdio: 'inherit', env: process.env }).status === 0;
}
function removeLocalAuth() {
  if (fs.existsSync(AUTH_PATH)) fs.rmSync(AUTH_PATH, { force: true });
  console.log('Removed deepseek-auth.json. The Chrome profile is kept so your browser is not logged out unnecessarily.');
}
function printHelp() {
  divider();
  console.log('deepseek-free — manage your DeepSeek Web login');
  divider();
  console.log('Options:');
  console.log('  --login     Open Chrome and refresh the auth');
  console.log('  --import    Import a ready-made deepseek-auth.json / browser cookies');
  console.log('  --status    Show the auth status');
  console.log('  --remove    Delete the local deepseek-auth.json');
  console.log('  --help      Help');
  console.log('With no options an interactive menu starts.');
  divider();
}
async function menu() {
  while (true) {
    divider();
    status();
    divider();
    console.log('Menu:');
    console.log('1 - Authenticate / refresh the DeepSeek login');
    console.log('2 - Import an auth file / cookies');
    console.log('3 - Show status');
    console.log('4 - Delete the local auth file');
    console.log('5 - Exit');
    const choice = (await prompt('Your choice (Enter = 5): ')) || '5';
    if (choice === '1') runDirectAuth();
    else if (choice === '2') runImportAuth();
    else if (choice === '3') { status(); await prompt('\nPress Enter to go back to the menu...'); }
    else if (choice === '4') removeLocalAuth();
    else if (choice === '5') break;
  }
}
(async () => {
  const args = new Set(process.argv.slice(2));
  if (args.has('--help') || args.has('-h')) return printHelp();
  if (args.has('--login') || args.has('--add') || args.has('--relogin')) return void runDirectAuth();
  if (args.has('--import')) return void runImportAuth();
  if (args.has('--status') || args.has('--list')) return status();
  if (args.has('--remove')) return removeLocalAuth();
  await menu();
})();
