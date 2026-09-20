# Emergency Handling Spec

Fills the gap identified in the original architecture: emergency handling was
"call 911 + escalate to caregiver" with no offline capability, no structured
response, no "what to do while waiting."

Sources: Crisis Connect (emirhan-duman/Crisis-Connect) for the action layer,
JustInCase (companionintelligence/JustInCase) for the knowledge layer.

## Two layers

| Layer | Source | What it does | When |
|-------|--------|--------------|------|
| **Action** | Crisis Connect | SOS broadcast, emergency toolkit, offline maps, caregiver verification | Immediate need |
| **Knowledge** | JustInCase | Emergency medical/survival knowledge search, cited answers | Waiting for help, or uncertain what to do |

## Action layer (Crisis Connect patterns)

### SOS trigger

- 5-second countdown before activation (prevents accidental triggers)
- BLE broadcast to nearby devices running the app (no infrastructure needed)
- Simultaneous: call 911, notify caregiver, activate toolkit

### Emergency toolkit

| Tool | Purpose | Implementation |
|------|---------|--------------|
| Whistle | Audible location signal | Phone speaker, max volume, repeating pattern |
| Strobe | Visual location signal | Screen flash, high contrast, SOS pattern |
| Compass | Orientation | Device magnetometer |
| Signal finder | Best direction for cell signal | Signal strength gradient, guide user to walk |
| Offline maps | Navigation without network | Downloaded map tiles, GPS-only |

### Caregiver verification

- Role certificates: caregiver, family, neighbor, responder
- QR code pairing for trusted contacts (Crisis Connect pattern)
- SOS broadcast includes verification level so responders know who's who

## Knowledge layer (JustInCase patterns)

### Emergency knowledge search

- RAG over curated emergency PDFs (medical, survival, first aid)
- Hybrid search: vector + BM25 → reciprocal rank fusion
- Grounded answers with source citations
- Works entirely offline

### Content manifest

- `sources.yaml` — curated, verified, categorized documents
- Checksums and magic-byte verification for downloads
- Tiered profiles: core (~350MB), extended (~2GB), full (~20GB)
- Atomic writes, no partial downloads

### Categories

| Category | Examples | Priority |
|----------|----------|----------|
| Medical emergency | Heart attack, stroke, choking, bleeding | Critical |
| Medication | Interactions, missed dose, side effects | High |
| Fall / injury | Fractures, head injury, hip pain | High |
| Fire / evacuation | Escape routes, smoke inhalation | Critical |
| Weather / disaster | Tornado, flood, power outage | Medium |
| Utility failure | Gas leak, water main, electrical | Medium |

## Integration with Boosh architecture

```
User: "I fell and I can't get up"
  ↓
Intent router → emergency skill (bypasses confidence checks)
  ↓
Emergency module activates:
  ├─ Action layer: SOS countdown → 911 call + caregiver notify + toolkit
  └─ Knowledge layer: "What to do after a fall" → cited first-aid guidance
  ↓
If user conscious and able: knowledge layer provides guidance
If user unresponsive: action layer continues SOS, location sharing
```

## v1 scope

- SOS trigger with 5-sec countdown
- 911 call + caregiver notification
- Emergency toolkit (whistle, strobe, compass)
- Basic offline maps (single region)
- Core medical emergency knowledge (10-15 documents)

## v2 scope

- BLE mesh broadcast to nearby devices
- Full offline map packs
- Extended knowledge library
- Role certificates for responders
- Integration with Crisis Connect app (if installed)

## Dependencies

| Package | Purpose | Source |
|---------|---------|--------|
| `llama.cpp` | Local LLM for knowledge search | Already in stack |
| `sqlite-vec` | Vector search for RAG | New |
| `FTS5` | BM25 lexical search | Already in stack |
| Map tiles | Offline maps | OpenStreetMap, downloaded |

## Open questions

- [ ] Which emergency PDFs to curate for v1? (JustInCase sources.yaml is 115 docs — too many)
- [ ] BLE broadcast range on iPhone 16 Plus? (Crisis Connect claims ~100m)
- [ ] Offline map format? (MBTiles vs. vector tiles)
- [ ] Integration with Apple Emergency SOS? (iOS native feature, may conflict)