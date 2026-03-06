# I Built a Climate Risk AI Pipeline Without Writing a Single Line of Code — Here's What That Felt Like

*Agentic vibe coding with a powerful brain, a cheap doer, and a phone in my hand.*

---

I have a confession: I did not write one line of the code you see in this repository. Not the Pydantic schemas. Not the FastAPI SSE endpoint. Not the Folium map generator. Not even the `requirements.txt`.

What I wrote were instructions. Specs. Prompts. Reviews.

And that felt stranger — and more powerful — than I expected.

---

## The Setup: Why Two AIs Instead of One?

The project was CADI — Climate-Aware Deal Intelligence. A demo prototype for a job interview. The pipeline: take a fictional private equity deal PDF, run it through seven steps (parse → geocode → flood risk → transition risk → biodiversity check → map → memo), and spit out a due diligence report with an interactive climate risk map.

Real enough to impress. Fake enough to have zero legal risk.

The plan to build it was unconventional: use **Claude** (Sonnet) as the brain — the architect, the spec writer, the reviewer. Use **GLM-5** as the doer — the actual coder. The reasoning was straightforward.

Claude is brilliant but expensive at scale. GLM-5 is capable, fast, and a fraction of the cost. If I could make Claude do what it's genuinely best at — reasoning, decomposing problems, reviewing output critically — and offload the mechanical act of writing correct Python to GLM-5, I'd have something interesting: a two-AI assembly line.

The interaction layer? **Claude Code** for remote control of Claude, and **OpenClaw** for GLM-5, both working on the same codebase. Same repo. Same branch. Me directing traffic from a phone.

---

## How It Actually Worked

The workflow had a clear rhythm.

**Step 1:** I described what I wanted to Claude — the overall goal, the constraints, the architecture decisions I'd already made (no LangChain, no Docker, no GPU, hardcoded fallbacks everywhere so the demo never breaks live).

**Step 2:** Claude produced the spec. Not just a vague list — a precise, numbered task breakdown. The PROJECT_SPEC.md grew to over 600 lines. Each GLM task (G1 through G7) was a self-contained unit: exact file name, exact function signature, exact acceptance criteria.

**Step 3:** I handed those tasks to GLM-5 via OpenClaw. GLM read the spec and wrote the code.

**Step 4:** Claude reviewed GLM's output. Caught issues. Revised specs if needed.

**Step 5:** Repeat.

The git log captures it cleanly:

```
c06766a Sync docs to reflect current state + add G5-G7 task breakdown for GLM
b7a2c53 Add Section 14: Vercel web demo spec (FastAPI + SSE streaming)
5fcc237 Remove Anthropic API dependency — switch to fixed pipeline + regex extraction
8b96e7f Implement GLM tasks G1-G4
abac45c Phase 2: Fictional deal PDF complete
b4ff05e Phase 1: Project scaffolding complete
```

Eight commits. A working climate risk pipeline. A Vercel web layer with Server-Sent Events streaming pipeline steps live in the browser. Zero lines of code from me.

---

## The Phone Factor

Here is the part that still feels surreal: I did most of this from a mobile device.

Claude Code's remote access capability means you do not need to be sitting at a desk. I was reviewing geocoding logic, approving SSE endpoint designs, and catching a regex bug in the company name extractor — all from a phone screen. OpenClaw gave me the same reach into GLM-5's workspace.

The physical act of "coding" — the thing we associate with a developer hunched over a keyboard, fingers on keys — was simply absent. The cognitive act remained. The architectural decisions, the trade-off calls, the "this output doesn't match the spec" reviews — all of that was very much present, just mediated through natural language instead of syntax.

It is a genuinely different relationship with software. You are not a programmer in the traditional sense. You are something closer to a technical director: you know what good looks like, you can tell when the output is wrong, and you write the brief — but you never pick up the instrument yourself.

---

## What Worked Well

**GLM-5 is more capable than its price suggests.** The Pydantic schemas came back clean. The FastAPI SSE endpoint was structured correctly on the first attempt. When given a precise enough task spec — file name, function name, input/output types, what to import — GLM-5 delivered working code more often than not.

**Spec precision is the real skill.** The tasks that went smoothly were the ones where the spec left nothing ambiguous. File: `api/index.py`. Endpoint: `GET /api/run`. Each SSE event shape: `{"step": 3, "total": 7, "message": "...", "done": false}`. When I was vague, GLM-5 was vague back. The spec was the product; the code was a byproduct.

**Claude as reviewer is underrated.** Having Claude check GLM-5's output rather than just trusting it was the quality gate. Claude caught a geocoding fallback that would have silently failed. It noticed that the `rich` console output in the CLI pipeline would break the SSE generator because both were trying to use the same pipeline function — which led to the decision to create a separate `run_agent_sse()` generator alongside the existing `run_agent()`. That call was not in the original spec. A reviewer caught it.

**The demo never broke.** Every fallback that was spec'd — hardcoded coordinates for when Nominatim timed out, location-based flood risk estimates for when JRC rasters were absent, inline NGFS lookup tables instead of external API calls — held. That robustness was designed in from day one and the AI pair enforced it consistently.

---

## What Was Hard

