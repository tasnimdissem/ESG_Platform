import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const rootDir = process.cwd();
const backendPythonCandidates = [
  path.join(rootDir, '.venv', 'Scripts', 'python.exe'),
  path.join(rootDir, '.venv', 'bin', 'python'),
  'python',
];

function pickBackendPython() {
  for (const candidate of backendPythonCandidates) {
    if (candidate === 'python' || fs.existsSync(candidate)) {
      return candidate;
    }
  }
  return 'python';
}

function start(command, args, label) {
  const child = spawn(command, args, {
    cwd: rootDir,
    stdio: 'inherit',
    shell: process.platform === 'win32',
  });

  child.on('exit', (code, signal) => {
    if (signal || code !== 0) {
      const reason = signal ? `signal ${signal}` : `code ${code}`;
      console.error(`${label} exited with ${reason}`);
      process.exitCode = code ?? 1;
      terminateChildren();
    }
  });

  return child;
}

const children = [];
function terminateChildren() {
  for (const child of children) {
    if (!child.killed) {
      child.kill();
    }
  }
}

process.on('SIGINT', () => {
  terminateChildren();
  process.exit(0);
});

process.on('SIGTERM', () => {
  terminateChildren();
  process.exit(0);
});

children.push(start('npm', ['run', 'dev', '--', '--host'], 'frontend'));
children.push(start(pickBackendPython(), ['backend/app.py'], 'backend'));
