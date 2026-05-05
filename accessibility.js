/**
 * accessibility.js — Rizzo Labs Shared Accessibility Layer
 *
 * Injects into every page automatically:
 *   A. Floating toolbar: TTS reader, high-contrast toggle, text-size controls
 *   B. Hero section audio button (index.html only)
 *   C. Per-project card speaker buttons (index.html + projects.html)
 *   D. Video CC badges + region wrapping
 *   E. Keyboard focus rings (suppressed for mouse users)
 *   F. High-contrast CSS
 *   G. Reads hidden .a11y-audio-desc elements in TTS order
 *   H. Speaker button on every image (reads alt text aloud on click)
 *   I. Audio description button on every video (🔊 reads desc, ⏹ stops TTS)
 */

(function () {
  'use strict';

  // ─── Constants ────────────────────────────────────────────────────────────
  var LS_CONTRAST = 'a11y_high_contrast';
  var LS_FONTSIZE = 'a11y_font_size';
  var DEFAULT_FONTSIZE = 16;
  var MIN_FONTSIZE = 10;
  var MAX_FONTSIZE = 28;
  var FONT_STEP = 2;

  // Tracks the current logical font-size level (avoids re-reading getComputedStyle)
  var currentFontSize = DEFAULT_FONTSIZE;

  // Dynamic <style> for font-size overrides — injected into <head> and updated
  // by applyFontSize(). Using !important ensures we beat style.css's px values.
  var fontOverrideEl = document.createElement('style');
  fontOverrideEl.id = 'a11y-font-override';
  document.head.appendChild(fontOverrideEl);

  // Scales all key text elements relative to the DEFAULT_FONTSIZE baseline.
  // style.css uses absolute px throughout (body=15, h1=36, h2=28, h3=24,
  // h4=18, h5=14) so we must override each explicitly with !important.
  function applyFontSize(px) {
    currentFontSize = px;
    if (px === DEFAULT_FONTSIZE) {
      fontOverrideEl.textContent = '';
      return;
    }
    var s = px / DEFAULT_FONTSIZE;
    fontOverrideEl.textContent = [
      'html { font-size: ' + px + 'px !important; }',
      'body, p, li, td, th, blockquote {',
      '  font-size: ' + Math.round(15 * s) + 'px !important;',
      '  line-height: ' + Math.round(26 * s) + 'px !important;',
      '}',
      'h1 { font-size: ' + Math.round(36 * s) + 'px !important;',
      '     line-height: ' + Math.round(48 * s) + 'px !important; }',
      'h2 { font-size: ' + Math.round(28 * s) + 'px !important;',
      '     line-height: ' + Math.round(36 * s) + 'px !important; }',
      'h3 { font-size: ' + Math.round(24 * s) + 'px !important; }',
      'h4 { font-size: ' + Math.round(18 * s) + 'px !important;',
      '     line-height: ' + Math.round(28 * s) + 'px !important; }',
      'h5 { font-size: ' + Math.round(14 * s) + 'px !important;',
      '     line-height: ' + Math.round(24 * s) + 'px !important; }',
    ].join('\n');
  }

  // ─── E. Keyboard focus rings ───────────────────────────────────────────────
  // Inject focus ring CSS + mouse/keyboard tracking
  (function injectFocusStyles() {
    var style = document.createElement('style');
    style.id = 'a11y-focus-styles';
    style.textContent = [
      // Visible rings for keyboard users
      '*:focus-visible {',
      '  outline: 2px solid #1a73e8 !important;',
      '  outline-offset: 3px !important;',
      '  box-shadow: 0 0 0 4px rgba(26,115,232,0.25) !important;',
      '  border-radius: 3px;',
      '}',
      // Suppress rings when mouse is in use
      'body.using-mouse *:focus-visible {',
      '  outline: none !important;',
      '  box-shadow: none !important;',
      '}',

      // ─── F. High-contrast overrides ──────────────────────────────────────
      // Nuclear reset: force ALL elements to black background + white text.
      // This catches inline styles, component-specific grays, and brand colors
      // that would otherwise be invisible on a black background.
      'body.a11y-high-contrast,',
      'body.a11y-high-contrast * {',
      '  background-color: #000 !important;',
      '  color: #fff !important;',
      '  border-color: #555 !important;',
      '  box-shadow: none !important;',
      '  text-shadow: none !important;',
      '}',

      // Images: keep visible with slightly boosted contrast
      'body.a11y-high-contrast img {',
      '  filter: contrast(1.2) brightness(1.1) !important;',
      '  border: 1px solid #555 !important;',
      '}',

      // Links: yellow is the highest-contrast hue on black
      'body.a11y-high-contrast a,',
      'body.a11y-high-contrast a:visited,',
      'body.a11y-high-contrast .nav-link,',
      'body.a11y-high-contrast .nav-link:visited {',
      '  color: #ffff00 !important;',
      '}',
      'body.a11y-high-contrast a:hover,',
      'body.a11y-high-contrast .nav-link:hover {',
      '  color: #fff !important;',
      '}',

      // Buttons and form controls: dark bg, white text, visible border
      'body.a11y-high-contrast button,',
      'body.a11y-high-contrast .btn,',
      'body.a11y-high-contrast input,',
      'body.a11y-high-contrast select,',
      'body.a11y-high-contrast textarea {',
      '  background-color: #111 !important;',
      '  color: #fff !important;',
      '  border: 1px solid #fff !important;',
      '}',
      'body.a11y-high-contrast input::placeholder {',
      '  color: #aaa !important;',
      '}',

      // Cards, rows, sections: slightly off-black so they read as containers
      'body.a11y-high-contrast .card,',
      'body.a11y-high-contrast .project-card,',
      'body.a11y-high-contrast .project-row,',
      'body.a11y-high-contrast .pub-card,',
      'body.a11y-high-contrast .pub-year-group,',
      'body.a11y-high-contrast .pub-year-toggle,',
      'body.a11y-high-contrast .pub-year-body,',
      'body.a11y-high-contrast .team-card,',
      'body.a11y-high-contrast .video-card,',
      'body.a11y-high-contrast .gallery-card,',
      'body.a11y-high-contrast .metric,',
      'body.a11y-high-contrast .project-head,',
      'body.a11y-high-contrast footer,',
      'body.a11y-high-contrast .footer,',
      'body.a11y-high-contrast .footer-main,',
      'body.a11y-high-contrast .site-navigation,',
      'body.a11y-high-contrast .navbar,',
      'body.a11y-high-contrast nav {',
      '  background-color: #111 !important;',
      '  border: 1px solid #fff !important;',
      '}',

      // Tags / badges: dark fill with white text + white border
      'body.a11y-high-contrast .tag,',
      'body.a11y-high-contrast .badge,',
      'body.a11y-high-contrast .pub-count {',
      '  background-color: #222 !important;',
      '  color: #fff !important;',
      '  border: 1px solid #aaa !important;',
      '}',

      // Colored labels that use brand red / gray — make them yellow so they
      // stay visually distinct without disappearing on black
      'body.a11y-high-contrast .section-sub-title,',
      'body.a11y-high-contrast .into-sub-title,',
      'body.a11y-high-contrast .section-title,',
      'body.a11y-high-contrast .logo-text,',
      'body.a11y-high-contrast .alumni-year,',
      'body.a11y-high-contrast .alumni-list-header span,',
      'body.a11y-high-contrast .project-row-title,',
      'body.a11y-high-contrast .project-card-title,',
      'body.a11y-high-contrast .widget-title,',
      'body.a11y-high-contrast .metric-k,',
      'body.a11y-high-contrast .pub-year-label {',
      '  color: #ffff00 !important;',
      '}',

      // Alumni section borders
      'body.a11y-high-contrast .alumni-list li,',
      'body.a11y-high-contrast .alumni-list-header {',
      '  border-color: #555 !important;',
      '}',

      // Accessibility toolbar: keep it usable in high-contrast mode
      'body.a11y-high-contrast .a11y-toolbar-panel {',
      '  background-color: #111 !important;',
      '  border: 1px solid #fff !important;',
      '}',
      'body.a11y-high-contrast .a11y-btn {',
      '  background-color: #222 !important;',
      '  color: #fff !important;',
      '  border: 1px solid #aaa !important;',
      '}',
      'body.a11y-high-contrast .a11y-btn[aria-pressed="true"] {',
      '  background-color: #ffff00 !important;',
      '  color: #000 !important;',
      '}',

      // Toolbar button base styles
      '.a11y-toolbar {',
      '  position: fixed;',
      '  bottom: 24px;',
      '  right: 24px;',
      '  z-index: 9999;',
      '  display: flex;',
      '  flex-direction: column;',
      '  align-items: flex-end;',
      '  gap: 6px;',
      '}',
      '.a11y-toolbar-panel {',
      '  display: flex;',
      '  flex-direction: row;',
      '  align-items: center;',
      '  gap: 6px;',
      '  background: #fff;',
      '  border: 1px solid rgba(0,0,0,0.12);',
      '  box-shadow: 0 4px 16px rgba(0,0,0,0.14);',
      '  border-radius: 40px;',
      '  padding: 6px 10px;',
      '}',
      '.a11y-btn {',
      '  width: 36px;',
      '  height: 36px;',
      '  border-radius: 50%;',
      '  border: 1px solid rgba(0,0,0,0.1);',
      '  background: #f5f5f5;',
      '  cursor: pointer;',
      '  font-size: 15px;',
      '  display: flex;',
      '  align-items: center;',
      '  justify-content: center;',
      '  transition: background 0.15s;',
      '  padding: 0;',
      '  line-height: 1;',
      '}',
      '.a11y-btn:hover {',
      '  background: #e0e0e0;',
      '}',
      '.a11y-btn[aria-pressed="true"] {',
      '  background: #1a73e8;',
      '  color: #fff;',
      '  border-color: #1a73e8;',
      '}',
      // Mobile toggle button
      '.a11y-mobile-toggle {',
      '  width: 44px;',
      '  height: 44px;',
      '  border-radius: 50%;',
      '  background: #1a73e8;',
      '  color: #fff;',
      '  border: none;',
      '  font-size: 22px;',
      '  cursor: pointer;',
      '  box-shadow: 0 4px 12px rgba(0,0,0,0.2);',
      '  display: none;',
      '  align-items: center;',
      '  justify-content: center;',
      '}',
      '@media (max-width: 600px) {',
      '  .a11y-mobile-toggle { display: flex; }',
      '  .a11y-toolbar-panel { display: none; }',
      '  .a11y-toolbar-panel.a11y-expanded { display: flex; flex-wrap: wrap; border-radius: 16px; padding: 10px; }',
      '}',

      // Hero audio button
      '.a11y-hero-btn {',
      '  position: absolute;',
      '  top: 16px;',
      '  right: 16px;',
      '  z-index: 10;',
      '  background: rgba(0,0,0,0.55);',
      '  color: #fff;',
      '  border: none;',
      '  border-radius: 50%;',
      '  width: 40px;',
      '  height: 40px;',
      '  font-size: 18px;',
      '  cursor: pointer;',
      '  display: flex;',
      '  align-items: center;',
      '  justify-content: center;',
      '  transition: background 0.15s;',
      '}',
      '.a11y-hero-btn:hover { background: rgba(0,0,0,0.8); }',

      // Project card speaker button
      '.a11y-card-btn {',
      '  width: 24px;',
      '  height: 24px;',
      '  border-radius: 50%;',
      '  border: 1px solid rgba(0,0,0,0.15);',
      '  background: #f5f5f5;',
      '  cursor: pointer;',
      '  font-size: 12px;',
      '  display: inline-flex;',
      '  align-items: center;',
      '  justify-content: center;',
      '  vertical-align: middle;',
      '  margin-left: 6px;',
      '  padding: 0;',
      '  transition: background 0.15s;',
      '  flex-shrink: 0;',
      '}',
      '.a11y-card-btn:hover { background: #e0e0e0; }',

      // CC badge
      '.a11y-cc-badge {',
      '  position: absolute;',
      '  bottom: 6px;',
      '  right: 6px;',
      '  background: rgba(0,0,0,0.75);',
      '  color: #fff;',
      '  font-size: 10px;',
      '  font-weight: 700;',
      '  font-family: monospace;',
      '  padding: 2px 5px;',
      '  border-radius: 4px;',
      '  pointer-events: none;',
      '  z-index: 5;',
      '  letter-spacing: 0.5px;',
      '}',

      // Hidden audio description paragraphs
      '.a11y-audio-desc {',
      '  position: absolute;',
      '  left: -9999px;',
      '  width: 1px;',
      '  height: 1px;',
      '  overflow: hidden;',
      '}',

      // ─── H. Image speaker button wrapper + button ─────────────────────────
      '.a11y-img-wrap {',
      '  position: relative;',
      '  display: block;',
      '  line-height: 0;',   // removes baseline gap below img
      '}',
      '.a11y-img-btn {',
      '  position: absolute;',
      '  bottom: 6px;',
      '  right: 6px;',
      '  z-index: 6;',
      '  background: rgba(0,0,0,0.58);',
      '  color: #fff;',
      '  border: none;',
      '  border-radius: 50%;',
      '  width: 28px;',
      '  height: 28px;',
      '  font-size: 13px;',
      '  cursor: pointer;',
      '  display: flex;',
      '  align-items: center;',
      '  justify-content: center;',
      '  padding: 0;',
      '  line-height: 1;',
      '  transition: background 0.15s, opacity 0.15s;',
      '  opacity: 0;',          // hidden until hover
      '}',
      '.a11y-img-wrap:hover .a11y-img-btn,',
      '.a11y-img-wrap:focus-within .a11y-img-btn {',
      '  opacity: 1;',
      '}',
      '.a11y-img-btn:hover { background: rgba(0,0,0,0.85); }',

      // ─── I. Video speaker button ──────────────────────────────────────────
      // Sits to the left of the CC badge; fades in on hover/focus of container
      '.a11y-vid-btn {',
      '  position: absolute;',
      '  bottom: 6px;',
      '  right: 38px;',   // 28px button + 4px gap + 6px CC badge offset
      '  z-index: 7;',
      '  background: rgba(0,0,0,0.58);',
      '  color: #fff;',
      '  border: none;',
      '  border-radius: 50%;',
      '  width: 28px;',
      '  height: 28px;',
      '  font-size: 13px;',
      '  cursor: pointer;',
      '  display: flex;',
      '  align-items: center;',
      '  justify-content: center;',
      '  padding: 0;',
      '  line-height: 1;',
      '  opacity: 0;',
      '  transition: background 0.15s, opacity 0.15s;',
      '}',
      '[data-a11y-vid]:hover .a11y-vid-btn,',
      '[data-a11y-vid]:focus-within .a11y-vid-btn {',
      '  opacity: 1;',
      '}',
      '.a11y-vid-btn:hover { background: rgba(0,0,0,0.85); }',
    ].join('\n');
    document.head.appendChild(style);
  })();

  // Mouse vs keyboard tracking
  document.addEventListener('mousedown', function () {
    document.body.classList.add('using-mouse');
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Tab') document.body.classList.remove('using-mouse');
  });

  // ─── Utility: restore persisted preferences ──────────────────────────────
  (function restorePrefs() {
    // High contrast
    if (localStorage.getItem(LS_CONTRAST) === '1') {
      document.body.classList.add('a11y-high-contrast');
    }
    // Font size
    var saved = parseInt(localStorage.getItem(LS_FONTSIZE), 10);
    if (saved && saved >= MIN_FONTSIZE && saved <= MAX_FONTSIZE) {
      applyFontSize(saved);
    }
  })();

  // ─── TTS helpers ─────────────────────────────────────────────────────────
  var ttsActive = false;

  function getReadableText() {
    var parts = [];

    // Page title heading
    var heading = document.querySelector('main h1, #banner-area h1, .banner-title, main h2, .section-title');
    if (heading) parts.push(heading.textContent.trim());

    // Main content container: prefer <main>, fallback to largest section
    var container = document.querySelector('main') ||
                    document.querySelector('#main-container') ||
                    document.querySelector('section') ||
                    document.body;

    // Collect visible paragraphs and list items
    var nodes = container.querySelectorAll('p, li');
    nodes.forEach(function (el) {
      // Skip toolbar injections, hidden elements, and nav
      if (el.closest('.a11y-toolbar')) return;
      if (el.closest('nav') || el.closest('.site-navigation') || el.closest('footer')) return;
      var style = window.getComputedStyle(el);
      if (style.display === 'none' || style.visibility === 'hidden') return;
      var text = el.textContent.trim();
      if (text.length > 5) parts.push(text);
    });

    // G. Also include hidden audio description paragraphs
    var audioParts = document.querySelectorAll('.a11y-audio-desc');
    audioParts.forEach(function (el) {
      var text = el.textContent.trim();
      if (text) parts.push(text);
    });

    return parts.join('. ');
  }

  function speakText(text, onEnd) {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    var utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.95;
    utterance.lang = 'en-US';
    utterance.onend = onEnd || null;
    utterance.onerror = onEnd || null;
    ttsActive = true;
    window.speechSynthesis.speak(utterance);
  }

  function stopSpeech() {
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    ttsActive = false;
  }

  // ─── A. Accessibility toolbar ─────────────────────────────────────────────
  (function buildToolbar() {
    var toolbar = document.createElement('div');
    toolbar.className = 'a11y-toolbar';
    toolbar.setAttribute('role', 'region');
    toolbar.setAttribute('aria-label', 'Accessibility controls');

    // Mobile toggle
    var mobileBtn = document.createElement('button');
    mobileBtn.className = 'a11y-mobile-toggle';
    mobileBtn.setAttribute('aria-label', 'Toggle accessibility toolbar');
    mobileBtn.setAttribute('aria-expanded', 'false');
    mobileBtn.textContent = '♿';

    var panel = document.createElement('div');
    panel.className = 'a11y-toolbar-panel';

    // — TTS button
    var ttsBtn = document.createElement('button');
    ttsBtn.className = 'a11y-btn';
    ttsBtn.setAttribute('aria-label', 'Read page aloud');
    ttsBtn.title = 'Read page aloud';
    ttsBtn.textContent = '🔊';

    ttsBtn.addEventListener('click', function () {
      if (ttsActive) {
        stopSpeech();
        ttsBtn.textContent = '🔊';
        ttsBtn.setAttribute('aria-label', 'Read page aloud');
      } else {
        var text = getReadableText();
        ttsBtn.textContent = '⏹';
        ttsBtn.setAttribute('aria-label', 'Stop reading');
        speakText(text, function () {
          ttsActive = false;
          ttsBtn.textContent = '🔊';
          ttsBtn.setAttribute('aria-label', 'Read page aloud');
        });
      }
    });

    // — High contrast toggle
    var contrastBtn = document.createElement('button');
    contrastBtn.className = 'a11y-btn';
    contrastBtn.setAttribute('aria-label', 'Toggle high contrast');
    contrastBtn.setAttribute('aria-pressed', localStorage.getItem(LS_CONTRAST) === '1' ? 'true' : 'false');
    contrastBtn.title = 'Toggle high contrast';
    contrastBtn.textContent = '◑';

    contrastBtn.addEventListener('click', function () {
      var on = document.body.classList.toggle('a11y-high-contrast');
      localStorage.setItem(LS_CONTRAST, on ? '1' : '0');
      contrastBtn.setAttribute('aria-pressed', on ? 'true' : 'false');
    });

    // — Text size increase
    var sizeUpBtn = document.createElement('button');
    sizeUpBtn.className = 'a11y-btn';
    sizeUpBtn.setAttribute('aria-label', 'Increase text size');
    sizeUpBtn.title = 'Increase text size';
    sizeUpBtn.textContent = 'A+';
    sizeUpBtn.style.fontSize = '11px';
    sizeUpBtn.style.fontWeight = '700';

    sizeUpBtn.addEventListener('click', function () {
      var next = Math.min(currentFontSize + FONT_STEP, MAX_FONTSIZE);
      applyFontSize(next);
      localStorage.setItem(LS_FONTSIZE, next);
    });

    // — Text size decrease
    var sizeDnBtn = document.createElement('button');
    sizeDnBtn.className = 'a11y-btn';
    sizeDnBtn.setAttribute('aria-label', 'Decrease text size');
    sizeDnBtn.title = 'Decrease text size';
    sizeDnBtn.textContent = 'A−';
    sizeDnBtn.style.fontSize = '11px';
    sizeDnBtn.style.fontWeight = '700';

    sizeDnBtn.addEventListener('click', function () {
      var next = Math.max(currentFontSize - FONT_STEP, MIN_FONTSIZE);
      applyFontSize(next);
      localStorage.setItem(LS_FONTSIZE, next);
    });

    panel.appendChild(ttsBtn);
    panel.appendChild(contrastBtn);
    panel.appendChild(sizeUpBtn);
    panel.appendChild(sizeDnBtn);

    // Mobile toggle logic
    mobileBtn.addEventListener('click', function () {
      var expanded = panel.classList.toggle('a11y-expanded');
      mobileBtn.setAttribute('aria-expanded', expanded ? 'true' : 'false');
    });

    toolbar.appendChild(mobileBtn);
    toolbar.appendChild(panel);
    document.body.appendChild(toolbar);
  })();

  // ─── B. Hero section audio button (index.html only) ──────────────────────
  (function injectHeroButton() {
    // Detect hero by presence of .banner-video containing h1
    var hero = document.querySelector('.banner-video');
    if (!hero) return;
    var h1 = hero.querySelector('h1');
    if (!h1) return;

    var btn = document.createElement('button');
    btn.className = 'a11y-hero-btn';
    btn.setAttribute('aria-label', 'Read hero section aloud');
    btn.title = 'Read hero section aloud';
    btn.textContent = '🔊';

    btn.addEventListener('click', function () {
      var heroH1 = hero.querySelector('h1');
      var heroSub = hero.querySelector('h2, h3');
      var text = (heroH1 ? heroH1.textContent.trim() : '') +
                 (heroSub ? '. ' + heroSub.textContent.trim() : '');
      speakText(text);
    });

    // Hero needs position:relative for the absolute button
    var heroStyle = window.getComputedStyle(hero);
    if (heroStyle.position === 'static') hero.style.position = 'relative';

    hero.appendChild(btn);
  })();

  // ─── C. Per-project card speaker buttons ─────────────────────────────────
  (function injectCardButtons() {
    function makeCardBtn(name, desc, container, anchor) {
      var playing = false;

      var btn = document.createElement('button');
      btn.className = 'a11y-card-btn';
      btn.setAttribute('aria-label', 'Read ' + name + ' aloud');
      btn.setAttribute('aria-pressed', 'false');
      btn.title = name;
      btn.textContent = '🔊';

      btn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        if (!playing) {
          playing = true;
          btn.textContent = '⏹';
          btn.setAttribute('aria-label', 'Stop reading');
          btn.setAttribute('aria-pressed', 'true');
          speakText(name + '. ' + desc, function () {
            playing = false;
            btn.textContent = '🔊';
            btn.setAttribute('aria-label', 'Read ' + name + ' aloud');
            btn.setAttribute('aria-pressed', 'false');
          });
        } else {
          stopSpeech();
          playing = false;
          btn.textContent = '🔊';
          btn.setAttribute('aria-label', 'Read ' + name + ' aloud');
          btn.setAttribute('aria-pressed', 'false');
        }
      });

      anchor.parentNode.insertBefore(btn, anchor.nextSibling);
    }

    // Index.html: .project-card with .project-card-title and .project-card-desc
    document.querySelectorAll('.project-card').forEach(function (card) {
      var titleEl   = card.querySelector('.project-card-title, h3');
      var descEl    = card.querySelector('.project-card-desc, p');
      var learnMore = card.querySelector('a.btn, a[href]');
      if (!titleEl || !learnMore) return;
      makeCardBtn(titleEl.textContent.trim(), descEl ? descEl.textContent.trim() : '', card, learnMore);
    });

    // Projects.html / funding.html: .project-row with .project-row-title and .project-row-text
    document.querySelectorAll('.project-row').forEach(function (row) {
      var titleEl   = row.querySelector('.project-row-title, h3');
      var descEl    = row.querySelector('.project-row-text, p');
      if (!titleEl) return;

      // Prefer a real "Learn more" button; never use the image link as anchor
      // so the speaker button always ends up in the text column.
      var learnMore = row.querySelector('a.btn');
      if (!learnMore) {
        // Fall back: insert after the last child of .project-row-body
        var body = row.querySelector('.project-row-body');
        if (!body) return;
        learnMore = body.lastElementChild;
        if (!learnMore) return;
      }
      makeCardBtn(titleEl.textContent.trim(), descEl ? descEl.textContent.trim() : '', row, learnMore);
    });
  })();

  // ─── D. Video caption badges + region wrapping ───────────────────────────
  (function injectVideoBadges() {

    function nearestHeading(el) {
      // Walk up the DOM looking for a preceding heading
      var node = el;
      while (node && node !== document.body) {
        var prev = node.previousElementSibling;
        while (prev) {
          var h = prev.querySelector('h1,h2,h3,h4') || (prev.matches('h1,h2,h3,h4') ? prev : null);
          if (h) return h.textContent.trim();
          prev = prev.previousElementSibling;
        }
        node = node.parentElement;
      }
      return 'Research video';
    }

    function wrapWithRegion(el, label) {
      // Don't double-wrap
      if (el.parentElement && el.parentElement.getAttribute('role') === 'region') return;
      var wrapper = document.createElement('div');
      wrapper.setAttribute('role', 'region');
      wrapper.setAttribute('aria-label', label + ' video');
      wrapper.style.position = 'relative';
      wrapper.style.display = el.style.display || 'block';
      el.parentNode.insertBefore(wrapper, el);
      wrapper.appendChild(el);
      return wrapper;
    }

    function addCCBadge(container) {
      // Don't add duplicate
      if (container.querySelector('.a11y-cc-badge')) return;
      var badge = document.createElement('span');
      badge.className = 'a11y-cc-badge';
      badge.textContent = 'CC';
      badge.setAttribute('aria-label', 'Captions pending');
      // Container needs relative positioning for badge placement
      var pos = window.getComputedStyle(container).position;
      if (pos === 'static') container.style.position = 'relative';
      container.appendChild(badge);
    }

    // Process <video> elements
    document.querySelectorAll('video').forEach(function (video) {
      video.setAttribute('data-caption-status', 'pending');
      var label = nearestHeading(video);

      // Use existing wrapper if it's already positioned
      var parent = video.parentElement;
      var posParent = window.getComputedStyle(parent).position;
      var container;

      if (posParent !== 'static') {
        // Parent is already a positioned container (e.g. .ratio)
        container = parent;
      } else {
        container = wrapWithRegion(video, label) || parent;
      }

      // Ensure the container has role=region
      if (container.getAttribute('role') !== 'region') {
        container.setAttribute('role', 'region');
        container.setAttribute('aria-label', label + ' video');
      }

      addCCBadge(container);
    });

    // Process <a> tags wrapping .mp4 files (not already inside a video element)
    document.querySelectorAll('a[href]').forEach(function (anchor) {
      if (!/\.mp4(\?|#|$)/i.test(anchor.href)) return;
      anchor.setAttribute('data-caption-status', 'pending');
      var label = nearestHeading(anchor);

      var parent = anchor.parentElement;
      if (parent && parent.getAttribute('role') !== 'region') {
        var pos = window.getComputedStyle(parent).position;
        if (pos !== 'static') {
          parent.setAttribute('role', 'region');
          parent.setAttribute('aria-label', label + ' video');
          addCCBadge(parent);
        } else {
          var wrapper = wrapWithRegion(anchor, label);
          if (wrapper) addCCBadge(wrapper);
        }
      } else if (parent) {
        addCCBadge(parent);
      }
    });
  })();

  // ─── I. Audio description button on every video ─────────────────────────
  // First click: reads the audio description (or aria-label) aloud via TTS.
  // Second click: stops TTS playback.
  // Does NOT affect video playback — videos continue to autoplay/loop as normal.
  (function injectVideoButtons() {
    document.querySelectorAll('video').forEach(function (video) {
      // Prefer the full .a11y-audio-desc sibling (richer text), fall back to aria-label
      var text = '';
      var sibling = video.nextElementSibling;
      while (sibling) {
        if (sibling.classList && sibling.classList.contains('a11y-audio-desc')) {
          text = sibling.textContent.trim();
          break;
        }
        sibling = sibling.nextElementSibling;
      }
      if (!text) text = (video.getAttribute('aria-label') || '').trim();
      if (!text) return; // nothing to read

      var container = video.parentElement;
      if (!container) return;

      if (container.querySelector('.a11y-vid-btn')) return; // no duplicates

      if (window.getComputedStyle(container).position === 'static') {
        container.style.position = 'relative';
      }
      container.setAttribute('data-a11y-vid', '');

      var playing = false;

      var btn = document.createElement('button');
      btn.className = 'a11y-vid-btn';
      btn.textContent = '🔊';
      btn.setAttribute('aria-label', 'Read video description aloud');
      btn.setAttribute('aria-pressed', 'false');

      btn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();

        if (!playing) {
          // First click: start TTS
          playing = true;
          btn.textContent = '⏹';
          btn.setAttribute('aria-label', 'Stop reading');
          btn.setAttribute('aria-pressed', 'true');
          speakText(text, function () {
            // Reset when TTS finishes naturally
            playing = false;
            btn.textContent = '🔊';
            btn.setAttribute('aria-label', 'Read video description aloud');
            btn.setAttribute('aria-pressed', 'false');
          });
        } else {
          // Second click: stop TTS
          stopSpeech();
          playing = false;
          btn.textContent = '🔊';
          btn.setAttribute('aria-label', 'Read video description aloud');
          btn.setAttribute('aria-pressed', 'false');
        }
      });

      container.appendChild(btn);
    });
  })();

  // ─── H. Speaker button on every image ────────────────────────────────────
  // First click: reads the alt text aloud via TTS, button switches to ⏹.
  // Second click: stops TTS, button resets to 🔊.
  // If TTS finishes naturally, button auto-resets to 🔊.
  (function injectImageButtons() {
    document.querySelectorAll('img').forEach(function (img) {
      // Skip: decorative images, nav logos, already-wrapped images
      if (img.getAttribute('role') === 'presentation') return;
      if (img.classList.contains('nav-logo')) return;
      if (img.parentElement && img.parentElement.classList.contains('a11y-img-wrap')) return;

      var alt = (img.getAttribute('alt') || '').trim();
      if (!alt) return; // nothing to read

      var playing = false;

      var btn = document.createElement('button');
      btn.className = 'a11y-img-btn';
      btn.setAttribute('aria-label', 'Read image description aloud');
      btn.setAttribute('aria-pressed', 'false');
      btn.title = alt;
      btn.textContent = '🔊';

      btn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();

        if (!playing) {
          // First click: start TTS
          playing = true;
          btn.textContent = '⏹';
          btn.setAttribute('aria-label', 'Stop reading');
          btn.setAttribute('aria-pressed', 'true');
          speakText(alt, function () {
            // Reset when TTS finishes naturally
            playing = false;
            btn.textContent = '🔊';
            btn.setAttribute('aria-label', 'Read image description aloud');
            btn.setAttribute('aria-pressed', 'false');
          });
        } else {
          // Second click: stop TTS
          stopSpeech();
          playing = false;
          btn.textContent = '🔊';
          btn.setAttribute('aria-label', 'Read image description aloud');
          btn.setAttribute('aria-pressed', 'false');
        }
      });

      // Wrap img in a positioned block so the button can sit in the corner.
      // Use display:block so the wrap fills its parent container the same way
      // a block-displayed img would (covers team photos, gallery cards, etc.).
      var wrap = document.createElement('span');
      wrap.className = 'a11y-img-wrap';

      img.parentNode.insertBefore(wrap, img);
      wrap.appendChild(img);
      wrap.appendChild(btn);
    });
  })();

  // ─── J. Awards & Honors section speaker button ────────────────────────────
  (function injectAwardsButton() {
    var section = document.getElementById('awards-honors');
    if (!section) return;

    // Collect all award text from list items (strip icon text/emoji, trim)
    var items = section.querySelectorAll('li');
    if (!items.length) return;

    var awardTexts = [];
    items.forEach(function (li) {
      // Clone so we can remove the <i> icon before reading text
      var clone = li.cloneNode(true);
      var icon = clone.querySelector('i');
      if (icon) icon.remove();
      var text = clone.textContent.trim();
      if (text) awardTexts.push(text);
    });

    var fullText = 'Awards and Honors. ' + awardTexts.join('. ');

    var playing = false;

    var btn = document.createElement('button');
    btn.className = 'a11y-card-btn';
    btn.setAttribute('aria-label', 'Read Awards and Honors aloud');
    btn.setAttribute('aria-pressed', 'false');
    btn.title = 'Read Awards and Honors aloud';
    btn.textContent = '🔊';
    btn.style.fontSize = '16px';
    btn.style.width = '32px';
    btn.style.height = '32px';
    btn.style.marginLeft = '12px';
    btn.style.verticalAlign = 'middle';

    btn.addEventListener('click', function () {
      if (!playing) {
        playing = true;
        btn.textContent = '⏹';
        btn.setAttribute('aria-label', 'Stop reading Awards and Honors');
        btn.setAttribute('aria-pressed', 'true');
        speakText(fullText, function () {
          playing = false;
          btn.textContent = '🔊';
          btn.setAttribute('aria-label', 'Read Awards and Honors aloud');
          btn.setAttribute('aria-pressed', 'false');
        });
      } else {
        stopSpeech();
        playing = false;
        btn.textContent = '🔊';
        btn.setAttribute('aria-label', 'Read Awards and Honors aloud');
        btn.setAttribute('aria-pressed', 'false');
      }
    });

    // Inject the button after the subtitle heading
    var subtitle = section.querySelector('.section-sub-title');
    if (subtitle) {
      subtitle.appendChild(btn);
    } else {
      var title = section.querySelector('.section-title, h2, h3');
      if (title) title.appendChild(btn);
    }

    // Add a hidden description for screen readers
    var desc = document.createElement('p');
    desc.className = 'a11y-audio-desc';
    desc.setAttribute('aria-live', 'polite');
    desc.textContent = fullText;
    section.insertBefore(desc, section.firstChild);
  })();

})();
