# Client document sources

The JSON files are the layout content for the current a365-toolkit executive brief and
one-pager. Editable Markdown companions are in the parent docs directory. Keep both
representations aligned when revising claims. PDFs contain vector text, not generated art.

To regenerate on macOS with Swift/AppKit:

```sh
swift scripts/render-briefs.swift a365-toolkit-executive-brief
swift scripts/render-briefs.swift a365-toolkit-one-pager
```

The renderer overwrites the corresponding PDFs under docs/assets, checks for text
clipping, reports page counts and writes layout previews under /tmp. Legacy a365-pilot
PDFs and the infographic are historical assets; README links to the current toolkit PDFs.
