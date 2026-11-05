import './styles.css';
import brandUrl from './assets/brand.png';
import { createIcons, ShieldCheck, CircleHelp, ImagePlus, Move, Hand, Minus, Plus, Scan, Images, RotateCcw, RectangleVertical, RectangleHorizontal, Sparkles, Check, Download, X, CircleAlert } from 'lucide';
import { defaults, positions, geometry, formatLabel, logoKey, inspectFile, previewBitmap, dispose, loadLogos, exportBatch, nextFrame } from './engine.js';
import { Viewport } from './viewport.js';

const $ = id => document.getElementById(id);
const icons = { ShieldCheck, CircleHelp, ImagePlus, Move, Hand, Minus, Plus, Scan, Images, RotateCcw, RectangleVertical, RectangleHorizontal, Sparkles, Check, Download, X, CircleAlert };
const paintIcons = () => createIcons({ icons, attrs: { 'aria-hidden': 'true' } });
const state = { photos: [], selected: null, settings: { ...defaults }, logos: null, importing: false, exporting: false, errors: [], mode: 'logo', bitmap: null, generation: 0 };
const quantity = n => `${n} ${n === 1 ? 'foto' : 'fotos'}`;
const selected = () => state.photos.find(photo => photo.id === state.selected);
const busy = () => state.importing || state.exporting;
const viewport = new Viewport($('stage'), $('preview-canvas'), (x, y) => {
  if (busy()) return;
  state.settings = { ...state.settings, position: 'free', x, y }; changed();
}, zoom => { $('zoom-value').textContent = zoom === null ? '—' : `${Math.round(zoom * 100)}%`; });
$('brand-image').src = brandUrl;

