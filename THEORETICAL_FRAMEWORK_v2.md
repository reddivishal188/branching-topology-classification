# Theoretical Framework, Falsifiable Predictions, and Research Hypothesis — REVISED

**Project:** Topological Signatures of Network Formation Mechanisms  
**Date:** July 9, 2026 (Revised)  
**Status:** Pre-implementation — theoretical foundation only  

---

## Preamble: What Changed in This Revision

The previous version of this document made an implicit assumption: that Transport, Dissipation, and Aggregation are three distinct topological classes waiting to be discovered. This version removes that assumption. It treats cluster formation as the experimental outcome, not the premise. It also strengthens the causal chain from physics to topology, replaces numerical predictions with directional ones, and includes a thorough self-critique. Every section now includes explicit falsification conditions.

---

## 1. The Central Question

> Does branching network topology contain sufficient information to identify the physical optimization principle that generated it, or do universal geometric constraints dominate across fundamentally different natural systems?

This is an **inverse problem**: given a network's topology, can we recover the physics that created it? The question is not "are these systems different?" — that is a descriptive comparison. The question is "does topology encode physics?" — that is a fundamental scientific inquiry.

### 1.1 Primary Hypothesis (H₁)

Governing optimization principles impose directional constraints on local growth rules. These constraints propagate upward through the formation process and leave measurable signatures in the resulting network topology. Consequently, networks formed under distinct optimization principles occupy statistically separable regions in topological feature space, even after controlling for scale and boundary conditions.

### 1.2 Null Hypothesis (H₀)

After controlling for network size, resolution, and domain-specific geometry, branching topology is dominated by universal constraints (planarity, space-filling, connectedness) rather than formation-specific physics. Networks from different formation mechanisms are topologically indistinguishable — any apparent differences arise from measurement artifacts, size mismatches, or boundary condition variation, not from the governing physics.

### 1.3 The Experimental Test

We compute a suite of topological descriptors across five branching networks formed by physically distinct processes. We ask: do the networks separate in feature space in a way that corresponds to their governing physics? The outcome is not assumed — it is discovered.

**Possible outcomes:**
1. **Strong separation:** Networks form discrete clusters by physics class → supports H₁
2. **Partial separation:** Some features discriminate, others don't → supports H₁ with nuance
3. **Continuum:** Networks arrange along a spectrum, not discrete clusters → supports neither H₁ nor H₀ cleanly (interesting!)
4. **No separation:** After normalization, all networks overlap → supports H₀
5. **Separation by domain, not physics:** Retina and leaf cluster together, but so do river and DLA → formation mechanism is not the driving factor

All five outcomes are publishable. The paper's value lies not in which outcome occurs, but in the rigorous testing of a fundamental question.

---

## 2. The Causal Chain: Why Topology Should (or Should Not) Encode Physics

This is the philosophical backbone of the paper. The argument is not that topology *must* encode physics — it is that there is a plausible causal pathway, and we test whether that pathway is strong enough to survive real-world noise and confounding factors.

### 2.1 The Chain

```
Physical Laws (conservation of energy, mass, momentum)
    ↓
Governing Optimization Principle (minimize work, maximize dissipation, or no optimization)
    ↓
Local Growth Rules (branch at angle θ, follow gradient ∇φ, or stick on contact)
    ↓
Branch Formation Events (bifurcation at (x,y), crack propagation direction, particle adhesion)
    ↓
Aggregate Architecture (tree topology, mesh topology, fractal cluster)
    ↓
Graph Representation (nodes = junctions, edges = segments, paths = connectivity)
    ↓
Topological Descriptors (assortativity, cyclomatic number, degree distribution, persistence)
```

At each step, information can be **preserved, distorted, or lost**. The experiment tests whether enough information survives to allow inference.

### 2.2 Step-by-Step Analysis

**Link 1: Physical Laws → Optimization Principle**

Physical laws define what is possible. Conservation laws constrain growth. The optimization principle selects among possible configurations:

- **Transport systems:** Conservation of mass + energy minimization → Murray's Law branching. The law is a consequence of calculus of variations applied to a flow network with fixed material budget.
- **Fracture systems:** Energy conservation + Griffith's criterion → cracks follow path of maximum energy release rate. The path is determined by stress field geometry and material heterogeneity.
- **DLA systems:** Conservation of particle number + no optimization → growth follows the harmonic measure. The structure is a random fractal, not an optimal configuration.

