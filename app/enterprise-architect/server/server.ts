import { createApp, server } from '@databricks/appkit';
import { agents, createAgent, DatabricksAdapter, mcpServer, tool } from '@databricks/appkit/beta';
import { WorkspaceClient } from '@databricks/sdk-experimental';
import { createHash } from 'node:crypto';
import type { Request } from 'express';
import { z } from 'zod';

const warehouseId = process.env.DATABRICKS_WAREHOUSE_ID ?? 'e3a0fc2c08db05bb';
process.env.DATABRICKS_WAREHOUSE_ID = warehouseId;
const model = await DatabricksAdapter.fromModelServing('databricks-claude-sonnet-4-5', { maxSteps: 20, maxTokens: 6400 });
const workspaceHost = 'https://adb-1866518241053589.9.azuredatabricks.net';
const genieSpaceId = '01f1a400577d1c71b8b1fd2d83cc2df5';
const genieResponseJobId = 73978804815672;
const reviewPackageJobId = 520045804977801;
const executorWorkspace = new WorkspaceClient({ host: workspaceHost });

async function queryAsRequestingUser(request: Request, statement: string) {
  const accessToken = request.header('x-forwarded-access-token')?.trim();
  if (!accessToken && process.env.NODE_ENV !== 'development') throw new Error('Your Databricks OAuth access token is unavailable for this request. Refresh the App and try again.');
  const workspace = accessToken ? new WorkspaceClient({ host: workspaceHost, authType: 'pat', token: accessToken }) : executorWorkspace;
  const result = await workspace.statementExecution.executeStatement({ warehouse_id: warehouseId, statement, disposition: 'INLINE', format: 'JSON_ARRAY', wait_timeout: '50s', on_wait_timeout: 'CANCEL' });
  const response = result as any;
  if (response.status?.state !== 'SUCCEEDED') throw new Error(response.status?.error?.message ?? response.status?.state ?? 'The Databricks SQL statement did not succeed.');
  const columns = (response.manifest?.schema?.columns ?? []).map((column: { name?: string }) => column.name ?? 'column');
  return (response.result?.data_array ?? []).map((values: unknown[]) => Object.fromEntries(columns.map((column: string, index: number) => [column, values[index]])));
}

