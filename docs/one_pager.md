# CNull: Directionality Sanity Check

**Claim.** If there is *real, directed information flow* from A to B that matters for B's next state, an intervention that selectively enables this channel (ON) should increase **TE(A→B)**, not **TE(B→A)**, relative to the OFF condition. ΔTE and Δz must separate ON vs OFF and scale with dose.

**Nulls.** (i) Circular shift: breaks alignment, preserves marginals. (ii) Block shuffle: preserves local structure, breaks long-range channel. z-scores are computed against both.

**Sanity.** A weak watermark embedded in A should only decode at B in ON.

**Pass.** ON: large positive Δz_block (and ΔTE), OFF: near zero; watermark ON≫OFF.
