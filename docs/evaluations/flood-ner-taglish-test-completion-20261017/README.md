# Flood NER Taglish Test Completion Evaluation (Round v5)
**Date:** 2026-10-17  
**Status:** Completed (Closed)  
**Compatible Witness Size:** 53 passages (30 English [27 pos + 3 neg], 23 Taglish [20 pos + 3 neg])  
**Target Coverage:** 60 passages (30 English [27 pos + 3 neg], 30 Taglish [27 pos + 3 neg])  
**Shortage:** Seven Taglish positive passages remain missing.

## Summary
Under explicit /goal authorization, bounded targeted collection round v5 was executed to search for operational Taglish flood reporting from approved publishers (GMA News Online) across historical non-overlapping windows (2017–2022). 

1. **Accounting Ledger & Budgets:**
   - 11 search queries were reserved and accounted for in journal.jsonl.
   - Raw identity occurrences were tracked from baseline 585 up to 649 cumulative raw identities (within the 700 ceiling; 47 slots remaining).
   - Publisher attempts remained at 84 (0 new requests dispatched; 16 attempts remaining under 100).
   - Collection is closed.

2. **Findings on Leads:**
   - Candidate articles from historical weather events (e.g. Typhoon Rosita 2018, Basyang 2018/2026, Shear Line 2022) were evaluated:
     - Promdi / Balitambayan Tagalog articles largely overlap with historical training/validation corpora or prior test exclusions.
     - English-language regional coverage from Northern Luzon or Mindanao contains complete six-class place entities but does not meet the operational Taglish requirement (Filipino clauses with untranslated English common/technical vocabulary).
   - Zero new admissible Taglish positive passages were added.

3. **Status:**
   - All 53 existing test witness members remain preserved and supported.
   - The seven-passage Taglish shortage remains unchanged.
   - All 6,750 protected repository files remain unchanged.
   - Training, test freezing, partition sealing, exports, and desktop GPU activation remain blocked until a fully qualified 60-passage dataset is complete.
