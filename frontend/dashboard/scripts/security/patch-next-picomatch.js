const fs = require("fs");
const path = require("path");

const projectRoot = path.resolve(__dirname, "..", "..");
const sourceDir = path.join(projectRoot, "node_modules", "picomatch");
const targetDir = path.join(projectRoot, "node_modules", "next", "dist", "compiled", "picomatch");
const expectedVersion = "4.0.4";

function copyDirectory(source, target) {
  fs.rmSync(target, { recursive: true, force: true });
  fs.mkdirSync(target, { recursive: true });

  for (const entry of fs.readdirSync(source, { withFileTypes: true })) {
    const sourcePath = path.join(source, entry.name);
    const targetPath = path.join(target, entry.name);

    if (entry.isDirectory()) {
      copyDirectory(sourcePath, targetPath);
      continue;
    }

    if (entry.isFile()) {
      fs.copyFileSync(sourcePath, targetPath);
    }
  }
}

if (!fs.existsSync(sourceDir)) {
  throw new Error(`picomatch dependency not found: ${sourceDir}`);
}

if (!fs.existsSync(targetDir)) {
  throw new Error(`Next.js compiled picomatch not found: ${targetDir}`);
}

copyDirectory(sourceDir, targetDir);

const patchedPackageJson = JSON.parse(
  fs.readFileSync(path.join(targetDir, "package.json"), "utf8"),
);

if (patchedPackageJson.version !== expectedVersion) {
  throw new Error(
    `Unexpected patched picomatch version: ${patchedPackageJson.version}. Expected ${expectedVersion}.`,
  );
}

console.log(`Patched next/dist/compiled/picomatch with picomatch ${expectedVersion}.`);
