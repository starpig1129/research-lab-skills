#!/usr/bin/env node
'use strict';

const path = require('path');
const fs   = require('fs');
const os   = require('os');

// ── constants ─────────────────────────────────────────────────────────────────

const VERSION    = require('../package.json').version;
const PKG_SKILLS = path.join(__dirname, '..', 'skills');
const SKILLS     = ['research-log', 'report-slides'];

// AI target → skills root path
const AI_PATHS = {
  claude:   path.join(os.homedir(), '.claude',  'skills'),
  cursor:   path.join(os.homedir(), '.cursor',  'skills'),
  windsurf: path.join(os.homedir(), '.windsurf','skills'),
  copilot:  path.join(os.homedir(), '.github',  'copilot-skills'),
};

// ── helpers ───────────────────────────────────────────────────────────────────

function copyDir(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const s = path.join(src, entry.name);
    const d = path.join(dest, entry.name);
    if (entry.isDirectory()) copyDir(s, d);
    else fs.copyFileSync(s, d);
  }
}

function log(msg)  { process.stdout.write(msg + '\n'); }
function warn(msg) { process.stderr.write('Warning: ' + msg + '\n'); }
function die(msg)  { process.stderr.write('Error: ' + msg + '\n'); process.exit(1); }

function parseArgs(args) {
  const flags = {
    global: args.includes('--global'),
    ai:     'claude',
  };
  const aiFlag = args.find(a => a.startsWith('--ai=') || a === '--ai');
  if (aiFlag) {
    const val = aiFlag.includes('=')
      ? aiFlag.split('=')[1]
      : args[args.indexOf(aiFlag) + 1];
    if (val) flags.ai = val.toLowerCase();
  }
  return flags;
}

function resolveTarget(flags) {
  if (!flags.global) {
    // project-local
    const localBase = flags.ai === 'claude'
      ? path.join(process.cwd(), '.claude', 'skills')
      : path.join(process.cwd(), `.${flags.ai}`, 'skills');
    return localBase;
  }
  if (!(flags.ai in AI_PATHS)) {
    die(`Unknown AI target: ${flags.ai}\nSupported: ${Object.keys(AI_PATHS).join(', ')}`);
  }
  return AI_PATHS[flags.ai];
}

// ── commands ──────────────────────────────────────────────────────────────────

function cmdInit(args) {
  const flags  = parseArgs(args);
  const target = resolveTarget(flags);

  log(`Installing claude-research-skills v${VERSION}`);
  log(`Target (${flags.global ? 'global' : 'project'}): ${target}`);
  log('');

  for (const skill of SKILLS) {
    const src  = path.join(PKG_SKILLS, skill);
    const dest = path.join(target, skill);
    if (!fs.existsSync(src)) { warn(`Skill source not found: ${src} (skipped)`); continue; }
    copyDir(src, dest);
    log(`  ✓ ${skill}`);
  }

  log('');
  log('Done. Restart Claude Code — /research-log and /report-slides will be available.');

  if (flags.ai === 'claude') {
    log('');
    log('First time in a project? Run:');
    log(`  bash "$(find ~/.claude -path "*/report-slides/scripts/setup.sh" | head -1)"`);
  }
}

function cmdUninstall(args) {
  const flags  = parseArgs(args);
  const target = resolveTarget(flags);

  log(`Uninstalling from: ${target}`);
  for (const skill of SKILLS) {
    const dest = path.join(target, skill);
    if (fs.existsSync(dest)) {
      fs.rmSync(dest, { recursive: true, force: true });
      log(`  ✓ Removed: ${dest}`);
    } else {
      log(`  - Not found (skipped): ${dest}`);
    }
  }
  log('Done.');
}

function cmdUpdate(args) {
  log('Updating skills (reinstalling from current package)...');
  log('');
  cmdInit(args);
}

function cmdVersions() {
  log(`claude-research-skills v${VERSION}`);
  log('To update: npm update -g claude-research-skills');
}

function cmdHelp() {
  log(`
claude-research-skills (crs) v${VERSION}

Skills for AI coding assistants:
  /research-log  — structured experiment journal
  /report-slides — generate SVG + PPTX slide decks from journal entries

Usage:
  crs init                     Install to .claude/skills/ (project-local)
  crs init --global            Install to ~/.claude/skills/ (all projects)
  crs init --ai cursor         Install for Cursor (project-local)
  crs init --ai claude --global  Install globally for Claude Code

  crs update [--global]        Reinstall from this package version
  crs uninstall [--global]     Remove installed skills

  crs versions                 Show installed version
  crs help                     Show this help

Supported AI targets: ${Object.keys(AI_PATHS).join(', ')}

After install, restart your AI assistant.
Project setup (copies helper scripts):
  bash "$(find ~/.claude -path "*/report-slides/scripts/setup.sh" | head -1)"
`.trim());
}

// ── main ──────────────────────────────────────────────────────────────────────

const [,, cmd, ...rest] = process.argv;

switch (cmd) {
  case 'init':      cmdInit(rest);      break;
  case 'update':    cmdUpdate(rest);    break;
  case 'uninstall': cmdUninstall(rest); break;
  case 'versions':  cmdVersions();      break;
  case 'help':
  case '--help':
  case '-h':        cmdHelp();          break;
  case undefined:   cmdHelp();          break;
  default: die(`Unknown command: ${cmd}\nRun "crs help" for usage.`);
}
