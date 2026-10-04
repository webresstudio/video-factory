(async function () {
  const btn = Array.from(document.querySelectorAll('button')).find(b => (b.getAttribute('aria-label') || '') === 'Ingrediente' || (b.innerText || '').includes('add face'));
  if (!btn) return 'no btn';
  btn.click();
  await new Promise(r => setTimeout(r, 1500));
  const dlg = document.querySelectorAll('[role="dialog"], [role="menu"], [role="listbox"], .cdk-overlay-pane, [data-radix-popper-content-wrapper]');
  return JSON.stringify(Array.from(dlg).map(d => ({ role: d.getAttribute('role'), text: d.innerText.slice(0, 800), imgs: Array.from(d.querySelectorAll('img')).map(i => i.alt + ' ' + i.src.slice(0, 80)) })), null, 1);
})();
