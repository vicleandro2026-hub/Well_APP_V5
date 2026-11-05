import { Zip, ZipPassThrough } from 'fflate';
import layouts from './assets/layouts.json';
import horizontalUrl from './assets/logo_horizontal.png';
import verticalUrl from './assets/logo_vertical.png';

export const defaults = Object.freeze({ position: 'original', scale: 100, opacity: 100, margin: 4, x: 0.5, y: 0.78 });
export const positions = [
  ['top_left', 'Superior esquerdo', 'Sup. esq.'], ['top', 'Superior central', 'Superior'], ['top_right', 'Superior direito', 'Sup. dir.'],
  ['left', 'Centro esquerdo', 'Meio esq.'], ['center', 'Centro', 'Centro'], ['right', 'Centro direito', 'Meio dir.'],
  ['bottom_left', 'Inferior esquerdo', 'Inf. esq.'], ['bottom', 'Inferior central', 'Inferior'], ['bottom_right', 'Inferior direito', 'Inf. dir.'],
];
export const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
export const logoKey = photo => photo.height > photo.width ? 'vertical' : 'horizontal';
export const formatLabel = photo => photo.height === photo.width ? 'Quadrada' : photo.height > photo.width ? 'Vertical' : 'Horizontal';
export const nextFrame = () => new Promise(resolve => requestAnimationFrame(() => resolve()));

export function geometry(photo, settings) {
  const { width, height } = photo;
  const layout = layouts[logoKey(photo)];
  const [cw, ch] = layout.canvas;
  const [left, top, right, bottom] = layout.bbox;
  const template = Math.min(width / cw, height / ch);
  const factor = clamp(settings.scale / 100, 0.25, 3);
  let w = (right - left) * template * factor;
  let h = (bottom - top) * template * factor;
  const margin = Math.min(width, height) * settings.margin / 100;
  const padding = ['original', 'free'].includes(settings.position) ? 0 : margin;
  const fit = Math.min(1, Math.max(1, width - padding * 2) / w, Math.max(1, height - padding * 2) / h);
  w = Math.max(1, Math.round(w * fit)); h = Math.max(1, Math.round(h * fit));
  let x = (width - w) / 2, y = (height - h) / 2;
  if (settings.position === 'free') { x = settings.x * width - w / 2; y = settings.y * height - h / 2; }
  else if (settings.position === 'original') {
    x = (width - cw * template) / 2 + (left + right) / 2 * template - w / 2;
    y = (height - ch * template) / 2 + (top + bottom) / 2 * template - h / 2;
  } else {
    if (['top_left', 'left', 'bottom_left'].includes(settings.position)) x = margin;
    if (['top_right', 'right', 'bottom_right'].includes(settings.position)) x = width - w - margin;
    if (['top_left', 'top', 'top_right'].includes(settings.position)) y = margin;
    if (['bottom_left', 'bottom', 'bottom_right'].includes(settings.position)) y = height - h - margin;
  }
  return { x: Math.round(clamp(x, 0, width - w)), y: Math.round(clamp(y, 0, height - h)), width: w, height: h };
}

export function dispose(image) { if (typeof image?.close === 'function') image.close(); }

export async function decode(source) {
  if (typeof createImageBitmap === 'function') {
    try { return await createImageBitmap(source, { imageOrientation: 'from-image' }); }
    catch (error) { if (!(source instanceof Blob)) throw error; }
  }
  const url = URL.createObjectURL(source);
  try {
    const image = new Image(); image.src = url; await image.decode();
    return image;
  } finally { URL.revokeObjectURL(url); }
}

let logosPromise;
export function loadLogos() {
  if (!logosPromise) logosPromise = Promise.all([horizontalUrl, verticalUrl].map(async url => {
    const response = await fetch(url); if (!response.ok) throw new Error('Não foi possível carregar os logos. Atualize a página.');
    return decode(await response.blob());
  })).then(([horizontal, vertical]) => ({ horizontal, vertical })).catch(error => { logosPromise = null; throw error; });
  return logosPromise;
}

export function canvasBlob(canvas, type = 'image/jpeg', quality = 0.95) {
  return new Promise((resolve, reject) => canvas.toBlob(blob => blob ? resolve(blob) : reject(new Error('Esta foto excede a capacidade de exportação do navegador. Tente em um computador.')), type, quality));
}

