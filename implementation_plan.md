# Strawberry Hollow · Fairy Grotto implementation plan

**Level** `Lvl_FirstSteps` in the Unreal Parkour project  
**Current milestone** Direction approved. Capture the saved baseline, then begin the layout study.  
**Next user checkpoint** Review 1 — camera views and route walkthrough after blockout.  
**Revision tracking destination** [countnoobula/strawberry-hollow](https://github.com/countnoobula/strawberry-hollow)

## What we are building

From ChibiRunner’s starting bank, four glossy amber mushrooms draw a diagonal across a shallow creek to Pip’s acorn cottage. A moss-covered root arch frames the creek on the left. The cottage nestles into the roots of a much larger tree on the right. Warm windows, a peach lantern, and patches of afternoon sun lead the eye toward Pip. Preserve that relationship from both the elevated overview and the playable camera.

The ground should feel soft and continuous. Moss wraps banks, stones, and roots wherever traffic has spared it. The dirt path wears through that cover. Bark ridges catch light, pebbles cast contact shadows, water reveals its bed, and mushroom rims transmit a little sunlight. Those small changes in shape, material, and shadow are what give the reference its depth. A possible later interaction is a temporary, slowly recovering depression when ChibiRunner steps into moss.

**Primary references** The user-selected “Bring the lantern to Pip” gameplay image and the [approved elevated composition](<C:/Users/count/.codex/generated_images/01a209fe-2157-7d60-bfa0-6df3163d7128/exec-c7c20ef0-94f5-4de9-bd0d-e55ade713bc8.png>). Preserve both with the project during baseline setup after checking the images already in `SourceArt/ConceptArt`.

## How to follow progress

A checked task means its stated result has been verified. A checked user review means the user has accepted that checkpoint. As work advances, update the current milestone, check completed items, and record evidence or requested changes in the log below. At each review, present the relevant screenshots or playtest and wait for feedback before building on that decision.

## 0 · Agree on the target and protect the starting point

- [x] Inspect the saved level, placed actors, Blender sources, enabled plugins, and Git prerequisites. The initial inspection found 89 external actor packages and existing Landscape, creek, lighting, and forest traversal actors.
- [x] Record the supplied GitHub destination and the approved visual direction.
- [x] **User review 0 — direction.** Confirm the composition above and flag any existing Act 1 traversal or Act 2 quest beats that must keep their location or order.
- [x] After Antigravity’s final save and handoff, inspect current local and remote Git state. Preserve any existing remote history. Set up Git LFS and ignore generated Unreal caches, autosaves, and Blender backup files.
- [ ] Capture the original project descriptor, config, Content (including external actor/object packages), and SourceArt. Verify representative LFS files, the level’s actor packages, and a clean working tree. Record the baseline commit and remote sync status here. Create a working branch before editing.
- [ ] Open `Lvl_FirstSteps` explicitly. Capture the current overview and player view, then walk the route once. Record working traversal and quest behavior for comparison.

## 1 · Settle the whole map layout

- [ ] Map the current spawn, lantern pickup, creek, mushroom crossing, cottage, approach route, and optional traversal. Identify what the player can see at each decision point.
- [ ] Block out the full route with simple shapes and existing actors. Establish stream direction, bank heights, path widths, crossings, main tree masses, and the space around the cottage. Keep the four caps and the arch readable in silhouette.
- [ ] Fit the birch, rope line, zip line, and pendulum swing around the terrain. Check approach room, release arcs, landing visibility, and a way back after a missed jump. Confirm which mechanics are working after handoff.
- [ ] Save a repeatable elevated camera and a player-height view. Walk from spawn to Pip, carrying the lantern, and capture the same crossing from both cameras.
- [ ] **User review 1 — layout lock.** Show the full-map overview, the crossing at player height, and a short route walkthrough. Agree on scale, landmark positions, and route flow before detailed modeling.

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
