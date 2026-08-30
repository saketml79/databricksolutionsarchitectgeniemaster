export function normalizeMarkdown(markdown: string) {
  const standardized = standardizeArchitectureTables(markdown);
  const lines = standardized.replace(/\|[ \t]*\|/g, '|\n|').split('\n');
  const normalized: string[] = [];
  let columnCount = 0;

  for (const line of lines) {
    const trimmedLine = line.trim();
    const isTableLine = trimmedLine.startsWith('|') && trimmedLine.endsWith('|');
    const cells = isTableLine ? trimmedLine.split('|').slice(1, -1).map((cell) => cell.trim()) : [];
    const isSeparator = isTableLine && cells.length > 0 && cells.every((cell) => /^:?-{3,}:?$/.test(cell));

    if (isSeparator) {
      columnCount = cells.length;
      normalized.push(line);
      continue;
    }

    if (isTableLine && columnCount > 0 && cells.length !== columnCount) {
      if (cells.length > columnCount && cells.length % columnCount === 0) {
        for (let index = 0; index < cells.length; index += columnCount) {
          normalized.push(`| ${cells.slice(index, index + columnCount).join(' | ')} |`);
        }
      } else {
        normalized.push(cells.join(' | '));
        columnCount = 0;
      }
      continue;
    }

    if (!isTableLine && trimmedLine) columnCount = 0;
    normalized.push(line);
  }

  return normalized.join('\n');
}

export function formatElapsedTime(startedAt: number, now: number) {
  const elapsedSeconds = Math.max(0, Math.floor((now - startedAt) / 1000));
  const minutes = Math.floor(elapsedSeconds / 60).toString().padStart(2, '0');
  const seconds = (elapsedSeconds % 60).toString().padStart(2, '0');
  return `${minutes}:${seconds}`;
}

const architectureTables = new Map([
  ['Options Comparison', ['Option', 'Benefits', 'Trade-offs', 'Cost drivers', 'Recommendation']],
  ['Evidence', ['Component', 'Source', 'Justification']],
  ['Phased Implementation', ['Phase', 'Duration', 'Activities', 'Success criteria']],
]);

function standardizeArchitectureTables(markdown: string) {
  const sections = markdown.split(/(?=^##\s+)/m);
  return sections.map((section) => {
    const heading = section.match(/^##\s+([^\n]+)/)?.[1]?.trim();
    const headers = heading ? architectureTables.get(heading) : undefined;
    if (!headers) return section;

    const body = section.replace(/^##\s+[^\n]+\n?/, '').trim();
    if (!body || /^\|\s*[^\n]+\|\s*\n\|\s*:?-{3,}/.test(body)) return section;

    const cells = body.split('|').map((cell) => cell.trim()).filter(Boolean);
    if (cells.length <= 1) return section;
    const dataCells = cells.slice(1);
    if (dataCells.length === 0 || dataCells.length % headers.length !== 0) {
      return `## ${heading}\n\n${dataCells.map((cell) => `- ${cell}`).join('\n')}`;
    }

    const rows = [];
    for (let index = 0; index < dataCells.length; index += headers.length) {
      rows.push(`| ${dataCells.slice(index, index + headers.length).join(' | ')} |`);
    }
    return `## ${heading}\n\n| ${headers.join(' | ')} |\n| ${headers.map(() => '---').join(' | ')} |\n${rows.join('\n')}`;
  }).join('\n\n');
}