export async function inspectFile(file) {
  if (file.size > 100 * 1024 * 1024) throw new Error('O limite é 100 MB por foto.');
  const signature = new Uint8Array(await file.slice(0, 12).arrayBuffer());
  const png = signature[0] === 137 && signature[1] === 80 && signature[2] === 78 && signature[3] === 71;
  const jpeg = signature[0] === 255 && signature[1] === 216;
  const webp = String.fromCharCode(...signature.slice(0, 4)) === 'RIFF' && String.fromCharCode(...signature.slice(8, 12)) === 'WEBP';
  if (!png && !jpeg && !webp) throw new Error('Formato não suportado. Escolha JPG, PNG ou WebP.');
  const bitmap = await decode(file);
  try {
    const width = bitmap.width || bitmap.naturalWidth, height = bitmap.height || bitmap.naturalHeight;
    if (width * height > 80_000_000) throw new Error('Esta imagem é muito grande. O limite é 80 megapixels por foto.');
    const canvas = document.createElement('canvas');
    const ratio = Math.min(1, 220 / width, 160 / height);
    canvas.width = Math.max(1, Math.round(width * ratio)); canvas.height = Math.max(1, Math.round(height * ratio));
    canvas.getContext('2d').drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    const thumbnail = URL.createObjectURL(await canvasBlob(canvas, 'image/jpeg', 0.8));
    canvas.width = canvas.height = 1;
    return { id: crypto.randomUUID(), file, width, height, thumbnail, mime: png ? 'image/png' : jpeg ? 'image/jpeg' : 'image/webp', state: 'ready' };
  } finally { dispose(bitmap); }
}

export async function previewBitmap(photo) {
  const bitmap = await decode(photo.file);
  const width = bitmap.width || bitmap.naturalWidth, height = bitmap.height || bitmap.naturalHeight;
  const ratio = Math.min(1, 3200 / width, 3200 / height);
  if (ratio === 1) return bitmap;
  const canvas = document.createElement('canvas');
  canvas.width = Math.round(width * ratio); canvas.height = Math.round(height * ratio);
  canvas.getContext('2d').drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  dispose(bitmap);
  if (typeof createImageBitmap !== 'function') return canvas;
  try { return await createImageBitmap(canvas); }
  finally { canvas.width = canvas.height = 1; }
}

export async function exportPhoto(photo, settings, outputFormat, logos) {
  const bitmap = await decode(photo.file);
  const canvas = document.createElement('canvas');
  try {
    const mime = outputFormat === 'original' ? photo.mime : `image/${outputFormat}`;
    canvas.width = photo.width; canvas.height = photo.height;
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('Não foi possível preparar esta foto. Tente em outro navegador.');
    ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'high';
    if (mime === 'image/jpeg') { ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, canvas.width, canvas.height); }
    ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    const box = geometry(photo, settings);
    ctx.globalAlpha = settings.opacity / 100;
    ctx.drawImage(logos[logoKey(photo)], box.x, box.y, box.width, box.height);
    const blob = await canvasBlob(canvas, mime);
    if (blob.type !== mime) throw new Error('Este navegador não exporta esse formato. Escolha JPG ou PNG.');
    const extension = mime === 'image/jpeg' ? 'jpg' : mime === 'image/png' ? 'png' : 'webp';
    const stem = photo.file.name.replace(/\.[^.]+$/, '').replace(/[\\/:*?"<>|]/g, '_');
    return { blob, name: `marcadagua_${stem}.${extension}` };
  } finally { dispose(bitmap); canvas.width = canvas.height = 1; }
}

export async function exportBatch(photos, settings, outputFormat, signal, onProgress) {
  const logos = await loadLogos();
  const failed = [], successful = [], chunks = [], usedNames = new Set();
  let zipError = null, totalBytes = 0;
  const zip = photos.length > 1 ? new Zip((error, data) => { if (error) zipError = error; else chunks.push(data); }) : null;
  for (let index = 0; index < photos.length; index++) {
    if (signal.aborted) return { cancelled: true, successful, failed };
    const photo = photos[index];
    try {
      const result = await exportPhoto(photo, settings, outputFormat, logos);
      if (signal.aborted) return { cancelled: true, successful, failed };
      let name = result.name, count = 2;
      while (usedNames.has(name.toLowerCase())) { name = result.name.replace(/(\.[^.]+)$/, `_${count++}$1`); }
      usedNames.add(name.toLowerCase());
      totalBytes += result.blob.size;
      if (totalBytes > 512 * 1024 * 1024) throw new Error('O lote ultrapassou 512 MB. Baixe um lote menor.');
      if (zip) {
        const entry = new ZipPassThrough(name); zip.add(entry);
        entry.push(new Uint8Array(await result.blob.arrayBuffer()), true);
        if (zipError) throw zipError;
      } else successful.push({ photo, ...result, name });
      if (zip) successful.push({ photo, name });
      onProgress(index + 1, photo, null);
    } catch (error) { failed.push({ photo, message: error.message }); onProgress(index + 1, photo, error.message); }
    await nextFrame();
  }
  if (!successful.length) return { successful, failed };
  if (!zip) return { successful, failed, blob: successful[0].blob, name: successful[0].name };
  zip.end(); if (zipError) throw zipError;
  const stamp = new Date().toISOString().slice(0, 19).replace(/[T:]/g, '-');
  return { successful, failed, blob: new Blob(chunks, { type: 'application/zip' }), name: `Well_fotos_${stamp}.zip` };
}
