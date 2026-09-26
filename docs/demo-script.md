# ProofChange — 3-Minute Demo Script

> **Total runtime: 3:00 | Format: live screen-share**
> Pre-flight: app running at `http://localhost:8501`, browser open on that tab,
> GitHub PR open in a second tab, `.env` credentials configured.

---

## 0:00–0:20 — Opening Hook

**Say:**
> "The tests are green. But did we actually verify the change?"

CI answered one question: *did the configured tests pass?*
It did not answer the question that matters after a code change:
*is the newly changed behavior adequately verified?*

ProofChange answers that question — and produces evidence you can audit.

---

## 0:20–0:50 — The Problem

**Say:**
> "Here is the exact scenario. A developer opens a PR that adds a VIP discount
> tier to `calculate_discount()`. Existing tests cover `premium` and `regular`.
> Nothing covers `vip`. CI is green. Nobody notices."

**Show** (switch to the GitHub PR tab):
- The diff: `demo_repo/src/pricing.py` — the new `if customer_type == "vip"` branch.
- The existing test file: `demo_repo/tests/test_pricing.py` — no `vip` test.
- The green CI check. **Point out:** "Green. And the new path is unverified."

**Return** to the ProofChange tab (`http://localhost:8501`).

---

## 0:50–1:30 — Live Demo: Run the Pipeline

**Click path:**
1. In the left sidebar, click **Live PR Test**.
2. In the **Repository** field, confirm `Zeeshantariqpkn/proofchange-test`
   (or type the correct `owner/repo`).
3. In the **PR number** field, enter the PR number for the VIP branch PR.
4. Leave **Post Check Run back to GitHub** checked.
5. Click **▶ Run Live Analysis** (blue primary button).

**Say while the log streams:**
> "It's authenticating with GitHub … fetching the diff … cloning the branch …
> running the AST walk … mapping existing tests … detecting the VIP gap …
> generating a focused pytest test … executing pytest … posting the Check Run."

**When complete, point to the four result metrics:**
- **Evidence: STRONG**
- **Tests: 3/3**
- **Gaps: 1**
- **Generated: 1**

**Say:**
> "One gap detected. One test generated. Three of three pass. Evidence: STRONG."

---

## 1:30–2:00 — Evidence Page

**Click path:**
1. In the left sidebar, click **Evidence**.

**Show:**
- The **Change Evidence Package** — changed-code map, impact analysis,
  test-gap report, generated tests, execution report, verification summary.
- The **STRONG** evidence badge and its auditable rationale
  ("all gaps addressed, ≥ 70 % of paths verified").
- Click **Download Evidence JSON** — a `proofchange_live_<commit>.json` file
  downloads to the presenter's machine.

**Say:**
> "This is the Change Evidence Package. It is a structured artifact that
> answers every question a reviewer needs: what changed, what was untested,
> what test was generated, and what the result was."

---

## 2:00–2:20 — GitHub: The Check Run

**Click path:**
1. In the left sidebar, click **GitHub**.

   *— or —*

2. Switch to the GitHub PR tab directly.
   Navigate to the PR → **Checks** tab → find
   **ProofChange — Change Verification**.

**Show:**
- The check status (pass / fail).
- The check details panel with the evidence level and rationale posted
  directly on the PR by ProofChange.

**Say:**
> "ProofChange posts a GitHub Check Run back to the PR — so the evidence
> lives where the review happens."

---

## 2:20–2:40 — IBM Bob Page

**Click path:**
1. In the left sidebar, click **IBM Bob**.

**Show:**
- The five expandable **Reusable Bob task prompts**:
  1. **Repository Understanding** — identify affected functions and untested scenarios
  2. **Test Gap Analysis** — review changed code against existing tests
  3. **Test Generation** — produce focused pytest tests for missing scenarios
  4. **Failure Analysis** — classify failing generated tests
  5. **Verification Summary** — produce the human-readable evidence summary
- The **Where Bob assisted** section underneath.

**Say:**
> "IBM Bob 2.0 is a first-class part of the architecture — five documented
> task prompts, each mapping one-to-one to a pipeline step. Every generated
> artifact records whether it came from `bob-assisted` or `runtime_llm`,
> so the origin of every decision is always traceable."

---

## 2:40–3:00 — Closing

**Say:**
> "Not just test generation. Change verification.
> ProofChange turns every code change into evidence — scoped to the diff,
> executed by real pytest, scored by auditable rules, and posted to the PR
> as a GitHub Check Run.
> The tests were green. Now you can prove the change was verified."

---

## ⚠ Fallback Plan — Live Demo Fails

> Use this if GitHub credentials are missing, the API is unavailable,
> or `▶ Run Live Analysis` returns an error.

**Say:**
> "Let me run the bundled demo pipeline instead — same change, same pipeline,
> no credentials needed."

**Click path:**
1. In the left sidebar, toggle **Demo Mode** on (default: on).
2. Click **Run Demo Pipeline** (button below the toggle).
3. Wait ~5–10 seconds for the pipeline to complete.
4. Continue the script from **1:30 — Evidence Page** — the result is
   the identical Change Evidence Package with **STRONG** evidence.

**Resume** at the Evidence page → GitHub page → IBM Bob page → Closing
exactly as scripted above. The only difference: the GitHub Check Run will
show as "— no" (not posted), since no live credentials are used.

---

## Quick Reference

| Timestamp | Action | URL / Click path |
|-----------|--------|-----------------|
| 0:00 | Open hook | — |
| 0:20 | Show PR diff + green CI | GitHub PR tab → Files changed |
| 0:50 | Sidebar → **Live PR Test** | `http://localhost:8501` → sidebar |
| 0:55 | Enter repo + PR number | Repository field + PR number field |
| 1:00 | Click **▶ Run Live Analysis** | Blue primary button |
| 1:20 | Point to STRONG metrics | Result panel, four metric tiles |
| 1:30 | Sidebar → **Evidence** | Sidebar nav |
| 1:45 | Click **Download Evidence JSON** | Button below Evidence Package |
| 2:00 | Sidebar → **GitHub** (or PR tab) | Sidebar nav or GitHub PR → Checks |
| 2:20 | Sidebar → **IBM Bob** | Sidebar nav |
| 2:25 | Expand each of the 5 prompts | Expander rows on IBM Bob page |
| 2:40 | Closing statement | — |
| **FALLBACK** | Sidebar → toggle Demo Mode + **Run Demo Pipeline** | Sidebar, below nav |
