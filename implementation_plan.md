# Strawberry Hollow · Fairy Grotto implementation plan

**Level** `Lvl_FirstSteps` in the Unreal Parkour project  
**Current milestone** Act 2 is the playable focus of `Lvl_FirstSteps`. The southern Act 1 course has been removed. ChibiRunner starts on the near bank of the valley.

**Next user checkpoint** Review the Act 2 clearing from the player start and the birch approach.

**Revision tracking destination** [countnoobula/strawberry-hollow](https://github.com/countnoobula/strawberry-hollow)

## What we are building

From ChibiRunner’s starting bank, four glossy amber mushrooms draw a diagonal across a shallow creek to Pip’s acorn cottage. A moss-covered root arch frames the creek on the left. The cottage nestles into the roots of a much larger tree on the right. Warm windows, a peach lantern, and patches of afternoon sun lead the eye toward Pip. Preserve that relationship from both the elevated overview and the playable camera.

The ground should feel soft and continuous. Moss wraps banks, stones, and roots wherever traffic has spared it. The dirt path wears through that cover. Bark ridges catch light, pebbles cast contact shadows, water reveals its bed, and mushroom rims transmit a little sunlight. Those small changes in shape, material, and shadow are what give the reference its depth. A possible later interaction is a temporary, slowly recovering depression when ChibiRunner steps into moss.

**Primary references** The user-selected “Bring the lantern to Pip” gameplay image, FirstSteps.png, FirstSteps Top Down.png, and FirstSteps 3 Angle.png in the ConceptArt folder.

### Approved playable boundary

Build one enclosed woodland valley matching the visible clearing. Worn dirt paths curl around the mossy banks and meet the mushroom crossing, with a clear approach to Pip’s door. Use dense shrubbery backed by roots and rising ground along the perimeter. Leave readable openings only where the player can travel. Check sightlines and boundary collision at running, jumping, and swinging height. Fit traversal beats inside this footprint only where they serve the pictured clearing.

### Left-bank route and bridges

Follow the reference from the near bank. A worn dirt path curves left along the water and climbs to the pale fallen birch on the upper-left trail. The log spans a small break in that trail and is playable as a balance crossing. Closer to the mushroom crossing, the large moss-covered root arches over the creek. Its crown is a second playable bridge, with walkable approaches at both ends and an open view of water beneath the arch. Keep the two crossings distinct in silhouette and position. The four amber mushrooms remain the direct crossing toward Pip.

- [ ] At user review 1, compare the overview with the reference for the left path’s curve, upstream birch span, root arch, and open water beneath it. Walk both bridges from their dirt-path approaches and check their exits at player height.

### Creek depth and wading

Use ChibiRunner’s in-game body as the scale reference. Beneath the mushroom crossing, shape the creek bed so that after a missed jump she can plant her feet with the waterline between her waist and chest. Grade the bed up toward the banks so she can wade back onto the path. Keep the clear water and visible pebbles of the reference.

- [x] Test the creek beside the middle mushrooms. Drop ChibiRunner onto the bed, capture the waterline and wading pose, then walk back to dry ground.
- [x] Traversal pass — have ChibiRunner move through this depth with grounded wading steps and her arms held out to either side for balance. Check the transition from landing to wading and back to normal movement on the bank.

## How to follow progress

A checked task means its stated result has been verified. A checked user review means the user has accepted that checkpoint. As work advances, update the current milestone, check completed items, and record evidence or requested changes in the log below. Collect screenshots and playtest evidence at each review. The current stop is the layout check-in. Resume art development after the user sets the new style direction. User approval stays open until that review.

## 0 · Agree on the target and protect the starting point

- [x] Inspect the saved level, placed actors, Blender sources, enabled plugins, and Git prerequisites. The initial inspection found 89 external actor packages and existing Landscape, creek, lighting, and forest traversal actors.
- [x] Record the supplied GitHub destination and the approved visual direction.
- [x] **User review 0 — direction.** Confirm the composition above and flag any existing Act 1 traversal or Act 2 quest beats that must keep their location or order.
- [x] After Antigravity’s final save and handoff, inspect current local and remote Git state. Preserve any existing remote history. Set up Git LFS and ignore generated Unreal caches, autosaves, and Blender backup files.
- [x] Capture the original project descriptor, config, Content (including external actor/object packages), and SourceArt. Verify representative LFS files, the level’s actor packages, and a clean working tree. Record the baseline commit and remote sync status here. Create a working branch before editing.
- [ ] Open `Lvl_FirstSteps` explicitly. Capture the current overview and player view, then walk the route once. Record working traversal and quest behavior for comparison.

## 1 · Settle the whole map layout

- [x] Map the current spawn, lantern pickup, creek, mushroom crossing, cottage, approach route, and optional traversal. Identify what the player can see at each decision point.
- [x] Block out the full route with simple shapes and existing actors. Establish stream direction, bank heights, path widths, crossings, main tree masses, and the space around the cottage. Keep the four caps and the arch readable in silhouette.
- [x] Fit the birch, rope line, zip line, and pendulum swing around the terrain. Check approach room, release arcs, landing visibility, and a way back after a missed jump. Confirm which mechanics are working after handoff.
- [x] Save a repeatable elevated camera and a player-height view. Walk from spawn to Pip, carrying the lantern, and capture the same crossing from both cameras.
- [ ] **User review 1 — layout lock.** Show the full-map overview, the crossing at player height, and a short route walkthrough. Agree on scale, landmark positions, and route flow before detailed modeling.

### Revised ravine and pool checkpoint

- [x] Carry the left dirt trail across a side ravine on the starting bank. The birch stays level across a roughly three-metre clearance. The far end turns onto the launch ramp. The zip line crosses the main creek to a dry shelf.
- [x] Shape the lower pool and narrow its outlet. Refit the existing gravel surface to the river while keeping native Landscape collision beneath the water.
- [x] Turn the four mushroom landings upstream toward Pip. The first and last cap centers are separated by 3.43 m upstream and 4.55 m across the water. A playable run collected the lantern and delivered it to Pip across all four.
- [x] Verify a missed crossing can recover. At the downstream pool sample, the waterline was between ChibiRunner’s pelvis and upper spine. Wading speed was 125 cm/s and normal movement returned ashore.
- [ ] **User review 1** — review the view from spawn, the left turn off the birch, and the shape of the mushroom pool. Art direction remains open.

[Reference and revised Unreal survey](SourceArt/LayoutReview/ravine-and-pool-review.jpg) · [Gameplay view](SourceArt/LayoutReview/ravine-and-pool-gameplay.jpg) · [Both routes in Play-in-Editor](SourceArt/LayoutReview/ravine-and-ford-walkthrough.mp4)

### Earlier layout review evidence

- [x] Compare the new top-down and three-angle concepts with the saved level. The [annotated comparison](SourceArt/LayoutReview/layout-comparison.png) shows the straight creek, long parallel trails, cross-creek birch, and shorter ford approach. Layout review remains open. Proposed first change for review is to shape the upper-left ravine and its birch trail before adjusting the downstream pool and crossings.

- [Playable reference angle](SourceArt/LayoutReview/gameplay-valley.png) and [bank-height view](SourceArt/LayoutReview/gameplay-approach.png). The named cameras in the Outliner are `Valley_ReferenceOverview` and `Valley_PlayerBank`.
- [Overhead layout survey](SourceArt/LayoutReview/valley-overview.png). Overhead trees were hidden for this editor capture and restored afterward.
- [Continuous playtest from spawn to Pip](SourceArt/LayoutReview/birch-walkthrough.mp4). ChibiRunner collected the lantern, followed the left dirt trail, crossed the upstream birch, and delivered it at the cottage. The route needed more clearance where the upper landing shelf met the far-bank path.
- The root crown was walked in both directions. Near the center, the walk surface rises approximately 3.14 m above the level origin. The four-mushroom route was tested with four successive perch states and a landing on the far-bank Landscape.
- [Wading test at the crossing](SourceArt/LayoutReview/gameplay-wading.png). At the sample point, the creek surface sits between the pelvis and upper spine. The grounded wade runs at 125 cm/s and returns to ordinary movement on shore. Splash rings now have no pawn collision.
- The silk zip and crawl vine were tested in an isolated copy with the same placements now saved in the live level. Both allow a running jump onto the line, full travel, automatic release, and a dry landing on the cliff shelf.
- The right-hand pendulum was verified as a short cottage-side swing with a dry-bank landing. The art currently placed in the level is provisional. The separately authored moss-footstep prototype is parked for the new art direction.

## 2 · Establish the ground, creek, and paths

- [ ] Finish one representative stretch from dirt path through mossy bank to shallow creek. Use Unreal Landscape for broad forms and reserve meshes for overhangs, roots, and exposed rock.
- [ ] Build continuous moss coverage with controlled variation in thickness, roughness, and color. Blend it into worn dirt using irregular edges and patches of exposed soil. Check for texture stretching and visible repetition at ChibiRunner’s scale.
- [ ] Create a small family of stones and pebbles with distinct silhouettes. Seat them into the bank and streambed, vary wetness at the waterline, and tune water clarity so the shallow bed reads while moving.
- [ ] **User review 2 — ground sample.** Show the same patch close up and from gameplay distance in fixed lighting. Approve moss coverage, path texture, water clarity, and pebble scale before extending them across the level.

## 3 · Build and review the individual pieces

Use the existing forest Blender kits as starting material. For each piece, inspect the placed mesh in context, decide whether to retain, revise, or rebuild it, then verify its pivot, scale, collision, material response, and fit in Unreal. Keep source files and exports traceable. Bring each family back for review as it is ready.

- [ ] **Tree and arch.** Shape the cottage tree’s trunk flare, the arch opening, and the roots entering the banks. Place the canopy to frame the crossing and let light reach the route. **User review 3A** — approve tree silhouettes, bark scale, and cast shadows.
- [ ] **Cottage and Pip’s clearing.** Seat the acorn cottage against the roots. Tune roof scales, window depth, doorstep, fence, and lantern placement from the approach camera. **User review 3B** — approve the cottage and its relationship to Pip and the tree.
- [ ] **Mushrooms.** Shape the four readable landing caps and pale stems. Tune roughness, rim translucency, cap highlights, and stem shadows under the scene light. Verify perch and bounce variants individually. **User review 3C** — approve the amber finish, lighting, and landing readability.
- [ ] **Flora.** Build a small reusable set of strawberry plants, bellflowers, wildflowers, and moss tufts. Check leaf thickness, petal translucency, and shadows before placing clusters around the hand-authored landmarks. **User review 3D** — approve a dressed bank from player height before wider scattering.

## 4 · Integrate lighting, movement, and final detail

- [ ] Establish a repeatable afternoon lighting setup early for comparisons. In the finishing pass, balance sun direction, skylight, water reflections, exposure, and cottage glow. Compare fixed-camera images against the reference for light direction and separation between foreground and background.
- [ ] Extend approved materials and dressing across the route. Use the existing Landscape, Water, lighting, and PCG setup where appropriate. Record any proposed plugin change with the specific effect it enables.
- [ ] **Optional moss-footstep experiment.** Once the static moss is approved, test one patch that depresses beneath a foot and slowly springs back. Check the effect while walking, sprinting, and revisiting the same spot. **User review 4A** — decide whether the response is worth extending.
- [ ] Playtest the full route, camera clearance, missed-jump recovery, lantern delivery, and HUD. Check frame time on the agreed target hardware and capture comparable before/after views.
- [ ] **User review 4B — final walkthrough.** Review the elevated overview, playable approach, close-up material samples, and full traversal. Record requested fixes and the accepted revision.

## Progress log

| Date | Result | Next decision |
| --- | --- | --- |
| 2026-11-24 | Read-only project inventory completed. Visual target, layout-first approach, and GitHub destination recorded. | User review 0, then baseline after handoff. |
| 2026-11-24 | User approved the direction and confirmed Antigravity finished and saved. Remote had no refs before setup. | Establish baseline and start layout study. |
| 2026-11-24 | Local baseline 36a6be9 verified with 596 LFS files and 89 First Steps actor packages. Created local layout branch. User confirmed the pictured valley, dirt paths, and shrub boundaries. | Remote upload pending approval. Capture in-engine views for layout review. |
| 2026-11-24 | User confirmed the left dirt trail, pale birch balance bridge, and walkable root arch as distinct features of the reference layout. | Include both crossings in layout review 1. |
| 2026-11-24 | Captured baseline views, relocated the spawn and lantern to the near bank, added a playable upstream birch and separated the arch from the cottage sightline. Built a Landscape path mask and creek bed. In PIE at (135, 970), water Z −8.5 cm fell between pelvis −23.2 and upper spine −5.0 while grounded. | Finish terrain dressing and bridge / quest / shore tests. |
| 2026-11-24 | User requested the layout check-in ahead of final art. Saved a playable camera comparison and a continuous lantern-delivery recording; verified mushroom, root, birch and water routes. First Steps is set as the editor and game default map. | Review scale, paths and crossing positions; revisit visual style separately. |
| 2026-11-24 | Revised the left trail, birch ravine, zip-line launch, pool outline, and upstream mushroom route. Checked the saved level after reopening. | Review the revised layout before the art pass. |
| 2026-11-24 | Approved the concept clover thickness and built one near-bank foliage trial. Recorded it at runner height and verified lantern delivery over the four mushrooms. | Review the patch in motion before wider placement. |
| 2026-11-24 | Revised the crossing patch with fuller clover rims and thicker curved grass blades. | Compare the two eye-height captures before wider placement. |
| 2026-11-24 | Fuller clover approved. Broadened the three grass blades in the crossing patch and captured a matched eye-height comparison. | Review the grass silhouette beside the approved clover. |
| 2026-11-24 | Approved the outer arching blade and placed a nine-blade tuft beside the first mushroom. Captured both views in Play-in-Editor. | Review density, height variation, and curl. |
| 2026-11-24 | Approved the nine-blade tuft and placed three more at varied scales along the path, interleaved with clover. | Review the spacing at gameplay height. |
| 2026-11-24 | Crossing mix approved. Placed eight arch tufts and eight clover plants in four groups along the left trail toward the birch. Checked the moss gaps and bridge approach in Play-in-Editor. | Review the [trail overview](SourceArt/LayoutReview/birch_mix_overview.jpg) and [uphill patch at runner height](SourceArt/LayoutReview/birch_pocket_eye.jpg). |
| 2026-11-24 | Left-trail tuft and clover spacing approved. Trialled one cushion-moss patch between the uphill plant groups, tapering its height at the dirt edge. | Review the [runner-eye view](SourceArt/LayoutReview/birch_moss_eye.jpg) before extending the treatment. |
| 2026-11-24 | Birch cushion approved. Softened the Landscape earth and grassy ground colors and normal maps. | Compare the [original ground](SourceArt/LayoutReview/birch_moss_eye.jpg) and [softened ground](SourceArt/LayoutReview/birch_soft_ground_eye.jpg) at runner height. |
| 2026-11-24 | Softer ground approved. Extended cushion moss in three low groups along the planted shoulder toward the birch. | Review the [runner-eye view](SourceArt/LayoutReview/birch_creep_eye.jpg) and [character-scale view](SourceArt/LayoutReview/birch_creep_scale.jpg) for how far the moss should creep onto dirt. |
| 2026-11-24 | Moss encroachment approved. Nestled five rounded river pebbles into the birch trail edge. | Review the [matched eye-height view](SourceArt/LayoutReview/birch_pebbles_eye.jpg) for size, color and spacing. |
| 2026-11-24 | Pebble shapes approved. Tried honey, pale buff and rose-clay tones on the five birch pebbles, with small cushion-moss lobes at their bases. | Compare the [warm pebble trial](SourceArt/LayoutReview/birch_warm_stone_eye.jpg) with the [gray pebbles](SourceArt/LayoutReview/birch_pebbles_eye.jpg) from the same angle. |
| 2026-11-24 | Warm birch pebble palette approved. Placed six more along the left trail in a pair, a single and a trio toward the mushroom crossing, each bedded in cushion moss. | Review the [crossing trio at runner height](SourceArt/LayoutReview/crossing_stones_eye.jpg) and [trail spacing](SourceArt/LayoutReview/crossing_stones_overview.jpg). |
| 2026-11-24 | Crossing pebble placement approved. Modelled one three-flower patch beside the crossing stones with cupped, rounded ivory petals. | Review the [runner-height view](SourceArt/LayoutReview/crossing_petals_eye.jpg) and [petal detail](SourceArt/LayoutReview/crossing_petals_detail.jpg). |
| 2026-11-24 | Widened the five petals on each crossing trial bloom so their curved edges overlap. Added shallow surface ridges, a bumpy golden center and a ring of rounded anthers from the strawberry-blossom reference. | Review the [petal detail](SourceArt/LayoutReview/crossing_overlap_detail.jpg) and [runner-height view](SourceArt/LayoutReview/crossing_overlap_eye.jpg). |
| 2026-11-24 | Moved the trial flowers clear of the neighboring stems. Changed the shared forest foliage wind to slow lateral bending with height-weighted movement and a breeze that travels across plants. | Review the [eight-second eye-height clip](SourceArt/LayoutReview/crossing_soft_wind.mp4) for clearance and motion. |
| 2026-11-24 | Removed the SoftMeadow PCG volume and its 5,779 generated clover, moss tuft and wildflower instances from First Steps. Verified the hand-placed crossing patch in Play-in-Editor. | [Crossing after meadow removal](SourceArt/LayoutReview/crossing_meadow_wide.jpg). |
| 2026-11-24 | Placed three small groups of rounded ivory flowers along the left trail. Varied their scale and orientation, aligned the middle group with the slope, and checked the lower and upper groups in Play-in-Editor. | Review the [lower path](SourceArt/LayoutReview/birch_blooms_lower.jpg) and [birch approach](SourceArt/LayoutReview/birch_blooms_eye.jpg) at runner height. |
| 2026-11-24 | Replaced one foreground bellflower at the mushroom crossing with a bowed spray of six fluted bells. Modelled curled rims and pale interiors and reused the slow foliage breeze. | Review the [runner-height silhouette](SourceArt/LayoutReview/crossing_bells_eye.jpg) and [bell detail](SourceArt/LayoutReview/crossing_bells_detail.jpg) before wider placement. |
| 2026-11-24 | Bellflower spray approved. Updated the five remaining individually placed bellflowers and the foliage type for all 36 painted sprays. Verified all 42 placements use the approved mesh. | [Crossing at runner height](SourceArt/LayoutReview/valley_bells_eye.jpg). |
| 2026-11-24 | Also found bellflowers embedded in 36 mixed wildflower clusters. Rebuilt the bellflower part with the approved spray and retained the white flowers and clover. Final level count is 78 sprays. | Review the crossing capture above. |
| 2026-11-24 | Replaced one foreground strawberry at the crossing with a plump modelled fruit, seeds seated in individual dimples, and thick curved leaflets on bowed stalks. | Review the [runner-height view](SourceArt/LayoutReview/crossing_berry_eye.jpg) and [seed detail](SourceArt/LayoutReview/crossing_berry_detail.jpg) before wider placement. |
| 2026-11-24 | Strawberry trial approved. Updated the remaining five individually placed plants, including both cottage garden berries, and all 54 painted plants. Verified all 60 in Play-in-Editor. | [Garden berry at runner height](SourceArt/LayoutReview/garden_berries_eye.jpg). |
| 2026-11-24 | Removed 23 actors belonging to the southern course, including the tributary and its footbridge. Reassigned the four traversal actors already used inside the valley to Act 2. Shared Landscape retained. | Play-in-Editor passed both routes from the near-bank spawn: all four mushrooms and lantern delivery to Pip, plus the birch beam, zip line and dry landing. |
| 2026-11-24 | Revised all 20 birch-trail cushion and pebble-base moss placements with smooth mounds and two short, irregular layers of surface fuzz. The complete mesh uses 2,415 triangles per placement. | Compare the [runner-height trial](SourceArt/LayoutReview/birch_plush_eye.jpg) with the [previous cushion](SourceArt/LayoutReview/birch_soft_ground_eye.jpg). |
| 2026-11-24 | Trialled the supplied 2K Moss Ground 01 maps on the Landscape grass layer. Used the base color, DirectX normal, roughness and ambient occlusion with the existing dirt path mask. | Review the [lower path](SourceArt/LayoutReview/mossground_lower_eye.jpg) and [birch bank](SourceArt/LayoutReview/birch_mossground_eye.jpg) at runner height. |
| 2026-11-24 | Moss Ground 01 approved. Enlarged its Landscape repeat from 92 cm to 115 cm. | Compare the [larger pattern](SourceArt/LayoutReview/mossground_larger_eye.jpg) with the [previous scale](SourceArt/LayoutReview/mossground_lower_eye.jpg) from the same camera. |
| 2026-11-24 | Enlarged the moss pattern another 30%, from 115 cm to 149.5 cm per repeat. | [Runner-height review](SourceArt/LayoutReview/mossground_149_eye.jpg). |
| 2026-11-24 | Enlarged the moss repeat to 194.35 cm. The supplied height map drives a subtle parallax offset shared by the moss color, normal and surface maps. | Compare the [runner-height relief pass](SourceArt/LayoutReview/mossground_relief_eye.jpg) with the [149.5 cm pass](SourceArt/LayoutReview/mossground_149_eye.jpg). |
| 2026-11-24 | Increased moss parallax strength from 0.038 to 0.080 at the 194.35 cm repeat. | Compare the [deeper relief](SourceArt/LayoutReview/mossground_deeper_eye.jpg) with the [previous pass](SourceArt/LayoutReview/mossground_relief_eye.jpg). |
| 2026-11-24 | Authored a seamless dirt-path material inspired by [Stylized Ground by Roy Salaysay](https://roysalaysay.artstation.com/projects/Dx3n6e), with worn ochre slabs, soil seams, pebbles, twigs and shallow height relief. | Compare the [runner-height trial](SourceArt/LayoutReview/woodland_path_eye.jpg) with the [previous dirt](SourceArt/LayoutReview/mossground_deeper_eye.jpg). |
| 2026-11-24 | Smoothed the fine dirt grain in the normal, height, color and roughness maps, retaining the larger slab forms. | Compare the [softened path](SourceArt/LayoutReview/woodland_path_soft_eye.jpg) with the [previous surface](SourceArt/LayoutReview/woodland_path_eye.jpg). |
| 2026-11-24 | Rebuilt the dirt maps around broad clay faces with a narrow ochre palette, smooth raised shoulders and worn-through seams. | Compare the [gradient clay pass](SourceArt/LayoutReview/path_clay_gradient_eye.jpg) with the [smoothed dirt pass](SourceArt/LayoutReview/woodland_path_soft_eye.jpg). |
| 2026-11-24 | Sampled the exposed olive-brown soil in Moss Ground 01, brought the clay palette toward it, and added sparse rounded depressions in the normal and height maps. | Compare the [soil-matched path](SourceArt/LayoutReview/path_moss_soil_eye.jpg) with the [ochre pass](SourceArt/LayoutReview/path_clay_gradient_eye.jpg). |
| 2026-11-24 | Added a smooth warm-cream color gradient across the raised clay faces, tapering to the soil color in the seams. | Compare the [lighter tops](SourceArt/LayoutReview/path_cream_tops_eye.jpg) with the [previous path](SourceArt/LayoutReview/path_moss_soil_eye.jpg). |
| 2026-11-24 | Restored earth-brown step tops with a gentle clay gradient and limited pale wear to short edge accents. | [Runner-height review](SourceArt/LayoutReview/path_earth_accents_eye.jpg). |