*Information preserved at this step:* Yes — the optimization principle fundamentally constrains which configurations are allowed. The constraint is strong in transport, moderate in fracture, absent in DLA.
*Information lost at this step:* Boundary conditions (domain shape, seed location) are not determined by the optimization principle. A river on a slope and a river on a plain share the same physics but different boundaries.

**Link 2: Optimization Principle → Local Growth Rules**

The optimization principle is a global statement. It must be instantiated through local rules:

- **Transport:** Vessels grow along VEGF gradients (retina) or along erosion gradients (rivers). The local rule is "grow in direction of steepest gradient of signaling molecule or shear stress." This naturally produces bifurcations when the gradient splits.
- **Fracture:** Cracks advance in the direction of maximum stress intensity. The local rule is "break the next material element that exceeds strength threshold." Intersections occur when two approaching cracks' stress fields overlap.
- **DLA:** Particles execute random walks. The local rule is "stick to the cluster on first contact." There is no directionality — growth is isotropic on average.

*Information preserved:* The local rules differ fundamentally: directed gradient-following (transport) vs. path-of-least-resistance (fracture) vs. isotropic random (DLA).
*Information lost:** Material heterogeneity introduces noise at this step. In concrete, random aggregate locations deflect cracks. In DLA, the random number seed changes the cluster. This noise is a confound we must control for.

**Link 3: Local Growth Rules → Branch Formation**

Each local rule produces characteristic branching patterns:

| Rule | Branch Type | Junction Angle | Frequency |
|---|---|---|---|
| Gradient-following (transport) | Y-shaped bifurcation | ~30-90° (constrained by optimization) | Regular, hierarchical |
| Stress-field propagation (fracture) | X-shaped intersection | Variable (determined by stress field) | Random, stress-dependent |
| Random walker accretion (DLA) | Y-shaped bifurcation | Broad distribution | Irregular, side-branch dominated |

*Information preserved:* Junction type (Y vs X) is a strong signal — it directly reflects whether the growth rule produces bifurcations or intersections.
*Information lost:* Image resolution can merge nearby branches, converting Y-junctions into apparent X-junctions or vice versa. This must be validated.

**Link 4: Branch Formation → Aggregate Architecture**

Individual branches assemble into a global architecture:

- **Transport hierarchy:** Large vessels feed medium vessels feed small vessels. The result is a nested, hierarchical tree with power-law scaling of branch diameters and lengths.
- **Fracture mesh:** Cracks intersect to form polygonal cells. The result is a mesh-like network with loops at multiple scales.
- **DLA cluster:** Random branching with no hierarchy. The result is a fractal with characteristic dimension D_f ≈ 1.71 and minimal loop formation.

*Information preserved:* The hierarchical vs. mesh vs. fractal distinction is the coarsest topological feature and likely the most robust.
*Information lost:* Both transport and DLA produce tree-like structures. Distinguishing them requires finer measures (Horton ratios, degree distribution shape).

**Link 5: Aggregate Architecture → Graph Representation**

The continuous network is discretized into a graph. This step is necessary for computation but introduces potential artifacts:

- Skeletonization errors (spurs, false connections)
- Junction detection errors (missed bifurcations, false positives)
- Resolution limits (thin branches become disconnected)

*Information preserved:* If skeletonization is accurate (validated against ground truth), the graph preserves the network's topology.
*Information lost:* This is the most dangerous step. A 5% error in skeletonization can produce 50% change in cyclomatic number. We must quantify this through synthetic data validation.

**Link 6: Graph Representation → Topological Descriptors**

The graph is reduced to numerical descriptors. Each descriptor integrates over local structure to produce a global summary:

- Assortativity integrates degree correlations across all edges
- Cyclomatic number counts independent cycles
- Degree distribution summarizes branch point statistics
- Persistence diagrams encode multi-scale loop structure

*Information preserved:* Descriptors are designed to be summary statistics. They preserve the information we want at the cost of discarding spatial detail.
*Information lost:* Two graphs with identical degree distributions can have completely different spatial arrangements (graph isomorphism problem). This is a fundamental limitation — topology alone cannot distinguish spatial embedding.

### 2.3 Where the Chain Could Break

The causal chain is plausible but not guaranteed. It could break at any point:

