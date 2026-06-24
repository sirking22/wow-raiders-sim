# Prompt · Game State Kit / Situation Board

Create a War Raiders / Blackstar Raiders v0.53 Game State Kit / Situation Board.

Structure:
- Header with project and version.
- Base strategic map: 32x32 open-world hex sector or cropped sector window.
- Legend: terrain + fog states.
- 8 situation cards with situation IDs.
- Review/production board feel, readable in one screen.

Hard rules:
- No route-lines as main strategic mechanic.
- No invented HP, damage, rewards, XP, currency, threat numbers or campaign stats.
- Use exact fog states: unknown / visible / scanned / discovered.
- Every situation must look like a reusable production state, not a random illustration.
- If data is missing, show TBD from runtime or omit it.

Runtime anchors for v0.53 board:
- start_camp
- collapsed_streets
- bastion
- field_bazaar

Situation IDs:
- state.scouting
- state.intel_discovered
- state.resource_opportunity
- state.stronghold_located
- state.under_attack
- state.extraction_available
- state.sector_secured
- state.post_battle_return
