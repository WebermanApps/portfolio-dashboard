# Portfolio deck submissions (R66 Ready To Swipe)

The top of the Portfolio dashboard shows the **Ready To Swipe** shelf (kit `deck-shelf.js?v=2`) from `shelf.json`:
up to 5 ready 20-card decks plus any pinned unfinished decks (`pinned`, synced from `data.json` decks by `build.py`), 5 total max.
Agent id is `portfolio` (must match the submit agent so swipe counts show).

## After a deck is submitted
1. Save the results and run `carry_over.py record` as usual.
2. Refill the slot with a fresh 20-card deck on the same topic:
   ```
   python3 /workspace/style-swipe/tools/ready_shelf.py refill <deck_id> --shelf /workspace/ops/folio/dashboard/shelf.json --agent portfolio
   ```
   (Sources for refills are remembered per deck: `shelf-sources/*.json`. Thumbnail source regenerates with `shelf-sources/build_thumbnail_source.py`.)
3. Commit + push style-swipe (new deck, page, `banks/used.json`, `decks/pages.json`), then run `./update.sh` here to publish `shelf.json`.

No financial figures on any card or on the public page. Descriptive deck names only (no numbers).