| Link | Breakage Mode | Severity |
|---|---|---|
| Laws → Optimization | Boundary conditions override physics | High |
| Optimization → Rules | Material noise swamps signal | High |
| Rules → Branches | Resolution merges distinct patterns | Medium |
| Branches → Architecture | Different rules produce same architecture | Critical |
| Architecture → Graph | Skeletonization introduces errors | High |
| Graph → Descriptors | Descriptors are not discriminative enough | Medium |

**The experiment tests whether the chain holds despite these risks.**

---

## 3. Systems and Their Physics

### 3.1 Retinal Vascular Network

**Process:** Angiogenesis driven by VEGF diffusion from hypoxic tissue. Endothelial cells migrate up the VEGF gradient, form tubes, and remodel under shear stress. The developmental program is genetically encoded but responds to local metabolic demand.

**Governing principle:** Minimize total power dissipation for nutrient delivery, subject to material cost constraint. This is equivalent to solving a constrained optimization problem where the objective function is the sum of viscous dissipation over all vessels plus a Lagrange multiplier times total vessel volume. The solution is Murray's law at each bifurcation.

**Predicted topological signatures (directional, not numerical):**
- Higher assortativity than fracture or DLA (hierarchical organization)
- Higher proportion of degree-3 nodes than degree-4 nodes (bifurcations dominate)
- Horton-Strahler bifurcation ratio higher than random branching (R_b > ~2)
- Narrower tortuosity distribution than fracture or DLA (smooth, optimized paths)
- Lower cyclomatic number than fracture (fewer loops)

**Falsification conditions:**
- Assortativity is statistically indistinguishable from fracture or DLA
- Degree-4 nodes outnumber degree-3 nodes
- Horton ratio ≈ 2 (random branching)
- Tortuosity distribution matches DLA (random paths)

### 3.2 Concrete Crack Network

**Process:** Cracks initiate when tensile stress exceeds material strength. They propagate when the stress intensity factor K_I exceeds fracture toughness K_IC. In heterogeneous concrete, cracks follow the path of least fracture resistance, deflecting around aggregates. Intersecting cracks form when their stress fields overlap.

**Governing principle:** The crack advances along the direction of maximum energy release rate (equivalently, minimum local fracture resistance). There is no global optimization — each propagation step is locally determined by the stress field and material heterogeneity. The resulting network maximizes total energy dissipated, but this is a consequence, not a goal.

**Predicted topological signatures (directional):**
- Lower assortativity than transport networks (no hierarchy)
- Higher proportion of degree-4 nodes than transport (intersections common)
- Higher cyclomatic number than transport or DLA (loops from intersecting cracks)
- Horton-Strahler ratio near 2 (no hierarchical organization)
- Power-law edge length distribution (characteristic of fragmentation)
- Higher tortuosity than transport (crack deflection)

**Falsification conditions:**
- Assortativity > 0.3 (hierarchical organization present)
- Degree-4 nodes are rare (cracks rarely intersect)
- Cyclomatic number is zero (no loops — isolated cracks)
- Horton ratio > 3 (hierarchical branching)

### 3.3 Diffusion-Limited Aggregation (DLA)

**Process:** Random walkers released from a boundary stick to the growing cluster on first contact. Growth probability at the interface is proportional to the harmonic measure (gradient of the Laplacian field). There is no optimization — the structure is a statistical fractal.

**Governing principle:** No optimization. Growth is purely stochastic. The only constraint is that the growth probability satisfies Laplace's equation with a moving boundary. This produces a fractal with no characteristic length scale and a specific fractal dimension.

**Predicted topological signatures (directional):**
- Lower assortativity than transport (no hierarchy)
- Lower cyclomatic number than fracture (DLA is nearly tree-like)
- Degree-3 dominated (bifurcations from side-branching)
- Horton-Strahler ratio near 2 (random branching)
- Characteristic fractal dimension D_f ≈ 1.71 (if measurable from graph)
- Broadest tortuosity distribution (random walk paths)

**Falsification conditions:**
- Assortativity > 0.3 (hierarchy present)
- Cyclomatic number > fracture (loops present)
- Horton ratio > 3 (hierarchical branching)

### 3.4 River Networks

**Process:** Erosion by water flow concentrates into channels. The network evolves over geological time toward a configuration that minimizes total energy dissipation in the drainage basin.