function message(text, tone = '') { $('status-text').textContent = text; $('status-text').dataset.tone = tone; }
function errors(items) {
  state.errors = items; $('errors-panel').hidden = !items.length;
  $('error-list').replaceChildren(...items.map(item => { const li = document.createElement('li'); li.textContent = item; return li; }));
}
function updateViewport() { viewport.update(state.settings, state.logos, $('show-original').checked, busy()); }
function syncSettings() {
  const s = state.settings, photo = selected();
  $('position-label').textContent = s.position === 'original' ? 'Padrão Well' : s.position === 'free' ? 'Livre' : positions.find(p => p[0] === s.position)?.[2];
  for (const button of document.querySelectorAll('[data-position]')) {
    const active = button.dataset.position === s.position;
    button.classList.toggle('selected', active); button.setAttribute('aria-pressed', String(active));
  }
  for (const [id, key, output] of [['logo-size', 'scale', 'size-value'], ['logo-opacity', 'opacity', 'opacity-value'], ['logo-margin', 'margin', 'margin-value']]) {
    $(id).value = s[key]; $(output).value = `${s[key]}%`;
  }
  let x = s.x, y = s.y;
  if (photo) { const b = geometry(photo, s); x = (b.x + b.width / 2) / photo.width; y = (b.y + b.height / 2) / photo.height; }
  if (document.activeElement !== $('position-x')) $('position-x').value = (x * 100).toFixed(1);
  if (document.activeElement !== $('position-y')) $('position-y').value = (y * 100).toFixed(1);
  updateViewport();
}
function controls() {
  const hasPhotos = state.photos.length > 0, hasPreview = Boolean(selected() && state.bitmap);
  for (const id of ['add-button', 'empty-add', 'file-input']) $(id).disabled = busy();
  for (const el of document.querySelectorAll('.settings-scroll button, .settings-scroll input, .settings-scroll select')) el.disabled = busy();
  $('remove-button').disabled = !hasPhotos || busy(); $('clear-button').disabled = !hasPhotos || busy();
  $('download-button').disabled = !hasPhotos || busy();
  for (const id of ['tool-logo', 'tool-pan', 'zoom-out', 'zoom-in', 'fit-button', 'actual-button', 'show-original']) $(id).disabled = !hasPreview;
  $('tool-logo').disabled = !hasPreview || busy();
  $('download-button').querySelector('span').textContent = state.exporting ? 'Preparando download…' : hasPhotos ? `Baixar ${quantity(state.photos.length)}` : 'Baixar fotos';
  $('download-caption').textContent = hasPhotos ? state.photos.length === 1 ? 'Download direto da foto com a marca Well.' : 'Todas as fotos reunidas em um arquivo ZIP.' : 'Uma foto ou um ZIP com todo o lote.';
  $('photo-count').textContent = quantity(state.photos.length);
  $('cancel-button').hidden = !state.exporting;
  updateViewport();
}
function changed() {
  const hasBadges = state.photos.some(photo => photo.state !== 'ready');
  for (const photo of state.photos) photo.state = 'ready';
  $('coordinate-error').hidden = true;
  syncSettings(); if (hasBadges) renderTray();
  if (state.photos.length) message('Ajustes prontos. Baixe o lote para aplicar.');
}
function renderTray() {
  const list = $('photo-list');
  if (!state.photos.length) { const p = document.createElement('p'); p.className = 'tray-empty'; p.textContent = 'As fotos adicionadas aparecem aqui.'; list.replaceChildren(p); return; }
  list.replaceChildren(...state.photos.map((photo, index) => {
    const item = document.createElement('div'); item.className = 'photo-item'; item.setAttribute('role', 'listitem');
    const button = document.createElement('button'); button.type = 'button'; button.className = `photo-card${photo.id === state.selected ? ' selected' : ''}`;
    button.setAttribute('aria-pressed', String(photo.id === state.selected)); button.setAttribute('aria-label', `${index + 1}. ${photo.file.name}, ${formatLabel(photo).toLowerCase()}${photo.state === 'exported' ? ', exportada' : photo.state === 'error' ? ', erro ao exportar' : ''}`);
    button.disabled = state.exporting;
    const img = document.createElement('img'); img.src = photo.thumbnail; img.alt = ''; img.draggable = false;
    const name = document.createElement('span'); name.className = 'photo-file-name'; name.textContent = photo.file.name; button.title = photo.file.name;
    button.append(img, name); button.addEventListener('click', () => selectPhoto(photo.id));
    const orientation = document.createElement('span'); orientation.className = 'photo-orientation';
    const icon = document.createElement('i'); icon.dataset.lucide = logoKey(photo) === 'vertical' ? 'rectangle-vertical' : 'rectangle-horizontal';
    orientation.append(icon, document.createTextNode(formatLabel(photo)));
    item.append(button, orientation);
    if (photo.state !== 'ready') {
      const badge = document.createElement('span'); badge.className = `photo-state${photo.state === 'error' ? ' error' : ''}`;
      const mark = document.createElement('i'); mark.dataset.lucide = photo.state === 'error' ? 'circle-alert' : 'check';
      badge.title = photo.state === 'error' ? 'Erro ao exportar' : 'Exportada'; badge.append(mark); item.append(badge);
    }
    return item;
  }));
  paintIcons();
}
async function selectPhoto(id) {
  const token = ++state.generation; state.selected = id;
  dispose(state.bitmap); state.bitmap = null; viewport.setPhoto(null, null);
  const photo = selected(); $('loading-state').hidden = !photo; $('empty-state').hidden = Boolean(photo); $('photo-badge').hidden = true;
  $('show-original').checked = false;
  if (!photo) {
    $('photo-name').textContent = 'Seu próximo lote começa aqui.'; $('photo-info').textContent = 'Adicione suas fotos. A Well cuida da assinatura.';
    $('image-index').textContent = ''; $('preview-hint').textContent = 'O fundo é da Well. O próximo destaque é o seu imóvel.';
    renderTray(); controls(); syncSettings(); return;
  }
  $('photo-name').textContent = photo.file.name; $('photo-name').title = photo.file.name;
  $('photo-info').textContent = `${photo.width.toLocaleString('pt-BR')} × ${photo.height.toLocaleString('pt-BR')} px · ${formatLabel(photo)} · Logo ${logoKey(photo) === 'vertical' ? 'vertical' : 'horizontal'}`;
  $('image-index').textContent = `${state.photos.indexOf(photo) + 1} / ${state.photos.length}`;
  $('preview-hint').textContent = 'Arraste o logo · Roda do mouse para zoom · Espaço + arrastar para navegar';
  renderTray(); controls(); syncSettings();
  try {
    const bitmap = await previewBitmap(photo);
    if (token !== state.generation) { dispose(bitmap); return; }
    state.bitmap = bitmap; viewport.setPhoto(photo, bitmap);
    $('photo-badge').textContent = `Logo ${logoKey(photo) === 'vertical' ? 'vertical' : 'horizontal'} automático`; $('photo-badge').hidden = false;
  } catch (error) { if (token === state.generation) { message(`Não foi possível abrir a prévia: ${error.message}`, 'error'); errors([...state.errors, `${photo.file.name}: ${error.message}`]); } }
  finally { if (token === state.generation) { $('loading-state').hidden = true; controls(); syncSettings(); } }
}
async function importFiles(files) {
  if (busy() || !files.length) return;
  state.importing = true; controls(); errors([]);
  const failures = [], added = [];
  const keys = new Set(state.photos.map(p => `${p.file.name}:${p.file.size}:${p.file.lastModified}`));
  let duplicates = 0;
  try {
    for (const [index, file] of [...files].entries()) {
      if (state.photos.length >= 200) { failures.push('O lote comporta até 200 fotos. Baixe este lote antes de adicionar mais.'); break; }
      const key = `${file.name}:${file.size}:${file.lastModified}`;
      if (keys.has(key)) { duplicates++; continue; }
      message(`Abrindo arquivo ${index + 1} de ${files.length}…`);
      try { const photo = await inspectFile(file); state.photos.push(photo); added.push(photo); keys.add(key); }
      catch (error) { failures.push(`${file.name}: ${error.message}`); }
      await nextFrame();
    }
    errors(failures);
    if (added.length) { if (!state.selected) await selectPhoto(added[0].id); else renderTray(); }
    const extra = duplicates ? ` ${duplicates} ${duplicates === 1 ? 'arquivo repetido ignorado' : 'arquivos repetidos ignorados'}.` : '';
    message(added.length ? `${quantity(added.length)} ${added.length === 1 ? 'adicionada' : 'adicionadas'}.${extra}${failures.length ? ' Alguns arquivos não foram abertos.' : ' O lote está pronto.'}` : failures.length ? 'Não foi possível adicionar os arquivos. Veja os detalhes.' : `Essas fotos já estão no lote.${extra}`, failures.length ? 'error' : '');
  } finally { state.importing = false; controls(); syncSettings(); }
}

