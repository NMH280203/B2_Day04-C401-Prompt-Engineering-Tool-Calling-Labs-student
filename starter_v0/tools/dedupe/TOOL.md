---
name: dedupe
track: core
kind: local_formatter
requires_env: []
inputs: [items, by]
outputs: [items, input_count, output_count]
side_effect: false
---

# dedupe

Remove duplicate items from a list of research results (same URL or same title).
Use after lookup/fetch/social_search when the user asks to remove duplicates before formatting.
