# Example projects

The examples are original fictional teaching content, released under CC0-1.0. They contain no experimental Cell-iSCAT data or real scientific study results.

```sh
uv run scientist-os demo --workspace workspaces/microscopy
uv run scientist-os demo --workspace workspaces/environment --domain environment
```

The domain switch demonstrates that record storage and independent-unit analysis are generic. It is not external validation in environmental science.

`evaluation_cases.json` is a frozen candidate evaluation set with supported, contradictory, unknown and stale-evidence questions. Exact record IDs are generated when loading; resolve case selection by title. See [evaluation protocol](../docs/EVALUATION_PROTOCOL.md). Published cases are useful regression fixtures, not an undisclosed benchmark for later tuned models.

## Software provenance record example

Create a Software record, then put these fields in Additional metadata (replace every placeholder with verified information):

```json
{
  "repository_url": "https://github.com/your-team/your-analysis",
  "code_commit": "FULL_IMMUTABLE_COMMIT_SHA",
  "environment_lock_sha256": "HASH_OF_YOUR_ENVIRONMENT_LOCK",
  "command": "documented non-interactive analysis command",
  "dirty_worktree": false,
  "parameters": {},
  "seed": 42,
  "license": "Unresolved"
}
```

Link an Analysis record to that Software record and the input Dataset records. Link the figure and manuscript claim to the analysis. A record of a commit is not proof that the code was executed; preserve the actual run manifest and check it during human review.