for (const [index, [key, label, short]] of positions.entries()) {
  const button = document.createElement('button'); button.type = 'button'; button.className = 'position-preset'; button.dataset.position = key;
  button.title = label; button.setAttribute('aria-label', label); button.setAttribute('aria-pressed', 'false');
  const symbol = document.createElement('span'); symbol.className = 'anchor-symbol'; symbol.setAttribute('aria-hidden', 'true');
  const dot = document.createElement('span'); dot.style.gridColumn = String(index % 3 + 1); dot.style.gridRow = String(Math.floor(index / 3) + 1); symbol.append(dot);
  button.append(symbol, document.createTextNode(short)); $('position-grid').append(button);
}
$('original-position').dataset.position = 'original'; $('free-position').dataset.position = 'free';
for (const button of document.querySelectorAll('[data-position]')) button.addEventListener('click', () => {
  if (busy()) return;
  const photo = selected();
  if (button.dataset.position === 'free' && photo) { const b = geometry(photo, state.settings); state.settings.x = (b.x + b.width / 2) / photo.width; state.settings.y = (b.y + b.height / 2) / photo.height; }
  state.settings.position = button.dataset.position; changed();
});
for (const [id, key] of [['logo-size', 'scale'], ['logo-opacity', 'opacity'], ['logo-margin', 'margin']]) $(id).addEventListener('input', () => { if (!busy()) { state.settings[key] = Number($(id).value); changed(); } });
for (const id of ['position-x', 'position-y']) {
  $(id).addEventListener('change', () => {
    if (busy()) return;
    const x = Number($('position-x').value), y = Number($('position-y').value);
    if (!$('position-x').value || !$('position-y').value || !Number.isFinite(x) || !Number.isFinite(y) || x < 0 || x > 100 || y < 0 || y > 100) {
      $('coordinate-error').textContent = 'Informe uma posição de 0 a 100% nos dois campos.'; $('coordinate-error').hidden = false; return;
    }
    state.settings = { ...state.settings, position: 'free', x: x / 100, y: y / 100 }; changed();
  });
  $(id).addEventListener('blur', () => { if ($('coordinate-error').hidden) syncSettings(); });
}
$('reset-button').addEventListener('click', () => { if (!busy()) { state.settings = { ...defaults }; $('output-format').value = 'original'; changed(); } });
$('output-format').addEventListener('change', changed);
$('show-original').addEventListener('change', updateViewport);
for (const mode of ['logo', 'pan']) $(`tool-${mode}`).addEventListener('click', () => {
  state.mode = mode; viewport.setMode(mode);
  for (const m of ['logo', 'pan']) { $(`tool-${m}`).classList.toggle('active', m === mode); $(`tool-${m}`).setAttribute('aria-pressed', String(m === mode)); }
});
$('zoom-in').addEventListener('click', () => viewport.zoom(1.25)); $('zoom-out').addEventListener('click', () => viewport.zoom(.8));
$('fit-button').addEventListener('click', () => viewport.fit()); $('actual-button').addEventListener('click', () => viewport.actual());
for (const id of ['add-button', 'empty-add']) $(id).addEventListener('click', () => $('file-input').click());
$('file-input').addEventListener('change', () => { const files = [...$('file-input').files]; $('file-input').value = ''; importFiles(files); });
$('remove-button').addEventListener('click', () => {
  if (busy()) return; const index = state.photos.findIndex(p => p.id === state.selected); if (index < 0) return;
  URL.revokeObjectURL(state.photos[index].thumbnail); state.photos.splice(index, 1);
  selectPhoto(state.photos[Math.min(index, state.photos.length - 1)]?.id || null);
  errors([]); message(state.photos.length ? `${quantity(state.photos.length)} no lote.` : 'Lote vazio. Adicione novas fotos.');
});
$('clear-button').addEventListener('click', () => {
  if (busy()) return; for (const photo of state.photos) URL.revokeObjectURL(photo.thumbnail);
  state.photos = []; selectPhoto(null); errors([]); message('Lote vazio. Adicione novas fotos.');
});
let dragDepth = 0;
window.addEventListener('dragover', e => { if ([...e.dataTransfer.types].includes('Files')) { e.preventDefault(); e.dataTransfer.dropEffect = busy() ? 'none' : 'copy'; } });
window.addEventListener('dragenter', e => { if ([...e.dataTransfer.types].includes('Files')) { e.preventDefault(); dragDepth++; if (!busy()) $('drop-overlay').hidden = false; } });
window.addEventListener('dragleave', () => { if (--dragDepth <= 0) { dragDepth = 0; $('drop-overlay').hidden = true; } });
window.addEventListener('drop', e => { e.preventDefault(); dragDepth = 0; $('drop-overlay').hidden = true; importFiles([...e.dataTransfer.files]); });

