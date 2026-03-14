# WAT Framework
## Workflows, Agents, Tools

An agentic system that separates probabilistic AI reasoning from deterministic execution.

## Architecture

**Workflows** (`workflows/`) - Markdown SOPs defining what to do and how
**Agents** (Claude) - Intelligent orchestration and decision-making
**Tools** (`tools/`) - Python scripts for reliable execution

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment:**
   ```bash
   cp .env.template .env
   # Edit .env with your actual API keys
   ```

3. **Create your first workflow:**
   - Add a markdown file to `workflows/` describing your process
   - Build tools in `tools/` to execute the steps
   - Run through Claude Code

## Directory Structure

```
.tmp/           # Temporary processing files (gitignored)
tools/          # Python scripts for deterministic execution
workflows/      # Markdown SOPs (your instructions)
.env            # API keys (gitignored - use .env.template as reference)
CLAUDE.md       # Core agent instructions
```

## Philosophy

- **AI handles reasoning** - Claude reads workflows, makes decisions, handles failures
- **Code handles execution** - Python scripts do the actual work reliably
- **Separation = reliability** - Each layer does what it's best at
- **Continuous improvement** - Every failure makes the system stronger

## Usage Pattern

1. Write a workflow describing what you want done
2. Claude reads the workflow and determines required tools
3. Claude executes tools in the correct sequence
4. When things fail, Claude learns and updates the workflow
5. System gets more robust over time

Read [CLAUDE.md](CLAUDE.md) for complete agent instructions.
