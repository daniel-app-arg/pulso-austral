import sharp from 'sharp';

const base = 'C:\\Users\\danie\\Pulso Austral\\branding\\logo\\';

const jobs = [
  ['apple-icon-source.svg', 'apple-icon-180.png', 180],
  ['pulso-austral-mark.svg', 'pulso-austral-mark-512.png', 512],
  ['pulso-austral-mark.svg', 'pulso-austral-mark-192.png', 192],
  ['pulso-austral-mark.svg', 'favicon-32.png', 32],
];

for (const [src, out, size] of jobs) {
  await sharp(base + src).resize(size, size).png().toFile(base + out);
  console.log(out, 'OK');
}
