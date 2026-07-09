# Scientific Story — One Page

## 1. What problem exists?

Branching networks appear everywhere — blood vessels, leaf veins, river deltas, concrete cracks, lightning, lungs. They look similar. For decades, scientists have asked whether this similarity reflects a deeper mathematical unity or is just a coincidence. The standard answer has been fractal dimension. But fractal dimension collapses a complex network into a single number — it cannot distinguish a hierarchical tree from a random mesh from a fractal cluster if their dimensions happen to overlap. We need richer descriptors to compare branching networks meaningfully.

## 2. Why has nobody solved it?

Most studies compare two systems at a time using different methods — making true cross-comparison impossible. A river paper uses Horton-Strahler ordering. A leaf paper uses fractal dimension. A crack paper uses something else. When methods differ, you cannot tell whether observed differences are real or methodological. What has been missing is a unified pipeline applied to multiple systems simultaneously, computing identical descriptors from identical preprocessing.

## 3. Why does it matter?

At stake is a fundamental question: do the physical laws that govern growth leave a measurable fingerprint in the topology of the resulting network? If yes, then topology becomes a tool for inferring physics from structure — with applications from medical imaging to materials science. If no, then branching network topology is dominated by universal geometric constraints, and formation physics is invisible to topological analysis. Either answer advances our understanding.

## 4. What did we actually do?

We built one pipeline. We applied it identically to four branching systems: retinal vasculature (transport, centrifugal), leaf venation (transport, centripetal), concrete crack networks (stress dissipation), and diffusion-limited aggregation (stochastic growth). For each network, we computed degree distribution, assortativity, cyclomatic ratio, and clustering. We compared them statistically.

## 5. What did we actually discover?

Two transport-optimized systems — retina and leaf — have opposite hierarchical organization. Retina is assortative (+0.31). Leaf is disassortative (−0.35). This means optimization principle alone does not determine topology. The proportion of bifurcation points (degree-3 nodes) partially follows physical expectations: retina highest, DLA intermediate, leaf moderate, crack lowest. But leaf falls below DLA despite being a transport system. The fraction of loops (cyclomatic ratio) is nearly constant across all systems — it appears geometrically constrained, not physically informative.

## 6. Why is that discovery important?

Because it refines the question. The answer is not "topology encodes physics" or "topology does not encode physics." The answer is: **some topological features encode physics, some encode geometry, and some are system-specific.** Which feature tells you what depends on what aspect of formation you are looking at. Degree distribution partially reflects optimization. Assortativity reflects source-sink geometry. Cyclomatic ratio reflects planar embedding constraints. This is a more nuanced picture than either a universal law or complete randomness.

## 7. What remains unknown?

We have identified three candidate factors that may jointly determine topology — optimization principle, source-sink geometry, and growth modality — but we have not proven any causal relationship because in natural systems, all three factors vary simultaneously. The critical next step is a controlled generative experiment where one factor is varied while the others are held constant. Our attempt at such an experiment failed because the generative model was too simplistic. A proper implementation of transport optimization (e.g., Constrained Constructive Optimization) could provide the causal evidence needed to confirm or reject the three-axis hypothesis. That is the next paper.
