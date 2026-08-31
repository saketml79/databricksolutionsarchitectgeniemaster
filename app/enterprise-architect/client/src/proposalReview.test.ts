import { describe, expect, it } from 'vitest';
import { selectedProposalAfterGeneration, shouldClearSelectedProposal } from './proposalReview';

describe('proposal review state', () => {
  it('selects a newly generated proposal once it appears in the pending list', () => {
    expect(selectedProposalAfterGeneration(['proposal_new_v2'], 'proposal_new_v2')).toBe('proposal_new_v2');
  });

  it('keeps a proposal selected after a nonterminal option rejection', () => {
    expect(shouldClearSelectedProposal(['proposal_pending_v2'], 'proposal_pending_v2')).toBe(false);
  });

  it('clears selection when approval or final rejection removes a parent from pending', () => {
    expect(shouldClearSelectedProposal([], 'proposal_completed_v2')).toBe(true);
  });
});