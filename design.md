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
- **Second Unreal sample · thicker edges.** The concept established the clover shape. After seeing the first patch at runner height, the user requested a fuller rim. The second mesh increases nominal leaflet body thickness from 11.6% to 16% of leaflet length, rounds the shoulder of the rim, and carries a thicker grass cross-section through the curl. The satin material settings carry over from the first sample. [Compare the two meshes at eye height](SourceArt/LayoutReview/clover-rim-comparison.jpg).
- **Fuller clover approved.** Use the second sample as the reference for leaflet thickness and rounded rims.
- **Grass width trial · open for review.** At mid-blade the three grass silhouettes are 43%, 56%, and 64% wider than the preceding sample. Each blade has a fuller cross-section and a slight turn through the curl, with the existing satin material. Review the broad rear blade and the arcing outer blade together at runner height. [Grass comparison](SourceArt/LayoutReview/grass-width-comparison.jpg).
- **Arching blade approved.** Use the outer, right-hand blade from the grass width trial as the grass shape reference.
- **Tuft density trial · open for review.** One nine-blade tuft sits beside the first mushroom. Short outer blades curl toward the moss while taller blades stand through the middle. One blade retains the approved profile at its original size. [Eye height](SourceArt/LayoutReview/arch_tuft_eye.jpg) · [Beside ChibiRunner](SourceArt/LayoutReview/arch_tuft_character.jpg).
- **Nine-blade tuft approved.** Use the arch tuft as a repeatable grass model. At the crossing, the placement trial adds three rotated copies at 82%, 101% and 91% asset scale, interleaved with two smaller clover groups. Leave gaps where moss and the worn edge can show. [View from the approach](SourceArt/LayoutReview/crossing_edge_eye.jpg) · [Whole path edge](SourceArt/LayoutReview/crossing_edge_character.jpg).



[Eye-height view](SourceArt/LayoutReview/clover_pawn_eye.jpg) · [Character scale](SourceArt/LayoutReview/clover_character.jpg) · [Idle and crossing playtest](SourceArt/LayoutReview/clover-bank-playtest.mp4)


<details><summary>Study 01 generation prompt · built-in ImageGen</summary>

A close-up 3D art-direction still of one path edge in ChibiRunner’s Fairy Grotto, at a tiny runner’s eye height. Focus on a handful of plump heart-shaped clover leaflets and a clump of broad grass blades. Each blade has visible thickness along the rim, a shallow central fold and a tapered, gently hooked tip. A turned leaf shows its underside. Subtle organic veins, broad waxy highlights, rich lime transmission where late-afternoon sunlight passes through a leaf, deep cool contact shadows between overlapping leaves. Moss wraps a rounded pebble and gives way to worn earth. The creek and an amber mushroom landing recede into soft focus. A hand-arranged miniature woodland with living botanical surfaces. Keep the path edge and nearest landing legible. Landscape framing. No lettering, UI, knit, stitching, fabric weave or plastic toy shine.

</details>

### Left trail to the birch

The mushroom-crossing mix of arching grass and full clover is approved. Along the left dirt path, gather them in small groups with exposed moss between them. The last group sits on the shoulder before the birch so the player can see where to step onto the trunk.

The birch cushion moss is approved. The surrounding ground is in review. The current trial uses warm brown earth and a softer green grass base, keeping broad patches of color and dialing back small bright grains and surface bumps.
Forest foliage should sway sideways in a slow passing breeze. Keep the roots anchored and the flowers, centers and leaves moving together. Give trial blooms clearance from neighboring stems throughout the sway.
Bellflowers across First Steps use a bowed green stem with six hanging lavender bells. Each bell has five soft folds and a pale curled rim. Vary the scale of the spray to suit its planting.
Strawberries use a plump fruit with golden seeds nestled in individual dimples, a bowed stalk, and thick, gently curved leaflets.
Birch-trail moss should look deep and soft enough to lie on. Broad rounded cushions carry a short, dense green nap, with gentle tonal variation and soft grazing highlights. Keep the dirt-edge lobes and pebble pockets legible.
For the dirt path, keep the ochre faces smooth with broad gradients. Put the strongest relief on the shoulders of the slabs and let parts of the edges wear into the ground.
Painted foliage follows the hand-placed planting palette. Pair rounded ivory or violet blooms with clover and arching grass, build shrubs from softly folded leaves, and nestle warm pebbles into cushion moss.
Give broad leaves a tapering midrib with curved side veins and grass a few lengthwise ridges. Use gentle color variation and shallow normal-map relief so the veins catch grazing light. Keep the waxy highlight broad and the backlit edges yellow-green.
Bellflower cups have five shallow, curved folds. A muted lavender shadow follows each groove and fades before the rolled lip.
The four creek landings are emergent lotus leaves on slender stems. Give each a broad landing surface, a softly rolled edge, a central dimple and radial veins. Reserve the amber mushroom models for woodland ground.
A lotus leaf settles up to 3.5 cm under a perched runner. Her perch follows the leaf. On release the stem lifts it more slowly toward its resting height, without oscillation.
When a lotus takes weight, one soft ripple expands from the stem at the creek surface and fades over 1.35 seconds. Holding a perch keeps the water quiet after that first ring.
A small pink lotus grows outside the second landing. Its cupped petals overlap around a warm seedpod. Light catches the shallow radial ribs of the larger landing leaves. Across the creek rocks, use soft warm-grey stone layers with broad color transitions and a raised moss cushion. Roll the moss over the lip so its thickness reads in silhouette and preserve the fine, rounded nap across that turn.
On creek boulders, draw moss greens from the adjacent terrain and let the nap catch the light. Vary the cushion edge locally with a few tapered patches that follow the face. Leave exposed bands of medium warm-gray stone between them, with soft patches of umber weathering.
Exposed creekstone has angular, weathered faces. Give each break a narrow recess and a broader chipped shoulder. Let some seams disappear across intact stone. Keep mineral variation muted and use a dry, granular finish under the raised moss.
Read each creek rock as one continuous mass. Let a few broad chipped faces change its silhouette. Keep most of the weathered stone face open, with short tapered nicks along occasional projecting edges.
Repeat the creek boulders as a family of four silhouettes. Alternate the low wedge, bluff with an off-center shoulder, and stepped flank with the original chipped rock. Moss reaches down different faces on each shape, using the same terrain-sampled olive green throughout.
