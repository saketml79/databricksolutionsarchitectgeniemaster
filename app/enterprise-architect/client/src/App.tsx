import { Card, CardContent, CardHeader, CardTitle } from '@databricks/appkit-ui/react';
import { ArrowUpRight, BookOpenCheck, Database, FileImage, ShieldCheck } from 'lucide-react';
import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { formatElapsedTime, normalizeMarkdown } from './responseContent';

const workspaceUrl = 'https://adb-1866518241053589.9.azuredatabricks.net';
const genieUrl = `${workspaceUrl}/genie/rooms/01f1a400577d1c71b8b1fd2d83cc2df5`;
const volumePath = '/Volumes/databricks_architect_agent/agent_demo/architecture_artifacts';

async function readApiJson<T>(response: Response, fallbackMessage: string): Promise<T> {
  if (!response.headers.get('content-type')?.includes('application/json')) {
    throw new Error('The localhost preview does not run the Databricks App API. Open the deployed App to generate or review architecture packages.');
  }
  const payload = await response.json() as T & { error?: string };
  if (!response.ok) throw new Error(payload.error ?? fallbackMessage);
  return payload;
}

export default function App() {
  const [packages, setPackages] = useState<ReviewPackage[]>([]);
  const [loadError, setLoadError] = useState('');
  const [decisionError, setDecisionError] = useState('');
  const [decisionInFlight, setDecisionInFlight] = useState('');
  const [showArchived, setShowArchived] = useState(false);
  const [selectedProposalId, setSelectedProposalId] = useState('');
  const [requestText, setRequestText] = useState('We acquired a company. Design a new governed solution architecture for onboarding 200 TB of acquired-company data, near-real-time Customer 360 analytics, semantic search, and low operating cost. Use our current environment and return the recommended options, a reviewable architecture diagram, and the evidence used.');
  const [agentResponse, setAgentResponse] = useState('');
  const [chatError, setChatError] = useState('');
  const [chatting, setChatting] = useState(false);
  const [progressStage, setProgressStage] = useState<'grounding' | 'approval' | 'rendering' | 'complete'>('complete');
  const [threadId, setThreadId] = useState('');
  const [pendingApproval, setPendingApproval] = useState<{ approvalId: string; streamId: string }>();
  const [generatedArtifact, setGeneratedArtifact] = useState<GeneratedArtifact>();
  const [startedAt, setStartedAt] = useState<number>();
  const [now, setNow] = useState(Date.now());
  const [evidenceRefreshToken, setEvidenceRefreshToken] = useState(0);
  const [pdfInFlight, setPdfInFlight] = useState(false);

  useEffect(() => {
    setSelectedProposalId('');
    fetch(`/api/review-packages?view=${showArchived ? 'archived' : 'pending'}`).then(async (response) => {
      const payload = await readApiJson<{ rows?: ReviewPackage[] }>(response, 'Unable to load review packages.');
      setPackages(payload.rows ?? []);
    }).catch((error: Error) => setLoadError(error.message));
  }, [showArchived]);

  useEffect(() => {
    if (!startedAt || progressStage === 'complete') return;
    const timer = window.setInterval(() => setNow(Date.now()), 1_000);
    return () => window.clearInterval(timer);
  }, [progressStage, startedAt]);

  async function recordDecision(reviewPackage: ReviewPackage, decision: 'APPROVED' | 'REJECTED') {
    const reason = window.prompt(`Reason for ${decision.toLowerCase()}:`);
    if (!reason?.trim() || !window.confirm(`Record ${decision} for "${reviewPackage.title}"? This does not execute infrastructure changes.`)) return;
    setDecisionError('');
    setDecisionInFlight(reviewPackage.proposal_id);
    try {
      const response = await fetch(`/api/proposals/${encodeURIComponent(reviewPackage.proposal_id)}/decision`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ decision, reason }) });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error ?? 'Unable to record decision.');
      setPackages((current) => current.map((item) => item.proposal_id === reviewPackage.proposal_id ? { ...item, status: decision } : item));
    } catch (error) {
      setDecisionError(error instanceof Error ? error.message : 'Unable to record decision.');
    } finally {
      setDecisionInFlight('');
    }
  }

  async function recordOptionDecision(reviewPackage: ReviewPackage, optionId: string, decision: 'APPROVED' | 'REJECTED') {
    const reason = window.prompt(`Reason for ${decision.toLowerCase()} this architecture option:`);
    if (!reason?.trim() || !window.confirm(`${decision === 'APPROVED' ? 'Select' : 'Reject'} ${optionId.replace('_', ' ')} for "${reviewPackage.title}"?`)) return;
    setDecisionError('');
    setDecisionInFlight(`${reviewPackage.proposal_id}_${optionId}`);
    try {
      const response = await fetch(`/api/proposals/${encodeURIComponent(reviewPackage.proposal_id)}/options/${optionId}/decision`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ decision, reason }) });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error ?? 'Unable to record option decision.');
      if (decision === 'APPROVED') setPackages((current) => current.filter((item) => item.proposal_id !== reviewPackage.proposal_id));
    } catch (error) {
      setDecisionError(error instanceof Error ? error.message : 'Unable to record option decision.');
    } finally { setDecisionInFlight(''); }
  }

  async function submitArchitectureRequest() {
    if (!requestText.trim()) return;
    setChatting(true); setProgressStage('grounding'); setStartedAt(Date.now()); setNow(Date.now()); setChatError(''); setAgentResponse(''); setPendingApproval(undefined); setGeneratedArtifact(undefined);
    try {
      const response = await fetch('/api/agents/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: requestText, threadId: threadId || undefined, agent: 'solutionsArchitect' }) });
      if (!response.headers.get('content-type')?.includes('text/event-stream')) {
        throw new Error('The localhost preview does not run the Databricks App API. Open the deployed App to generate or review architecture packages.');
      }
      if (!response.ok || !response.body) {
        throw new Error('The Solutions Architect could not start the request.');
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let pending = '';
      let completeResponse = '';
      let lastResponseItemId = '';
      let generatedProposalId = '';
      let toolResultMessage = '';
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        pending += decoder.decode(value, { stream: true });
        const events = pending.split('\n\n');
        pending = events.pop() ?? '';
        for (const event of events) {
          const data = event.split('\n').find((line) => line.startsWith('data: '))?.slice(6);
          if (!data) continue;
          const payload = JSON.parse(data);
          if (payload.type === 'response.output_text.delta') {
            const messageBoundary = lastResponseItemId && lastResponseItemId !== payload.item_id ? '\n\n' : '';
            lastResponseItemId = payload.item_id ?? lastResponseItemId;
            completeResponse += messageBoundary + payload.delta;
            setAgentResponse((current) => current + messageBoundary + payload.delta);
          }
          if (payload.type === 'response.output_item.done' && payload.item?.type === 'function_call_output') {
            try {
              const artifact = JSON.parse(payload.item.output);
              toolResultMessage = typeof artifact.message === 'string' ? artifact.message : '';
              if (artifact.option_artifacts && artifact.proposal_id) {
                generatedProposalId = artifact.proposal_id;
                setGeneratedArtifact(artifact);
                setShowArchived(false);
              }
              else if (artifact.status === 'FAILED') setChatError(artifact.message ?? 'The governed artifact generator did not complete.');
            } catch {
              setChatError(`The governed artifact generator did not complete: ${String(payload.item.output).slice(0, 500)}`);
            }
          }
          if (payload.type === 'appkit.metadata' && typeof payload.data?.threadId === 'string') setThreadId(payload.data.threadId);
          if (payload.type === 'appkit.approval_pending') { setPendingApproval({ approvalId: payload.approval_id, streamId: payload.stream_id }); setProgressStage('approval'); }
          if (payload.type === 'error') throw new Error(payload.error ?? 'The Solutions Architect encountered an error.');
        }
      }
      if (!generatedProposalId) throw new Error(toolResultMessage || 'The agent returned analysis without creating a governed review package. No approval or rejection can be recorded until the request is generated again successfully.');
      if (generatedProposalId && completeResponse.trim()) {
        const savedConversation = await fetch(`/api/proposals/${encodeURIComponent(generatedProposalId)}/conversation`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ content: completeResponse }) });
        if (!savedConversation.ok) {
          const payload = await savedConversation.json().catch(() => ({}));
          throw new Error(payload.error ?? 'The proposal was created, but its Genie response could not be retained.');
        }
        setEvidenceRefreshToken((current) => current + 1);
      }
      if (generatedProposalId) {
        const refreshedPackages = await fetch('/api/review-packages?view=pending');
        const payload = await refreshedPackages.json();
        if (!refreshedPackages.ok) throw new Error(payload.error ?? 'The proposal was created, but the pending review queue could not be refreshed.');
        setPackages(payload.rows ?? []);
      }
      setProgressStage('complete');
    } catch (error) {
      setChatError(error instanceof Error ? error.message : 'The Solutions Architect could not complete the request.');
    } finally { setChatting(false); }
  }

  async function decideToolApproval(decision: 'approve' | 'deny') {
    if (!pendingApproval) return;
    setChatError('');
    try {
      const response = await fetch('/api/agents/approve', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ streamId: pendingApproval.streamId, approvalId: pendingApproval.approvalId, decision }) });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error ?? 'Unable to record the tool decision.');
      setPendingApproval(undefined);
      setProgressStage(decision === 'approve' ? 'rendering' : 'complete');
    } catch (error) {
      setChatError(error instanceof Error ? error.message : 'Unable to record the tool decision.');
    }
  }

  async function downloadReviewPdf() {
    if (!generatedArtifact) return;
    setPdfInFlight(true);
    setChatError('');
    try {
      const response = await fetch(`/api/proposals/${encodeURIComponent(generatedArtifact.proposal_id)}/pdf`, { method: 'POST' });
      const payload = await response.json() as { downloadUrl?: string; error?: string };
      if (!response.ok || !payload.downloadUrl) throw new Error(payload.error ?? 'Unable to generate the review PDF.');
      window.open(payload.downloadUrl, '_blank', 'noreferrer');
    } catch (error) {
      setChatError(error instanceof Error ? error.message : 'Unable to generate the review PDF.');
    } finally {
      setPdfInFlight(false);
    }
  }

  const visibleResponse = normalizeMarkdown(agentResponse.trim());
  const showResponse = visibleResponse || pendingApproval || generatedArtifact || chatting;
  const inProgress = progressStage !== 'complete';
  const elapsedTime = startedAt ? formatElapsedTime(startedAt, now) : '00:00';
  const selectedReviewPackage = packages.find((reviewPackage) => reviewPackage.proposal_id === selectedProposalId);

  return <main className="architect-shell">
    <header className="masthead">
      <div><p className="eyebrow">GOVERNED DESIGN WORKSPACE</p><h1>Databricks Solutions Architect Genie</h1></div>
      <a className="genie-link" href={genieUrl} target="_blank" rel="noreferrer">Open Genie <ArrowUpRight size={16} /></a>
    </header>
    <section className="status-strip" aria-label="System status">
      <span><i className="ready" />Digital twin refreshes every 6 hours</span>
      <span><i className="ready" />Knowledge claims require review</span>
      <span><i className="ready" />Proposals stay pending approval</span>
    </section>
    <section className="workbench">
      <div className="lead-copy"><p className="eyebrow">ARCHITECTURE REVIEW</p><h2>Build from the platform you have.</h2><p>Use Genie for evidence-grounded questions. Use the controlled workflows below to persist a proposal and its review artifacts.</p></div>
      <Card><CardHeader><CardTitle>Current governed scope</CardTitle></CardHeader><CardContent><dl><dt>Catalog</dt><dd>databricks_architect_agent</dd><dt>Schema</dt><dd>agent_demo</dd><dt>Artifact volume</dt><dd className="path">{volumePath}</dd></dl></CardContent></Card>
    </section>
    <section className="architect-chat"><div className="chat-intro"><div><p className="eyebrow">SOLUTIONS ARCHITECT CHAT</p><h2>Describe the outcome you need.</h2></div><p>Genie analyzes the governed environment first. The App then formats its response, renders the governed diagrams, and creates a review package.</p></div><textarea value={requestText} onChange={(event) => setRequestText(event.target.value)} aria-label="Architecture request" /><button onClick={() => void submitArchitectureRequest()} disabled={chatting || !!pendingApproval}>{chatting ? 'Working...' : 'Generate architecture'}</button>{chatError && <p className="load-error">{chatError}</p>}{showResponse && <section className="response-panel" aria-live="polite"><header><span>Genie SA Agent's Architecture Response</span><span className="response-state">{inProgress ? <>In progress <time dateTime={`PT${elapsedTime}`}>{elapsedTime}</time></> : <><span>Complete</span>{generatedArtifact && <button className="pdf-download" onClick={() => void downloadReviewPdf()} disabled={pdfInFlight}>{pdfInFlight ? 'Preparing PDF...' : 'Download PDF'}</button>}</>}</span></header>{inProgress && <div className="agent-progress" aria-label="Genie SA Agent progress"><span className={progressStage === 'grounding' ? 'active' : 'complete'}>1. Genie is analyzing governed context</span><span className={progressStage === 'approval' ? 'active' : progressStage === 'rendering' ? 'complete' : ''}>2. Preparing review package</span><span className={progressStage === 'rendering' ? 'active' : ''}>3. Rendering governed diagrams</span></div>}<div className="response-scroll">{visibleResponse && <ReactMarkdown remarkPlugins={[remarkGfm]}>{visibleResponse}</ReactMarkdown>}{generatedArtifact && <ResponseDiagrams proposalId={generatedArtifact.proposal_id} />}</div>{pendingApproval && <footer className="approval-decision"><p>Approve creation of the pending proposal and review artifacts?</p><div className="approval-buttons"><button onClick={() => decideToolApproval('approve')}>Approve artifacts</button><button className="reject" onClick={() => decideToolApproval('deny')}>Decline</button></div></footer>}</section>}</section>
    <section className="capability-grid">
      <Capability icon={<Database />} title="Platform twin" detail="Unity Catalog inventory, registered lineage, policy, workload, cost, and manifest-only code evidence are recorded with observation status." />
      <Capability icon={<BookOpenCheck />} title="Reviewed knowledge" detail="Scheduled staging only creates CANDIDATE facts. A separate explicit review workflow promotes approved claims to REVIEWED." />
      <Capability icon={<ShieldCheck />} title="Proposal control" detail="The proposal writer records requirements, evidence, options, migration, rollback, and draft IaC only as PENDING_APPROVAL." />
      <Capability icon={<FileImage />} title="Diagram artifacts" detail="The renderer validates architecture JSON and writes Mermaid, SVG, and PNG review artifacts into the governed volume." />
    </section>
    <section className="review-packages"><div className="review-heading"><div><p className="eyebrow">REVIEW PACKAGES</p><h2>{showArchived ? 'Archived proposals.' : 'Proposals waiting for a decision.'}</h2></div><span>{packages.length} available</span></div><button className="archive-toggle" onClick={() => setShowArchived((current) => !current)}>{showArchived ? 'Back to pending proposals' : 'View archived proposals'}</button>{loadError || decisionError ? <p className="load-error">{loadError || decisionError}</p> : <><table className="proposal-table"><thead><tr><th>Proposal</th><th>Generated</th><th>Status</th><th aria-label="Actions" /></tr></thead><tbody>{packages.map((reviewPackage) => <tr key={reviewPackage.proposal_id}><td><strong>{reviewPackage.title}</strong><span>{reviewPackage.proposal_id}</span></td><td>{reviewPackage.created_at ? new Date(reviewPackage.created_at).toLocaleString() : 'Unknown'}</td><td><span className="status-pill">{reviewPackage.status}</span></td><td><button className="load-proposal" onClick={() => setSelectedProposalId((current) => current === reviewPackage.proposal_id ? '' : reviewPackage.proposal_id)}>{selectedProposalId === reviewPackage.proposal_id ? 'Hide' : 'Load'}</button></td></tr>)}</tbody></table>{selectedReviewPackage && <article className="package-row"><div><strong>{selectedReviewPackage.title}</strong><p>{selectedReviewPackage.proposal_id}</p></div><div><span className="status-pill">{selectedReviewPackage.status}</span><p>{selectedReviewPackage.package_status ?? 'ARTIFACTS_PENDING'}</p></div><div className="artifact-links">{selectedReviewPackage.pdf_path && <a href={`/api/artifacts/${encodeURIComponent(selectedReviewPackage.proposal_id)}/pdf`} target="_blank" rel="noreferrer">Open PDF</a>}{selectedReviewPackage.status === 'PENDING_APPROVAL' && !selectedReviewPackage.svg_path?.includes('_option_1.svg') && <div className="decision-controls"><button disabled={decisionInFlight === selectedReviewPackage.proposal_id} onClick={() => void recordDecision(selectedReviewPackage, 'APPROVED')}>Approve</button><button className="reject" disabled={decisionInFlight === selectedReviewPackage.proposal_id} onClick={() => void recordDecision(selectedReviewPackage, 'REJECTED')}>Reject</button></div>}</div>{selectedReviewPackage.svg_path && (selectedReviewPackage.svg_path.includes('_option_1.svg') ? <OptionDiagrams proposalId={selectedReviewPackage.proposal_id} selectedOptionId={selectedReviewPackage.selected_option_id} evidenceRefreshToken={evidenceRefreshToken} onDecision={selectedReviewPackage.status === 'PENDING_APPROVAL' ? (optionId, decision) => recordOptionDecision(selectedReviewPackage, optionId, decision) : undefined} decisionInFlight={decisionInFlight} /> : <img className="package-preview" src={`/api/artifacts/${encodeURIComponent(selectedReviewPackage.proposal_id)}/svg`} alt={`${selectedReviewPackage.title} architecture diagram`} />)}</article>}</>}</section>
    <section className="workflow-band"><div><p className="eyebrow">OPERATING MODEL</p><h2>Ask. Review. Propose.</h2></div><ol><li>Ask current-state and impact questions in Genie.</li><li>Run the proposal writer for a reviewed requirement.</li><li>Run the diagram renderer for the proposal graph.</li><li>Review artifacts in the governed volume before any execution.</li></ol></section>
  </main>;
}

