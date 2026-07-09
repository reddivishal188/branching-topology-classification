# Revision Plan — Reviewer #2 Response

## Priority 1: Structural Changes (can do now, no experiments needed)

| Issue | Fix | Impact |
|---|---|---|
| Two papers fighting each other | Reframe Introduction to foreground comparative topology. Three-axis becomes Discussion-only artifact, not the paper's central claim. Title change: remove "Three Axes" framing. | High |
| Three-axis framework over-dominates | Move to a boxed subsection titled "A Working Interpretive Framework (Hypothesis)" in Discussion, with explicit disclaimer | High |
| "Partially consistent with predictions from formation physics" | Change to "partially consistent with our predictions, which were derived from consideration of formation physics" | Medium |
| Results contains interpretation (source-sink geometry) | Move all source-sink discussion to Discussion section. Results stays observational. | High |
| Conclusion overgeneralizes | Change "optimization principle alone is insufficient to determine topological organization" to "within the systems analyzed" | High |
| No effect size interpretation | Add Cohen's d interpretation (small/medium/large) to Results | Medium |
| AI language patterns | Reduce "consistent with," "however," "this indicates," "we propose," "natural candidate," "jointly constrained," "interpretive hypothesis" repetition | Medium |

## Priority 2: Analyses That Require Running Code (can do in 1-2 hours)

| Issue | Fix | Time |
|---|---|---|
| DLA sample size too small (n=15) | Generate 30 more DLA clusters → n=45 total | 15 min |
| No size correlation analysis | Compute correlation between n_nodes and each normalized descriptor within each group | 10 min |
| No pairwise statistical tests | Run Mann-Whitney U + Cohen's d for all descriptor pairs across all groups | 10 min |
| No PCA/UMAP visualization | Generate 2D projection of all 4 systems in feature space | 10 min |
| No correlation matrix | Generate heatmap of descriptor correlations | 5 min |
| No pipeline figure | Generate pipeline schematic | 20 min |
| Synthetic experiment failure analysis | Expand in Discussion — add subsection "4.4 Why the Controlled Experiment Failed" | Text only |

## Priority 3: Validation That Requires Manual Work (1-2 days)

| Issue | Fix | Time |
|---|---|---|
| Graph extraction validation | Compare extracted junction counts to hand-counted on 20 images per dataset | ~4 hours |
| Sensitivity analysis | Test alternate skeletonization, threshold values, resolution | ~2 hours |
| Multi-resolution downsampling | Process retina at 3 resolutions to quantify resolution effects | ~1 hour |
| Additional systems | Add river or cerebral vasculature data | 1-2 days |

## Revised Implementation Order

Phase A (now, text changes):
- Reframe Introduction
- Move three-axis to boxed subsection
- Fix all overclaims
- Fix AI language
- Expand synthetic experiment failure analysis
- Add effect size interpretation

Phase B (run code, 1-2 hours):
- Generate 30+ DLA clusters
- Size correlation analysis
- Pairwise statistical tests
- PCA/UMAP visualization
- Correlation matrix heatmap
- Pipeline schematic figure

Phase C (after Phase B, update manuscript):
- Insert new results from Phase B
- Update tables and figures
- Re-check all claims against new data

Phase D (validation, before submission):
- Graph extraction validation (manual)
- Sensitivity analysis
- Final proofread