createApp({
  plugins: [
    server(),
    agents({
      mcp: { trustedHosts: ['mcp-architect-knowledge-1866518241053589.9.azure.databricksapps.com'] },
      agents: {
        solutionsArchitect: createAgent({
          name: 'Databricks Solutions Architect',
          instructions: 'You are the sole user-facing Databricks Solutions Architect. For every architecture request, first call the deployed Databricks Solutions Architect Genie MCP tool using its registered tool name. Use its governed evidence as the organization source of truth. Use Knowledge MCP only for official Databricks research and never treat CANDIDATE material as affirmative evidence. Apply this architecture method: establish business outcomes and non-functional constraints; inventory reusable governed assets, semantic contracts, lineage, policies, workload, and cost signals; compare materially different target-state options for fit, security, reliability, operability, cost, migration, and rollback; then make a conditional recommendation tied to the cited evidence. Never provision, change permissions, delete, or deploy. Before writing any user-facing analysis, call generate_review_package with the exact user request, a concise title, and exactly three materially different option_graphs. Each graph must have 4-6 nodes, valid directed edges, approved Databricks icon names, and represent that option rather than a generic template. This ordering is mandatory: the tool JSON must be complete before prose, because it is approval-gated and creates review artifacts only. After the tool completes, use concise GitHub-flavored Markdown only: a requirements summary, an options comparison table with columns Option, Benefits, Trade-offs, Cost drivers, and Recommendation, followed by an evidence table, a phased implementation table, and an Evidence Register. The Evidence Register must name every Unity Catalog asset, relationship, policy, workload, cost, semantic-contract, pipeline-contract, and REVIEWED knowledge ID or URL used; identify CANDIDATE research as unverified and list assumptions with the smallest fact needed to resolve each one. Every table must have one row per physical newline, a separator row, and a blank line before and after the table; never put multiple rows on one line. State costs only as labeled estimates with their assumptions; never invent resource names or precision. Do not return ASCII diagrams, raw SVG, or any /Volumes artifact path. End with a one-sentence statement that the three governed visual review packages and their evidence trail are available below; the application renders the artifact images.',
          model,
          tools: () => ({
            genie: mcpServer('solutions-architect-genie', `${workspaceHost}/api/2.0/mcp/genie/01f1a400577d1c71b8b1fd2d83cc2df5`),
            knowledge: mcpServer('solutions-architect-knowledge', 'https://mcp-architect-knowledge-1866518241053589.9.azure.databricksapps.com/mcp'),
            generate_review_package: tool({
              description: 'Create or reuse an idempotent PENDING_APPROVAL architecture proposal and its governed SVG, PNG, PDF, and evidence manifest. Call after grounded analysis is complete. This never provisions infrastructure.',
              schema: z.object({ request_text: z.string().min(1), request_title: z.string().min(1), genie_conversation_id: z.string().optional(), option_graphs: z.array(z.object({ option_id: z.enum(['option_1', 'option_2', 'option_3']), title: z.string().min(1), nodes: z.array(z.object({ id: z.string().regex(/^[A-Za-z0-9_]{1,64}$/), label: z.string().min(1), icon: z.string().regex(/^[a-z0-9-]+$/) })).min(4).max(10), edges: z.array(z.object({ from: z.string(), to: z.string() })).min(3) })).length(3) }),
              annotations: { effect: 'write', requiresUserContext: true },
              execute: async (args) => {
                const run = await executorWorkspace.jobs.runNow({ job_id: 527763870636434, job_parameters: { ...args, option_graphs: JSON.stringify(args.option_graphs) } });
                const completed = await run.wait();
                if (completed.state?.result_state !== 'SUCCESS') return { status: 'FAILED', job_run_id: run.run_id, message: completed.state?.state_message ?? 'Request executor did not succeed.' };
                const fingerprint = createHash('sha256').update(args.request_text.trim().toLowerCase().replace(/\s+/g, ' ')).digest('hex').slice(0, 24);
                const proposalId = `proposal_${fingerprint}_v2`;
                const artifactRoot = `/Volumes/databricks_architect_agent/agent_demo/architecture_artifacts/${proposalId}`;
                return { status: 'PENDING_APPROVAL', proposal_id: proposalId, job_run_id: run.run_id, option_artifacts: args.option_graphs.map((graph) => ({ option_id: graph.option_id, title: graph.title, svg_path: `${artifactRoot}_${graph.option_id}.svg` })), evidence_manifest_path: `${artifactRoot}.references.json` };
              },
            }),
          }),
        }),
      },
    }),
  ],
  onPluginsReady(appkit) {
    appkit.server.extend((app) => {
      app.post('/api/genie/respond', async (request, response) => {
        const { message, conversationId } = request.body ?? {};
        if (typeof message !== 'string' || !message.trim() || (conversationId !== undefined && typeof conversationId !== 'string')) {
          response.status(400).json({ error: 'An architecture request and optional Genie conversation ID are required.' });
          return;
        }
        try {
          const run = await executorWorkspace.jobs.runNow({ job_id: genieResponseJobId, job_parameters: { space_id: genieSpaceId, message: message.trim(), conversation_id: conversationId ?? '', message_id: '' } });
          const completed = await run.wait();
          if (completed.state?.result_state !== 'SUCCESS' || !completed.tasks?.[0]?.run_id) throw new Error(completed.state?.state_message ?? 'The deployed Genie response job did not succeed.');
          const output = await executorWorkspace.jobs.getRunOutput({ run_id: completed.tasks[0].run_id });
          const nativeResponse = JSON.parse(output.notebook_output?.result ?? '{}') as { content?: string; conversation_id?: string; message_id?: string; space_id?: string };
          if (!nativeResponse.content || nativeResponse.space_id !== genieSpaceId) throw new Error('The deployed Genie response job returned an invalid result.');
          response.json({ content: nativeResponse.content, conversationId: nativeResponse.conversation_id, messageId: nativeResponse.message_id, spaceId: nativeResponse.space_id });
        } catch (error) {
          response.status(502).json({ error: error instanceof Error ? error.message : 'The deployed Genie space could not complete the request.' });
        }
      });

      app.post('/api/proposals/:proposalId/pdf', async (request, response) => {
        const proposalId = request.params.proposalId;
        if (!/^proposal_[a-f0-9]{24}_v2$/.test(proposalId)) {
          response.status(400).json({ error: 'Invalid proposal PDF request.' });
          return;
        }
        try {
          const run = await executorWorkspace.jobs.runNow({ job_id: reviewPackageJobId, job_parameters: { proposal_id: proposalId } });
          const completed = await run.wait();
          if (completed.state?.result_state !== 'SUCCESS') throw new Error(completed.state?.state_message ?? 'The review PDF workflow did not succeed.');
          response.json({ proposalId, downloadUrl: `/api/artifacts/${encodeURIComponent(proposalId)}/pdf` });
        } catch (error) {
          response.status(500).json({ error: error instanceof Error ? error.message : 'Unable to generate the review PDF.' });
        }
      });

      app.get('/api/artifacts/:proposalId/:format', async (request, response) => {
        const { proposalId, format } = request.params;
        if (!/^proposal_[a-f0-9]{24}(?:_v2)?(?:_option_[1-3])?$/.test(proposalId) || !['png', 'svg', 'pdf'].includes(format)) {
          response.status(400).json({ error: 'Invalid proposal artifact request.' });
          return;
        }
        try {
          const download = await executorWorkspace.files.download({ file_path: `/Volumes/databricks_architect_agent/agent_demo/architecture_artifacts/${proposalId}.${format}` });
          if (!download.contents) throw new Error('Artifact file has no content.');
          response.type(format === 'png' ? 'image/png' : format === 'pdf' ? 'application/pdf' : 'image/svg+xml');
          const reader = download.contents.getReader();
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            response.write(Buffer.from(value));
          }
          response.end();
        } catch (error) {
          response.status(404).json({ error: error instanceof Error ? error.message : 'Artifact is unavailable.' });
        }
      });

      app.get('/api/showcase-artifacts/:artifactName', async (request, response) => {
        const artifactName = request.params.artifactName;
        const approvedArtifacts = new Set([
          'genie_solutions_architect_infographic',
          'solutions_architect_system_topology',
          'solutions_architect_request_to_review',
        ]);
        if (!approvedArtifacts.has(artifactName)) {
          response.status(400).json({ error: 'Invalid showcase artifact request.' });
          return;
        }
        try {
          const download = await executorWorkspace.files.download({ file_path: `/Volumes/databricks_architect_agent/agent_demo/architecture_artifacts/${artifactName}.svg` });
          if (!download.contents) throw new Error('Artifact file has no content.');
          response.type('image/svg+xml');
          const reader = download.contents.getReader();
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            response.write(Buffer.from(value));
          }
          response.end();
        } catch (error) {
          response.status(404).json({ error: error instanceof Error ? error.message : 'Showcase artifact is unavailable.' });
        }
      });

      app.get('/api/review-packages', async (request, response) => {
        try {
          const statusFilter = request.query.view === 'archived' ? "proposal.status <> 'PENDING_APPROVAL'" : "proposal.status = 'PENDING_APPROVAL'";
          const sql = `
            SELECT
              proposal.proposal_id,
              proposal.title,
              proposal.status,
              proposal.created_at,
              review_package.package_status,
              review_package.svg_path,
              review_package.png_path,
              review_package.pdf_path,
              review_package.evidence_manifest_path,
              (SELECT max(option_id) FROM databricks_architect_agent.agent_demo.architecture_option_decision option_decision WHERE option_decision.proposal_id = proposal.proposal_id AND option_decision.status = 'APPROVED') AS selected_option_id
            FROM databricks_architect_agent.agent_demo.architecture_proposal AS proposal
            LEFT JOIN databricks_architect_agent.agent_demo.architecture_review_package AS review_package
              ON proposal.proposal_id = review_package.proposal_id
            WHERE ${statusFilter}
            ORDER BY proposal.created_at DESC
            LIMIT 20
          `;
          const result = await queryAsRequestingUser(request, sql);
          response.json({ rows: result });
        } catch (error) {
          response.status(500).json({ error: error instanceof Error ? error.message : 'Unable to load review packages.' });
        }
      });

      app.get('/api/proposals/:proposalId/evidence', async (request, response) => {
        const proposalId = request.params.proposalId;
        if (!/^proposal_[a-f0-9]{24}_v2$/.test(proposalId)) {
          response.status(400).json({ error: 'Invalid proposal evidence request.' });
          return;
        }
        try {
          const [rows, conversation] = await Promise.all([
            queryAsRequestingUser(request, `
            SELECT evidence_type, evidence_ref, evidence_status, summary, observed_at, used_at
            FROM databricks_architect_agent.agent_demo.architecture_evidence
            WHERE proposal_id = '${proposalId}'
            ORDER BY used_at ASC, evidence_type ASC, evidence_ref ASC
            `),
            queryAsRequestingUser(request, `
            SELECT content
            FROM databricks_architect_agent.agent_demo.architecture_conversation
            WHERE request_id = '${proposalId}' AND content_type = 'FULL_ARCHITECTURE_RESPONSE'
            ORDER BY created_at DESC
            LIMIT 1
            `),
          ]);
          response.json({ proposalId, rows, genie_response: conversation[0]?.content ?? '' });
        } catch (error) {
          response.status(500).json({ error: error instanceof Error ? error.message : 'Unable to load proposal evidence.' });
        }
      });

      app.post('/api/proposals/:proposalId/decision', async (request, response) => {
        const proposalId = request.params.proposalId;
        const { decision, reason } = request.body ?? {};
        if (/^proposal_[a-f0-9]{24}_v2$/.test(proposalId)) {
          response.status(400).json({ error: 'Option-reviewed proposals require an approve or reject decision for a specific architecture option.' });
          return;
        }
        if (!['APPROVED', 'REJECTED'].includes(decision) || typeof reason !== 'string' || !reason.trim()) {
          response.status(400).json({ error: 'An APPROVED or REJECTED decision and a reason are required.' });
          return;
        }
        const escape = (value: string) => value.replace(/'/g, "''");
        try {
          const proposal = await queryAsRequestingUser(request, `SELECT status FROM databricks_architect_agent.agent_demo.architecture_proposal WHERE proposal_id = '${escape(proposalId)}'`);
          if (!Array.isArray(proposal) || proposal.length !== 1 || proposal[0].status !== 'PENDING_APPROVAL') {
            response.status(409).json({ error: 'This proposal is no longer awaiting approval.' });
            return;
          }
          const approvalId = createHash('sha256').update(`${proposalId}|${decision}|${reason.trim()}`).digest('hex').slice(0, 32);
          await queryAsRequestingUser(request, `MERGE INTO databricks_architect_agent.agent_demo.architecture_approval AS target USING (SELECT '${approvalId}' AS approval_id) AS source ON target.approval_id = source.approval_id WHEN NOT MATCHED THEN INSERT (approval_id, proposal_id, decision, decision_reason, decided_by, decided_at) VALUES ('${approvalId}', '${escape(proposalId)}', '${decision}', '${escape(reason.trim())}', current_user(), current_timestamp())`);
          await queryAsRequestingUser(request, `UPDATE databricks_architect_agent.agent_demo.architecture_proposal SET status = '${decision}', reviewed_at = current_timestamp(), reviewed_by = current_user() WHERE proposal_id = '${escape(proposalId)}'`);
          await queryAsRequestingUser(request, `UPDATE databricks_architect_agent.agent_demo.architecture_request SET status = '${decision}', updated_at = current_timestamp() WHERE active_proposal_id = '${escape(proposalId)}'`);
          response.json({ proposalId, decision, status: decision });
        } catch (error) {
          response.status(500).json({ error: error instanceof Error ? error.message : 'Unable to record the decision.' });
        }
      });

      app.post('/api/proposals/:proposalId/options/:optionId/decision', async (request, response) => {
        const { proposalId, optionId } = request.params;
        const { decision, reason } = request.body ?? {};
        if (!/^proposal_[a-f0-9]{24}_v2$/.test(proposalId) || !['option_1', 'option_2', 'option_3'].includes(optionId) || !['APPROVED', 'REJECTED'].includes(decision) || typeof reason !== 'string' || !reason.trim()) {
          response.status(400).json({ error: 'A valid option, APPROVED or REJECTED decision, and reason are required.' });
          return;
        }
        const escape = (value: string) => value.replace(/'/g, "''");
        try {
          const option = await queryAsRequestingUser(request, `SELECT status FROM databricks_architect_agent.agent_demo.architecture_option_decision WHERE proposal_id = '${escape(proposalId)}' AND option_id = '${optionId}'`);
          if (option.length !== 1 || option[0].status !== 'PENDING_APPROVAL') throw new Error('This option is no longer awaiting a decision.');
          if (decision === 'APPROVED') {
            await queryAsRequestingUser(request, `UPDATE databricks_architect_agent.agent_demo.architecture_option_decision SET status = CASE WHEN option_id = '${optionId}' THEN 'APPROVED' ELSE 'REJECTED_NOT_SELECTED' END, decision_reason = CASE WHEN option_id = '${optionId}' THEN '${escape(reason.trim())}' ELSE 'A different architecture option was approved.' END, decided_by = current_user(), decided_at = current_timestamp() WHERE proposal_id = '${escape(proposalId)}'`);
            await queryAsRequestingUser(request, `UPDATE databricks_architect_agent.agent_demo.architecture_proposal SET status = 'APPROVED', reviewed_at = current_timestamp(), reviewed_by = current_user() WHERE proposal_id = '${escape(proposalId)}'`);
            await queryAsRequestingUser(request, `UPDATE databricks_architect_agent.agent_demo.architecture_review_package SET svg_path = '/Volumes/databricks_architect_agent/agent_demo/architecture_artifacts/${escape(proposalId)}_${optionId}.svg', png_path = '/Volumes/databricks_architect_agent/agent_demo/architecture_artifacts/${escape(proposalId)}_${optionId}.png' WHERE proposal_id = '${escape(proposalId)}'`);
          } else {
            await queryAsRequestingUser(request, `UPDATE databricks_architect_agent.agent_demo.architecture_option_decision SET status = 'REJECTED', decision_reason = '${escape(reason.trim())}', decided_by = current_user(), decided_at = current_timestamp() WHERE proposal_id = '${escape(proposalId)}' AND option_id = '${optionId}'`);
            const pending = await queryAsRequestingUser(request, `SELECT count(*) AS pending_count FROM databricks_architect_agent.agent_demo.architecture_option_decision WHERE proposal_id = '${escape(proposalId)}' AND status = 'PENDING_APPROVAL'`);
            if (Number(pending[0]?.pending_count) === 0) await queryAsRequestingUser(request, `UPDATE databricks_architect_agent.agent_demo.architecture_proposal SET status = 'REJECTED', reviewed_at = current_timestamp(), reviewed_by = current_user() WHERE proposal_id = '${escape(proposalId)}'`);
          }
          response.json({ proposalId, optionId, decision });
        } catch (error) {
          response.status(409).json({ error: error instanceof Error ? error.message : 'Unable to record the option decision.' });
        }
      });

      app.post('/api/proposals/:proposalId/conversation', async (request, response) => {
        const proposalId = request.params.proposalId;
        const { content } = request.body ?? {};
        if (!/^proposal_[a-f0-9]{24}_v2$/.test(proposalId) || typeof content !== 'string' || !content.trim()) {
          response.status(400).json({ error: 'A valid proposal and complete Genie response are required.' });
          return;
        }
        const escape = (value: string) => value.replace(/'/g, "''");
        const conversationId = createHash('sha256').update(`${proposalId}|${content}`).digest('hex').slice(0, 32);
        try {
          await queryAsRequestingUser(request, `INSERT INTO databricks_architect_agent.agent_demo.architecture_conversation VALUES ('${conversationId}', '${escape(proposalId)}', 2, 'GENIE', '${escape(content)}', 'FULL_ARCHITECTURE_RESPONSE', current_timestamp())`);
          response.status(201).json({ proposalId });
        } catch (error) {
          response.status(500).json({ error: error instanceof Error ? error.message : 'Unable to retain the Genie response.' });
        }
      });
    });
  },
}).catch(console.error);