**Governing principle:** Optimal Channel Network (OCN) — minimize sum of A_i^γ L_i over all channels, where A_i is drainage area and L_i is channel length. This is the same mathematical structure as transport optimization in blood vessels but with different exponents and physical constraints (erosion vs. viscous flow).

**Predicted topological signatures:**
- Similar to retinal in many respects (both transport-optimized)
- Very low cyclomatic number (rivers are nearly tree-like; braided reaches are an exception)
- Horton-Strahler ratio R_b ≈ 3-5 (classic signature of OCN)
- Similar assortativity to retinal (hierarchical)

**Falsification conditions:**
- Horton ratio ≈ 2 (not an OCN)
- Cyclomatic number comparable to fracture (too many loops)
- Assortativity near zero (no hierarchy)

### 3.5 Leaf Venation

**Process:** Auxin canalization — auxin transport through developing leaf tissue concentrates into channels, which differentiate into veins. Positive feedback amplifies initial fluctuations. The network also remodels under hydraulic and mechanical constraints.

**Governing principle:** Same as retinal — minimize hydraulic resistance for water transport subject to material cost. However, leaves have an additional constraint: mechanical support and damage tolerance, producing the characteristic areole (loop) structure.

**Predicted topological signatures:**
- Similar to retinal (both transport-optimized)
- Distinct persistence H₁ signature: bimodal loop size distribution (small areoles + large primary veins)
- Moderate assortativity, potentially lower than retinal due to reticulate structure
- High degree-3 proportion

**Falsification conditions:**
- H₁ persistence is unimodal (no distinct scale separation)
- Assortativity near zero
- Degree-4 nodes outnumber degree-3

---

## 4. Summary of Directional Predictions

The table below shows predicted **relative ordering**, not numerical values. The experiment tests whether these relative patterns hold across systems.

| Feature | Transport (Retina) | Transport (River) | Transport (Leaf) | Dissipation (Concrete) | Aggregation (DLA) |
|---|---|---|---|---|---|
| Assortativity | High | High | Mod-High | Low | Low |
| Cyclomatic/edge | Mod | Very Low | Mod-High | High | Low |
| Degree-3 / Degree-4 ratio | High | High | High | Low | Moderate |
| Horton R_b | >2 | >2 | >2 | ~2 | ~2 |
| Tortuosity | Low | Low | Low | Moderate | High |
| Clustering | Moderate | Low | Moderate | Low | Very Low |

**Note:** If river and retinal cluster together despite different materials and scales, that supports the hypothesis that transport optimization leaves a common topological signature. If they separate, it suggests domain-specific factors dominate over physics.

---

## 5. Justification of Descriptors

### 5.1 Why Assortativity Should Respond to Physics

Assortativity measures the correlation between the degrees of connected nodes. In hierarchical transport networks, the branching structure naturally produces degree correlations: a high-degree root vessel connects to medium-degree sub-branches, which connect to low-degree terminal branches. This correlation is a direct consequence of the optimization principle — the network must efficiently transport flow from a single source to many sinks, which requires organized hierarchy. In fracture networks, cracks are independent — a large crack is equally likely to intersect another large crack or a small crack. In DLA, the tree is also un-hierarchical.

**Caveat:** Assortativity is sensitive to graph size. Small graphs have unreliable assortativity estimates. This must be controlled by subsampling.

### 5.2 Why Cyclomatic Number Should Respond to Physics

The cyclomatic number counts independent cycles. Transport optimization favors trees (no cycles) because loops waste material without contributing to transport. However, real transport networks include loops for robustness against damage, producing intermediate cyclomatic numbers. Fracture networks naturally form loops when cracks intersect — the stress field creates polygonal cells. DLA rarely forms loops because random walkers do not produce intersecting trajectories.

**Caveat:** Image segmentation can merge nearby branches into apparent loops (pseudo-loops). Skeletonization quality must be validated for each system.

### 5.3 Why Degree Distribution Should Respond to Physics

Degree-3 nodes are bifurcations (Y-shaped), natural for branching transport and random trees. Degree-4 nodes are intersections (X-shaped), natural for crossing cracks. The ratio of degree-3 to degree-4 nodes directly reports whether the network grows by branching or by intersection.

**Caveat:** In pixel-based skeletonization, a bifurcation and an intersection can appear similar at coarse resolution. Validation against ground truth is essential.

### 5.4 Why Horton-Strahler Ratios Should Respond to Physics

