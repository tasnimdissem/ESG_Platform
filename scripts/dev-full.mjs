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
    }
  });

  return child;
}

function runOnce(command, args, label) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd: rootDir,
      stdio: 'inherit',
      shell: process.platform === 'win32',
    });

    child.on('error', (error) => {
      reject(new Error(`${label} failed to start: ${error.message}`));
    });

    child.on('exit', (code, signal) => {
      if (signal || code !== 0) {
        const reason = signal ? `signal ${signal}` : `code ${code}`;
        reject(new Error(`${label} exited with ${reason}`));
        return;
      }

      resolve();
    });
  });
}

function inspectDockerHealth() {
  return new Promise((resolve) => {
    const child = spawn('docker', ['inspect', '--format={{.State.Health.Status}}', 'esg-postgres'], {
      cwd: rootDir,
      shell: process.platform === 'win32',
    });

    let output = '';
    let errorOutput = '';

    child.stdout?.on('data', (chunk) => {
      output += chunk.toString();
    });

    child.stderr?.on('data', (chunk) => {
      errorOutput += chunk.toString();
    });

    child.on('error', (error) => {
      resolve({
        code: 1,
        status: '',
        errorOutput: error.message,
      });
    });

    child.on('close', (code) => {
      resolve({
        code: code ?? 1,
        status: output.trim(),
        errorOutput: errorOutput.trim(),
      });
    });
  });
}

async function waitForPostgresHealthy() {
  const timeoutMs = 120000;
  const pollIntervalMs = 2000;
  const deadline = Date.now() + timeoutMs;

  while (Date.now() < deadline) {
    const { code, status, errorOutput } = await inspectDockerHealth();

    if (code === 0 && status === 'healthy') {
      return;
    }

    if (status === 'unhealthy') {
      throw new Error(`postgres container esg-postgres reported unhealthy${errorOutput ? `: ${errorOutput}` : ''}`);
    }

    await new Promise((resolve) => setTimeout(resolve, pollIntervalMs));
  }

  throw new Error('Timed out waiting for postgres container esg-postgres to become healthy');
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

async function main() {
  await runOnce('docker-compose', ['up', '-d', 'postgres'], 'postgres');
  await waitForPostgresHealthy();

  children.push(start('npm', ['run', 'dev', '--', '--host'], 'frontend'));
  children.push(start(pickBackendPython(), ['-m', 'backend.app'], 'backend'));
  children.push(start(pickBackendPython(), ['-m', 'RAG_SYSTEM.app'], 'rag-system'));
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