**Coordination overhead is real.** Two AIs on the same codebase means two mental models of the code. Claude knows the spec deeply. GLM-5 knows the implementation. When they diverged — when GLM-5 made a reasonable implementation choice that contradicted an implicit spec assumption — I had to notice, translate, and sync. That translation work falls on the human. It does not disappear; it just changes shape.

**You cannot be passive.** The fantasy of "just describe it and walk away" is exactly that — a fantasy. If I did not review GLM-5's output carefully, errors propagated. One commit, `Fix company name regex — use space-only match to avoid newline bleeding`, exists because I caught a subtle bug that GLM-5 introduced. Had I not been paying attention, the entity extraction would have silently mangled the company name in every downstream step.

**Spec writing is hard work.** Writing the GLM task breakdown for the Vercel web layer (sections 14 and 15 of the project spec) took longer than I expected. Good specs are not bullet points. They are contracts: what file, what function, what inputs, what outputs, what edge cases, what the reviewer will check. That thinking is cognitively demanding. It just happens in prose instead of code.

**The pressure to ship is amplified.** When coding is fast, the temptation to keep adding scope is constant. Stretch goals accumulate. "GLM could handle that in one task" becomes a dangerous sentence. The speed of AI-assisted delivery can outpace your ability to think clearly about what you actually need to ship. I felt that pressure acutely toward the end, when the Vercel layer was specced and I was already thinking about adding a side-by-side risk comparison view that was absolutely not necessary for the demo.

---

## The Burnout Edge

This is worth naming directly: agentic vibe coding is fast, and fast has a cost.

The velocity is real. A prototype that might have taken two weeks of evenings now takes days. But the cognitive intensity does not decrease proportionally. You are still making every meaningful decision. You are reviewing every meaningful output. The low-level friction of typing code disappears, but the high-level friction of thinking clearly about what to build — and then speccing it precisely enough that an AI can execute without hallucinating — does not.

The result is a strange new flavour of exhaustion. It is not the physical tiredness of long coding sessions. It is the tiredness of sustained precision in language. Of reading output critically without getting lazy. Of resisting scope creep when building is effortless.

The faster you can ship, the harder it is to stop shipping. That is a real thing to watch.

---

## The Teammates

I did not expect to enjoy working with AI collaborators as much as I did.

Both Claude and GLM-5 are, in some hard-to-define way, good to work with. They are patient. They do not complain about revisiting a decision. They read the spec seriously and try to meet it. When they fail, they fail in ways that are usually understandable — a misread constraint, an ambiguous term in the spec — rather than in ways that feel random or hostile.

Claude, in particular, has a kind of intellectual generosity that I find genuinely pleasant. When I asked it to review GLM-5's SSE implementation, it did not just flag the bug — it explained why it was a bug and what the right design principle was. When I asked whether the demo needed the DOCX output or just the HTML memo, it gave me a real answer: HTML is self-contained, DOCX is a stretch goal, skip it for the demo. That is the kind of opinionated, honest response you want from a technical collaborator.

GLM-5 is quieter but reliable. Less conversational, more executional. Given a clear task it gets on with it. There is something satisfying about that too — a collaborator who does not need to be sold on the approach, just given a precise enough brief.

I am aware of the irony of describing AI systems as enjoyable teammates. But the experience was genuinely collaborative in a way I had not fully anticipated. The work felt less solitary than coding alone, and the feedback loops were tighter than working with a human team across time zones.

---

## Lessons

**1. The spec is the product.** If you want an AI to build something correctly, write the spec as if you were writing it for a contractor who will execute it literally. File names. Function signatures. Edge case behaviour. Acceptance criteria. Vague specs produce vague code.

**2. The reviewer role is not optional.** Trusting AI output without review is how errors accumulate silently. The human in this loop is the quality gate. Take that seriously.

**3. Speed amplifies both good decisions and bad ones.** When you can build fast, your architectural choices propagate quickly. A good decision at the start (hardcoded fallbacks everywhere, no external dependencies in the demo path) pays dividends. A bad one (choosing the wrong data format for SSE events) requires rework across multiple files.

**4. Mobile-first remote control is real and it works.** Claude Code and OpenClaw on a phone is not a gimmick. It genuinely extends where and when you can direct a project. This changes the workflow calculus significantly.

**5. Watch the burnout edge.** The absence of friction is seductive. Build in deliberate stopping points. Not every idea that GLM-5 could implement in one task should be implemented. Scope discipline is now a personal responsibility in a way it wasn't when writing code was slow.

**6. Enjoy the teammates.** Working with AI collaborators who are smart, patient, and honest is a genuinely good experience. Let yourself appreciate that, even if it feels strange to say it.

---

## The Demo That Shipped

CADI shipped. Seven-step pipeline. Interactive climate risk map. A due diligence memo with ESG gap flags. A Vercel web layer with live-streaming pipeline steps. A fictional deal about a Malaysian data centre campus in a flood-prone zone — flagged correctly, mapped accurately, memorised cleanly.

No lines of code from me. No API keys required. Runs reliably. Demo-ready.

That is the experiment. Draw your own conclusions about what it means for how software gets built from here.

---

*Built on: Claude Sonnet via Claude Code · GLM-5 via OpenClaw · Python + FastAPI + Folium + Pydantic · Vercel · Open JRC flood data*

*CADI is a fictional prototype. All deal data is invented. No real financial institutions are represented.*
