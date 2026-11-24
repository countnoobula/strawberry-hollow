# Strawberry Hollow · Art direction

## A woodland at ChibiRunner’s scale

A clover beside the dirt path should look thick enough to turn between your fingers. Give each leaflet a cushioned heart shape, a shallow fold where it meets the stem, and a rim that catches a sliver of afternoon light. A turned leaf should show a different face from its neighbour. This is the quality we like in LittleBigPlanet’s physical sets, translated into living plants, stone, soil and bark. Knitting, felt weave, stitched seams and button props fall outside the botanical direction.

[First clover-bank concept study](SourceArt/ConceptArt/Moodboard/Clover%20Bank%20Study%2001.png)

## Shape, light and movement

| Element | Working direction | What to look for in the first Unreal sample |
| --- | --- | --- |
| Grass and clover | Build a few broad blades with a curved cross-section, rounded edges and a gentle taper. Curl the tips by different amounts. Let a few stems turn sideways so their thickness reads from the path. | At runner height, individual silhouettes stay soft and distinct. A grazing camera angle still shows a rim. |
| Ground and props | Let moss cover the undisturbed bank and curl over stone edges. Worn dirt shows through along the tread. Nest rounded pebbles and amber mushrooms into the ground. | Overlaps cast small shadows. The path edge and the next landing can be picked out at a glance. |
| Leaf surface | Use a shallow central vein and a smooth change in sheen across the fold. Reserve fine branching veins for close inspection. | In side light, the fold catches one broad highlight. Backlighting brings out the thinner edge. Shaded leaves keep their deeper green. |
| Wind | Anchor the roots and most of the blade. Allow the tips a small, slow bend, with slightly different timing between clumps. | In a still camera shot the motion becomes apparent over a few seconds. During a jump the landing silhouette stays steady. |
| Camera | Use selective focus to suggest a tabletop set. Focus on the path edge for a study and on the takeoff and landing area during play. | Nearby leaves can soften at the frame edge. ChibiRunner and the next usable cap stay easy to judge during a jump. |

## First Unreal material and camera trial

Use **Two Sided Foliage** for the grass and clover trial. Compare **Subsurface** on a solid modeled leaf if the underside needs a different response. Start with roughness **0.65** and specular **0.4**. Explore **0.55–0.75** and **0.35–0.5** respectively under fixed lighting. Feed a saturated yellow-green into Subsurface Color and tune the strength against a leaf in shade. Keep the normal map gentle enough that the modeled fold does most of the work.

For upright grass, start with vertex normals pointing up in the authored mesh, **(0, 0, 1)**. Compare this with normals blended toward up on a curled blade. Use the version that gives a soft, continuous clump while preserving the rim and the curl in side light. Model leaf thickness into the silhouette.

For a **Cine Camera** still, start at **f/2.8**, set the focus distance on the middle clover, and compare **f/1.8** at the same framing. Judge foreground softness and far-bank separation. Test the playable camera separately with a moving runner. These values are starting points for the trial.

## Decision log and next check-in

- **2026-11-24 · Direction supplied.** Chunky botanical forms, tapered curls, subtle wind, warm transmitted light and a miniature sense of scale.
- **2026-11-24 · Clover approved.** Keep the thickness shown in Study 01. Carry the rounded rim and shallow fold through to gameplay scale. Give grass a softer satin highlight.
- **First Unreal sample.** The near bank just beside the first mushroom has five-stem clover clusters at two sizes and two tufts of three curled grass blades. Both meshes have thickness. The clover uses a subtle vein texture, roughness 0.61 and specular 0.40. Grass uses roughness 0.72 and specular 0.35. Both materials use Two Sided Foliage and a slow 5.6-second bend weighted toward the tips.
- **Open for review.** Inspect the three-leaf silhouette beside ChibiRunner, the grass highlight in motion, and the space between the clump and the landing. The eye-height capture uses the runtime pawn's eye position. The scale view shows the character beside the same patch.

[Eye-height view](SourceArt/LayoutReview/clover_pawn_eye.jpg) · [Character scale](SourceArt/LayoutReview/clover_character.jpg) · [Idle and crossing playtest](SourceArt/LayoutReview/clover-bank-playtest.mp4)


<details><summary>Study 01 generation prompt · built-in ImageGen</summary>

A close-up 3D art-direction still of one path edge in ChibiRunner’s Fairy Grotto, at a tiny runner’s eye height. Focus on a handful of plump heart-shaped clover leaflets and a clump of broad grass blades. Each blade has visible thickness along the rim, a shallow central fold and a tapered, gently hooked tip. A turned leaf shows its underside. Subtle organic veins, broad waxy highlights, rich lime transmission where late-afternoon sunlight passes through a leaf, deep cool contact shadows between overlapping leaves. Moss wraps a rounded pebble and gives way to worn earth. The creek and an amber mushroom landing recede into soft focus. A hand-arranged miniature woodland with living botanical surfaces. Keep the path edge and nearest landing legible. Landscape framing. No lettering, UI, knit, stitching, fabric weave or plastic toy shine.

</details>
