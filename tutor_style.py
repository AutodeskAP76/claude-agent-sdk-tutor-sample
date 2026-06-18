"""CSS and JS for the tutor UI, kept separate from the app logic.

Palette: gold #ecad0a, blue #209dd7, purple #753991, with grays.
Sharp, clean, professional. No gradients, no left-border accent lines.
"""

CSS = """
:root {
  --gold: #ecad0a;
  --blue: #209dd7;
  --purple: #753991;
  --ink: #1b1f24;
  --muted: #828a94;
  --line: #e7e9ee;
  --panel: #ffffff;
  --bg: #f4f5f7;
}

/* The UI is designed light. Force a light appearance even if the browser/OS is in dark mode
   by overriding Gradio's dark-theme variables (otherwise the chat is light-text-on-light). */
.dark {
  color-scheme: light !important;
  --body-background-fill: #f4f5f7 !important;
  --background-fill-primary: #ffffff !important;
  --background-fill-secondary: #f4f5f7 !important;
  --block-background-fill: #ffffff !important;
  --panel-background-fill: #ffffff !important;
  --block-label-background-fill: #ffffff !important;
  --input-background-fill: #ffffff !important;
  --input-background-fill-focus: #ffffff !important;
  --code-background-fill: #f4f5f7 !important;
  --body-text-color: #1b1f24 !important;
  --body-text-color-subdued: #828a94 !important;
  --block-title-text-color: #1b1f24 !important;
  --block-label-text-color: #828a94 !important;
  --block-info-text-color: #828a94 !important;
  --table-text-color: #1b1f24 !important;
  --accordion-text-color: #1b1f24 !important;
  --border-color-primary: #e7e9ee !important;
  --block-border-color: #e7e9ee !important;
  --panel-border-color: #e7e9ee !important;
  --input-border-color: #e7e9ee !important;
}

html, body, gradio-app { background: var(--bg) !important; color-scheme: light; }
.gradio-container { background: var(--bg) !important; max-width: 1180px !important; margin-left: auto !important; margin-right: auto !important; }
.gradio-container, .gradio-container * {
  font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
}
footer { display: none !important; }

#app_title { font-weight: 750; font-size: 1.4rem; letter-spacing: -0.02em; margin: 4px 2px 12px; color: var(--ink); }
#app_title b { color: var(--blue); font-weight: 750; }

/* cards */
.card { background: var(--panel) !important; border: 1px solid var(--line) !important; border-radius: 12px !important; padding: 14px 16px !important; box-shadow: 0 1px 2px rgba(20,24,33,.05); }
.card-label { font-size: .70rem; font-weight: 700; text-transform: uppercase; letter-spacing: .09em; color: var(--muted); margin-bottom: 8px; }
.empty { color: var(--muted); font-size: .85rem; }

/* Gradio applies elem_classes to a nested wrapper too; flatten so each card is single & clean */
.card .card { border: 0 !important; box-shadow: none !important; background: transparent !important; padding: 0 !important; border-radius: 0 !important; }
.card .styler, .card .block, .card .form { background: transparent !important; border: 0 !important; box-shadow: none !important; }
.card .block.padded { padding: 0 !important; }
.card .html-container { padding: 0 !important; }
.card .block + .block { margin-top: 2px; }
/* hide Gradio's per-component loading overlay (the blue "generating" border) on the static panels */
.card .wrap { display: none !important; }

/* xp */
.xp-head { display:flex; align-items:baseline; justify-content:space-between; margin-bottom: 9px; }
.xp-level { font-weight: 800; font-size: 1.05rem; color: var(--ink); }
.xp-level span { color: var(--purple); }
.xp-total { font-size: .8rem; color: var(--muted); font-variant-numeric: tabular-nums; }
.xp-track { height: 12px; background: #edeff3; border-radius: 999px; overflow: hidden; }
.xp-fill { height: 100%; background: var(--gold); border-radius: 999px; transition: width .6s cubic-bezier(.22,1,.36,1); }
.xp-sub { font-size: .72rem; color: var(--muted); margin-top: 7px; }
#xp_card.bump .xp-fill { animation: pop .55s ease; }
@keyframes pop { 0%{filter:brightness(1)} 45%{filter:brightness(1.18)} 100%{filter:brightness(1)} }

/* vocab */
.vocab-row { display:flex; align-items:center; justify-content:space-between; padding: 7px 0; border-bottom: 1px solid var(--line); }
.vocab-row:last-child { border-bottom: 0; }
.vocab-es { font-weight: 650; color: var(--ink); }
.vocab-en { color: var(--muted); font-size: .85rem; margin-left: 8px; }
.vocab-conf { display:flex; gap:3px; flex-shrink:0; }
.dot { width:7px; height:7px; border-radius:50%; background:#dfe2e8; }
.dot.on { background: var(--blue); }

/* grammar */
.gram-row { display:flex; align-items:center; justify-content:space-between; gap:10px; padding: 6px 0; }
.gram-topic { color: var(--ink); font-size: .88rem; }
.pill { font-size:.66rem; font-weight:700; padding:2px 9px; border-radius:999px; text-transform:uppercase; letter-spacing:.04em; white-space:nowrap; }
.pill.introduced { color: var(--blue); background: rgba(32,157,215,.12); }
.pill.practising { color: #a8790a; background: rgba(236,173,10,.16); }
.pill.comfortable { color: var(--purple); background: rgba(117,57,145,.12); }

/* journey */
#journey_card .journey-scroll { max-height: 240px; overflow-y: auto; padding-right: 8px; }
#journey_card .journey-scroll h1, #journey_card .journey-scroll h2, #journey_card .journey-scroll h3 { font-size: .9rem; margin: 12px 0 4px; color: var(--ink); }
#journey_card .journey-scroll h1 { color: var(--blue); margin-top: 2px; }
#journey_card .journey-scroll p, #journey_card .journey-scroll li { font-size: .82rem; color: #4b5159; line-height: 1.5; }
#journey_card .journey-scroll blockquote { border: 0 !important; padding: 0 !important; margin: 6px 0 !important; color: var(--muted); font-style: normal; }
#journey_card .journey-scroll hr { display:none; }

/* chat */
#chat { border: 1px solid var(--line) !important; border-radius: 12px !important; background: var(--panel) !important; }
#chat .message.user, #chat .user { background: rgba(32,157,215,.10) !important; border: 0 !important; }
#chat .message.bot, #chat .bot { background: #f3f4f6 !important; border: 0 !important; }
#msgbox textarea { border-radius: 10px !important; border: 1px solid var(--line) !important; background: var(--panel) !important; }
#msgbox textarea:focus { border-color: var(--blue) !important; box-shadow: 0 0 0 3px rgba(32,157,215,.14) !important; }

/* thinking dots */
.thinking { display:inline-flex; gap:5px; align-items:center; padding: 2px 0; }
.thinking i { width:7px; height:7px; border-radius:50%; background: var(--blue); display:inline-block; animation: blink 1.2s infinite ease-in-out; }
.thinking i:nth-child(2) { animation-delay:.18s; }
.thinking i:nth-child(3) { animation-delay:.36s; }
@keyframes blink { 0%,80%,100%{opacity:.25; transform:translateY(0)} 40%{opacity:1; transform:translateY(-3px)} }
"""

# Injected into <head> so it runs reliably: pin light mode (the UI is designed light),
# then focus the input and pulse the XP card whenever it changes.
HEAD = """
<script>
(function () {
  var u = new URL(window.location.href);
  if (u.searchParams.get('__theme') !== 'light') {
    u.searchParams.set('__theme', 'light');
    window.location.replace(u.href);
    return;
  }
  var tries = 0;
  var iv = setInterval(function () {
    var ta = document.querySelector('#msgbox textarea');
    if (ta) ta.focus();
    var card = document.querySelector('#xp_card');
    if (card) {
      clearInterval(iv);
      var last = card.innerText;
      new MutationObserver(function () {
        var now = card.innerText;
        if (now !== last) { last = now; card.classList.remove('bump'); void card.offsetWidth; card.classList.add('bump'); }
      }).observe(card, { childList: true, subtree: true, characterData: true });
    }
    if (++tries > 60) clearInterval(iv);
  }, 250);
})();
</script>
"""