const downloadUrls = new Set();
function save(blob, name) {
  const url = URL.createObjectURL(blob); downloadUrls.add(url);
  const a = document.createElement('a'); a.href = url; a.download = name; a.hidden = true; document.body.append(a); a.click(); a.remove();
  setTimeout(() => { URL.revokeObjectURL(url); downloadUrls.delete(url); }, 60_000);
}
let exportController;
$('download-button').addEventListener('click', async () => {
  if (busy() || !state.photos.length) return;
  state.exporting = true; exportController = new AbortController(); errors([]);
  $('export-progress').hidden = false; $('export-progress').max = state.photos.length; $('export-progress').value = 0;
  controls(); renderTray(); message('Preparando suas fotos…');
  try {
    const result = await exportBatch([...state.photos], { ...state.settings }, $('output-format').value, exportController.signal, (index, photo, error) => {
      $('export-progress').value = index; message(`Processando ${index} de ${state.photos.length}: ${photo.file.name}`);
      if (error) photo.state = 'error';
    });
    errors(result.failed.map(({ photo, message: detail }) => `${photo.file.name}: ${detail}`));
    if (result.cancelled || exportController.signal.aborted) { message('Download cancelado. Suas fotos continuam no lote.'); }
    else if (result.blob) {
      save(result.blob, result.name);
      for (const { photo } of result.successful) photo.state = 'exported';
      message(`${quantity(result.successful.length)} ${result.successful.length === 1 ? 'pronta' : 'prontas'}. Download iniciado.${result.failed.length ? ' Confira os arquivos com erro.' : ''}`, result.failed.length ? 'error' : 'success');
    } else message('Nenhuma foto foi exportada. Confira os detalhes abaixo.', 'error');
  } catch (error) { message(`Não foi possível baixar: ${error.message}`, 'error'); }
  finally { state.exporting = false; $('export-progress').hidden = true; controls(); renderTray(); }
});
$('cancel-button').addEventListener('click', () => { exportController?.abort(); message('Cancelando após a foto atual…'); $('cancel-button').disabled = true; });
$('download-button').addEventListener('click', () => { $('cancel-button').disabled = false; });
$('help-button').addEventListener('click', () => $('help-dialog').showModal());
$('close-help').addEventListener('click', () => $('help-dialog').close());
$('help-dialog').addEventListener('click', e => { if (e.target === $('help-dialog')) { const r = e.target.getBoundingClientRect(); if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) e.target.close(); } });
window.addEventListener('keydown', e => { if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'o' && !busy()) { e.preventDefault(); $('file-input').click(); } });
window.addEventListener('pagehide', () => { for (const url of downloadUrls) URL.revokeObjectURL(url); });
paintIcons(); controls(); syncSettings();
loadLogos().then(logos => { state.logos = logos; updateViewport(); }).catch(error => message(error.message, 'error'));
