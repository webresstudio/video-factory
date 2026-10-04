(function () {
  const out = { url: location.href, title: document.title };
  out.inputs = Array.from(document.querySelectorAll('textarea, input[type="text"], [contenteditable="true"], [role="textbox"]')).map(el => ({
    tag: el.tagName, cls: String(el.className).slice(0, 80), ph: el.placeholder || el.getAttribute('aria-label') || el.getAttribute('data-placeholder'),
    val: (el.value || el.innerText || '').slice(0, 120)
  }));
  out.buttons = Array.from(document.querySelectorAll('button, [role="button"], [role="tab"], [role="menuitem"], [role="option"]'))
    .filter(b => b.offsetParent !== null)
    .map(b => ((b.getAttribute('aria-label') || '') + ' | ' + (b.innerText || '').replace(/\s+/g, ' ').trim()).slice(0, 90))
    .filter(s => s.trim() !== '|');
  return JSON.stringify(out, null, 1);
})();
