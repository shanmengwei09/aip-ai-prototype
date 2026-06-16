# Microsoft RAG Design

This document describes a future Microsoft-based Retrieval Augmented Generation (RAG) proof of concept for Asset Investment Planning.

The key principle is that the AI tool must answer only from approved and traceable sources. It should not act as a generic chatbot.

## Target Outcome

Users should be able to ask questions such as:

- Which schemes are critical for handback in 2027?
- Which pavement schemes have weak evidence?
- What changed between the previous AAMP position and the current 5AMP position?
- Which schemes have high affordability pressure and low delivery confidence?
- What source evidence supports a specific scheme?

The response should include:

- A concise answer.
- The source dataset or document used.
- Specific citations or links.
- Confidence or caveats where evidence is incomplete.
- No answer where approved evidence is absent.

## Potential Microsoft Tools

### SharePoint

Use SharePoint as the controlled source library for approved planning documents, evidence packs and reference extracts.

Recommended uses:

- Store approved AMFP / AAMP / 5AMP documents.
- Store controlled CSV or Excel extracts.
- Store scheme evidence packs.
- Apply metadata such as asset class, plan version, source owner and approval status.

### Teams

Use Teams for user access and collaboration, but not as the uncontrolled data source.

Recommended uses:

- Provide a channel for AIP review.
- Link to the dashboard and approved source library.
- Capture review actions and governance discussions.

### Power BI

Use Power BI for governed reporting once the data model is stable.

Recommended uses:

- Publish controlled dashboards.
- Apply row-level security if required.
- Provide certified semantic models for investment planning data.
- Expose approved measures such as total investment, challenge score and carryover risk.

### Copilot

Use Microsoft 365 Copilot only where it can respect permissions and approved content boundaries.

Recommended uses:

- Summarise approved documents.
- Help users find relevant evidence.
- Support drafting of governance notes where sources are cited.

### Copilot Studio

Use Copilot Studio to build a controlled business-facing assistant.

Recommended uses:

- Define approved topics.
- Connect to controlled data sources.
- Add guardrails and refusal behaviours.
- Provide a Teams-facing interface for specific AIP questions.

### Azure AI Search

Use Azure AI Search as the retrieval layer for indexed documents and structured extracts.

Recommended uses:

- Index approved documents and datasets.
- Store metadata fields for filtering by asset class, route, plan version and approval status.
- Support hybrid keyword and vector search.
- Return citations to source chunks or records.

### Azure OpenAI

Use Azure OpenAI as the language model layer, grounded by Azure AI Search results.

Recommended uses:

- Generate answers from retrieved evidence.
- Summarise source snippets.
- Refuse answers where retrieval does not provide sufficient evidence.
- Apply system instructions that prevent generic or unsupported responses.

## Sources To Index

Start with a limited, approved source set:

- Current AMFP / AAMP / 5AMP documents.
- Approved scheme list.
- Approved asset inventory extract.
- Approved condition extract.
- Approved risk register extract.
- Approved cost plan extract.
- Approved delivery tracker.
- Approved handback requirements and gap register.
- Scheme evidence packs.
- Decision logs and governance records, if approved for this purpose.

Do not index informal drafts, personal notes, email chains or uncontrolled working files in the first proof of concept.

## Source Control

Each source should have metadata:

- Source name
- Source owner
- Approval status
- Plan version
- Date approved
- Review date
- Asset class
- Route or area
- Sensitivity level
- Retention status

Only sources marked as approved for AIP query use should be indexed.

## Permissions

Permissions should follow existing corporate access controls.

Recommended approach:

- Store source documents in permission-controlled SharePoint libraries.
- Use Microsoft Entra ID groups for user access.
- Keep sensitive cost, commercial or risk data restricted to approved groups.
- Ensure the RAG service respects source-level permissions.
- Log user queries and cited sources for audit.

The AI tool must not reveal information from documents the user could not otherwise access.

## Citations

Responses should cite the exact source used.

For documents, cite:

- Document name
- Version
- Section or page, where available
- SharePoint link

For datasets, cite:

- Dataset name
- Extract date
- Row identifier, such as `scheme_id` or `asset_id`
- Source owner

Example response pattern:

```text
Scheme S012 is currently treated as handback critical because it links to asset A012, which has a high handback risk level and an open retaining wall movement gap. Source: handback register extract, 2026-06-16, row A012; scheme list extract, 2026-06-16, row S012.
```

## Reducing Hallucination Risk

Controls:

- Restrict retrieval to approved sources.
- Use strict system instructions: answer only from retrieved evidence.
- Require citations for every material claim.
- Refuse or say "not found in approved sources" when evidence is absent.
- Keep prompts short and task-specific.
- Use metadata filters for plan version and approval status.
- Test with known-answer questions.
- Review logs for unsupported claims.

## Version Control

Versioning should be explicit.

Recommended approach:

- Store dated extracts for each planning cycle.
- Use `plan_version`, `extract_date` and `approval_status` metadata.
- Preserve previous AMFP / AAMP / 5AMP snapshots.
- Avoid overwriting historic extracts without archiving.
- Record change reasons for scheme movements.

This is important because users will ask what has changed between planning positions.

## Managing AMFP / AAMP / 5AMP Documents

Recommended source library structure:

```text
SharePoint AIP Source Library/
  01_Approved_Plans/
    AMFP/
    AAMP/
    5AMP/
    30AMP/
  02_Approved_Data_Extracts/
    Asset_Inventory/
    Condition/
    Schemes/
    Risks/
    Delivery/
    Costs/
    Handback/
  03_Scheme_Evidence_Packs/
  04_Decision_Logs/
  05_Archive/
```

Each file should have a named owner and approval status.

## Simple Proof Of Concept

The Streamlit prototype now includes a local `Ask AIP Data` workspace. This should be treated as a user-experience prototype for the future RAG tool, not as the final AI architecture.

The first Microsoft RAG proof of concept could be:

1. Select one asset class, for example structures.
2. Create a controlled SharePoint folder with approved sample documents and extracts.
3. Index those files in Azure AI Search.
4. Build a simple Copilot Studio or web app interface.
5. Use Azure OpenAI to answer only from search results.
6. Require source citations in every answer.
7. Test 20 to 30 known-answer questions with asset leads.
8. Record where the system refuses correctly because evidence is missing.

Success criteria:

- Answers cite approved sources.
- Unsupported questions are refused.
- Users can trace statements back to source rows or documents.
- Permissions are respected.
- Asset leads agree the answer behaviour is useful and controlled.

## What Not To Do At This Stage

Avoid:

- Indexing uncontrolled Teams chats or email chains.
- Allowing answers from the public internet.
- Treating AI output as an approval decision.
- Replacing engineering judgement or governance review.
- Connecting directly to live systems before the data model is stable.
- Building a large custom application before the source control model is agreed.
- Allowing uncited answers for planning decisions.
- Using the tool as a general chatbot.

The first objective should be a controlled evidence assistant, not a broad conversational agent.
