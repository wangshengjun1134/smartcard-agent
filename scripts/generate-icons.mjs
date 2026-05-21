import sharp from 'sharp';
import { readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync, unlinkSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const iconsDir = join(__dirname, '..', 'src-tauri', 'icons');
const svgPath = join(iconsDir, 'icon.svg');

// PNG sizes needed
const pngSizes = [
  { name: '32x32.png', size: 32 },
  { name: '64x64.png', size: 64 },
  { name: '128x128.png', size: 128 },
  { name: '128x128@2x.png', size: 256 },
  { name: 'icon.png', size: 512 },
  { name: 'Square30x30Logo.png', size: 30 },
  { name: 'Square44x44Logo.png', size: 44 },
  { name: 'Square71x71Logo.png', size: 71 },
  { name: 'Square89x89Logo.png', size: 89 },
  { name: 'Square107x107Logo.png', size: 107 },
  { name: 'Square142x142Logo.png', size: 142 },
  { name: 'Square150x150Logo.png', size: 150 },
  { name: 'Square284x284Logo.png', size: 284 },
  { name: 'Square310x310Logo.png', size: 310 },
  { name: 'StoreLogo.png', size: 50 },
];

// Android icons
const androidSizes = [
  { name: 'mipmap-mdpi/ic_launcher.png', size: 48 },
  { name: 'mipmap-hdpi/ic_launcher.png', size: 72 },
  { name: 'mipmap-xhdpi/ic_launcher.png', size: 96 },
  { name: 'mipmap-xxhdpi/ic_launcher.png', size: 144 },
  { name: 'mipmap-xxxhdpi/ic_launcher.png', size: 192 },
];

// iOS icons (based on actual file naming)
const iosSizes = [
  { name: 'AppIcon-20x20@1x.png', size: 20 },
  { name: 'AppIcon-20x20@2x.png', size: 40 },
  { name: 'AppIcon-20x20@3x.png', size: 60 },
  { name: 'AppIcon-29x29@1x.png', size: 29 },
  { name: 'AppIcon-29x29@2x.png', size: 58 },
  { name: 'AppIcon-29x29@3x.png', size: 87 },
  { name: 'AppIcon-40x40@1x.png', size: 40 },
  { name: 'AppIcon-40x40@2x.png', size: 80 },
  { name: 'AppIcon-40x40@3x.png', size: 120 },
  { name: 'AppIcon-60x60@2x.png', size: 120 },
  { name: 'AppIcon-60x60@3x.png', size: 180 },
  { name: 'AppIcon-76x76@1x.png', size: 76 },
  { name: 'AppIcon-76x76@2x.png', size: 152 },
  { name: 'AppIcon-83.5x83.5@2x.png', size: 167 },
  { name: 'AppIcon-512@2x.png', size: 1024 },
];

async function generatePng(svgBuffer, size, outputPath) {
  await sharp(svgBuffer)
    .resize(size, size)
    .png()
    .toFile(outputPath);
  console.log(`Generated: ${outputPath}`);
}

async function generateIco(svgBuffer) {
  const sizes = [16, 32, 48, 64, 128, 256];
  const pngBuffers = await Promise.all(
    sizes.map(size => 
      sharp(svgBuffer)
        .resize(size, size)
        .png()
        .toBuffer()
    )
  );

  // ICO file format
  const iconDirSize = 6 + pngBuffers.length * 16;
  const buffers = [];
  
  // ICONDIR header
  const iconDir = Buffer.alloc(6);
  iconDir.writeUInt16LE(0, 0); // Reserved
  iconDir.writeUInt16LE(1, 2); // Type (1 = ICO)
  iconDir.writeUInt16LE(pngBuffers.length, 4); // Number of images
  buffers.push(iconDir);

  // Calculate offsets
  let dataOffset = iconDirSize;
  const entries = [];
  const dataBuffers = [];

  for (let i = 0; i < pngBuffers.length; i++) {
    const png = pngBuffers[i];
    const size = sizes[i];
    
    // ICONDIRENTRY
    const entry = Buffer.alloc(16);
    entry.writeUInt8(size >= 256 ? 0 : size, 0); // Width (0 = 256)
    entry.writeUInt8(size >= 256 ? 0 : size, 1); // Height (0 = 256)
    entry.writeUInt8(0, 2); // Color palette
    entry.writeUInt8(0, 3); // Reserved
    entry.writeUInt16LE(1, 4); // Color planes
    entry.writeUInt16LE(32, 6); // Bits per pixel
    entry.writeUInt32LE(png.length, 8); // Size of image data
    entry.writeUInt32LE(dataOffset, 12); // Offset to image data
    entries.push(entry);
    
    dataBuffers.push(png);
    dataOffset += png.length;
  }

  buffers.push(...entries);
  buffers.push(...dataBuffers);

  const ico = Buffer.concat(buffers);
  const icoPath = join(iconsDir, 'icon.ico');
  writeFileSync(icoPath, ico);
  console.log(`Generated: ${icoPath}`);
}

async function generateIcns(svgBuffer) {
  // ICNS format for macOS - we'll generate a simple PNG-based one
  // For proper ICNS, we need specific icon types
  const sizes = [16, 32, 64, 128, 256, 512, 1024];
  
  // Generate all PNG buffers
  const pngData = {};
  for (const size of sizes) {
    pngData[size] = await sharp(svgBuffer)
      .resize(size, size)
      .png()
      .toBuffer();
  }

  // ICNS structure
  const iconTypes = [
    { type: 'icp4', size: 16 },
    { type: 'icp5', size: 32 },
    { type: 'icp6', size: 64 },
    { type: 'ic07', size: 128 },
    { type: 'ic08', size: 256 },
    { type: 'ic09', size: 512 },
    { type: 'ic10', size: 1024 },
    { type: 'ic11', size: 32 },  // @2x 16
    { type: 'ic12', size: 64 },  // @2x 32
    { type: 'ic13', size: 256 }, // @2x 128
    { type: 'ic14', size: 512 }, // @2x 256
  ];

  const buffers = [];
  
  // Calculate total size
  let totalSize = 8; // Header
  
  const entries = [];
  for (const { type, size } of iconTypes) {
    const png = pngData[size];
    if (png) {
      const entrySize = 8 + png.length;
      entries.push({ type, png, entrySize });
      totalSize += entrySize;
    }
  }

  // Header
  const header = Buffer.alloc(8);
  header.write('icns', 0, 4, 'ascii');
  header.writeUInt32BE(totalSize, 4);
  buffers.push(header);

  // Icon entries
  for (const { type, png, entrySize } of entries) {
    const entry = Buffer.alloc(8);
    entry.write(type, 0, 4, 'ascii');
    entry.writeUInt32BE(entrySize, 4);
    buffers.push(entry);
    buffers.push(png);
  }

  const icns = Buffer.concat(buffers);
  const icnsPath = join(iconsDir, 'icon.icns');
  writeFileSync(icnsPath, icns);
  console.log(`Generated: ${icnsPath}`);
}

async function main() {
  console.log('Reading SVG file...');
  const svgBuffer = readFileSync(svgPath);

  console.log('\nGenerating PNG files...');
  for (const { name, size } of pngSizes) {
    await generatePng(svgBuffer, size, join(iconsDir, name));
  }

  console.log('\nGenerating Android icons...');
  const androidDir = join(iconsDir, 'android');
  for (const { name, size } of androidSizes) {
    const [folder] = name.split('/');
    const folderPath = join(androidDir, folder);
    if (!existsSync(folderPath)) {
      mkdirSync(folderPath, { recursive: true });
    }
    await generatePng(svgBuffer, size, join(androidDir, name));
  }

  console.log('\nGenerating iOS icons...');
  const iosDir = join(iconsDir, 'ios');
  for (const { name, size } of iosSizes) {
    await generatePng(svgBuffer, size, join(iosDir, name));
  }

  console.log('\nGenerating ICO file...');
  await generateIco(svgBuffer);

  console.log('\nGenerating ICNS file...');
  await generateIcns(svgBuffer);

  console.log('\nDone! All icons generated.');
}

main().catch(console.error);