type ReviewPackage = { proposal_id: string; title: string; status: string; created_at?: string; package_status?: string; svg_path?: string; png_path?: string; pdf_path?: string; selected_option_id?: string };
type GeneratedArtifact = { proposal_id: string; option_artifacts: Array<{ option_id: string; title: string; svg_path: string }> };
type EvidenceRecord = { evidence_type: string; evidence_ref: string; evidence_status: string; summary: string; observed_at: string; used_at: string };
type EvidencePayload = { rows?: EvidenceRecord[]; genie_response?: string; error?: string };

function ResponseDiagrams({ proposalId }: { proposalId: string }) {
  return <section className="response-diagrams"><h3>Governed architecture diagrams</h3>{['option_1', 'option_2', 'option_3'].map((optionId, index) => <figure className="architecture-image" key={optionId}><img src={`/api/artifacts/${encodeURIComponent(`${proposalId}_${optionId}`)}/svg`} alt={`Architecture option ${index + 1}`} /><figcaption>Architecture option {index + 1}</figcaption></figure>)}</section>;
}

function OptionDiagrams({ proposalId, selectedOptionId, agentResponse, evidenceRefreshToken, onDecision, decisionInFlight }: { proposalId: string; selectedOptionId?: string; agentResponse?: string; evidenceRefreshToken?: number; onDecision?: (optionId: string, decision: 'APPROVED' | 'REJECTED') => void; decisionInFlight?: string }) {
  const optionIds = selectedOptionId ? [selectedOptionId] : ['option_1', 'option_2', 'option_3'];
  const [evidence, setEvidence] = useState<EvidenceRecord[]>([]);
  const [persistedResponse, setPersistedResponse] = useState('');
  const [evidenceError, setEvidenceError] = useState('');

  useEffect(() => {
    let cancelled = false;
    setEvidence([]);
    setPersistedResponse('');
    setEvidenceError('');
    void fetch(`/api/proposals/${encodeURIComponent(proposalId)}/evidence`).then(async (response) => {
      const payload = await response.json() as EvidencePayload;
      if (!response.ok) throw new Error(payload.error ?? 'Unable to load the evidence trail.');
      if (!cancelled) {
        setEvidence(payload.rows ?? []);
        setPersistedResponse(payload.genie_response ?? '');
      }
    }).catch((error: Error) => {
      if (!cancelled) setEvidenceError(error.message);
    });
    return () => { cancelled = true; };
  }, [evidenceRefreshToken, proposalId]);

  const explainabilityResponse = normalizeMarkdown((agentResponse || persistedResponse).trim());

  return <section className="artifact-gallery"><h3>{selectedOptionId ? 'Selected architecture' : 'Option-specific architecture diagrams'}</h3>{optionIds.map((optionId, index) => <figure className="architecture-image" key={optionId}><img src={`/api/artifacts/${encodeURIComponent(`${proposalId}_${optionId}`)}/svg`} alt={`Architecture option ${index + 1}`} /><figcaption>Architecture option {optionId.replace('option_', '')}</figcaption></figure>)}<section className="evidence-trail" aria-label="Explainability and source trail"><div className="evidence-heading"><h3>Explainability and source trail</h3><span>{evidence.length} sources</span></div>{explainabilityResponse && <section className="agent-rationale"><h4>Genie reasoning and evidence register</h4><ReactMarkdown remarkPlugins={[remarkGfm]}>{explainabilityResponse}</ReactMarkdown></section>}{evidenceError ? <p className="load-error">{evidenceError}</p> : evidence.length > 0 ? <ul>{evidence.map((item) => <li key={`${item.evidence_type}-${item.evidence_ref}`}><span className="evidence-status">{item.evidence_type} / {item.evidence_status}</span><strong>{item.evidence_ref}</strong><p>{item.summary}</p></li>)}</ul> : <p className="evidence-loading">Loading governed evidence...</p>}{onDecision && <section className="evidence-decisions"><h4>Review decision</h4><div className="decision-controls">{optionIds.map((optionId) => <div className="option-decision" key={optionId}><strong>Architecture option {optionId.replace('option_', '')}</strong><button disabled={decisionInFlight === `${proposalId}_${optionId}`} onClick={() => void onDecision(optionId, 'APPROVED')}>Approve</button><button className="reject" disabled={decisionInFlight === `${proposalId}_${optionId}`} onClick={() => void onDecision(optionId, 'REJECTED')}>Reject</button></div>)}</div></section>}</section></section>;
}

function Capability({ icon, title, detail }: { icon: React.ReactNode; title: string; detail: string }) {
  return <article className="capability"><div className="capability-icon">{icon}</div><h3>{title}</h3><p>{detail}</p></article>;
}
