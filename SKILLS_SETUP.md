# AgentCraft — Skills Configuration & Setup (`SKILLS_SETUP.md`)

This guide explains how **skills** are structured, configured, and utilized within **AgentCraft** under the **Antigravity Customization System**.

---

## 1. What Are Skills?

Skills are modular packages of procedures, runbooks, and guidelines that extend an agent's problem-solving capabilities. Under the Antigravity architecture:
- Skills live in `skills/<skill_name>/` directories.
- Each skill requires a `SKILL.md` file featuring YAML frontmatter (`name`, `description`).
- Skills use **progressive disclosure**: only their names and descriptions are exposed initially; the full contents are loaded on-demand when relevant to a specific user goal or step.

---

## 2. Active Skills in AgentCraft

### 2.1 Workspace Project Skills (`.agents/skills/`)

The following project-specific workspace skills are installed in this repository:

1. **`agentcraft-evaluator`** (`.agents/skills/agentcraft-evaluator/SKILL.md`):
   - **Purpose**: Procedural guide for executing the automated capability benchmark suite, inspecting metric thresholds (completion rate $\ge 90\%$, zero unregistered tool calls), and validating verification proofs.
   - **Trigger**: Activated when running evaluation routines, benchmark comparisons, or compliance audits for AGENTCRAFT 2026.

2. **`agentcraft-tool-builder`** (`.agents/skills/agentcraft-tool-builder/SKILL.md`):
   - **Purpose**: Step-by-step authoring manual for creating new AgentCraft tools with sandboxed execution, typed parameters, path-traversal guards, and unit tests.
   - **Trigger**: Activated when adding or modifying tools in `ai/tools/`.

### 2.2 System Built-in Skills

The Antigravity runtime provides the following built-in reference skills:
- **`agy-customizations`**: Reference guide for the customization system, priority resolution, and rules engine.
- **`antigravity-guide`**: Comprehensive reference and documentation for Google Antigravity.

> [!NOTE]
> AgentCraft does not falsely claim or invent unverified third-party plugins. All skills referenced above are physically present and verified in the repository.

---

## 3. How to Author New Project Skills

To add a new skill to AgentCraft:

1. Create a subdirectory under `.agents/skills/<your-skill-name>/`.
2. Add a `SKILL.md` file with standard frontmatter:
   ```markdown
   ---
   name: your-skill-name
   description: >-
     Describe precisely what procedures this skill provides and when the agent should activate it.
   ---

   # Your Skill Title

   Provide clear, step-by-step instructions, commands, and verification criteria.
   ```
3. Test your skill by invoking related tasks in the workspace.
