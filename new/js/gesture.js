/**
 * 隔空手勢（筆記本攝像頭）：MediaPipe Hand Landmarker 在瀏覽器裡跑，全部檔案本地（離線包可用）。
 * 三個動作：張開手掌移動（拖／轉）、拇指食指捏合（點）、雙手拉開合攏（縮放／透視）。
 * 食指單獨伸出 = 指點（刻銘那幕當刻刀）。
 *
 * 用法：
 *   Gesture.start({ onFrame(state) {}, onPinch(pointer) {}, mount: document.body })
 *   Gesture.stop()
 * state = { hands, primary, second, twoDist, t }
 * primary = { x, y (0..1，已鏡像、左上為原點), palmX, palmY, pinch, open, pointing, handed, scale }
 */
(function () {
    'use strict';
    const BASE = (document.currentScript && document.currentScript.src) ? document.currentScript.src.replace(/js\/gesture\.js.*$/, '') : './';
    const WASM = BASE + 'js/vendor/mediapipe/wasm';
    const BUNDLE = BASE + 'js/vendor/mediapipe/vision_bundle.mjs';
    const MODEL = BASE + 'assets/models/hand_landmarker.task';

    const G = { running: false, state: null, status: '', _cb: {}, _el: null, _video: null, _lm: null, _raf: 0, _stream: null, _pinchWas: [false, false], _smooth: [null, null], _prevTime: -1 };

    function dist(a, b) { const dx = a.x - b.x, dy = a.y - b.y, dz = (a.z || 0) - (b.z || 0); return Math.sqrt(dx * dx + dy * dy + dz * dz); }
    // 21 個關鍵點：0 腕，4 拇指尖，8 食指尖，12 中指尖，16 無名指尖，20 小指尖；6/10/14/18 是各指第二關節
    function derive(lm, handedness, idx) {
        const wrist = lm[0], scale = Math.max(1e-3, dist(wrist, lm[9]));
        const ext = (tip, pip) => dist(lm[tip], wrist) > dist(lm[pip], wrist) * 1.12;
        const fingers = [ext(8, 6), ext(12, 10), ext(16, 14), ext(20, 18)];
        const pinchD = dist(lm[4], lm[8]) / scale;
        const was = G._pinchWas[idx];
        const pinch = was ? pinchD < 0.55 : pinchD < 0.38;   // 遲滯，免得抖
        G._pinchWas[idx] = pinch;
        const open = fingers.every(Boolean) && !pinch;
        const pointing = fingers[0] && !fingers[1] && !fingers[2] && !pinch;
        const palm = [0, 5, 9, 13, 17].reduce((a, i) => ({ x: a.x + lm[i].x / 5, y: a.y + lm[i].y / 5 }), { x: 0, y: 0 });
        // 鏡像：攝像頭是自拍視角，手往右移畫面上也往右
        const raw = { x: 1 - lm[8].x, y: lm[8].y, palmX: 1 - palm.x, palmY: palm.y };
        const s = G._smooth[idx];
        const k = 0.45;
        const sm = s ? { x: s.x + (raw.x - s.x) * k, y: s.y + (raw.y - s.y) * k, palmX: s.palmX + (raw.palmX - s.palmX) * k, palmY: s.palmY + (raw.palmY - s.palmY) * k } : raw;
        G._smooth[idx] = sm;
        return { ...sm, pinch, pinchD, open, pointing, fingers, handed: handedness, scale };
    }

    function ui(mount) {
        if (G._el) return G._el;
        const el = document.createElement('div'); el.id = 'gestureUI';
        el.innerHTML = `
            <style>
                #gestureUI { position: fixed; right: max(12px, env(safe-area-inset-right)); bottom: max(12px, env(safe-area-inset-bottom)); z-index: 60; font-family: "Noto Serif TC", serif; color: #f4d58a; pointer-events: none; }
                #gestureUI .box { position: relative; width: 168px; height: 126px; border: 1px solid rgba(244,213,138,.45); background: #16130f; overflow: hidden; display: none; }
                #gestureUI.on .box { display: block; }
                #gestureUI canvas { width: 100%; height: 100%; display: block; transform: scaleX(-1); }
                #gestureUI .st { font-size: 11px; letter-spacing: .15em; margin-top: 4px; text-align: right; opacity: .8; text-shadow: 0 0 4px #000; }
                #gestureCursor { position: fixed; left: 0; top: 0; width: 26px; height: 26px; margin: -13px 0 0 -13px; border-radius: 50%; border: 2px solid #f4d58a; box-shadow: 0 0 10px rgba(244,213,138,.8); z-index: 61; pointer-events: none; display: none; transition: transform .08s; }
                #gestureCursor.pinch { transform: scale(.55); background: rgba(244,213,138,.8); }
                #gestureCursor.open { border-style: dashed; }
            </style>
            <div class="box"><canvas width="320" height="240"></canvas></div>
            <div class="st" id="gestureStatus"></div>`;
        (mount || document.body).appendChild(el);
        const cur = document.createElement('div'); cur.id = 'gestureCursor'; document.body.appendChild(cur);
        G._el = el; G._cursor = cur; G._canvas = el.querySelector('canvas');
        return el;
    }
    function setStatus(s) { G.status = s; const e = document.getElementById('gestureStatus'); if (e) e.textContent = s; if (G._cb.onStatus) G._cb.onStatus(s); }

    function draw(result) {
        const cv = G._canvas, ctx = cv.getContext('2d'), v = G._video;
        if (!v.videoWidth) return;
        ctx.drawImage(v, 0, 0, cv.width, cv.height);
        ctx.fillStyle = 'rgba(22,19,15,.35)'; ctx.fillRect(0, 0, cv.width, cv.height);
        const EDGES = [[0, 1], [1, 2], [2, 3], [3, 4], [0, 5], [5, 6], [6, 7], [7, 8], [5, 9], [9, 10], [10, 11], [11, 12], [9, 13], [13, 14], [14, 15], [15, 16], [13, 17], [17, 18], [18, 19], [19, 20], [0, 17]];
        for (const lm of (result.landmarks || [])) {
            ctx.strokeStyle = 'rgba(244,213,138,.8)'; ctx.lineWidth = 2; ctx.beginPath();
            for (const [a, b] of EDGES) { ctx.moveTo(lm[a].x * cv.width, lm[a].y * cv.height); ctx.lineTo(lm[b].x * cv.width, lm[b].y * cv.height); }
            ctx.stroke();
            ctx.fillStyle = '#fff';
            for (const p of lm) { ctx.beginPath(); ctx.arc(p.x * cv.width, p.y * cv.height, 2.5, 0, Math.PI * 2); ctx.fill(); }
        }
    }

    async function start(opts) {
        opts = opts || {}; G._cb = opts;
        ui(opts.mount);
        if (G.running) return true;
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) { setStatus('此瀏覽器沒有攝像頭接口'); return false; }
        if (!window.isSecureContext) { setStatus('攝像頭需要 https 或 localhost'); return false; }
        G._el.classList.add('on');
        setStatus('載入手勢模型…');
        try {
            const vision = await import(BUNDLE);
            const files = await vision.FilesetResolver.forVisionTasks(WASM);
            let lm;
            try {
                lm = await vision.HandLandmarker.createFromOptions(files, { baseOptions: { modelAssetPath: MODEL, delegate: 'GPU' }, runningMode: 'VIDEO', numHands: 2, minHandDetectionConfidence: 0.5, minTrackingConfidence: 0.5 });
            } catch (e) {
                lm = await vision.HandLandmarker.createFromOptions(files, { baseOptions: { modelAssetPath: MODEL, delegate: 'CPU' }, runningMode: 'VIDEO', numHands: 2 });
            }
            G._lm = lm;
        } catch (e) { console.warn('gesture model', e); setStatus('手勢模型載入失敗'); G._el.classList.remove('on'); return false; }
        setStatus('打開攝像頭…');
        try {
            G._stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } }, audio: false });
        } catch (e) { console.warn('camera', e); setStatus('沒有拿到攝像頭權限'); G._el.classList.remove('on'); return false; }
        const v = document.createElement('video'); v.playsInline = true; v.muted = true; v.srcObject = G._stream; v.style.display = 'none'; document.body.appendChild(v);
        await v.play(); G._video = v;
        G.running = true; setStatus('請把手舉到鏡頭前');
        loop();
        return true;
    }
    function loop() {
        if (!G.running) return;
        G._raf = requestAnimationFrame(loop);
        const v = G._video; if (!v || v.readyState < 2) return;
        const now = performance.now(); if (now === G._prevTime) return; G._prevTime = now;
        let result;
        try { result = G._lm.detectForVideo(v, now); } catch (e) { return; }
        draw(result);
        const hands = (result.landmarks || []).map((lm, i) => derive(lm, (result.handedness && result.handedness[i] && result.handedness[i][0]) ? result.handedness[i][0].categoryName : '', i));
        for (let i = hands.length; i < 2; i++) { G._pinchWas[i] = false; G._smooth[i] = null; }
        const primary = hands[0] || null, second = hands[1] || null;
        const twoDist = (primary && second) ? Math.hypot(primary.palmX - second.palmX, primary.palmY - second.palmY) : null;
        const state = { hands: hands.length, primary, second, twoDist, t: now };
        // 游標
        const cur = G._cursor;
        if (primary) {
            cur.style.display = 'block'; cur.style.left = (primary.x * innerWidth) + 'px'; cur.style.top = (primary.y * innerHeight) + 'px';
            cur.classList.toggle('pinch', primary.pinch); cur.classList.toggle('open', primary.open);
            setStatus(primary.pinch ? '捏合 · 點' : primary.open ? '手掌 · 拖' : primary.pointing ? '食指 · 指' : (second ? '雙手 · 縮放' : '看到手了'));
        } else { cur.style.display = 'none'; setStatus('請把手舉到鏡頭前'); }
        if (primary && primary.pinch && !G._lastPinch && G._cb.onPinch) G._cb.onPinch({ x: primary.x * innerWidth, y: primary.y * innerHeight }, state);
        G._lastPinch = !!(primary && primary.pinch);
        G.state = state;
        if (G._cb.onFrame) G._cb.onFrame(state);
    }
    function stop() {
        G.running = false; cancelAnimationFrame(G._raf);
        if (G._stream) { G._stream.getTracks().forEach(t => t.stop()); G._stream = null; }
        if (G._video) { G._video.remove(); G._video = null; }
        if (G._el) G._el.classList.remove('on');
        if (G._cursor) G._cursor.style.display = 'none';
        G.state = null; G._lastPinch = false; setStatus('');
    }
    // 捏合 = 在游標處點一下（按鈕、熱點、字都能點）
    function clickAt(x, y) {
        const el = document.elementFromPoint(x, y); if (!el) return null;
        const init = { bubbles: true, cancelable: true, clientX: x, clientY: y, pointerType: 'touch' };
        try { el.dispatchEvent(new PointerEvent('pointerdown', init)); el.dispatchEvent(new PointerEvent('pointerup', init)); } catch (e) {}
        el.dispatchEvent(new MouseEvent('click', init));
        return el;
    }
    window.Gesture = { start, stop, clickAt, derive, get running() { return G.running; }, get state() { return G.state; }, get status() { return G.status; } };
})();
