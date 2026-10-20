# Known limitations (2026-10-19)

Geeza is a hackathon demo with invented data and a fake vendor.

Fixed on 2026-10-19 and covered by offline tests (not verified on the live model route): the note filter now rejects more number formats, a non-YES reply now says it cancelled the waiting request, and a bill request with a second money request now says only the bill can be paid.

Still true:
- The note-saving filter is a simple rule and is not complete. Do not type real personal or financial numbers into the demo.
- The assistant handles one request at a time.
- The optional Clairic bill reader is off for public visitors and only appears in the demo video.
