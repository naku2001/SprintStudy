function esc(t) {
  return String(t)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

/** Normalize raw markdown from backend into canonical section headings. */
export function normalizeMarkdown(text) {
  const raw = String(text || '').replace(/\r\n/g, '\n').replace(/\*\*/g, '');
  const map = {
    'one-sentence overview':    '# One-Sentence Overview',
    'key takeaways':            '## Key Takeaways',
    'topic flow':               '## Topic Flow',
    'important details':        '## Important Details',
    'risks or limitations':     '## Risks or Limitations',
    '3 quick review questions': '## 3 Quick Review Questions',
  };

  const lines = raw.split('\n').map((l) => {
    const k = l.trim().replace(/:$/, '').toLowerCase();
    return map[k] || l;
  });

  // Remove duplicate consecutive non-empty lines
  const ne = lines.reduce((a, l, i) => (l.trim() ? [...a, i] : a), []);
  if (ne.length >= 2) {
    const a = lines[ne[0]].trim().replace(/^#+\s*/, '').replace(/:$/, '').toLowerCase();
    const b = lines[ne[1]].trim().replace(/^#+\s*/, '').replace(/:$/, '').toLowerCase();
    if (a === b) lines[ne[1]] = '';
  }

  const out = lines.join('\n').replace(/\n{3,}/g, '\n\n').trim();
  const first = (out.split('\n').find((l) => l.trim()) || '')
    .trim().replace(/:$/, '').toLowerCase().replace(/^#+\s*/, '');

  if (!out.startsWith('# ') && first !== 'one-sentence overview') {
    return '# One-Sentence Overview\n' + out;
  }
  return out;
}

/** Convert simple Markdown to HTML (h1-h3, lists, paragraphs). */
export function renderMarkdownToHtml(md) {
  let h = esc(md).replace(/\*\*/g, '');
  h = h.replace(/^### (.*)$/gm, '<h3>$1</h3>');
  h = h.replace(/^## (.*)$/gm,  '<h2>$1</h2>');
  h = h.replace(/^# (.*)$/gm,   '<h1>$1</h1>');
  h = h.replace(/^\d+\. (.*)$/gm, '<li>$1</li>');
  h = h.replace(/^- (.*)$/gm,   '<li>$1</li>');
  // Wrap consecutive <li> in <ul>
  h = h.replace(/(<li>[\s\S]*?<\/li>)/g, (block) => {
    const items = block.match(/<li>.*?<\/li>/g) || [];
    return '<ul>' + items.join('') + '</ul>';
  });
  h = h.replace(/\n{2,}/g, '</p><p>');
  h = '<p>' + h + '</p>';
  // Clean up wrapping around block elements
  h = h.replace(/<p>\s*(<[hul])/g, '$1');
  h = h.replace(/(<\/[hul][123]?>)\s*<\/p>/g, '$1');
  return h;
}
