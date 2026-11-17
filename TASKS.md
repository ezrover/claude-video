# Tasks

## 01-watch-skill-after-agy-removal

Status: ready-for-human
Type: task
Blocked by: none

The owner removed agy from the shared harness on 2026-11-17 and chose to remove the agy engine and
agy transcription from the watch skill as well. Commit a15d956 ("add agy subscription engine and
transcription backend") is reverse-applied in the working tree, uncommitted: `agy.py` and
`tests/test_agy.py` are deleted and `SKILL.md`, `config.py`, `setup.py`, `watch.py`, `whisper.py` and
`tests/test_packaging.py` are back to their 0.3.2 state. `python3 -m pytest tests -q` passes (249).

Left for the owner: commit and push, cut a release with a CHANGELOG entry (a15d956 is already on
`origin/main`, so installed copies still offer agy until then), and run `dev-sync.sh` for the local
install. A saved `WATCH_WHISPER_BACKEND="agy"` or `WATCH_ENGINE="agy"` now raises a config error;
the owner's own `~/.config/watch/.env` was switched to `auto`.

### Comments

- 2026-11-17 — filed during the agy removal in the Agents repository.
