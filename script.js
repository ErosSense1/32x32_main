/* load codes.json (mapping of special codes -> character lists) */
let codesMap = {};
(async function loadCodes(){
	try{
		const resp = await fetch('./codes.json');
		if(resp.ok){
			codesMap = await resp.json();
		}
	}catch(e){
		// fallback: keep codesMap empty if fetch fails
		codesMap = codesMap || {};
	}
})();

/* optional pixels metadata file */
let pixelsMap = {};
(async function loadPixels(){
	try{
		const resp = await fetch('./pixels.json');
 		if(resp.ok) pixelsMap = await resp.json();
	}catch(e){
 		pixelsMap = {};
 	}
})();

// Basic mapping from simple color names to hex for display
const BASIC_COLOR_MAP = {
	black: '#000000',
	white: '#FFFFFF',
	red: '#FF0000',
	green: '#00FF00',
	blue: '#0000FF',
	yellow: '#FFFF00',
	magenta: '#FF00FF',
	cyan: '#00FFFF',
	gray: '#808080',
	pink: '#FF5EA8',
	purple: '#8A2BE2',
	orange: '#FFA500'
};

// Row labels used by the pixel-code format (A-Z, then a-f)
const ROW_LABELS = (()=>{
	const up = Array.from({length:26},(_,i)=>String.fromCharCode(65+i));
	return up.concat(['a','b','c','d','e','f']);
})();
/* reveal toggle */
(function(){
	const btn = document.getElementById('reveal');
	const input = document.getElementById('secret');
	if(!btn || !input) return;
	btn.addEventListener('click', () => {
		const isPwd = input.type === 'password';
		input.type = isPwd ? 'text' : 'password';
		btn.setAttribute('aria-pressed', String(isPwd));
		btn.title = isPwd ? 'Ocultar código' : 'Mostrar código';
	});
})();
/* Form submit: read code and process it (SHA-256 token shown) */
(function(){
	const form = document.getElementById('mainForm');
	const input = document.getElementById('secret');
	const status = document.getElementById('status');
	const submitBtn = document.getElementById('submitBtn');
	const revealBtn = document.getElementById('reveal');
	if(!form || !input || !status) return;

	function setStatus(html, cls){
		status.className = cls ? cls + ' muted-note' : 'muted-note';
		status.innerHTML = html;
	}

	function escapeHtml(s){
		return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
	}

	function loaderHtml(){
		return '<span class="loader">Procesando</span>';
	}

	async function sha256hex(str){
		const enc = new TextEncoder();
		const buf = await crypto.subtle.digest('SHA-256', enc.encode(str));
		return Array.from(new Uint8Array(buf)).map(b=>b.toString(16).padStart(2,'0')).join('');
	}

	/* show a full-screen centered overlay with characters converted to code/text */
	function showCharsOverlay(chars){
		// elements to hide while overlay is shown
		const formEl = document.getElementById('mainForm');
		const canvasEl = document.getElementById('matrixCanvas');
		const scanEl = document.querySelector('.scanlines');
		const vignEl = document.querySelector('.vignette');
		const toToggle = [formEl, canvasEl, scanEl, vignEl].filter(Boolean);
		const prev = new Map();
		toToggle.forEach(el => { prev.set(el, el.style.display || ''); el.style.display = 'none'; });

		const overlay = document.createElement('div');
		overlay.className = 'overlay';
		overlay.tabIndex = -1;
		overlay.innerHTML = `<button class="overlay-close" aria-label="Cerrar">✕</button><div class="overlay-inner"><div class="overlay-grid" role="list"></div></div>`;
		document.body.appendChild(overlay);
		const grid = overlay.querySelector('.overlay-grid');

		// Now treat each entry as a pixel-code string (example: 32H11Red or 32H11FF0000)
		chars.forEach(codeStr => {
			const item = document.createElement('div');
			item.className = 'char-item';
			const glyph = document.createElement('div');
			glyph.className = 'code-glyph';
			glyph.textContent = codeStr;

			// parse pieces: size (number), row (letter), column (number), color (text or hex)
			const m = /^\s*(\d+)([A-Za-z])(\d+)_?([A-Za-z0-9#]+)\s*$/.exec(codeStr);
			const meta = document.createElement('div');
			meta.className = 'code-meta';
			if(m){
				const row = m[2].toUpperCase();
				const col = m[3];
				// show row and column only (remove size info as requested)
				const rc = document.createElement('div');
				rc.textContent = `Fila: ${row}  •  Col: ${col}`;
				meta.appendChild(rc);

				// color square instead of text
				const colorPart = m[4];
				function colorPartToHex(part){
					if(!part) return '#FF00FF';
					let p = String(part).trim();
					if(p[0] === '#') p = p.slice(1);
					if(/^([0-9A-Fa-f]{6})$/.test(p)) return '#' + p.toUpperCase();
					if(/^([0-9A-Fa-f]{8})$/.test(p)) return '#' + p.slice(0,6).toUpperCase();
					const lookup = BASIC_COLOR_MAP[p.toLowerCase()];
					if(lookup) return lookup;
					return '#FF00FF';
				}
				const colorHex = colorPartToHex(colorPart);
				const colorBox = document.createElement('span');
				colorBox.setAttribute('aria-label', 'color');
				colorBox.style.display = 'inline-block';
				colorBox.style.width = '18px';
				colorBox.style.height = '18px';
				colorBox.style.marginLeft = '8px';
				colorBox.style.verticalAlign = 'middle';
				colorBox.style.borderRadius = '4px';
				colorBox.style.border = '1px solid rgba(255,255,255,0.06)';
				colorBox.style.background = colorHex;
				rc.appendChild(colorBox);
			} else {
				meta.textContent = 'Formato desconocido (esperado: 32H11Red)';
			}

			// attempt to show additional pixels.json data if available
			const lookupKey = codeStr;
			const extra = pixelsMap && (pixelsMap[lookupKey] || pixelsMap[lookupKey.toUpperCase()]);
			if(extra !== undefined){
				try{
					const pre = document.createElement('pre');
					pre.style.textAlign = 'left';
					pre.style.marginTop = '8px';
					pre.textContent = JSON.stringify(extra, null, 2);
					meta.appendChild(pre);
				}catch(e){
					const p = document.createElement('div');
					p.style.marginTop = '8px';
					p.textContent = String(extra);
					meta.appendChild(p);
				}
			}
			item.appendChild(glyph);
			item.appendChild(meta);
			grid.appendChild(item);
		});

		// After building the grid, additionally pick the first code and show
		// After building the grid, additionally show a visual table when the
		// returned `chars` represent a full row or the full image.
		if(chars.length > 0){
			const first = String(chars[0] || '').trim();
			const mm = /^\s*(\d+)([A-Za-z])(\d+)_?([A-Za-z0-9#]+)\s*$/.exec(first);
			if(mm){
				const size = parseInt(mm[1], 10);
				// helper: normalize color part into a hex string like #RRGGBB
				function colorPartToHex(part){
					if(!part) return '#FF00FF';
					let p = String(part).trim();
					if(p[0] === '#') p = p.slice(1);
					if(/^([0-9A-Fa-f]{6})$/.test(p)) return '#' + p.toUpperCase();
					if(/^([0-9A-Fa-f]{8})$/.test(p)) return '#' + p.slice(0,6).toUpperCase();
					const lookup = BASIC_COLOR_MAP[p.toLowerCase()];
					if(lookup) return lookup;
					return '#FF00FF';
				}

				function contrastColor(hex){
					if(!hex) return '#000';
					h = String(hex).replace('#','');
					const r = parseInt(h.slice(0,2),16);
					const g = parseInt(h.slice(2,4),16);
					const b = parseInt(h.slice(4,6),16);
					const lum = (0.2126*r + 0.7152*g + 0.0722*b)/255;
					return lum > 0.6 ? '#000' : '#fff';
				}

				// If chars length equals size -> single row; if size*size -> full image
				if(chars.length === size || chars.length === (size*size)){
					const tableWrap = document.createElement('div');
					tableWrap.style.marginTop = '18px';
					const tbl = document.createElement('table');
					tbl.style.borderCollapse = 'collapse';
					tbl.style.margin = '0 auto';
					// styling for cells
					for(let r=0;r<(chars.length === size ? 1 : size);r++){
						const tr = document.createElement('tr');
						for(let c=0;c<size;c++){
							const idx = (chars.length === size) ? c : (r*size + c);
							const code = chars[idx] || '';
							const mm2 = /^\s*(\d+)([A-Za-z])(\d+)_?([A-Za-z0-9#]+)\s*$/.exec(code);
							let hex = '#FF00FF';
							if(mm2) hex = colorPartToHex(mm2[4]);
							const td = document.createElement('td');
							td.textContent = hex;
							td.style.padding = '6px 8px';
							td.style.minWidth = '36px';
							td.style.textAlign = 'center';
							td.style.background = hex;
							td.style.color = contrastColor(hex);
							td.style.fontFamily = '"Share Tech Mono", monospace';
							td.style.border = '1px solid rgba(0,0,0,0.2)';
							tr.appendChild(td);
						}
						tbl.appendChild(tr);
					}
					tableWrap.appendChild(tbl);
					overlay.querySelector('.overlay-inner').appendChild(tableWrap);
				} else {
					// fallback: previous behavior (random row/col color-list)
					const row = mm[2];
					const col = parseInt(mm[3],10);
					const colorPart = mm[4];
					const chooseRow = Math.random() < 0.5;
					let codesList = [];
					if(pixelsMap && pixelsMap.rows && pixelsMap.rows[row.toUpperCase()]){
						codesList = pixelsMap.rows[row.toUpperCase()].slice();
					} else if(pixelsMap && pixelsMap.rows && pixelsMap.rows[row]){
						codesList = pixelsMap.rows[row].slice();
					} else {
						if(chooseRow){
							for(let x=0;x<size;x++) codesList.push(`${size}${row}${x}${colorPart}`);
						} else {
							for(let y=0;y<size && y<ROW_LABELS.length;y++){
								const rlabel = ROW_LABELS[y];
								codesList.push(`${size}${rlabel}${col}${colorPart}`);
							}
						}
					}

					const listWrap = document.createElement('div');
					listWrap.className = 'color-list-wrap';
					listWrap.style.marginTop = '18px';
					listWrap.style.display = 'flex';
					listWrap.style.flexWrap = 'wrap';
					listWrap.style.justifyContent = 'center';
					listWrap.style.gap = '10px';

					const title = document.createElement('div');
					title.textContent = chooseRow ? `Mostrando fila ${row.toUpperCase()}` : `Mostrando columna ${col}`;
					title.style.width = '100%';
					title.style.textAlign = 'center';
					title.style.marginBottom = '6px';
					title.style.color = '#bfffcf';
					title.style.fontWeight = '700';
					listWrap.appendChild(title);

					codesList.forEach(code => {
						const mm2 = /^\s*(\d+)([A-Za-z])(\d+)_?([A-Za-z0-9#]+)\s*$/.exec(code);
						let hex = '#FF00FF';
						if(mm2) hex = colorPartToHex(mm2[4]);
						const chip = document.createElement('div');
						chip.textContent = hex;
						chip.style.padding = '6px 10px';
						chip.style.borderRadius = '8px';
						chip.style.border = '1px solid rgba(255,255,255,0.04)';
						chip.style.background = 'rgba(255,255,255,0.02)';
						chip.style.color = hex;
						chip.style.fontFamily = '"Share Tech Mono", monospace';
						chip.style.fontWeight = '700';
						chip.style.minWidth = '90px';
						chip.style.textAlign = 'center';
						listWrap.appendChild(chip);
					});

					overlay.querySelector('.overlay-inner').appendChild(listWrap);
				}
			}
		}

		const closeBtn = overlay.querySelector('.overlay-close');
		function cleanup(){
			overlay.remove();
			prev.forEach((val, el) => { el.style.display = val; });
			document.removeEventListener('keydown', onKey);
		}
		function onKey(e){ if(e.key === 'Escape') cleanup(); }
		closeBtn.addEventListener('click', cleanup);
		overlay.addEventListener('click', (ev)=>{ if(ev.target === overlay) cleanup(); });
		document.addEventListener('keydown', onKey);
		// focus for keyboard users
		overlay.focus();
	}

	/* show a centered red announcement for wrong codes that blurs background
	   and displays hearts on the sides */
	function showWrongAnnouncement(message){
		const formEl = document.getElementById('mainForm');
		const canvasEl = document.getElementById('matrixCanvas');
		const scanEl = document.querySelector('.scanlines');
		const vignEl = document.querySelector('.vignette');
		const toToggle = [formEl, canvasEl, scanEl, vignEl].filter(Boolean);
		const prev = new Map();
		toToggle.forEach(el => { prev.set(el, el.style.filter || ''); el.style.filter = 'blur(4px)'; });

		const ann = document.createElement('div');
		ann.className = 'announce-overlay';
		ann.innerHTML = `
			<div class="announce-inner">
				<button class="announce-close" aria-label="Cerrar anuncio">✕</button>
				<div class="announce-heart left" aria-hidden="true"></div>
				<div class="announce-body"><div class="announce-msg">${message}</div></div>
				<div class="announce-heart right" aria-hidden="true"></div>
			</div>`;
		document.body.appendChild(ann);

		const closeBtn = ann.querySelector('.announce-close');
		function cleanup(){
			ann.remove();
			prev.forEach((val, el) => { el.style.filter = val; });
		}
		closeBtn.addEventListener('click', cleanup);
		ann.addEventListener('click', (ev)=>{ if(ev.target === ann) cleanup(); });

		// add keyboard escape to close
		document.addEventListener('keydown', function onKey(e){ if(e.key === 'Escape'){ cleanup(); document.removeEventListener('keydown', onKey); } });

		// focus the close button for accessibility
		closeBtn.focus();
	}

	/* generate a deterministic pixel-code similar to '32H11Red' from arbitrary input */
	function generatePixelCode(input){
		const s = String(input || '').trim();
		// choose size from length
		const len = s.length;
		let size = 32;
		if(len <= 2) size = 8;
		else if(len <= 4) size = 16;
		else if(len <= 8) size = 24;
		else if(len <= 12) size = 32;
		else if(len <= 20) size = 48;
		else size = 64;

		// find first letter for row, default 'M'
		const m = /[A-Za-z]/.exec(s);
		const row = m ? m[0].toUpperCase() : 'M';

		// simple numeric derived from char codes
		let sum = 0;
		for(let i=0;i<s.length;i++) sum += s.charCodeAt(i);
		const col = (sum % Math.max(1, size)) + 1; // column within size

		const colors = ['Red','Green','Blue','Purple','Cyan','Yellow','Pink','Orange','Magenta'];
		const color = colors[sum % colors.length];

		// include underscore between position and color for consistency
		return `${size}${row}${col}_${color}`;
	}

	form.addEventListener('submit', async (e)=>{
		e.preventDefault();
		const code = input.value || '';
		if(code.trim().length === 0){
			setStatus('Por favor, escribe el código antes de enviar.', 'status-error');
			input.focus();
			return;
		}

		// disable controls
		submitBtn.disabled = true;
		input.disabled = true;
		revealBtn.disabled = true;

		setStatus(loaderHtml());

		try{
			// check special codes (case-insensitive)
			const key = code.trim().toUpperCase();
			if(codesMap && Object.prototype.hasOwnProperty.call(codesMap, key)){
				const chars = codesMap[key];
				// show centered overlay with character glyphs and codes
				showCharsOverlay(chars);
			} else {
				// wrong code: show the requested announcement overlay
				showWrongAnnouncement('Error: No puedes adivinarlos mi amor Mwah <3');
			}
		}catch(err){
			setStatus('Error al procesar el código. Inténtalo de nuevo.','status-error');
		}

		// re-enable controls after short delay so user can see result
		setTimeout(()=>{
			submitBtn.disabled = false;
			input.disabled = false;
			revealBtn.disabled = false;
		},1000);
	});
})();

/* matrix rain effect (simplified for performance) */
(function(){
	const canvas = document.getElementById('matrixCanvas');
	if(!canvas) return;
	const ctx = canvas.getContext('2d');
	let w = 0, h = 0;

	// Use larger glyphs and a short character set to reduce columns and drawing work
	let fontSize = 28;
	let columns = 0;
	let drops = [];
	const chars = '01@#%'; // short set, fewer glyph draws

	let intervalId = null;
	const interval = 100; // ms -> ~10fps

	function resize(){
		const dpr = Math.max(1, window.devicePixelRatio || 1);
		// set physical canvas size with DPR for crispness, but keep logical size for drawing
		canvas.width = Math.floor(window.innerWidth * dpr);
		canvas.height = Math.floor(window.innerHeight * dpr);
		canvas.style.width = window.innerWidth + 'px';
		canvas.style.height = window.innerHeight + 'px';
		ctx.setTransform(dpr,0,0,dpr,0,0);
		w = window.innerWidth;
		h = window.innerHeight;
		columns = Math.max(4, Math.floor(w / fontSize));
		drops = new Array(columns).fill(1).map(()=>Math.floor(Math.random()*h/fontSize));
		ctx.textBaseline = 'top';
		ctx.font = fontSize + 'px "Share Tech Mono", monospace';
	}

	function step(){
		// skip drawing when not visible to save CPU
		if(document.hidden) return;

		// stronger fade so fewer frames look okay
		ctx.fillStyle = 'rgba(0,0,0,0.42)';
		ctx.fillRect(0,0,w,h);

		for(let i=0;i<columns;i++){
			// draw less often: skip many columns per frame
			if(Math.random() > 0.68) continue;
			const text = chars[(Math.random()*chars.length)|0];
			const x = i * fontSize;
			const y = drops[i] * fontSize;
			ctx.fillStyle = (Math.random()>0.98) ? '#b6ffb3' : '#00ff80';
			ctx.fillText(text, x, y);
			drops[i]++;
			if(drops[i]*fontSize > h && Math.random() > 0.98){
				drops[i] = 0;
			}
		}
	}

	function start(){
		if(intervalId) clearInterval(intervalId);
		intervalId = setInterval(step, interval);
	}

	function stop(){
		if(intervalId){ clearInterval(intervalId); intervalId = null; }
	}

	window.addEventListener('resize', resize);
	window.addEventListener('orientationchange', resize);
	document.addEventListener('visibilitychange', ()=>{ if(document.hidden) stop(); else start(); });

	resize();
	start();

	window.addEventListener('unload', ()=> stop());
})();
