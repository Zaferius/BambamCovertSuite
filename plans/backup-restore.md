# Backup and Restore Guide

## What should be backed up

For a self-hosted installation, the most important persistent locations are:

- `[data/db](../data/db)` for SQLite job metadata
- `[data/outputs](../data/outputs)` for generated files and bundles if you need historical retention

Optional:

- `[data/uploads](../data/uploads)` if you want to preserve original uploads still waiting for processing

## Minimum backup strategy

- Stop the stack or ensure no critical jobs are running
- Copy `[data/db](../data/db)` and `[data/outputs](../data/outputs)` to backup storage
- Keep at least one rolling backup before major updates

## Restore strategy

- Stop the containers
- Restore `[data/db](../data/db)` and `[data/outputs](../data/outputs)` from backup
- Start the stack again with `[docker-compose.yml](../docker-compose.yml)`
- Verify `/health`, `/jobs`, and a sample download flow

## Notes

- If outputs are not important, the minimum recoverable state is `[data/db](../data/db)` only
- If retention cleanup has removed old artifacts, restored database entries may reference files that no longer exist unless outputs are also restored
