(function () {
  const sc = Array.from(document.querySelectorAll('*')).filter(e => e.scrollHeight > e.clientHeight + 200 && getComputedStyle(e).overflowY !== 'visible' && !e.closest('.cdk-overlay-container'))
    .sort((a, b) => b.scrollHeight - a.scrollHeight)[0];
  if (!sc) return 'no scroller';
  if (window.__y === undefined) window.__y = 0;
  window.__y += 900; sc.scrollTop = window.__y;
  const hits = Array.from(document.querySelectorAll('*')).filter(e => e.children.length === 0 && /WhatsApp|flame|llama|habla|says|dice/i.test(e.textContent)).map(e => e.textContent.trim().slice(0, 600));
  return JSON.stringify({ y: sc.scrollTop, h: sc.scrollHeight, hits: [...new Set(hits)] });
})();
