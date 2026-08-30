import { describe, expect, it } from 'vitest';
import { formatElapsedTime, normalizeMarkdown } from './responseContent';

describe('normalizeMarkdown', () => {
  it('separates concatenated table rows using the detected column count', () => {
    const source = [
      '| Option | Benefits | Trade-offs |',
      '| --- | --- | --- |',
      '| Option 1 | Native governance | Higher platform dependence | Option 2 | Lower operating cost | Manual ETL |',
    ].join('\n');

    expect(normalizeMarkdown(source)).toContain('| Option 1 | Native governance | Higher platform dependence |\n| Option 2 | Lower operating cost | Manual ETL |');
  });

  it('renders incomplete table rows as ordinary text instead of invalid table markup', () => {
    const source = [
      '| Option | Benefits | Trade-offs |',
      '| --- | --- | --- |',
      '| Option 1 | Native governance |',
    ].join('\n');

    expect(normalizeMarkdown(source)).toContain('Option 1 | Native governance');
    expect(normalizeMarkdown(source)).not.toContain('| Option 1 | Native governance |');
  });

  it('rebuilds the required architecture tables when a streamed response omits all header delimiters', () => {
    const source = [
      '## Options Comparison',
      'OptionBenefitsTrade-offsCost driversRecommendation| **Option 1** | Native governance | Higher platform dependence | Usage-based | **Recommended** | | **Option 2** | Lower operations | Less flexibility | Continuous compute | Conditional |',
      '',
      '## Evidence',
      'ComponentSourceJustification| Auto Loader | Official documentation | Incremental ingestion | | Unity Catalog | Governed platform evidence | Access control |',
      '',
      '## Phased Implementation',
      'PhaseDurationActivitiesSuccess Criteria| Foundation | 2 weeks | Establish governance | Auditing enabled |',
    ].join('\n');

    const result = normalizeMarkdown(source);
    expect(result).toContain('| Option | Benefits | Trade-offs | Cost drivers | Recommendation |');
    expect(result).toContain('| **Option 1** | Native governance | Higher platform dependence | Usage-based | **Recommended** |');
    expect(result).toContain('| Component | Source | Justification |');
    expect(result).toContain('| Phase | Duration | Activities | Success criteria |');
    expect(result).toContain('| **Option 2** | Lower operations | Less flexibility | Continuous compute | Conditional |\n\n## Evidence');
  });
});

describe('formatElapsedTime', () => {
  it('formats elapsed seconds as a stable minutes-and-seconds value', () => {
    expect(formatElapsedTime(10_000, 75_000)).toBe('01:05');
  });
});