Horton-Strahler ordering classifies branches by their position in the hierarchy. The bifurcation ratio R_b measures how many sub-branches feed into each parent branch. Optimal Channel Networks converge to R_b ≈ 3-5. Random branching (uncorrelated) produces R_b ≈ 2. The ratio distinguishes optimized transport from un-optimized growth.

**Caveat:** Horton-Strahler ordering requires a rooted tree. Fracture networks and DLA clusters may not have a clear root. We may need to compute R_b on the largest connected component after artificially rooting at the highest-degree node, which introduces bias.

### 5.5 Why Persistent Homology H₁ Should Respond to Physics

Persistent homology computes the full distribution of loop sizes, not just a single count. Transport networks should have loops at specific scales (capillary size, areole size). Fracture networks should have loops at all scales (power-law). The persistence diagram captures this multi-scale information that single numbers miss.

**Caveat:** PH is computationally expensive for large graphs. Subsampling reduces this but discards information. The choice of filtration function (distance from root? radial distance?) can strongly affect results and must be justified.

### 5.6 Why Tortuosity Should Respond to Physics

Tortuosity (path length / straight-line distance) measures how much a branch deviates from a straight line. Transport optimization favors straight paths (lower energy). Crack paths are deflected by material heterogeneities. DLA random walks are highly tortuous.

**Caveat:** Tortuosity is scale-dependent — a tortuous path at one resolution may appear straight at another. Resolution standardization is required.

---

## 6. Potential Confounds and Their Mitigation

### 6.1 Confound: Image Resolution Differences

Retinal images: 565×584 to 3504×2336 pixels. Crack images: 1920×1080 pixels. Different resolutions could create artificial differences in graph size and topology.

**Mitigation:** Resize all images to a common resolution before processing. Subsample graphs to matched node counts for feature computation. Test sensitivity by processing the same image at multiple resolutions.

### 6.2 Confound: Segmentation Quality Variations

Retinal vessel segmentation is a mature field with high-quality ground truth. Concrete crack segmentation is less standardized. Differences in segmentation quality could create artificial topological differences.

**Mitigation:** Validate graph extraction against manual annotations for each system. Report skeletonization accuracy metrics. Include synthetic data with known ground truth as a positive control.

### 6.3 Confund: Boundary Condition Variations

Retinal networks have a centralized inlet (optic disc) and grow outward. Concrete cracks have no preferred inlet. River networks have distributed inlets (precipitation). These boundary condition differences could dominate over formation physics.

**Mitigation:** Test for boundary condition effects by analyzing sub-regions of large images. If central-to-peripheral topology gradient exists in retina but not in cracks, that is a real physical difference, not a confound.

### 6.4 Confound: Equifinality

Different formation mechanisms could converge to identical topologies. For example, a transport-optimized tree and a random tree can have similar degree distributions and Horton ratios.

**Mitigation:** Use multiple complementary descriptors — no single descriptor is sufficient. Persistent homology adds multi-scale information that single-scale descriptors miss.

---

## 7. Aggressive Self-Critique (Reviewer #2)

I will now attempt to destroy the hypothesis. This is not polite. It is necessary.

### 7.1 "Why should topology remember physics? The causal chain is too long."

**Argument:** Six links connect physics to topology. At each link, information is lost. Noise at any single link could destroy the signal. By the time we reach topological descriptors, the physical signal could be vanishingly small compared to noise from segmentation, resolution, and boundary conditions.

**Response:** This is a legitimate concern. The experiment is designed to detect whether any signal survives. If it does not, we report H₀. The paper's value does not depend on a positive result.

**Confidence this criticism is valid:** 70%. The causal chain is long, and each link is lossy.

### 7.2 "Boundary conditions dominate over physics."

**Argument:** A river on a steep mountain slope looks completely different from a river on a flat floodplain, despite identical physics. A concrete crack in a uniaxial stress field looks different from a crack in isotropic drying shrinkage. Boundary conditions may determine topology more than formation physics.

**Response:** We mitigate this by including multiple systems within each physics class (retina + river + leaf for transport; only concrete for dissipation; DLA for aggregation). If river and retinal cluster together despite different boundary conditions (centralized inlet vs. distributed drainage), that supports physics over boundaries. If they separate, boundary conditions may dominate.

**Confidence this criticism is valid:** 60%. This is a real threat that the multi-system design partially addresses.

### 7.3 "Image processing creates artificial differences."

