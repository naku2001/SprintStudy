function esc(t) {
  return String(t)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function escRe(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/** Normalize raw markdown from backend into canonical section headings. */
export function normalizeMarkdown(text) {
  let raw = String(text || '').replace(/\r\n/g, '\n').replace(/\*\*/g, '');
  const map = {
    'one-sentence overview':    '# One-Sentence Overview',
    'key takeaways':            '## Key Takeaways',
    'topic flow':               '## Topic Flow',
    'important details':        '## Important Details',
    'risks or limitations':     '## Risks or Limitations',
    '3 quick review questions': '## Quick Review Questions',
    'quick review questions':   '## Quick Review Questions',
  };
  const headingKeys = Object.keys(map).sort((a, b) => b.length - a.length);

  // Handle compact model outputs where heading and body are glued together.
  for (const key of headingKeys) {
    const k = escRe(key);
    raw = raw.replace(new RegExp(`(${k})(?=[A-Za-z0-9])`, 'gi'), '$1\n');
    raw = raw.replace(
      new RegExp(`(#{1,6}\\s*${k})\\s*[-_]+\\s*`, 'gi'),
      '$1\n- '
    );
  }

  const lines = [];
  for (const l of raw.split('\n')) {
    const trimmed = l.trim();
    const k = trimmed.replace(/:$/, '').toLowerCase();
    const normalizedKey = k
      .replace(/^#{1,6}\s*/, '')
      .replace(/^\d+\s+/, '')
      .trim();
    const mapped = map[k] || map[normalizedKey];
    if (mapped) {
      lines.push(mapped);
      continue;
    }

    // Split lines like "One-Sentence OverviewSome text..."
    let splitDone = false;
    for (const key of headingKeys) {
      if (!normalizedKey.startsWith(key)) continue;
      const heading = map[key];
      const lineNoHashes = trimmed.replace(/^#{1,6}\s*/, '').replace(/^\d+\s+/, '').trim();
      const rest = lineNoHashes.replace(new RegExp(`^${escRe(key)}\\s*[:：-]?\\s*`, 'i'), '').trim();
      lines.push(heading);
      if (rest) lines.push(rest);
      splitDone = true;
      break;
    }
    if (splitDone) continue;

    // Normalize heading forms like "## 3 Quick Review Questions"
    if (/^#{1,6}\s*3 quick review questions:?$/i.test(trimmed)) {
      lines.push('## Quick Review Questions');
      continue;
    }
    lines.push(l);
  }

  // Drop dangling heading markers produced by streamed partial tokens.
  const cleanedLines = lines.filter((l) => !/^#{1,6}\s*$/.test(l.trim()));

  // Remove duplicate consecutive non-empty lines
  const ne = cleanedLines.reduce((a, l, i) => (l.trim() ? [...a, i] : a), []);
  if (ne.length >= 2) {
    const a = cleanedLines[ne[0]].trim().replace(/^#+\s*/, '').replace(/:$/, '').toLowerCase();
    const b = cleanedLines[ne[1]].trim().replace(/^#+\s*/, '').replace(/:$/, '').toLowerCase();
    if (a === b) cleanedLines[ne[1]] = '';
  }

  // Remove "Risks or Limitations" section when it carries no real content.
  const sections = [];
  let current = { heading: '', lines: [] };
  for (const line of cleanedLines) {
    if (/^##\s+/.test(line.trim())) {
      sections.push(current);
      current = { heading: line.trim(), lines: [] };
    } else {
      current.lines.push(line);
    }
  }
  sections.push(current);

  const shouldDropRisks = (heading, lines) => {
    if (heading.toLowerCase() !== '## risks or limitations') return false;
    const content = lines.map((l) => l.trim()).filter(Boolean).join(' ').toLowerCase();
    if (!content) return true;
    return (
      content.includes('no explicit risks or limitations') ||
      content.includes('no specific risks or limitations') ||
      content.includes('not explicitly mentioned') ||
      content.includes('not mentioned') ||
      content === 'none' ||
      content === 'n/a'
    );
  };

  const rebuilt = [];
  for (const sec of sections) {
    if (shouldDropRisks(sec.heading, sec.lines)) continue;
    if (sec.heading) rebuilt.push(sec.heading);
    rebuilt.push(...sec.lines);
  }

  const out = rebuilt.join('\n').replace(/\n{3,}/g, '\n\n').trim();
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
