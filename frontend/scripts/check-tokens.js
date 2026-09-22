const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const allowedColors = ['ink', 'ink-secondary', 'muted', 'background', 'surface', 'surface-inverse', 'border', 'border-strong', 'white', 'black', 'transparent', 'current'];
const cssColors = ['red', 'blue', 'green', 'yellow', 'indigo', 'purple', 'pink', 'orange', 'teal', 'cyan', 'gray', 'slate', 'zinc', 'neutral', 'stone', 'amber', 'lime', 'emerald', 'sky', 'violet', 'fuchsia', 'rose'];

let failed = false;

function scanDir(dir) {
  const files = fs.readdirSync(dir);
  for (const file of files) {
    const fullPath = path.join(dir, file);
    if (fs.statSync(fullPath).isDirectory()) {
      scanDir(fullPath);
    } else if (fullPath.match(/\.(tsx|ts|jsx|js)$/)) {
      const content = fs.readFileSync(fullPath, 'utf8');
      for (const color of cssColors) {
        // Match Tailwind classes like text-red-500, bg-blue-100, etc.
        const regex = new RegExp(`(text|bg|border|ring|stroke|fill)-${color}(-\\d+)?\\b`, 'g');
        const matches = content.match(regex);
        if (matches) {
          console.error(`ERROR: Disallowed color class used in ${fullPath}: ${matches.join(', ')}`);
          failed = true;
        }
      }
    }
  }
}

scanDir(path.join(__dirname, '../app'));
const componentsDir = path.join(__dirname, '../components');
if (fs.existsSync(componentsDir)) {
  scanDir(componentsDir);
}

if (failed) {
  console.error("Monochrome design token test failed. Remove hardcoded Tailwind colors.");
  process.exit(1);
} else {
  console.log("Monochrome design token test passed.");
}
