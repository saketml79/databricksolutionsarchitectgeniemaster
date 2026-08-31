export function shouldClearSelectedProposal(pendingProposalIds: string[], proposalId: string) {
  return !pendingProposalIds.includes(proposalId);
}

export function selectedProposalAfterGeneration(pendingProposalIds: string[], generatedProposalId: string) {
  return pendingProposalIds.includes(generatedProposalId) ? generatedProposalId : '';
}