**Argument:** The pipeline applies identical processing to all systems, but optimal parameters differ. Retinal vessel segmentation works well with one threshold, crack segmentation with another. Choosing parameters that work for all systems guarantees suboptimal performance for each, potentially creating artifacts.

**Response:** We use ground truth segmentations (human-annotated) rather than algorithmic segmentation. This removes the parameter selection problem. However, ground truth quality varies across datasets.

**Confidence this criticism is valid:** 40%. Using expert annotations mitigates this, but annotation quality is uneven.

### 7.4 "Graph extraction destroys important information."

**Argument:** Converting a continuous branching network to a graph discards geometry (curvature, width, taper). These geometric features may contain more physical information than topology alone.

**Response:** This is true. Our approach privileges topology over geometry by design. The question is whether topology alone is sufficient. If not, the negative result is still informative — it tells the community that geometry is necessary.

**Confidence this criticism is valid:** 50%. Topology is a subset of the available information. The experiment tests whether that subset is sufficient.

### 7.5 "Different physics can produce identical topology."

**Argument:** A transport tree and a random tree can have identical degree distributions, Horton ratios, and assortativity. The only difference is in the spatial arrangement of branches (optimal vs. random), which topological descriptors may not capture.

**Response:** This is the equifinality problem. We use multiple descriptors (including persistence homology, which captures spatial scale information) to maximize discriminative power. If equifinality dominates, H₀ cannot be rejected.

**Confidence this criticism is valid:** 55%. Equifinality is a real concern that may limit the conclusions we can draw.

### 7.6 "The sample size is too small for reliable conclusions."

**Argument:** With ~50-70 images per system and 15-18 features, the feature-to-sample ratio is ~0.3. This makes overfitting likely in classification. Statistical significance may be inflated by multiple comparisons.

**Response:** We use Bonferroni correction (α adjusted to 0.05/n_features ≈ 0.003) and nested cross-validation. These conservative procedures reduce overfitting risk but increase the chance of Type II error (missing a real effect).

**Confidence this criticism is valid:** 35%. Our statistical procedures are standard, but the sample size is modest.

### 7.7 Summary of Self-Critique

| Criticism | Validity | Fatal? | Mitigation |
|---|---|---|---|
| Causal chain too long | High | No | Negative result is still publishable |
| Boundary conditions dominate | Moderate | Potentially | Multi-system comparison helps |
| Image processing artifacts | Low-Moderate | No | Expert annotations |
| Graph extraction discards information | Moderate | No | Defensible by design |
| Equifinality (same topology, different physics) | Moderate | Potentially | Multiple descriptors, PH |
| Small sample size | Low | No | Bonferroni, nested CV |

**Overall assessment:** The hypothesis is plausible but faces real threats. The experimental design mitigates these threats partially, not completely. The project is worth pursuing because either outcome (H₁ or H₀) is publishable and informative.

---

## 8. Complete Prediction Summary

| # | Prediction | Test | Systems | Falsified By |
|---|---|---|---|---|
| 1 | Transport networks (retina, river, leaf) cluster together | PCA + classification | All 5 | Retina and river separate in PCA |
| 2 | Assortativity: transport > fracture > DLA | Mann-Whitney U | All 5 | Any transport system has assortativity ≈ fracture |
| 3 | Cyclomatic/edge: fracture > transport > DLA | Mann-Whitney U | All 5 | Fracture has cyclomatic ≈ transport |
| 4 | Degree-3/4 ratio: transport > DLA > fracture | χ² test | All 5 | Transport has significant degree-4 nodes |
| 5 | Horton R_b: transport > 2, fracture ≈ DLA ≈ 2 | One-sample t-test | All 5 | Transport R_b ≈ 2 |
| 6 | H₁ persistence: fracture power-law, transport peaked | Distribution comparison | All 5 | Fracture persistence ≈ transport |

---

## 9. Next Steps (After Framework Approval)

Only after this framework is approved will we proceed to:

1. **Generate DLA clusters** computationally (existing code, 10 min)
2. **Download river network data** from public DEM sources
3. **Extract leaf venation graphs** from public dataset
4. **Run pipeline** on 5 systems
5. **Test each directional prediction** against real data
6. **Report outcome honestly** — regardless of which hypothesis survives

---

*This document defines the complete theoretical foundation. No code has been written. No dataset has been downloaded. Implementation begins only upon approval.*
