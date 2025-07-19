# Persuasion: Victorian Roguelike Investigation RPG Game
# Core Game Script

# Some mythos elements inspired by the works of H.P. Lovecraft (public domain).
# Some die rolling mechanics inspired by the FUDGE RPG system by Steffan O'Sullivan and Grey Ghost Press. No FUDGE SRD text or proprietary content is included.
#
# All other code, story, and mechanics are original.
#
# # Persuasion is a Victorian roguelike investigation RPG set in a haunted manor shrouded in fog and cosmic dread.
# You play as an investigator tasked with solving the mysterious disappearance of Bishop Alaric Greaves by gathering clues, interrogating suspects, and deducing the truth.
# The game features grid-based exploration, randomized rooms, and supernatural events. Dice rolls, stat-based skill checks, and a unique persuasion system is used to break through suspect defenses.
# Your choices, discoveries, and deductions shape the outcome—can you solve the case before madness or darkness claims you?

import os
import time
import random
import json
import sys
import time
import threading
import msvcrt  # For Windows key detection

GREEN = "\033[32m"
GREY = "\033[90m"
WHITE = "\033[97m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
ORANGE = "\033[38;5;208m"
RED = "\033[31m"
RESET = "\033[0m"

# --- Global State ---

MAP_MIN = -4
MAP_MAX = 4
MAP_SIZE = MAP_MAX - MAP_MIN + 1  # 9
MAP_CENTER = (MAP_SIZE // 2) - 1  # Center of the map grid

moves = {
    "n": (0, -1),
    "s": (0, 1),
    "e": (1, 0),
    "w": (-1, 0)
}
previous_menu_function = None

valid_moves = {"n", "s", "e", "w"}

male_first_names = [
    "Arthur", "Edmund", "Henry", "Charles", "Frederick", "Walter", "Reginald", "Albert", "Theodore", "Percival"
]
female_first_names = [
    "Eleanor", "Beatrice", "Clara", "Agnes", "Edith", "Florence", "Lillian", "Mabel", "Violet", "Winifred"
]
last_names = [
    "Ashcroft", "Blackwood", "Carrow", "Davenport", "Ellery", "Fairchild", "Godwin", "Hawthorne", "Ingram", "Jasper",
    "Kingsley", "Loxley", "Montague", "Norwood", "Ormond", "Pembroke", "Quill", "Ravenswood", "Sinclair", "Thorne"
]

azathoth_lashouts = [
    f"{RED}Azathoth's tendrils whip through the air, rending flesh and spirit alike! Agony explodes in your mind as cosmic power tears at your body!{RESET}",
    f"{RED}A thousand eyes open in Azathoth's mass, and a torrent of claws and teeth descend upon you, shredding sanity and skin!{RESET}",
    f"{RED}A wave of black ichor and writhing tentacles engulfs you, burning your nerves with pain beyond mortal comprehension!{RESET}",
    f"{RED}Azathoth's maw splits open, unleashing a scream that shatters bone and sends blood pouring from your ears!{RESET}"
]

amulet_azathoth_events = [
    f"{YELLOW}The amulet's power sears Azathoth! His form recoils, shrieking in a thousand voices!{RESET}",
    f"{YELLOW}A beam of golden light erupts from the amulet, burning through Azathoth's writhing mass. The air fills with the stench of scorched chaos!{RESET}",
    f"{YELLOW}The Abraxas Amulet pulses, unleashing a wave of force that tears through Azathoth's tentacles. The Blind Idiot God howls in agony!{RESET}",
    f"{YELLOW}Glyphs on the amulet blaze with forbidden light, carving wounds of pure order into Azathoth's chaotic flesh!{RESET}"
]

ACHIEVEMENT_SCORE = 10  # Points per achievement

# Achievement descriptions
ACHIEVEMENTS = {
    "Solved without violence": "Justice by wit alone—solved the case without resorting to violence.",
    "Found all artifacts": "Relic Hunter—discovered every hidden artifact in the manor.",
    "Kept sanity above 10": "Unbroken Mind—never let your sanity fall below 10.",
    "Solved the case on hard mode": "Master Detective—solved the mystery on hard difficulty.",
    "Evaded every monstrosity": "Fleet of Foot—escaped every supernatural horror without being caught.",
    "Never dropped below 5 faith": "Steadfast Believer—your faith never wavered below 5.",
    "Interrogated every suspect": "Relentless Investigator—questioned every suspect in the manor.",
    "Opened every chest": "Treasure Seeker—unlocked every chest and claimed its reward."
}

game_state = {
    "name": "",
    "gender": "",
    "background": "",
    "faith": 0,
    "sanity": 10,
    "health": 10,  # may adjust
    "perception": 0,
    "strength": 0,
    "stamina": 0,
    "agility": 0,
    "comeliness": 0,
    "inventory": [],
    "quests": [],
    "location": "",
    "suspects": [],
    "suspects_interrogated": set(),
    "clues": [],
    "journal": [],
    "turns": 0,
    "visited_locations": {},
    "position": (0, 0),
    "score": 0,
    "score_log": [],
    "achievements": set()
#    "walls": set(),  # Each wall is ((x1, y1), (x2, y2))
}

game_state["show_suspicion_hints"] = False
game_state["persuasion_active"] = False
game_state["persuasion_rounds"] = 0
game_state["persuasion_uses"] = 0
game_state["persuasion_targets"] = set()
game_state["chapel_pray_cooldown"] = 0
game_state["crime_type"] = random.choice([
    "murder", "kidnapping", "ritual sacrifice", "blackmail", "forced exile"
])

motive_pools = [
    [
        {"short": "Fanaticism", "long": "Driven by an obsessive devotion to forbidden rites and ancient faiths, often acting without regard for consequence."},
        {"short": "Revenge", "long": "Always considers revenge as a first option due to a quick temper and a deep disgust with the church's hypocrisy."},
        {"short": "Jealousy", "long": "Harbors envy for the Bishop's influence and resents being overlooked, fueling bitter rivalry."},
        {"short": "Forbidden Love", "long": "Secretly in love with someone close to the Bishop, willing to do anything to protect or possess them."},
        {"short": "Desperation", "long": "Haunted by debts and personal failures, willing to risk everything for a chance at redemption or escape."},
        {"short": "Ambition", "long": "Sees the Bishop's disappearance as a stepping stone to greater power within the church or society."},
        {"short": "Obsession", "long": "Fixated on unraveling cosmic mysteries, even at the cost of others' lives or sanity."},
        {"short": "Fear", "long": "Terrified of secrets being revealed, acts out of self-preservation and paranoia."}
    ],
    [
        {"short": "Blackmail", "long": "Holds or is held by dangerous secrets, manipulating others to maintain control."},
        {"short": "Guilt", "long": "Haunted by past misdeeds, desperate to cover up involvement in earlier crimes."},
        {"short": "Loyalty", "long": "Acts to protect a loved one or mentor, even if it means committing a terrible act."},
        {"short": "Resentment", "long": "Nurtures a long-standing grudge against the Bishop for personal slights or injustices."},
        {"short": "Zealotry", "long": "Believes the Bishop's removal is a holy duty, convinced of their own righteousness."},
        {"short": "Shame", "long": "Driven by the need to hide a scandal or personal failing at any cost."},
        {"short": "Manipulation", "long": "Sees others as pawns, orchestrating events to serve a hidden agenda."},
        {"short": "Greed", "long": "Motivated by material gain, coveting the Bishop's wealth or relics."}
    ],
    [
        {"short": "Remorse", "long": "Haunted by guilt, seeks to undo a past wrong even if it means drastic action."},
        {"short": "Hatred", "long": "Harbors deep-seated hatred for the Bishop, perhaps for a personal betrayal."},
        {"short": "Duty", "long": "Believes the Bishop's removal is necessary for the greater good or to fulfill an oath."},
        {"short": "Curiosity", "long": "Driven by a need to uncover forbidden knowledge, regardless of the cost."},
        {"short": "Ambivalence", "long": "Acts out of confusion or conflicting loyalties, unable to choose a side."},
        {"short": "Pride", "long": "Wounded pride compels them to prove their worth, no matter the consequences."},
        {"short": "Despair", "long": "Hopelessness has driven them to desperate measures."},
        {"short": "Envy", "long": "Covets the Bishop's status, possessions, or relationships."}
    ],
    [
        {"short": "Fanaticism", "long": "A zealot's fervor for the occult, convinced the Bishop stood in the way of a higher calling."},
        {"short": "Blackmail", "long": "Manipulates others with secrets, but is also ensnared by their own."},
        {"short": "Obsession", "long": "Cannot let go of a single idea, person, or artifact, regardless of the cost."},
        {"short": "Jealousy", "long": "Burns with envy over the Bishop's favor or affections."},
        {"short": "Ambition", "long": "Will stop at nothing to climb the social or ecclesiastical ladder."},
        {"short": "Fear", "long": "Acts out of terror—of discovery, of punishment, or of the unknown."},
        {"short": "Loyalty", "long": "Would do anything to protect a friend, mentor, or cause—even murder."},
        {"short": "Shame", "long": "Desperate to keep a personal failing or scandal hidden."}
    ],
    [
        {"short": "Manipulation", "long": "A master of schemes, always pulling strings from the shadows."},
        {"short": "Forbidden Love", "long": "A love that could never be, driving them to reckless acts."},
        {"short": "Desperation", "long": "Backed into a corner by circumstance, sees no other way out."},
        {"short": "Zealotry", "long": "Religious or ideological extremism justifies any means."},
        {"short": "Guilt", "long": "Haunted by a past mistake, tries to cover it up at all costs."},
        {"short": "Resentment", "long": "Long-standing bitterness finally boils over."},
        {"short": "Remorse", "long": "Tries to undo a terrible wrong, but only makes things worse."},
        {"short": "Curiosity", "long": "An insatiable need to know the truth, no matter the danger."}
    ],
    [
        {"short": "Ambition", "long": "Sees the Bishop's fall as a chance to seize power."},
        {"short": "Obsession", "long": "Fixated on a single goal, person, or artifact."},
        {"short": "Fear", "long": "Paralyzed by terror, acts rashly to protect themselves."},
        {"short": "Loyalty", "long": "Would betray anyone else to protect their chosen ally."},
        {"short": "Jealousy", "long": "Cannot stand to see the Bishop favored over them."},
        {"short": "Blackmail", "long": "Uses secrets as weapons, but is also vulnerable to exposure."},
        {"short": "Shame", "long": "Will do anything to keep their disgrace hidden."},
        {"short": "Despair", "long": "Hopelessness leads to desperate, dangerous acts."}
    ],
    [
        {"short": "Zealotry", "long": "Religious fervor blinds them to all but their cause."},
        {"short": "Forbidden Love", "long": "A secret passion drives them to extremes."},
        {"short": "Manipulation", "long": "Always plotting, always two steps ahead."},
        {"short": "Guilt", "long": "Haunted by what they've done, or failed to do."},
        {"short": "Resentment", "long": "Old wounds fester, fueling their actions."},
        {"short": "Remorse", "long": "Desperate to make amends, but only digs deeper."},
        {"short": "Ambition", "long": "Will stop at nothing to achieve their goals."},
        {"short": "Curiosity", "long": "Their need to know is greater than their fear."}
    ],
    [
        {"short": "Fanaticism", "long": "Believes the Bishop's death serves a higher, cosmic purpose."},
        {"short": "Jealousy", "long": "Envy poisons their every thought."},
        {"short": "Obsession", "long": "Cannot let go, even as it destroys them."},
        {"short": "Desperation", "long": "Sees no other way out."},
        {"short": "Blackmail", "long": "Trapped by secrets, lashes out to protect themselves."},
        {"short": "Loyalty", "long": "Would sacrifice anything for their chosen person or cause."},
        {"short": "Shame", "long": "Haunted by disgrace, will do anything to keep it hidden."},
        {"short": "Ambition", "long": "Sees opportunity in the Bishop's absence."}
    ]
]

# chosen_motive_pool = random.choice(motive_pools)
# chosen_alibi_pool = random.choice(alibi_pools)
# chosen_clue_pool = random.choice(clue_pools)

# game_state["score"] += 10
# game_state["score_log"].append(f"Clue: {clue} [+10]")
# game_state["score"] += 20
# game_state["score_log"].append(f"Artifact: {artifact['name']} [+20]")
# game_state["score"] += 15
# game_state["score_log"].append(f"Interrogated: {suspect['name']} [+15]")
# game_state["score"] += 100
# game_state["score_log"].append("Case Solved [+100]")
# game_state["score"] -= 1
# game_state["score_log"].append("Turn taken [-1]")

motive_descriptions = {
    "Fanaticism": "\"I have seen truths that would shatter lesser minds. My faith is a fire that cannot be quenched.\" The intensity in the suspect's eyes never wavers, and even silence feels charged.",
    "Revenge": "\"Justice was denied to me for too long. I will not rest until the scales are balanced.\" Every word from the suspect is edged with old wounds and bitter memory.",
    "Jealousy": "\"Why should the Bishop have everything? I have been overlooked for far too long.\" The suspect's posture is tense, as if measuring every gesture for hidden meaning.",
    "Forbidden Love": "\"There are secrets between us that no one else could ever understand. I would do anything to protect what we shared.\" The air around the suspect feels heavy with longing and regret.",
    "Desperation": "\"You cannot imagine what it is to be cornered by fate. I did what I had to do to survive.\" The suspect's voice trembles, and a restless energy clings to every movement.",
    "Ambition": "\"Power is not given, it is taken. The Bishop was simply in my way.\" The suspect's gaze is sharp, always searching for advantage.",
    "Obsession": "\"There is a pattern to all things, if you know where to look. I could not let go, even when I should have.\" The suspect seems distant, lost in thought even as you speak.",
    "Fear": "\"There are things in this house that should never be spoken of. I acted out of terror, not malice.\" The suspect glances over their shoulder, haunted by unseen threats.",
    "Blackmail": "\"Secrets are currency in this place. I have paid dearly for mine.\" The suspect's words are measured, and the air feels thick with unspoken threats.",
    "Guilt": "\"I wish I could undo what has been done. The past is a weight I cannot put down.\" The suspect avoids your gaze, burdened by invisible sorrow.",
    "Loyalty": "\"I would do anything for those I care about. Sometimes loyalty demands terrible choices.\" The suspect's conviction is unwavering, but a storm of conflict lingers beneath the surface.",
    "Resentment": "\"The Bishop never saw my worth. Every slight, every insult, I remember them all.\" The suspect's tone is clipped, colored by bitterness.",
    "Zealotry": "\"My cause is righteous, and I will not be swayed. The Bishop stood in the way of salvation.\" The suspect's certainty is unshakeable, and doubt finds no purchase.",
    "Shame": "\"There are things I cannot speak of. My failures haunt me every day.\" The suspect shrinks from your gaze, desperate to hide some personal failing.",
    "Manipulation": "\"Everyone here is a pawn, whether they know it or not. I simply play the game better.\" The suspect's smile never quite reaches their eyes, and every gesture feels rehearsed."
}

relationship_responses = [
    "\"I had my reasons for being here, but the Bishop and I were not close.\"",
    "\"The Bishop and I shared a cordial acquaintance, nothing more. Our paths crossed out of necessity, not friendship.\"",
    "\"We had our disagreements, but I respected his position. Still, there were matters best left unspoken between us.\"",
    "\"He was a distant figure in my life—always present, yet never truly known. I doubt he ever noticed me at all.\"",
    "\"Our relationship was... complicated. There were secrets between us, and not all of them were mine to tell.\""
]

room_templates = {
    "Foyer": [
        "The grand entry is dimly lit, dust motes floating through the silence. You hear footsteps upstairs, then silence again, as if the house is holding its breath. The heavy doors behind you seem to close of their own accord, sealing you inside."
    ],
    "Main Hall": [
        "A vast corridor stretches in both moves, portraits watching from above with eyes that seem to follow your every move. The chandeliers sway slightly despite the still air, casting shifting shadows on the marble floor. Something unseen seems to pace behind the walls, its presence felt but never seen."
    ],
    "Library": [
        "Bookshelves loom, many tomes written in languages you don’t recognize. A shattered inkwell and a missing journal page hint at a struggle that took place here. A cold draft whispers through the gaps in the shelves, carrying the faint scent of old paper and secrets."
    ],
    "Study": [
        "The desk is overturned, scattering scorched fragments of parchment across the floor. A painting swings ajar, revealing a keyhole behind it that begs investigation. The air is thick with the scent of burnt ink and desperation."
    ],
    "Cellar": [
        "Wine racks cover the walls, but the air smells of rot, not spirits. Chains and dried herbs hang together—ritual or restraint, it's hard to tell. The earth floor squelches underfoot, and something skitters just out of sight."
    ],
    "Parlor": [
        "A cracked mirror leans against the fireplace, reflecting nothing but darkness. A half-burnt letter lies beside an empty tea cup, its contents lost to the flames. The fire is warm, but no logs burn, and the room feels oddly inhabited."
    ],
    "Chapel": [
        "Faded icons peer down from peeling walls, their faces worn away by time and neglect. A candle flickers beneath a statue whose face has been scratched out, casting long shadows across the pews. Something shuffles in the darkness when you aren’t looking, and the silence feels sacred and heavy."
    ],
    "Conservatory": [
        "Glass walls reveal the fog beyond, pressing inward as if trying to enter. Overgrown vines have cracked through the tiles, and something glistens in the soil beneath your feet. A harp in the corner is missing a string, its remaining cords humming softly in the chill air."
    ],
    "Attic": [
        "Dust coats everything in thick fur, muffling your footsteps. Broken dolls and empty birdcages fill the room, their glassy eyes and open doors hinting at stories best forgotten. You hear a child’s whisper, but the room is empty and cold."
    ],
    "Laboratory": [
        "Vials and beakers line scorched tables, their contents long since evaporated or spilled. Something green bubbles inside a jar marked 'DO NOT OPEN', casting an eerie glow. Scratches on the wall form incomplete equations, as if someone tried to solve a puzzle and failed."
    ],
    "Torture Chamber": [
        "Instruments of pain are meticulously arranged, gleaming despite the filth and dust. The walls are soundproofed with old cloth, muffling any sound you might make. A metal mask smiles eternally from the center table, daring you to look away."
    ],
    "Kitchen": [
        "The air is thick with the scent of spoiled meat, making your stomach churn. Pots boil on their own, unattended, their contents bubbling ominously. A bloodied apron hangs from a hook like a ghost’s robe, swaying gently as if recently disturbed."
    ],
    "Smoking Room": [
        "The scent of old tobacco lingers, clinging to the velvet chairs and heavy drapes. Chairs face an empty hearth, their indentations fresh as if someone just left. A decanter trembles when you enter, sending ripples through the amber liquid inside."
    ],
    "Ballroom": [
        "Cobwebs dance where dancers once did, draping the grand chandeliers in silver lace. A phonograph crackles but spins no disc, filling the silence with static. In the moonlight, footprints appear on the dust-polished floor, leading nowhere."
    ],
    "East Bedchamber": [
        "The bed is made with surgical precision, its sheets crisp and untouched. A single rose lies across the pillow, already wilting and shedding petals. The window is nailed shut, and the air is heavy with the scent of faded perfume."
    ],
    "West Bedchamber": [
        "Curtains flutter though no window is open, their movement unsettling in the stillness. The mirror is draped in black cloth, hiding whatever reflection might appear. Something breathes beneath the floorboards, slow and steady."
    ],
    "Servant's Quarters": [
        "Bunks are made but still warm, as if their occupants left only moments ago. A diary lies open on the floor, pages torn and ink smeared. You hear humming from the hallway, though no one approaches."
    ],
    "Dining Hall": [
        "An enormous table is set for a feast no one attends, silverware gleaming in the candlelight. Mold creeps along the fine china, reclaiming the remnants of forgotten meals. A chair at the head is pulled back—waiting for someone who never arrives."
    ],
    "Gallery": [
        "Portraits line the walls, but their faces have been scraped off, leaving only blank ovals. A crimson smear crosses the floor and disappears behind a velvet curtain. You sense the paintings still watch, even without eyes."
    ],
    "Atrium": [
        "Twilight filters through the stained-glass ceiling, painting the marble floor in shifting colors. Ivy curls around marble statues with hollow eyes, their expressions unreadable. Water drips from somewhere unseen, echoing through the vast space."
    ],
    "Solarium": [
        "Rays of moonlight pour through broken panes, illuminating dust motes in the air. Potted plants have wilted into twisted shapes, their leaves curling like claws. A teacup rests beside a still-warm chair, as if someone just left."
    ],
    "Observatory": [
        "A great telescope points at nothing, its lens fogged with age. Charts and star maps are strewn in disarray across the tables. Something scratched 'They are already here' into the oak railing, the words deep and frantic."
    ],
    "Garden": [
        "Overgrown paths wind through headless statuary, the roses blooming black in the moonlight. A rusted gate creaks open on its own, inviting you deeper into the tangled greenery. The air is thick with the scent of earth and something sweeter, almost cloying."
    ],
    "Horse Stable": [
        "The stables smell of hay and rust, the scent mingling with something less pleasant. One stall door swings slowly, creaking on unseen hinges as if pushed by a phantom hand. Hoof prints lead out but never return, vanishing into the darkness."
    ],
    "Well House": [
        "The well is sealed with iron chains, their links cold and damp to the touch. Scratches climb the stone from inside, desperate and deep. A chill creeps up your spine, though no wind blows in this forgotten place."
    ],
    "Music Room": [
        "A grand piano dominates the room, its keys yellowed and silent. Sheet music is scattered across the floor, and a violin lies broken atop a velvet stool. Sometimes, you think you hear faint notes echoing in the silence."
    ],
    "Greenhouse": [
        "Glass panes are fogged with condensation, and the air is thick with the scent of earth and decay. Exotic plants twist toward the ceiling, some with blossoms that seem to watch you as you pass."
    ],
    "Laundry Room": [
        "The air is damp and heavy with the scent of soap and mildew. Baskets of linens are stacked in the corners, and a single shirt hangs, still wet, as if forgotten in haste."
    ],
    "Nursery": [
        "Faded wallpaper peels from the walls, revealing childish drawings beneath. A rocking horse stands in the corner, and a doll stares blankly from a crib. The room is cold, and the silence is oppressive."
    ],
    "Billiards Room": [
        "A green felt table sits beneath a dusty chandelier. Pool cues are scattered across the floor, and a single red ball rests in a pocket. The air smells faintly of cigars and old victories."
    ],
    "Wine Cellar": [
        "Rows of dusty bottles line the walls, some shattered on the stone floor. The air is cool and tinged with the scent of spilled wine and mold. You hear the faint drip of water somewhere in the darkness."
    ],
    "Armory": [
        "Racks of antique weapons and armor line the walls. Some pieces are missing, and a suit of armor stands in the corner, its visor lowered as if watching you."
    ],
    "Chapel Crypt": [
        "Stone steps descend into darkness. The air is cold and damp, and the walls are lined with ancient tombs. Candles flicker in alcoves, casting long shadows that seem to move on their own."
    ],
    "Portrait Gallery": [
        "A long, narrow hall filled with portraits of stern ancestors. Their eyes seem to follow you, and one painting hangs askew, revealing a dark gap in the wall behind it."
    ],
    "Map Room": [
        "Maps of distant lands and star charts cover every surface. A globe sits in the corner, its surface marked with strange symbols. A journal lies open on the desk, its ink still wet."
    ],
    "Master Bathroom": [
        "Marble tiles gleam in the candlelight. The tub is filled with cold, stagnant water, and a cracked mirror reflects your uneasy face. The scent of lavender barely masks something fouler."
    ],
    "Guest Suite": [
        "The bed is perfectly made, and a suitcase sits unopened at its foot. A letter lies on the nightstand, its contents hastily scrawled and unfinished."
    ],
    "Tower Room": [
        "A spiral staircase leads to a small chamber with windows on all sides. The wind howls through broken panes, and the view of the grounds is both beautiful and unsettling."
    ],
    "Vault": [
        "A heavy iron door guards this room. Inside, shelves are lined with ledgers and locked boxes. Dust motes swirl in the beam of your lantern, and the air is thick with secrets."
    ],
    "Secret Laboratory": [
        "Hidden behind a false wall, this room is filled with strange apparatus and bubbling vials. The scent of chemicals is overpowering, and notes in a spidery hand cover the desk."
    ],
    "Coach House": [
        "Old carriages and tack hang from the rafters. The floor is covered in straw, and the scent of horses lingers. A lantern swings gently from a hook, though there is no breeze."
    ],
    "Gamekeeper’s Lodge": [
        "A rustic room with hunting trophies on the walls. A rifle leans against the hearth, and muddy boots are lined up by the door. The air is thick with the scent of tobacco and wet dog."
    ],
    "Servant's Quarters": [
        "Simple bunks line the walls, each with a small trunk at its foot. The air is filled with the scent of soap and sweat, and a half-finished letter lies on one of the pillows."
    ],
    "Clock Tower": [
        "Gears and cogs fill the cramped space, ticking and grinding in the gloom. The great bell looms overhead, and the floor is littered with tools and oily rags. The view from the narrow window is dizzying."
    ],
}

# --- Suspects and Motives ---
suspect_templates = [
    {"name": "Miss Vexley", "trait": "Nervous", "alibi": "Claims she was in the chapel praying.", "motive": "Jealousy", "gender": "Female"},
    {"name": "Dr. Lorn", "trait": "Stoic", "alibi": "Was tending the fire in the lounge.", "motive": "Revenge", "gender": "Male"},
    {"name": "Ulric", "trait": "Fanatical", "alibi": "Says he heard voices in the cellar.", "motive": "Fanaticism", "gender": "Male"},
    {"name": "Colonel Catsup", "trait": "Charming", "alibi": "Claims he was entertaining guests all night.", "motive": "Desperation", "gender": "Male"},
    {"name": "Lady Ashcroft", "trait": "Secretive", "alibi": "Insists she was alone in the solarium, reading.", "motive": "Forbidden Love", "gender": "Female"},
    {"name": "Mr. Blackwood", "trait": "Cynical", "alibi": "Claims he was repairing a broken window in the attic.", "motive": "Ambition", "gender": "Male"},
    {"name": "Sister Mirabel", "trait": "Pious", "alibi": "Was lighting candles in the chapel crypt at midnight.", "motive": "Zealotry", "gender": "Female"},
    {"name": "Mr. Feynman", "trait": "Scheming", "alibi": "Was reviewing maps in the map room at 11pm.", "motive": "Manipulation", "gender": "Male"},
    {"name": "Mrs. Dalloway", "trait": "Anxious", "alibi": "Was sorting laundry in the laundry room at 9pm.", "motive": "Guilt", "gender": "Female"},
    {"name": "Father Mallory", "trait": "Stern", "alibi": "Was polishing armor in the armory at 10pm.", "motive": "Duty", "gender": "Male"},
    {"name": "Miss Penrose", "trait": "Curious", "alibi": "Was examining old maps in the study at 10pm.", "motive": "Curiosity", "gender": "Female"},
    {"name": "Mr. Quill", "trait": "Secretive", "alibi": "Was reading letters in the servant's quarters at 11pm.", "motive": "Blackmail", "gender": "Male"},

]

motive_flavor_texts = {
    "Fanaticism": {
        "Male": [
            "\"You do not understand the power that moves through these halls. I am chosen for something greater.\" \"Faith is my shield and my weapon. I will not falter.\" The fervor in the voice is unmistakable, and the room seems to grow colder."
        ],
        "Female": [
            "\"I have devoted my life to the truth, no matter the cost. Doubt is a luxury I cannot afford.\" \"The Bishop was an obstacle to enlightenment. I did what was necessary.\" The words tumble out in a rush, each one a desperate plea."
        ]
    },
    "Revenge": {
        "Male": [
            "\"You think justice is a luxury? For me, it is a necessity. I have waited too long.\" \"Every slight, every betrayal—I remember them all. The Bishop was no exception.\" The jaw clenches, and old anger flickers in the gaze."
        ],
        "Female": [
            "\"I have been wronged, and I will not forgive. The Bishop knew what was coming.\" \"Retribution is my right. I will see it done.\" The eyes never quite meet yours, as if afraid of what might spill out."
        ]
    },
    "Jealousy": {
        "Male": [
            "\"Why should the Bishop have everything? I have been overlooked for far too long.\" \"No one ever notices my efforts, but I see what others have.\" The posture is tense, measuring every gesture for hidden meaning."
        ],
        "Female": [
            "\"She always had more than me. I watched, I waited, but it was never enough.\" \"I would rather see it all burn than be left behind.\" The smile is brittle, and the air feels charged with rivalry."
        ]
    },
    "Forbidden Love": {
        "Male": [
            "\"There are secrets between us that no one else could ever understand. I would do anything to protect what we shared.\" \"Love is a dangerous thing in this house.\" The air feels heavy with longing and regret."
        ],
        "Female": [
            "\"We were never meant to be, but I could not let go.\" \"I would risk everything for a single moment more.\" The silence between sentences is thick with meaning."
        ]
    },
    "Desperation": {
        "Male": [
            "\"You cannot imagine what it is to be cornered by fate. I did what I had to do to survive.\" \"There was no other way out.\" The voice trembles, and a restless energy clings to every movement."
        ],
        "Female": [
            "\"I was drowning, and no one reached out to help.\" \"Desperation makes monsters of us all.\" The hands fidget constantly, betraying the strain."
        ]
    },
    "Ambition": {
        "Male": [
            "\"Power is not given, it is taken. The Bishop was simply in my way.\" \"I will not apologize for wanting more.\" The gaze is sharp, always searching for advantage."
        ],
        "Female": [
            "\"I have goals, and nothing will stand in my path.\" \"Ambition is not a sin, but a necessity.\" Every word is chosen with care, each gesture a step toward a goal."
        ]
    },
    "Obsession": {
        "Male": [
            "\"There is a pattern to all things, if you know where to look. I could not let go, even when I should have.\" \"The truth is always just out of reach.\" The suspect seems distant, lost in thought even as you speak."
        ],
        "Female": [
            "\"I see connections others miss. I cannot rest until I understand.\" \"Obsession is a curse, but I cannot escape it.\" The fingers trace invisible lines in the air, thoughts clearly elsewhere."
        ]
    },
    "Fear": {
        "Male": [
            "\"There are things in this house that should never be spoken of. I acted out of terror, not malice.\" \"I am not proud of what I did.\" The suspect glances over their shoulder, haunted by unseen threats."
        ],
        "Female": [
            "\"I was afraid, and fear makes us do terrible things.\" \"I wish I could forget what I saw.\" The words are barely above a whisper, and the air is thick with dread."
        ]
    },
    "Blackmail": {
        "Male": [
            "\"Secrets are currency in this place. I have paid dearly for mine.\" \"You would do the same if you were in my position.\" The words are measured, and the air feels thick with unspoken threats."
        ],
        "Female": [
            "\"Everyone here has something to hide. I am no different.\" \"Blackmail is a game, and I play to win.\" The laughter is forced, and the smile never quite reaches the eyes."
        ]
    },
    "Guilt": {
        "Male": [
            "\"I wish I could undo what has been done. The past is a weight I cannot put down.\" \"Regret is my only companion.\" The gaze avoids yours, burdened by invisible sorrow."
        ],
        "Female": [
            "\"I am haunted by what I did. I cannot escape it.\" \"Guilt is a shadow that follows me everywhere.\" The voice trembles, and the hands fidget with unease."
        ]
    },
    "Loyalty": {
        "Male": [
            "\"I would do anything for those I care about. Sometimes loyalty demands terrible choices.\" \"My actions were not for myself.\" The conviction is unwavering, but a storm of conflict lingers beneath the surface."
        ],
        "Female": [
            "\"I protect those I love, no matter the cost.\" \"Loyalty is my guiding star.\" The words are steady, but the eyes flicker with doubt."
        ]
    },
    "Resentment": {
        "Male": [
            "\"The Bishop never saw my worth. Every slight, every insult, I remember them all.\" \"Resentment is a poison, and I have drunk deeply.\" The tone is clipped, colored by bitterness."
        ],
        "Female": [
            "\"She never gave me a chance. I will not forgive.\" \"Old wounds do not heal in this house.\" The arms cross defensively, and the words are laced with pain."
        ]
    },
    "Zealotry": {
        "Male": [
            "\"My cause is righteous, and I will not be swayed. The Bishop stood in the way of salvation.\" \"I did what was necessary for the greater good.\" The certainty is unshakeable, and doubt finds no purchase."
        ],
        "Female": [
            "\"Faith is everything to me. I would walk into the abyss for my beliefs.\" \"The Bishop was a test, and I did not fail.\" The words burn with conviction, and the air grows heavy."
        ]
    },
    "Shame": {
        "Male": [
            "\"There are things I cannot speak of. My failures haunt me every day.\" \"I wish I could disappear.\" The suspect shrinks from your gaze, desperate to hide some personal failing."
        ],
        "Female": [
            "\"I am not proud of what I have done.\" \"Shame is a burden I carry alone.\" The voice is barely more than a whisper, and the cheeks flush with embarrassment."
        ]
    },
    "Manipulation": {
        "Male": [
            "\"Everyone here is a pawn, whether they know it or not. I simply play the game better.\" \"You should be careful whom you trust.\" The smile never quite reaches the eyes, and every gesture feels rehearsed."
        ],
        "Female": [
            "\"I see the strings others miss. I pull them when I must.\" \"Manipulation is an art, and I am its master.\" The laughter is light, but the gaze is sharp, watching for every weakness."
        ]
    },
    "Greed": {
        "Male": [
            "\"Wealth is power, and I intend to claim what is owed to me.\" \"The Bishop's fortune was always just out of reach.\" The eyes linger on every object of value, fingers twitching with the urge to possess."
        ],
        "Female": [
            "\"Riches open doors that faith never could.\" \"I have always wanted more than my share.\" The eyes sparkle at the mention of gold, ambition for more always apparent."
        ]
    },
    "Remorse": {
        "Male": [
            "\"I wish I could take it all back. Regret is a chain I cannot break.\" \"The past haunts me, and I am desperate to make amends.\" The voice is tinged with sorrow, and the gaze is clouded with regret."
        ],
        "Female": [
            "\"I am haunted by what I have done. I would do anything to set things right.\" \"Remorse is my constant companion.\" The eyes glisten with unshed tears, and the words tremble with regret."
        ]
    },
    "Hatred": {
        "Male": [
            "\"The Bishop deserved everything that happened. My anger burns hotter than any fire.\" \"I will never forgive, never forget.\" The jaw clenches at the mention of certain names, and the words drip with venom."
        ],
        "Female": [
            "\"I despise everything about her. Hatred is all I have left.\" \"She brought this on herself.\" The tone is icy, and the words are sharp as daggers."
        ]
    },
    "Duty": {
        "Male": [
            "\"I did what was required of me. Duty is not a choice, but a burden.\" \"Honor demanded action, no matter the cost.\" The posture is rigid, every word weighed with obligation."
        ],
        "Female": [
            "\"My responsibilities come before all else. I could not turn away.\" \"Duty is my shield, and my prison.\" The answers are precise, the demeanor formal."
        ]
    },
    "Curiosity": {
        "Male": [
            "\"There are secrets in this manor that beg to be uncovered.\" \"I could not resist the urge to know more.\" The eyes dart around the room, hungry for new information."
        ],
        "Female": [
            "\"Mysteries draw me in, even when I know I should walk away.\" \"Curiosity is my guiding star.\" The gaze is sharp and inquisitive, every question asked with intent."
        ]
    },
    "Ambivalence": {
        "Male": [
            "\"I am torn between what is right and what is necessary.\" \"My loyalties shift with the wind.\" The words are hesitant, and the thoughts clearly divided."
        ],
        "Female": [
            "\"I do not know what I truly want. My heart is divided.\" \"Ambivalence clouds every decision.\" The responses waver, torn between conflicting loyalties."
        ]
    },
    "Pride": {
        "Male": [
            "\"I am not one to be underestimated. Pride is my armor.\" \"I will not accept blame for what happened.\" The head is held high, confidence bordering on arrogance."
        ],
        "Female": [
            "\"I have earned my place here. Pride is my crown.\" \"Criticism rolls off me like rain.\" The self-assurance is unshakable, and the gaze dares you to challenge."
        ]
    },
    "Despair": {
        "Male": [
            "\"Hope abandoned me long ago. I see no way out.\" \"Despair is a weight I carry every day.\" The shoulders slump, and the words are heavy with resignation."
        ],
        "Female": [
            "\"I am lost in a fog of hopelessness. Nothing matters anymore.\" \"Despair is my only companion.\" The voice is flat, and the spirit weighed down by sorrow."
        ]
    },
    "Envy": {
        "Male": [
            "\"I watched others succeed while I was left behind.\" \"Envy poisons everything I touch.\" The gaze is covetous, and the words are colored by resentment."
        ],
        "Female": [
            "\"I compare myself to others constantly. I want what I cannot have.\" \"Envy is a hunger that never fades.\" The sigh is wistful, and every gesture betrays longing."
        ]
    }
}


# def generate_walls():
#     wall_chance = 0.18  # 18% chance for a wall between any two adjacent rooms
#     for x in range(MAP_MIN, MAP_MAX + 1):
#         for y in range(MAP_MIN, MAP_MAX + 1):
#             for dx, dy in [(0, 1), (1, 0)]:  # Only need to check E and S to avoid duplicates
#                 nx, ny = x + dx, y + dy
#                 if MAP_MIN <= nx <= MAP_MAX and MAP_MIN <= ny <= MAP_MAX:
#                     if random.random() < wall_chance:
#                         # Store both moves for easy lookup
#                         game_state["walls"].add(((x, y), (nx, ny)))
#                         game_state["walls"].add(((nx, ny), (x, y)))

import sys
import time

for suspect in game_state["suspects"]:
    # Find the correct long description from motive_pools
    found = False
    for pool in motive_pools:
        for m in pool:
            if m["short"] == suspect["motive"]:
                suspect["motive_long"] = m["long"]
                found = True
                break
        if found:
            break
    suspect["relationship"] = random.choice(relationship_responses)
    # Fallback: use motive_descriptions if not found
    if not found:
        suspect["motive_long"] = motive_descriptions.get(suspect["motive"], "No details.")
# --- Add this block here to ensure relationship is present after loading a game ---
for suspect in game_state.get("suspects", []):
    if "relationship" not in suspect:
        suspect["relationship"] = random.choice(relationship_responses)

def get_pronoun(suspect, case="subject"):
    # case: "subject" -> he/she, "object" -> him/her, "possessive" -> his/her
    gender = suspect.get("gender", "Male")
    if gender == "Female":
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
    else:
        return {"subject": "he", "object": "him", "possessive": "his"}[case]
    
def mark_quest_completed(quest_text):
    for idx, quest in enumerate(game_state["quests"]):
        plain_quest = quest.replace("\033[9m", "").replace("\033[0m", "")
        if plain_quest == quest_text:
            game_state["quests"][idx] = f"\033[9m{quest_text}\033[0m"
            break

def timing_bullseye_chase(rounds=3, escape_distance=4, mode="chase"):
    """
    A chase minigame: Press SPACE when the red circle (●) is in the bullseye (◎)!
    If mode == "boss", just return True/False for hit/miss (no escape logic, no room movement, no chase text).
    """
    import sys, time
    import msvcrt

    if mode == "boss":
        print("Time your attack! Press SPACE when the red circle (●) is in the bullseye (◎)!")
        positions = list(range(1, 22))  # 1 to 21
        center = 11
        pos = 1
        direction = 1
        hit = False

        start_time = time.time()
        while time.time() - start_time < 3:  # 3 seconds per round
            display = "|"
            for i in range(1, 22):
                if i == pos and i == center:
                    display += f"{YELLOW}{RED}◎{RESET}"  # Overlap
                elif i == pos:
                    display += f"{RED}◉{RESET}"
                elif i == center:
                    display += f"{YELLOW}◎{RESET}"
                else:
                    display += "."
            display += "|"
            sys.stdout.write("\r" + display)
            sys.stdout.flush()
            time.sleep(0.08)
            pos += direction
            if pos == 21 or pos == 1:
                direction *= -1
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key == b' ':
                    if abs(pos - center) <= 1:  # Forgiving: allow hit if within 1 of center
                        hit = True
                    break
        sys.stdout.write("\n")
        return hit

    # --- Original chase logic below ---
    print("A chase begins! Press SPACE when the red circle (●) is in the bullseye (◎)!")
    positions = list(range(1, 22))  # 1 to 21
    center = 11
    distance = 3

    while True:
        pos = 1
        direction = 1
        hit = False
        print(f"\nDistance from pursuer: {distance}")
        print("Get ready...")

        # Animate the cursor for a few cycles
        start_time = time.time()
        while time.time() - start_time < 3:  # 3 seconds per round
            display = "|"
            for i in range(1, 22):
                if i == pos and i == center:
                    display += f"{YELLOW}{RED}◎{RESET}"  # Overlap
                elif i == pos:
                    display += f"{RED}◉{RESET}"
                elif i == center:
                    display += f"{YELLOW}◎{RESET}"
                else:
                    display += "."
            display += "|"
            sys.stdout.write("\r" + display)
            sys.stdout.flush()
            time.sleep(0.08)
            pos += direction
            if pos == 21 or pos == 1:
                direction *= -1
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key == b' ':
                    if abs(pos - center) <= 1:  # Forgiving: allow hit if within 1 of center
                        hit = True
                        break
                    else:
                        break
        sys.stdout.write("\n")
        if hit:
            print("Bullseye! You gain ground!")
            distance += 1
        else:
            print("Missed! The pursuer closes in!")
            distance -= 1

        if distance >= escape_distance:
            print("You have escaped! The monster gives up the chase and slinks away into the shadows. In a panic you run through the manor, finding a safe place to hide in a previously visited room.")
            visited_rooms = [pos for pos in game_state["visited_locations"].keys() if pos != game_state["position"]]
            if visited_rooms:
                new_pos = random.choice(visited_rooms)
                game_state["position"] = new_pos
                game_state["location"] = game_state["visited_locations"][new_pos]
                delay_print(f"{YELLOW}You stumble blindly through the manor and find yourself in the {game_state['location']}.{RESET}")
                for suspect in game_state["suspects"]:
                    if suspect.get("transformed", False):
                        suspect["chasing_player"] = True
            move_suspects()
            mark_quest_completed("Successfully evade an underworld monstrosity")
            game_state["journal"].append("A monstrous horror chased me through the manor’s twisting halls. Heart pounding, I escaped its grasp and found refuge in a room I’d visited before.")
            wait_for_space("Press SPACE to continue.")

            # Achievement: Evaded every monstrosity
            total_monstrosities = sum(1 for s in game_state["suspects"] if s.get("transformed", False))
            evaded_count = sum(1 for entry in game_state["journal"] if "Successfully evade an underworld monstrosity" in entry or "escaped its grasp" in entry)
            if total_monstrosities > 0 and evaded_count >= total_monstrosities:
                if "Evaded every monstrosity" not in game_state["achievements"]:
                    game_state["achievements"].add("Evaded every monstrosity")
                    game_state["score"] += ACHIEVEMENT_SCORE
                    print(f"{CYAN}Achievement unlocked: {ACHIEVEMENTS['Evaded every monstrosity']} (+{ACHIEVEMENT_SCORE} points){RESET}")

            return True

        elif distance <= 0:
            if "Abraxas Amulet" in game_state["inventory"]:
                print(f"{ORANGE}As the monstrosity lunges, the Abraxas Amulet blazes with power! A wave of force banishes the horror in a flash of golden light. You are saved!{RESET}")
                wait_for_space("Press SPACE to continue.")
                return True  # Player escapes
            else:
                print(RED + "The monster catches you and rips out your heart, devouring it before your dying eyes." + RESET)
            print(RED + r"""
 __     __           _____  _          _ 
 \ \   / /          |  __ \(_)        | |
  \ \_/ /__  _   _  | |  | |_  ___  __| |
   \   / _ \| | | | | |  | | |/ _ \/ _` |
    | | (_) | |_| | | |__| | |  __/ (_| |
    |_|\___/ \__,_| |_____/|_|\___|\__,_|
    """ + RESET)
            game_state["stamina"] = 0
            wait_for_space("Press SPACE to continue.")
            show_score()
            wait_for_space()
            title_screen()
            return False

def wait_for_space(prompt="Press SPACE to continue."):
    print(prompt)
    while True:
        key = msvcrt.getch()
        if key == b' ':
            break

def get_direction_from_arrow():
    """Wait for an arrow key and return 'n', 's', 'e', or 'w', or None if not an arrow."""
    first = msvcrt.getch()
    if first == b'\xe0':  # Arrow key prefix
        second = msvcrt.getch()
        if second == b'H':
            return 'n'
        elif second == b'P':
            return 's'
        elif second == b'K':
            return 'w'
        elif second == b'M':
            return 'e'
    return None

def roll_fudge(num_dice=4): # FUDGE combat dice system
    return sum(random.choice([-1, 0, 1]) for _ in range(num_dice))

def show_setting():
    clear()
    print("\033[1;32m=== THE SETTING ===\033[0m")
    delay_print(
        "London, 1915. The city is a labyrinth of gaslit alleys and cobblestone streets, shrouded nightly in a fog so thick it seems to swallow sound and memory alike. "
        "Shadows stretch long beneath the flickering lamps, and the air is heavy with the scent of rain, coal smoke, and secrets best left unspoken.\n"
        "\n"
        "Beyond the city’s edge, a brooding manor rises from the mist, its windows dark and its gardens overgrown. Locals cross themselves and hurry past its gates, whispering of strange lights and unearthly sounds that drift from its halls after midnight. "
        "The house is said to be haunted, but none dare approach to find out for certain.\n"
        "\n"
        "You are an investigator, summoned by urgent letter to pierce the gloom and unravel the truth behind the manor’s growing legend. The night is thick with dread, and something ancient stirs beneath the veneer of civilization."
    )
    wait_for_space()

def show_mystery():
    clear()
    print("\033[1;32m=== THE MYSTERY ===\033[0m")
    text = (
        "The Bishop Alaric Greaves—a powerful, controversial and enigmatic figure known for his fiery sermons and secretive habits—has vanished without a trace. "
        "Four suspects, each with their own secrets and motives, have been detained within the manor by the fearful townsfolk. "
        "The house itself seems to resist intrusion, its corridors shifting and its rooms echoing with the past.\n"
        "\n"
        "Your task is clear: gather clues, collect alibis, and listen closely to the stories each suspect weaves.\n"
    )
    if "bishop_last_location" in game_state and "bishop_last_time" in game_state:
        text += f"The Bishop was last seen in the {game_state['bishop_last_location']} at {game_state['bishop_last_time']}.\n"
    text += (
        "Piece together the truth from your journal entries, for only by careful deduction can you hope to solve the mystery of the Bishop’s disappearance.\n"
        "\n"
        "Rumors speak of strange artifacts and forgotten relics hidden within the manor’s depths—items that may aid your investigation or test your resolve. "
        "The answers you seek lie somewhere within these haunted walls. Trust your wits, for the shadows are watching."
    )
    delay_print(text)
    wait_for_space()

def show_how_to_play():
    clear()
    print("\033[1;32m=== HOW TO PLAY ===\033[0m")
    delay_print(
        "To win, you must solve the Bishop's disappearance by deducing which suspect had the motive, opportunity, and means.\n"
        "\n"
        "Explore the haunted manor room by room. Search for clues and evidence—these are essential for piecing together the truth. "
        "Interrogate suspects you encounter: listen to their alibis, question their motives, and look for contradictions. "
        "A true detective aligns clues with alibis and motives, and identifies who had the opportunity to commit the crime.\n"
        "\n"
        "Scattered throughout the manor are mysterious artifacts and items. Some may aid your investigation, others may test your resolve or sanity.\n"
        "\n"
        "Once five clues are collected and two suspects interrogated you can attempt to solve the case by making an accusation. "
        "Movement is grid-based: use N/S/E/W or arrow keys to travel. The map and journal will help you keep track of your discoveries. "
        "Menus allow you to check your inventory, stats, and review your journal at any time.\n"
        "\n"
        "During character creation, choose your background and distribute your stats. Your choices affect your abilities and how you interact with the world.\n"
        "\n"
        "Persuasion is a special power—use it wisely to break through a suspect's defenses. "
        "Melee combat is possible, but discouraged; violence may have dire consequences and is rarely the path to true justice.\n"
        "\n"
        "A much larger mystery lurks in the shadows of the manor. Trust your wits, gather evidence, and let deduction be your guide."
    )
    wait_for_space()

def show_persuasion_lore():
    clear()
    print("\033[1;32m=== ON THE ART OF PERSUASION ===\033[0m")
    delay_print(
        '“To bend the will of another is not always a matter of lies, nor of truth—but of timing, tone, and tenacity. '
        'One must not only know what to say, but what they are ready to hear.”\n'
        '—Father Elric Greaves, Disputationes de Spiritu et Lingua\n'
        '\n'
        'Persuasion, like faith, is fragile. It thrives on:\n'
        '\n'
        '  Reputation – They must believe you are who you say you are.\n'
        '  Observation – Truth is seen in the pauses between words.\n'
        '  Comeliness – Beauty opens doors, but sincerity keeps them ajar.\n'
        '  Sanity – The broken mind sees patterns, but not always the right ones.\n'
        '\n'
        'You may persuade others only when the moment allows. Some will resist. Others will weep. '
        'The deeper your insight, the more likely your words will draw out what was hidden.\n'
        '\n'
        'Yet take heed:\n'
        '“Even the most honeyed voice can become a howl if madness takes root.”\n'
        '\n'
    )
    wait_for_space()

import random

def debug_add_artifact():
    """Debug: Add any artifact to inventory by name or number."""
    clear()
    print("=== DEBUG: Add Artifact to Inventory ===")
    print("Artifacts available:")
    for idx, artifact in enumerate(artifact_pool, 1):
        print(f"[{idx}] {artifact['name']}")
    print(f"[{len(artifact_pool)+1}] Return")
    choice = input("Select artifact by number or enter name: ").strip()
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(artifact_pool):
            artifact_name = artifact_pool[idx]["name"]
        elif idx == len(artifact_pool):
            return
        else:
            print("Invalid number.")
            wait_for_space()
            return
    else:
        artifact_name = choice
        if artifact_name not in [a["name"] for a in artifact_pool]:
            print("Invalid artifact name.")
            wait_for_space()
            return
    if artifact_name not in game_state["inventory"]:
        game_state["inventory"].append(artifact_name)
        print(f"Added '{artifact_name}' to inventory.")
    else:
        print(f"'{artifact_name}' is already in inventory.")
    wait_for_space()

def place_special_rooms():
    # Example: Place the chapel randomly
    possible_positions = [(x, y) for x in range(MAP_MIN, MAP_MAX+1) for y in range(MAP_MIN, MAP_MAX+1)]
    possible_positions.remove(game_state["entrance"])  # Don't place chapel at entrance
    chapel_pos = random.choice(possible_positions)
    game_state["chapel"] = chapel_pos
    game_state["rooms"][chapel_pos] = {"type": "Chapel", "visited": False}

def generate_passages():
    """
    Generate a maze with long corridors using a direction bias.
    Fills game_state['passages'] with a dict of {pos: set(moves)}.
    """
    width = MAP_MAX - MAP_MIN + 1
    height = MAP_MAX - MAP_MIN + 1
    grid = {}
    for x in range(MAP_MIN, MAP_MAX + 1):
        for y in range(MAP_MIN, MAP_MAX + 1):
            grid[(x, y)] = set()

    start = (0, 0)
    visited = set([start])
    stack = [(start, None)]  # (position, previous_direction)
    while stack:
        (x, y), prev_dir = stack[-1]
        unvisited_neighbors = []
        for dir_name, (dx, dy) in moves.items():
            nx, ny = x + dx, y + dy
            neighbor = (nx, ny)
            if MAP_MIN <= nx <= MAP_MAX and MAP_MIN <= ny <= MAP_MAX and neighbor not in visited:
                unvisited_neighbors.append((dir_name, neighbor))
        if unvisited_neighbors:
            # Bias: 90% chance to continue in the same direction if possible
            if prev_dir and any(d == prev_dir for d, _ in unvisited_neighbors) and random.random() < 0.9:
                dir_name, neighbor = next((d, n) for d, n in unvisited_neighbors if d == prev_dir)
            else:
                dir_name, neighbor = random.choice(unvisited_neighbors)
            # Carve passage
            grid[(x, y)].add(dir_name)
            # Add reverse direction for neighbor
            for rev_dir, (dx, dy) in moves.items():
                if (x, y) == (neighbor[0] + dx, neighbor[1] + dy):
                    grid[neighbor].add(rev_dir)
                    break
            visited.add(neighbor)
            stack.append((neighbor, dir_name))
        else:
            stack.pop()

    game_state["passages"] = grid

# def auto_generate_walls_and_doors():
#     """
#     After maze generation, explicitly add a wall or door for every non-passage between adjacent rooms.
#     Then, add extra random walls/doors to ensure at least 20 total barriers.
#     """
#     game_state["walls"] = set()
#     game_state["locked_doors"] = set()
#     foyer_pos = (0, 0)
#     door_ratio = 0.2  # 20% of barriers are doors, 80% are walls
#     min_barriers = 60  # Minimum total number of walls + doors

#     # First, add walls/doors for all non-passages
#     for (x, y), exits in game_state["passages"].items():
#         for dir_name, (dx, dy) in moves.items():
#             nx, ny = x + dx, y + dy
#             neighbor = (nx, ny)
#             if dir_name in {"n", "s", "e", "w"} and MAP_MIN <= nx <= MAP_MAX and MAP_MIN <= ny <= MAP_MAX:
#                 if dir_name not in exits:
#                     if random.random() < door_ratio:
#                         # Find reverse direction
#                         rev_dir = None
#                         for d, (ddx, ddy) in moves.items():
#                             if (ddx, ddy) == (-dx, -dy):
#                                 rev_dir = d
#                                 break
#                         if rev_dir is not None:
#                             game_state["passages"][pos].add(dir_name)
#                             game_state["passages"][neighbor].add(rev_dir)
#                             game_state["locked_doors"].add(((x, y), neighbor))
#                             game_state["locked_doors"].add((neighbor, (x, y)))
#                         else:
#                             # If reverse direction not found, do not add passage for neighbor
#                             game_state["passages"][pos].add(dir_name)
#                             game_state["locked_doors"].add(((x, y), neighbor))
#                             game_state["locked_doors"].add((neighbor, (x, y)))
#                     else:
#                         game_state["walls"].add(((x, y), neighbor))
#                         game_state["walls"].add((neighbor, (x, y)))

#     # Surround the grid with walls except for the foyer exit
#     for x in range(MAP_MIN, MAP_MAX + 1):
#         for y in range(MAP_MIN, MAP_MAX + 1):
#             pos = (x, y)
#             # North edge
#             if y == MAP_MIN:
#                 if pos != foyer_pos or "n" not in game_state["passages"].get(foyer_pos, set()):
#                     game_state["walls"].add(((x, y), (x, y - 1)))
#                     game_state["walls"].add(((x, y - 1), (x, y)))
#             # South edge
#             if y == MAP_MAX:
#                 game_state["walls"].add(((x, y), (x, y + 1)))
#                 game_state["walls"].add(((x, y + 1), (x, y)))
#             # West edge
#             if x == MAP_MIN:
#                 game_state["walls"].add(((x, y), (x - 1, y)))
#                 game_state["walls"].add(((x - 1, y), (x, y)))
#             # East edge
#             if x == MAP_MAX:
#                 game_state["walls"].add(((x, y), (x + 1, y)))
#                 game_state["walls"].add(((x + 1, y), (x, y)))

#     # --- Add extra random walls/doors to reach at least min_barriers ---
#     all_possible = []
#     for (x, y) in game_state["passages"]:
#         for dir_name, (dx, dy) in moves.items():
#             nx, ny = x + dx, y + dy
#             neighbor = (nx, ny)
#             if (
#                 dir_name in {"n", "s", "e", "w"}
#                 and MAP_MIN <= nx <= MAP_MAX and MAP_MIN <= ny <= MAP_MAX
#                 and ((x, y), neighbor) not in game_state["walls"]
#                 and ((x, y), neighbor) not in game_state["locked_doors"]
#                 and dir_name not in game_state["passages"][(x, y)]
#             ):
#                 # Only add each pair once
#                 if ((x, y), neighbor) < ((neighbor, (x, y))):
#                     all_possible.append(((x, y), neighbor))

#     current_barriers = len(game_state["walls"]) // 2 + len(game_state["locked_doors"]) // 2
#     target_barriers = max(current_barriers * 2, min_barriers)

#     random.shuffle(all_possible)
#     i = 0
#     while current_barriers < target_barriers and i < len(all_possible):
#         pair = all_possible[i]
#         if random.random() < door_ratio:
#             game_state["locked_doors"].add(pair)
#             game_state["locked_doors"].add((pair[1], pair[0]))
#         else:
#             game_state["walls"].add(pair)
#             game_state["walls"].add((pair[1], pair[0]))
#         current_barriers += 1
#         i += 1

# Call this function at the start of a new game/case, before initializing suspects and clues:

# def seal_region_with_locked_door(region_a, region_b):
#     """
#     Seal off region_b from region_a with a locked door, ensuring no other passages connect them.
#     region_a and region_b are lists of positions (tuples).
#     """
#     # Find all adjacent pairs between regions
#     for pos_a in region_a:
#         for pos_b in region_b:
#             if abs(pos_a[0] - pos_b[0]) + abs(pos_a[1] - pos_a[1]) == 1:
#                 # Remove all passages between region_a and region_b
#                 for dir_name, (dx, dy) in moves.items():
#                     if (pos_a[0] + dx, pos_a[1] + dy) == pos_b:
#                         game_state["passages"][pos_a].discard(dir_name)
#                     if (pos_b[0] + dx, pos_b[1] + dy) == pos_a:
#                         game_state["passages"][pos_b].discard(dir_name)
#                 # Add locked door both ways
#                 game_state["locked_doors"].add((pos_a, pos_b))
#                 game_state["locked_doors"].add((pos_b, pos_a))
#     # Remove any other passages between region_a and region_b (not just direct neighbors)
#     for pos_a in region_a:
#         for pos_b in region_b:
#             for dir_name, (dx, dy) in moves.items():
#                 if (pos_a[0] + dx, pos_a[1] + dy) == pos_b or (pos_b[0] + dx, pos_b[1] + dy) == pos_a:
#                     continue  # Already handled above
#                 # Remove indirect passages
#                 game_state["passages"][pos_a].discard(dir_name)
#                 game_state["passages"][pos_b].discard(dir_name)
            
# def seal_random_region_with_locked_door():
#     # Get all room positions (excluding Foyer)
#     all_positions = [pos for pos, room in game_state["visited_locations"].items() if room != "Foyer"]
#     if len(all_positions) < 2:
#         print("Not enough rooms to seal a region.")
#         return

#     # Pick two random positions to serve as the "bridge" for the locked door
#     pos_a, pos_b = random.sample(all_positions, 2)

#     # Find all positions connected to pos_b (the sealed region) via passages
#     sealed_region = set()
#     queue = [pos_b]
#     visited = set([pos_a])  # Don't include pos_a's region
#     while queue:
#         current = queue.pop()
#         sealed_region.add(current)
#         for dir_name in game_state["passages"].get(current, []):
#             dx, dy = moves[dir_name]
#             neighbor = (current[0] + dx, current[1] + dy)
#             if neighbor not in visited and neighbor not in sealed_region:
#                 queue.append(neighbor)
#                 visited.add(neighbor)

#     # Remove all passages between pos_a and pos_b, add a locked door
#     for dir_name, (dx, dy) in moves.items():
#         if (pos_a[0] + dx, pos_a[1] + dy) == pos_b:
#             game_state["passages"][pos_a].discard(dir_name)
#         if (pos_b[0] + dx, pos_b[1] + dy) == pos_a:
#             game_state["passages"][pos_b].discard(dir_name)
#     game_state["locked_doors"].add((pos_a, pos_b))
#     game_state["locked_doors"].add((pos_b, pos_a))

#     # Place a clue or artifact in the sealed region (pos_b)
#     room_b = game_state["visited_locations"][pos_b]
#     possible_clues = [c for c in game_state.get("clue_pool", []) if c not in game_state.get("clues", [])]
#     possible_artifacts = [a for a in artifact_pool if a["name"] != "Silver Ornate Key" and a["name"] not in [v["name"] for v in game_state.get("artifact_locations", {}).values()]]
#     if possible_clues and random.random() < 0.5:
#         clue_locations[room_b] = random.choice(possible_clues)
#     elif possible_artifacts:
#         game_state.setdefault("artifact_locations", {})[room_b] = random.choice(possible_artifacts)

#     # Place the Silver Ornate Key in a random room NOT in the sealed region
#     outside_positions = [pos for pos in all_positions if pos not in sealed_region and pos != pos_a]
#     if outside_positions:
#         key_pos = random.choice(outside_positions)
#         key_room = game_state["visited_locations"][key_pos]
#         game_state.setdefault("artifact_locations", {})[key_room] = next(a for a in artifact_pool if a["name"] == "Silver Ornate Key")
#         print(f"Silver Ornate Key placed in {key_room}.")
#     else:
#         print("No valid position found for Silver Ornate Key (all rooms are sealed or unavailable).")

#     # Debug output
#     print(f"Locked door placed between {game_state['visited_locations'][pos_a]} and {game_state['visited_locations'][pos_b]}.")
#     print(f"Clue/artifact placed in {room_b}.")

# # Call this after auto_generate_walls_and_doors() in character_creation():
# # seal_random_region_with_locked_door()

def random_15min_time(hour_range=(21, 24)):
    hour = random.randint(*hour_range)
    minute = random.choice([0, 15, 30, 45])
    suffix = "pm" if hour < 24 else "am"
    display_hour = hour if hour <= 12 else hour - 12
    if display_hour == 0:
        display_hour = 12
    return f"{display_hour}:{minute:02d}{suffix}"

def initialize_suspects():
    # Set number of suspects based on difficulty
    num_suspects = 4 if game_state.get("difficulty") == "easy" else 8

    # The culprit and other_suspects should already be set up by associate_culprit_and_pools()
    # game_state["suspects"] = [culprit] + other_suspects

    player_pos = (0, 0)
    # Generate possible positions within 2-4 tiles of player and inside bounds
    possible_positions = []
    for dx in range(-4, 5):
        for dy in range(-4, 5):
            dist = abs(dx) + abs(dy)
            pos = (player_pos[0] + dx, player_pos[1] + dy)
            if 2 <= dist <= 4 and MAP_MIN <= pos[0] <= MAP_MAX and MAP_MIN <= pos[1] <= MAP_MAX and pos != player_pos:
                possible_positions.append(pos)
    chosen_positions = random.sample(possible_positions, num_suspects)
    for suspect, pos in zip(game_state["suspects"], chosen_positions):
        suspect["position"] = pos
        suspect["wait_turns"] = 0
        # Only assign random stats if not already set
        if "strength" not in suspect:
            suspect["strength"] = random.randint(10, 16)
        if "stamina" not in suspect:
            suspect["stamina"] = random.randint(10, 16)
        if "agility" not in suspect:
            suspect["agility"] = random.randint(9, 15)
        suspect["tolerance"] = game_state.get("suspect_tolerance", 5)

    # --- Assign murderer at random if not already set ---
    if not any(s.get("is_murderer") for s in game_state["suspects"]):
        murderer = random.choice(game_state["suspects"])
        for suspect in game_state["suspects"]:
            suspect["is_murderer"] = (suspect is murderer)
        game_state["murderer"] = murderer["name"]

    # Assign random, gendered, motive-matching flavor text
    for suspect in game_state["suspects"]:
        motive = suspect.get("motive")
        gender = suspect.get("gender", "Male")
        options = motive_flavor_texts.get(motive, {}).get(gender, [])
        if options:
            suspect["flavor_text"] = random.choice(options)
        else:
            suspect["flavor_text"] = motive_descriptions.get(motive, "They seem difficult to read.")
        suspect["flavor_text_shown"] = False  # Track if long flavor text has been shown

    # --- Assign new interrogation fields to each suspect ---
    for i, suspect in enumerate(game_state["suspects"]):
        suspect["means"] = means_pool[i % len(means_pool)]
        suspect["knowledge"] = knowledge_pool[i % len(knowledge_pool)]
        suspect["witnesses"] = witnesses_pool[i % len(witnesses_pool)]
        suspect["financial"] = financial_pool[i % len(financial_pool)]
        suspect["secret_relationship"] = secret_relationship_pool[i % len(secret_relationship_pool)]
        suspect["blackmail"] = blackmail_pool[i % len(blackmail_pool)]
        suspect["confession"] = confession_pool[i % len(confession_pool)]
        
    # After assigning suspects, randomly pick 2-3 suspects to have "strong" opportunity, rest get "weak" or "uncertain"
    # opportunity_levels = ["strong", "weak", "uncertain"]
    num_strong = min(3, len(game_state["suspects"]))  # Up to 3 suspects per game

    strong_indices = random.sample(range(len(game_state["suspects"])), num_strong)
    for i, suspect in enumerate(game_state["suspects"]):
        if i in strong_indices:
            suspect["opportunity"] = "strong"
        else:
            suspect["opportunity"] = random.choice(["weak", "uncertain"])

# Define motive flavor texts
flavor_text_pool = [
    "A cold breeze blows by.",
    "You hear the baying of wolves in the distance.",
    "A floorboard creaks behind you.",
    "A faint whisper echoes through the hall.",
    "The candlelight flickers, casting strange shadows.",
    "You feel as if someone is watching.",
    "A distant clock chimes, though you see no clock.",
    "The scent of old incense lingers in the air.",
    "A shiver runs down your spine.",
    "You hear a door slam somewhere far away."
]
if "room_flavor_used" not in game_state:
    game_state["room_flavor_used"] = {}

clue_pools = [
    [
        "A blood-stained prayer book.",
        "A silver pendant etched with tentacles.",
        "An empty ritual circle drawn in chalk.",
        "A coded diary mentioning a 'Summoning'.",
        "A torn hymnbook page with a cryptic note.",
        "A broken locket containing a faded photograph.",
        "A vial of strange blue liquid.",
        "A chess piece carved from bone."
    ],
    [
        "A torn dance card.",
        "A wilted rose with a hidden note.",
        "A pawn ticket for a golden chalice, issued the day before the Bishop vanished.",
        "A threatening note warning the Bishop to abandon his 'awakening.'",
        "A bloodied handkerchief embroidered with initials.",
        "A letter confessing to a secret affair.",
        "A diary entry mentioning a midnight visitor.",
        "A set of muddy footprints leading to the attic."
    ],
    [
        "A candle stub melted into the shape of a screaming face.",
        "A cryptic telegram signed only with the letter 'V'.",
        "A bloodied scrap of choir robe hidden behind the altar.",
        "A torn page from a bestiary describing 'The Watcher in the Fog.'",
        "A chess piece carved from bone.",
        "A vial labeled 'Do Not Drink'.",
        "A burnt scrap of parchment with arcane symbols.",
        "A lock of hair tied with a red ribbon."
    ],
    [
        "A broken window latch.",
        "A missing library ledger.",
        "A muddy boot print.",
        "A page torn from a forbidden tome.",
        "A shattered monocle near the cellar stairs.",
        "A bloodstained glove found in the garden.",
        "A torn map showing secret passages.",
        "A scorched scrap of sermon notes."
    ],
    [
        "A star chart with strange markings.",
        "A bloodstained handkerchief.",
        "A monogrammed glove found in the garden.",
        "A shattered monocle near the cellar stairs.",
        "A faded photograph of the Bishop and an unknown figure.",
        "A silver key engraved with runes.",
        "A pressed flower stained with blood.",
        "A page from a diary describing a hidden ritual."
    ],
    [
        "A pawn ticket for a golden chalice.",
        "A burnt letter addressed to the Bishop.",
        "A torn page from a guestbook.",
        "A vial of laudanum, nearly empty.",
        "A bloodied handkerchief with a family crest.",
        "A coded message hidden in a painting.",
        "A scrap of fabric matching the Bishop's robe.",
        "A broken rosary found in the crypt."
    ],
    [
        "A diary entry about a forbidden meeting.",
        "A pressed flower from the conservatory.",
        "A torn invitation to a secret gathering.",
        "A bloodstained page from a ledger.",
        "A silver ring inscribed with strange symbols.",
        "A burnt candle stub found in the attic.",
        "A cryptic note referencing the 'Elder Ones'.",
        "A page from a lost sermon."
    ],
    [
        "A bloodied scrap of choir robe.",
        "A torn letter from the Bishop addressed to Lady Ashcroft.",
        "A pawn ticket for a golden chalice.",
        "A threatening note warning the Bishop.",
        "A coded diary mentioning a 'Summoning'.",
        "A vial of strange blue liquid.",
        "A chess piece carved from bone.",
        "A lock of hair tied with a red ribbon."
    ]
]

clue_motives_pools = [
    {
        "A blood-stained prayer book.": "Fanaticism",
        "A silver pendant etched with tentacles.": "Fanaticism",
        "An empty ritual circle drawn in chalk.": "Fanaticism",
        "A coded diary mentioning a 'Summoning'.": "Revenge",
        "A torn hymnbook page with a cryptic note.": "Jealousy",
        "A broken locket containing a faded photograph.": "Forbidden Love",
        "A vial of strange blue liquid.": "Desperation",
        "A chess piece carved from bone.": "Obsession"
    },
    {
        "A torn dance card.": "Jealousy",
        "A wilted rose with a hidden note.": "Forbidden Love",
        "A pawn ticket for a golden chalice, issued the day before the Bishop vanished.": "Desperation",
        "A threatening note warning the Bishop to abandon his 'awakening.'": "Fear",
        "A bloodied handkerchief embroidered with initials.": "Guilt",
        "A letter confessing to a secret affair.": "Blackmail",
        "A diary entry mentioning a midnight visitor.": "Loyalty",
        "A set of muddy footprints leading to the attic.": "Ambition"
    },
    {
        "A candle stub melted into the shape of a screaming face.": "Obsession",
        "A cryptic telegram signed only with the letter 'V'.": "Blackmail",
        "A bloodied scrap of choir robe hidden behind the altar.": "Guilt",
        "A torn page from a bestiary describing 'The Watcher in the Fog.'": "Fear",
        "A chess piece carved from bone.": "Obsession",
        "A vial labeled 'Do Not Drink'.": "Despair",
        "A burnt scrap of parchment with arcane symbols.": "Curiosity",
        "A lock of hair tied with a red ribbon.": "Forbidden Love"
    },
    {
        "A broken window latch.": "Ambition",
        "A missing library ledger.": "Blackmail",
        "A muddy boot print.": "Desperation",
        "A page torn from a forbidden tome.": "Blackmail",
        "A shattered monocle near the cellar stairs.": "Ambition",
        "A bloodstained glove found in the garden.": "Revenge",
        "A torn map showing secret passages.": "Curiosity",
        "A scorched scrap of sermon notes.": "Remorse"
    },
    {
        "A star chart with strange markings.": "Obsession",
        "A bloodstained handkerchief.": "Revenge",
        "A monogrammed glove found in the garden.": "Jealousy",
        "A shattered monocle near the cellar stairs.": "Ambition",
        "A faded photograph of the Bishop and an unknown figure.": "Forbidden Love",
        "A silver key engraved with runes.": "Curiosity",
        "A pressed flower stained with blood.": "Remorse",
        "A page from a diary describing a hidden ritual.": "Zealotry"
    },
    {
        "A pawn ticket for a golden chalice.": "Greed",
        "A burnt letter addressed to the Bishop.": "Resentment",
        "A torn page from a guestbook.": "Duty",
        "A vial of laudanum, nearly empty.": "Despair",
        "A bloodied handkerchief with a family crest.": "Guilt",
        "A coded message hidden in a painting.": "Manipulation",
        "A scrap of fabric matching the Bishop's robe.": "Loyalty",
        "A broken rosary found in the crypt.": "Zealotry"
    },
    {
        "A diary entry about a forbidden meeting.": "Forbidden Love",
        "A pressed flower from the conservatory.": "Remorse",
        "A torn invitation to a secret gathering.": "Curiosity",
        "A bloodstained page from a ledger.": "Blackmail",
        "A silver ring inscribed with strange symbols.": "Obsession",
        "A burnt candle stub found in the attic.": "Despair",
        "A cryptic note referencing the 'Elder Ones'.": "Fanaticism",
        "A page from a lost sermon.": "Zealotry"
    },
    {
        "A bloodied scrap of choir robe.": "Guilt",
        "A torn letter from the Bishop addressed to Lady Ashcroft.": "Forbidden Love",
        "A pawn ticket for a golden chalice.": "Greed",
        "A threatening note warning the Bishop.": "Fear",
        "A coded diary mentioning a 'Summoning'.": "Revenge",
        "A vial of strange blue liquid.": "Desperation",
        "A chess piece carved from bone.": "Obsession",
        "A lock of hair tied with a red ribbon.": "Jealousy"
    }
]

clue_flavor_explanations = {
    "A torn hymnbook page with a cryptic note.": {
        "Jealousy": "The torn page and cryptic note suggest resentment over the Bishop’s attention to another.",
        "Fanaticism": "The cryptic note may be a fragment of forbidden scripture, torn out by a zealot.",
        "Revenge": "The hymnbook was defaced as an act of spite, a symbolic attack on what the Bishop held dear.",
        "Forbidden Love": "A secret message, perhaps a lover’s lament, hidden in the hymnbook.",
        "Desperation": "A desperate plea or warning, scrawled in haste.",
        "Ambition": "A coded message about seizing opportunity, hidden in plain sight.",
        "Obsession": "The cryptic note is a fixation, a clue left by someone who cannot let go.",
        "Fear": "A warning, torn out in panic, left behind by someone afraid of discovery."
    },
    "A monogrammed glove found in the garden.": {
        "Jealousy": "A personal item left at the scene of a secret confrontation, likely driven by envy.",
        "Forbidden Love": "The glove hints at a clandestine meeting, perhaps between lovers forced to hide their passion.",
        "Revenge": "A token dropped during a heated argument, a sign of personal vendetta.",
        "Ambition": "Evidence of a late-night meeting to plot advancement.",
        "Desperation": "Lost in a frantic escape, the glove marks a desperate act.",
        "Obsession": "The glove was taken as a keepsake, then lost in pursuit.",
        "Fear": "Dropped in flight, the owner terrified of being caught.",
        "Fanaticism": "A ritual token, left behind after a secret ceremony."
    },
    "A blood-stained prayer book.": {
        "Fanaticism": "Blood on a sacred text suggests a ritual gone awry or a zealot's sacrifice.",
        "Revenge": "The prayer book was defiled as a message to the Bishop.",
        "Jealousy": "A rival may have destroyed what the Bishop cherished most.",
        "Forbidden Love": "A lover's quarrel turned violent, leaving a mark on the Bishop's faith.",
        "Desperation": "A desperate act, perhaps in a plea for forgiveness.",
        "Ambition": "A warning to the Bishop, left by someone seeking his position.",
        "Obsession": "The book was handled obsessively, its pages worn and stained.",
        "Fear": "Blood stains left by trembling hands, perhaps in self-defense."
    },
    "A silver pendant etched with tentacles.": {
        "Fanaticism": "A cultist's token, worn by those devoted to forbidden gods.",
        "Obsession": "The pendant is a focus for dark, consuming thoughts.",
        "Curiosity": "A collector's curiosity led to dangerous discoveries.",
        "Ambition": "A symbol of secret society membership, used to gain influence.",
        "Desperation": "Pawned or stolen in a moment of need.",
        "Jealousy": "A gift given to another, now reclaimed in anger.",
        "Revenge": "A mark of those who seek to punish the Bishop.",
        "Fear": "Kept as a ward against unknown terrors."
    },
    "An empty ritual circle drawn in chalk.": {
        "Fanaticism": "A zealot prepared the circle for a forbidden rite.",
        "Obsession": "Drawn and redrawn, the circle is a sign of compulsive behavior.",
        "Curiosity": "A scholar's experiment gone too far.",
        "Desperation": "A last-ditch effort to summon help or power.",
        "Ambition": "A calculated risk to gain supernatural advantage.",
        "Jealousy": "A rival tried to curse the Bishop.",
        "Revenge": "A ritual intended to bring ruin to an enemy.",
        "Fear": "A protective ward, hastily drawn in terror."
    },
    "A coded diary mentioning a 'Summoning'.": {
        "Revenge": "Plans for vengeance are hidden in the diary's code.",
        "Fanaticism": "The diary details preparations for a sacred summoning.",
        "Obsession": "The writer is fixated on unlocking forbidden secrets.",
        "Curiosity": "A record of dangerous experiments.",
        "Ambition": "A plot to summon power for personal gain.",
        "Desperation": "A plea for supernatural intervention.",
        "Jealousy": "A rival's attempt to win favor through dark means.",
        "Fear": "A warning to self, never to attempt the ritual again."
    },
    "A broken locket containing a faded photograph.": {
        "Forbidden Love": "A keepsake from a secret romance, now shattered.",
        "Jealousy": "A rival destroyed the locket in a fit of envy.",
        "Remorse": "The locket was broken in regret after a tragic event.",
        "Obsession": "The photograph is worn from constant handling.",
        "Desperation": "A memento clung to in times of crisis.",
        "Revenge": "A symbol of a relationship destroyed by betrayal.",
        "Ambition": "A reminder of what must be sacrificed for power.",
        "Fear": "Broken in panic, the locket's owner fled."
    },
    "A vial of strange blue liquid.": {
        "Desperation": "A desperate attempt to cure or poison.",
        "Obsession": "The result of endless, secret experiments.",
        "Curiosity": "A sample taken from a forbidden laboratory.",
        "Fanaticism": "A potion used in occult rites.",
        "Ambition": "A concoction to enhance performance or manipulate others.",
        "Jealousy": "Intended for a rival, to weaken or harm.",
        "Revenge": "A poison brewed for a hated enemy.",
        "Fear": "A last defense against supernatural threats."
    },
    "A chess piece carved from bone.": {
        "Obsession": "A collector's prize, handled obsessively.",
        "Fanaticism": "A relic used in ritual games of fate.",
        "Curiosity": "A curiosity, its origin shrouded in mystery.",
        "Revenge": "A token left as a warning to the Bishop.",
        "Ambition": "A symbol of strategic maneuvering.",
        "Desperation": "Pawned or stolen in a moment of need.",
        "Jealousy": "Taken from a rival's set.",
        "Fear": "Kept as a talisman against evil."
    },
    "A torn dance card.": {
        "Jealousy": "A rival tore the card in anger at being overlooked.",
        "Forbidden Love": "A secret rendezvous, now ruined.",
        "Desperation": "A desperate attempt to erase evidence of a meeting.",
        "Ambition": "A calculated move to disrupt social alliances.",
        "Obsession": "The card is worn from constant handling.",
        "Revenge": "A symbolic act of rejection.",
        "Fanaticism": "A zealot's rejection of worldly pleasures.",
        "Fear": "Torn in panic during a confrontation."
    },
    "A wilted rose with a hidden note.": {
        "Forbidden Love": "A secret message between lovers, now faded.",
        "Jealousy": "A rival intercepted and destroyed the token.",
        "Remorse": "A symbol of regret for a love lost.",
        "Obsession": "The rose is kept long past its prime.",
        "Desperation": "A last plea for forgiveness.",
        "Ambition": "A coded message about a secret alliance.",
        "Revenge": "A warning to a former lover.",
        "Fear": "A message of warning, hidden in haste."
    },
    "A pawn ticket for a golden chalice, issued the day before the Bishop vanished.": {
        "Desperation": "A sign of financial ruin, forced to pawn valuables.",
        "Greed": "A calculated move to profit from the Bishop's possessions.",
        "Ambition": "Selling off assets to fund a rise to power.",
        "Jealousy": "A rival stole and pawned the chalice out of spite.",
        "Revenge": "A symbolic act to hurt the Bishop.",
        "Obsession": "The chalice is an object of fixation.",
        "Fanaticism": "A sacred object sold to fund a ritual.",
        "Fear": "Pawned in haste to escape a threat."
    },
    "A threatening note warning the Bishop to abandon his 'awakening.'": {
        "Fear": "A warning from someone terrified of the Bishop's plans.",
        "Revenge": "A threat from an enemy seeking retribution.",
        "Fanaticism": "A zealot opposes the Bishop's heresy.",
        "Ambition": "A rival seeks to intimidate the Bishop.",
        "Desperation": "A last-ditch effort to prevent disaster.",
        "Jealousy": "A rival's attempt to scare off the Bishop.",
        "Obsession": "The note is one of many, sent obsessively.",
        "Forbidden Love": "A lover fears the Bishop's actions will endanger them."
    },
    "A bloodied handkerchief embroidered with initials.": {
        "Guilt": "A token left behind in a moment of panic.",
        "Revenge": "A trophy taken from the victim.",
        "Jealousy": "A rival's mark, left at the scene.",
        "Forbidden Love": "A lover's token, stained in tragedy.",
        "Desperation": "Used to staunch a wound in a desperate escape.",
        "Ambition": "A calculated plant to frame another.",
        "Obsession": "Kept as a memento of the crime.",
        "Fear": "Dropped in flight from the scene."
    },
    "A letter confessing to a secret affair.": {
        "Blackmail": "A confession used to manipulate or control.",
        "Forbidden Love": "A lover's desperate admission.",
        "Jealousy": "A rival exposes the affair out of spite.",
        "Remorse": "A confession written in regret.",
        "Desperation": "A plea for understanding before disaster.",
        "Ambition": "A calculated risk to gain leverage.",
        "Obsession": "The affair is all-consuming.",
        "Fear": "A confession written in terror of exposure."
    },
    "A diary entry mentioning a midnight visitor.": {
        "Loyalty": "A trusted friend visits in secret.",
        "Forbidden Love": "A lover's clandestine meeting.",
        "Jealousy": "A rival spies on the Bishop's meetings.",
        "Curiosity": "A curious observer records everything.",
        "Ambition": "A secret alliance is formed at midnight.",
        "Desperation": "A plea for help in the dead of night.",
        "Obsession": "The visitor is watched obsessively.",
        "Fear": "A midnight visitor brings terror."
    },
    "A set of muddy footprints leading to the attic.": {
        "Ambition": "A secret meeting or plot in the attic.",
        "Desperation": "A frantic escape to a hidden place.",
        "Curiosity": "Someone explores forbidden spaces.",
        "Jealousy": "A rival follows the Bishop in secret.",
        "Revenge": "A plot is hatched in the shadows.",
        "Obsession": "The attic is visited again and again.",
        "Fanaticism": "A ritual is performed in the attic.",
        "Fear": "Someone flees to the attic in terror."
    },
    "A candle stub melted into the shape of a screaming face.": {
        "Obsession": "A sign of compulsive, repeated rituals.",
        "Fanaticism": "A relic from a forbidden rite.",
        "Despair": "A symbol of hopelessness, melted by tears.",
        "Curiosity": "A strange artifact collected for study.",
        "Fear": "A candle burned in terror during a vigil.",
        "Ambition": "A token from a secret society.",
        "Jealousy": "A rival's curse, left as a warning.",
        "Revenge": "A symbol of suffering inflicted."
    },
    "A cryptic telegram signed only with the letter 'V'.": {
        "Blackmail": "A veiled threat from someone holding secrets.",
        "Curiosity": "A mysterious message, inviting investigation.",
        "Ambition": "A coded offer of alliance.",
        "Obsession": "The sender is fixated on the Bishop.",
        "Revenge": "A warning from an old enemy.",
        "Jealousy": "A rival's attempt to sow discord.",
        "Fanaticism": "A call to arms for a secret cult.",
        "Fear": "A warning sent in haste."
    },
    "A bloodied scrap of choir robe hidden behind the altar.": {
        "Guilt": "Evidence hidden by a remorseful hand.",
        "Revenge": "A trophy from a violent confrontation.",
        "Fanaticism": "A relic from a sacrificial rite.",
        "Desperation": "A desperate attempt to hide the truth.",
        "Jealousy": "A rival's mark, left in anger.",
        "Obsession": "The robe is kept as a memento.",
        "Ambition": "A calculated plant to frame another.",
        "Fear": "Hidden in terror after the act."
    },
    "A torn page from a bestiary describing 'The Watcher in the Fog.'": {
        "Fear": "A warning about a supernatural threat.",
        "Curiosity": "A scholar's search for forbidden knowledge.",
        "Obsession": "The page is studied obsessively.",
        "Fanaticism": "A zealot seeks to summon or banish the Watcher.",
        "Desperation": "A last hope to understand the danger.",
        "Ambition": "A plan to harness the Watcher's power.",
        "Jealousy": "A rival tries to outdo the Bishop's knowledge.",
        "Revenge": "A curse invoked using the Watcher's lore."
    },
    "A vial labeled 'Do Not Drink'.": {
        "Despair": "A poison kept for a final escape.",
        "Obsession": "A dangerous experiment, never meant to be used.",
        "Curiosity": "A sample taken for study.",
        "Fanaticism": "A potion for a forbidden rite.",
        "Ambition": "A tool for manipulation.",
        "Jealousy": "Intended for a rival.",
        "Revenge": "A weapon for retribution.",
        "Fear": "A last defense against evil."
    },
    "A burnt scrap of parchment with arcane symbols.": {
        "Curiosity": "A scholar's failed experiment.",
        "Obsession": "The result of endless, secret rituals.",
        "Fanaticism": "A relic from a forbidden ceremony.",
        "Desperation": "A desperate attempt to destroy evidence.",
        "Ambition": "A plan gone awry.",
        "Jealousy": "A rival's sabotage.",
        "Revenge": "A curse invoked and then hidden.",
        "Fear": "Burned in terror after a failed rite."
    },
    "A lock of hair tied with a red ribbon.": {
        "Forbidden Love": "A lover's keepsake, cherished and hidden.",
        "Jealousy": "A rival's trophy, taken in anger.",
        "Obsession": "Collected and kept as a token.",
        "Remorse": "A memento of regret.",
        "Desperation": "A token left behind in haste.",
        "Ambition": "A charm for luck in a risky plan.",
        "Revenge": "A symbol of a broken bond.",
        "Fear": "Cut and left behind in panic."
    },
    "A broken window latch.": {
        "Ambition": "A forced entry for a secret meeting or theft.",
        "Desperation": "A frantic escape route.",
        "Curiosity": "A search for hidden knowledge.",
        "Jealousy": "A rival sneaks in to spy.",
        "Revenge": "A break-in to settle a score.",
        "Obsession": "Repeated attempts to enter the Bishop's domain.",
        "Fanaticism": "A zealot seeks access for a rite.",
        "Fear": "A hasty exit from danger."
    },
    "A missing library ledger.": {
        "Blackmail": "Records stolen to hide incriminating evidence.",
        "Curiosity": "A scholar's search for secrets.",
        "Ambition": "A rival erases traces of their actions.",
        "Desperation": "A last-ditch effort to cover tracks.",
        "Jealousy": "A rival sabotages the Bishop's work.",
        "Revenge": "A record destroyed in anger.",
        "Obsession": "The ledger is hoarded obsessively.",
        "Fear": "Removed to prevent discovery."
    },
    "A muddy boot print.": {
        "Desperation": "A frantic escape leaves traces.",
        "Ambition": "A rival sneaks through forbidden areas.",
        "Curiosity": "A search for secrets leaves evidence.",
        "Jealousy": "A rival follows the Bishop.",
        "Revenge": "A plotter leaves a mark.",
        "Obsession": "Repeated visits to the scene.",
        "Fanaticism": "A zealot's path to a ritual.",
        "Fear": "A hasty retreat from danger."
    },
    "A page torn from a forbidden tome.": {
        "Blackmail": "A page used as leverage.",
        "Curiosity": "A scholar's theft for study.",
        "Fanaticism": "A zealot seeks forbidden knowledge.",
        "Desperation": "A last hope for salvation.",
        "Ambition": "A rival seeks power.",
        "Jealousy": "A rival sabotages the Bishop's research.",
        "Revenge": "A curse invoked from the page.",
        "Fear": "Torn out to prevent a ritual."
    },
    "A shattered monocle near the cellar stairs.": {
        "Ambition": "A rival's secret meeting interrupted.",
        "Desperation": "A frantic escape leads to broken glass.",
        "Curiosity": "A search for secrets goes awry.",
        "Jealousy": "A rival spies on the Bishop.",
        "Revenge": "A confrontation turns violent.",
        "Obsession": "The monocle is a symbol of fixation.",
        "Fanaticism": "A zealot's vision is shattered.",
        "Fear": "Dropped in panic."
    },
    "A bloodstained glove found in the garden.": {
        "Revenge": "A trophy from a violent act.",
        "Jealousy": "A rival's mark, left in anger.",
        "Forbidden Love": "A lover's token, stained in tragedy.",
        "Desperation": "Used to staunch a wound in a desperate escape.",
        "Ambition": "A calculated plant to frame another.",
        "Obsession": "Kept as a memento of the crime.",
        "Fear": "Dropped in flight from the scene.",
        "Fanaticism": "A relic from a sacrificial rite."
    },
    "A torn map showing secret passages.": {
        "Curiosity": "A scholar's search for hidden ways.",
        "Ambition": "A rival plots secret moves.",
        "Desperation": "A last hope for escape.",
        "Jealousy": "A rival spies on the Bishop.",
        "Revenge": "A plan for ambush.",
        "Obsession": "The map is studied obsessively.",
        "Fanaticism": "A zealot seeks hidden ritual sites.",
        "Fear": "A route planned for flight."
    },
    "A scorched scrap of sermon notes.": {
        "Remorse": "A confession burned in regret.",
        "Fanaticism": "A zealot destroys heretical words.",
        "Curiosity": "A scholar's experiment gone wrong.",
        "Desperation": "A last-ditch effort to hide evidence.",
        "Ambition": "A rival sabotages the Bishop's work.",
        "Jealousy": "A rival destroys what the Bishop values.",
        "Revenge": "A message burned in anger.",
        "Fear": "Notes destroyed to prevent discovery."
    },
    "A star chart with strange markings.": {
        "Obsession": "A fixation on cosmic patterns.",
        "Curiosity": "A scholar's search for meaning.",
        "Fanaticism": "A zealot seeks omens in the stars.",
        "Ambition": "A rival plots by the stars.",
        "Desperation": "A last hope for guidance.",
        "Jealousy": "A rival tries to outdo the Bishop's knowledge.",
        "Revenge": "A curse written in the stars.",
        "Fear": "Markings made in terror of what is coming."
    },
    "A bloodstained handkerchief.": {
        "Revenge": "A trophy from a violent act.",
        "Guilt": "A token left behind in a moment of panic.",
        "Jealousy": "A rival's mark, left in anger.",
        "Forbidden Love": "A lover's token, stained in tragedy.",
        "Desperation": "Used to staunch a wound in a desperate escape.",
        "Ambition": "A calculated plant to frame another.",
        "Obsession": "Kept as a memento of the crime.",
        "Fear": "Dropped in flight from the scene."
    },
    "A faded photograph of the Bishop and an unknown figure.": {
        "Forbidden Love": "A secret relationship, hidden from the world.",
        "Jealousy": "A rival envies the Bishop's companion.",
        "Remorse": "A memory of happier times, now lost.",
        "Obsession": "The photograph is handled obsessively.",
        "Desperation": "A last link to someone lost.",
        "Ambition": "A clue to a secret alliance.",
        "Revenge": "A reminder of betrayal.",
        "Fear": "A secret that could destroy reputations."
    },
    "A silver key engraved with runes.": {
        "Curiosity": "A key to forbidden knowledge.",
        "Obsession": "A focus for compulsive behavior.",
        "Fanaticism": "A tool for sacred rites.",
        "Ambition": "A means to unlock power.",
        "Desperation": "A last hope for escape.",
        "Jealousy": "A rival steals the key.",
        "Revenge": "A tool for sabotage.",
        "Fear": "A key to a place of safety."
    },
    "A pressed flower stained with blood.": {
        "Remorse": "A token of regret, stained by tragedy.",
        "Forbidden Love": "A lover's keepsake, ruined by violence.",
        "Jealousy": "A rival destroys a cherished gift.",
        "Obsession": "The flower is kept long past its prime.",
        "Desperation": "A last hope for reconciliation.",
        "Ambition": "A symbol of a secret alliance.",
        "Revenge": "A warning to a former lover.",
        "Fear": "A token left behind in panic."
    },
    "A page from a diary describing a hidden ritual.": {
        "Zealotry": "A zealot records forbidden rites.",
        "Fanaticism": "A sacred ritual, described in detail.",
        "Curiosity": "A scholar's dangerous discovery.",
        "Obsession": "The ritual is an all-consuming focus.",
        "Desperation": "A last hope for salvation.",
        "Ambition": "A plan to gain power.",
        "Jealousy": "A rival seeks to outdo the Bishop.",
        "Revenge": "A ritual for retribution."
    },
    "A pawn ticket for a golden chalice.": {
        "Greed": "A calculated move to profit from the Bishop's possessions.",
        "Desperation": "A sign of financial ruin.",
        "Ambition": "Selling off assets to fund a rise to power.",
        "Jealousy": "A rival stole and pawned the chalice out of spite.",
        "Revenge": "A symbolic act to hurt the Bishop.",
        "Obsession": "The chalice is an object of fixation.",
        "Fanaticism": "A sacred object sold to fund a ritual.",
        "Fear": "Pawned in haste to escape a threat."
    },
    "A burnt letter addressed to the Bishop.": {
        "Resentment": "A letter burned in anger.",
        "Remorse": "A confession destroyed in regret.",
        "Jealousy": "A rival destroys evidence of a relationship.",
        "Forbidden Love": "A lover's message, burned to hide the truth.",
        "Desperation": "A plea for help, never delivered.",
        "Ambition": "A plot revealed and then hidden.",
        "Revenge": "A threat destroyed after the act.",
        "Fear": "A warning burned in terror."
    },
    "A torn page from a guestbook.": {
        "Duty": "A record removed to protect someone's reputation.",
        "Curiosity": "A scholar seeks to hide their presence.",
        "Ambition": "A rival erases evidence of a meeting.",
        "Desperation": "A last-ditch effort to cover tracks.",
        "Jealousy": "A rival sabotages the Bishop's social standing.",
        "Revenge": "A name erased in anger.",
        "Obsession": "The guestbook is handled obsessively.",
        "Fear": "A page torn out to prevent discovery."
    },
    "A vial of laudanum, nearly empty.": {
        "Despair": "A sign of hopelessness and addiction.",
        "Remorse": "A means to dull the pain of guilt.",
        "Desperation": "A last hope for relief.",
        "Curiosity": "A sample taken for study.",
        "Ambition": "Used to manipulate or control others.",
        "Jealousy": "A rival tries to poison the Bishop.",
        "Revenge": "A tool for retribution.",
        "Fear": "Taken to calm nerves after a crime."
    },
    "A bloodied handkerchief with a family crest.": {
        "Guilt": "A token left behind in a moment of panic.",
        "Revenge": "A trophy from a violent act.",
        "Jealousy": "A rival's mark, left in anger.",
        "Forbidden Love": "A lover's token, stained in tragedy.",
        "Desperation": "Used to staunch a wound in a desperate escape.",
        "Ambition": "A calculated plant to frame another.",
        "Obsession": "Kept as a memento of the crime.",
        "Fear": "Dropped in flight from the scene."
    },
    "A coded message hidden in a painting.": {
        "Manipulation": "A secret message for a co-conspirator.",
        "Curiosity": "A scholar's puzzle.",
        "Ambition": "A plot hidden in plain sight.",
        "Obsession": "The painting is studied obsessively.",
        "Revenge": "A warning to an enemy.",
        "Jealousy": "A rival's attempt to sow discord.",
        "Fanaticism": "A sacred message for the initiated.",
        "Fear": "A warning hidden from prying eyes."
    },
    "A scrap of fabric matching the Bishop's robe.": {
        "Loyalty": "A token kept by a devoted follower.",
        "Jealousy": "A rival steals a piece of the Bishop's clothing.",
        "Remorse": "A memento of regret.",
        "Obsession": "The fabric is handled obsessively.",
        "Desperation": "Torn in a struggle.",
        "Ambition": "A clue to a secret alliance.",
        "Revenge": "A trophy from a confrontation.",
        "Fear": "A piece torn off in panic."
    },
    "A broken rosary found in the crypt.": {
        "Zealotry": "A zealot's tool, broken in a moment of crisis.",
        "Fanaticism": "A relic from a forbidden rite.",
        "Remorse": "A symbol of regret.",
        "Desperation": "Broken in a plea for help.",
        "Ambition": "A rival sabotages the Bishop's faith.",
        "Jealousy": "A rival destroys what the Bishop values.",
        "Revenge": "A message left in anger.",
        "Fear": "Broken in terror."
    },
    "A diary entry about a forbidden meeting.": {
        "Forbidden Love": "A secret rendezvous between lovers.",
        "Curiosity": "A scholar's dangerous curiosity.",
        "Remorse": "A confession of regret.",
        "Obsession": "The meeting is an all-consuming focus.",
        "Desperation": "A last hope for reconciliation.",
        "Ambition": "A plot hatched in secret.",
        "Jealousy": "A rival spies on the Bishop.",
        "Revenge": "A plan for retribution."
    },
    "A pressed flower from the conservatory.": {
        "Remorse": "A token of regret, kept as a reminder.",
        "Forbidden Love": "A lover's keepsake.",
        "Jealousy": "A rival destroys a cherished gift.",
        "Obsession": "The flower is kept long past its prime.",
        "Desperation": "A last hope for reconciliation.",
        "Ambition": "A symbol of a secret alliance.",
        "Revenge": "A warning to a former lover.",
        "Fear": "A token left behind in panic."
    },
    "A torn invitation to a secret gathering.": {
        "Curiosity": "A scholar's search for forbidden knowledge.",
        "Ambition": "A rival seeks entry to a powerful circle.",
        "Desperation": "A last hope for acceptance.",
        "Jealousy": "A rival is excluded and lashes out.",
        "Revenge": "A plan for retribution is hatched.",
        "Obsession": "The invitation is handled obsessively.",
        "Fanaticism": "A call to a sacred rite.",
        "Fear": "Torn in panic after a threat."
    },
    "A bloodstained page from a ledger.": {
        "Blackmail": "Evidence of financial wrongdoing.",
        "Revenge": "A record destroyed in anger.",
        "Desperation": "A last-ditch effort to cover tracks.",
        "Curiosity": "A scholar's dangerous discovery.",
        "Ambition": "A rival sabotages the Bishop's finances.",
        "Jealousy": "A rival exposes the Bishop's secrets.",
        "Obsession": "The ledger is handled obsessively.",
        "Fear": "A page torn out in terror."
    },
    "A silver ring inscribed with strange symbols.": {
        "Obsession": "A focus for compulsive behavior.",
        "Curiosity": "A scholar's puzzle.",
        "Fanaticism": "A sacred token.",
        "Ambition": "A symbol of secret society membership.",
        "Desperation": "Pawned or stolen in a moment of need.",
        "Jealousy": "A rival steals the ring.",
        "Revenge": "A token left as a warning.",
        "Fear": "A charm against evil."
    },
    "A burnt candle stub found in the attic.": {
        "Despair": "A sign of hopelessness.",
        "Obsession": "A relic from repeated rituals.",
        "Fanaticism": "A tool for sacred rites.",
        "Curiosity": "A scholar's experiment.",
        "Ambition": "A token from a secret meeting.",
        "Jealousy": "A rival's curse.",
        "Revenge": "A symbol of suffering.",
        "Fear": "Burned in terror."
    },
    "A cryptic note referencing the 'Elder Ones'.": {
        "Fanaticism": "A zealot's message about forbidden gods.",
        "Curiosity": "A scholar's dangerous discovery.",
        "Obsession": "The note is handled obsessively.",
        "Ambition": "A plot to gain supernatural power.",
        "Desperation": "A plea for help from beyond.",
        "Jealousy": "A rival seeks to outdo the Bishop.",
        "Revenge": "A curse invoked.",
        "Fear": "A warning about a coming threat."
    },
    "A page from a lost sermon.": {
        "Zealotry": "A zealot's sacred text.",
        "Fanaticism": "A forbidden sermon.",
        "Remorse": "A confession of regret.",
        "Curiosity": "A scholar's discovery.",
        "Desperation": "A plea for forgiveness.",
        "Ambition": "A rival sabotages the Bishop's work.",
        "Jealousy": "A rival destroys what the Bishop values.",
        "Revenge": "A message left in anger."
    },
    "A bloodied scrap of choir robe.": {
        "Guilt": "Evidence hidden by a remorseful hand.",
        "Revenge": "A trophy from a violent confrontation.",
        "Fanaticism": "A relic from a sacrificial rite.",
        "Desperation": "A desperate attempt to hide the truth.",
        "Jealousy": "A rival's mark, left in anger.",
        "Obsession": "The robe is kept as a memento.",
        "Ambition": "A calculated plant to frame another.",
        "Fear": "Hidden in terror after the act."
    },
    "A torn letter from the Bishop addressed to Lady Ashcroft.": {
        "Forbidden Love": "A secret romance revealed.",
        "Jealousy": "A rival intercepts and destroys the letter.",
        "Remorse": "A confession of regret.",
        "Obsession": "The letter is handled obsessively.",
        "Desperation": "A plea for forgiveness.",
        "Ambition": "A plot revealed.",
        "Revenge": "A message left in anger.",
        "Fear": "A warning about a coming threat."
    },
    "A threatening note warning the Bishop.": {
        "Fear": "A warning from someone terrified of the Bishop's plans.",
        "Revenge": "A threat from an enemy seeking retribution.",
        "Fanaticism": "A zealot opposes the Bishop's heresy.",
        "Ambition": "A rival seeks to intimidate the Bishop.",
        "Desperation": "A last-ditch effort to prevent disaster.",
        "Jealousy": "A rival's attempt to scare off the Bishop.",
        "Obsession": "The note is one of many, sent obsessively.",
        "Forbidden Love": "A lover fears the Bishop's actions will endanger them."
    },
    "A lock of hair tied with a red ribbon.": {
        "Jealousy": "A rival's trophy, taken in anger.",
        "Forbidden Love": "A lover's keepsake, cherished and hidden.",
        "Obsession": "Collected and kept as a token.",
        "Remorse": "A memento of regret.",
        "Desperation": "A token left behind in haste.",
        "Ambition": "A charm for luck in a risky plan.",
        "Revenge": "A symbol of a broken bond.",
        "Fear": "Cut and left behind in panic."
    }
}

alibi_pools = [
    [
        {"text": f"Praying in the Chapel at {random_15min_time((21, 24))}.", "location": "Chapel", "time": random_15min_time((21, 24))},
        {"text": f"Reading in the Library at {random_15min_time((21, 24))}.", "location": "Library", "time": random_15min_time((21, 24))},
        {"text": f"Tending the fire in the Parlor at {random_15min_time((21, 24))}.", "location": "Parlor", "time": random_15min_time((21, 24))},
        {"text": f"Searching for a book in the Study at {random_15min_time((21, 24))}.", "location": "Study", "time": random_15min_time((21, 24))},
        {"text": f"Practicing music in the Music Room at {random_15min_time((21, 24))}.", "location": "Music Room", "time": random_15min_time((21, 24))},
        {"text": f"Inspecting the Greenhouse at {random_15min_time((21, 24))}.", "location": "Greenhouse", "time": random_15min_time((21, 24))},
        {"text": f"Repairing the clock in the Clock Tower at {random_15min_time((21, 24))}.", "location": "Clock Tower", "time": random_15min_time((21, 24))},
        {"text": f"Feeding birds in the Garden at {random_15min_time((21, 24))}.", "location": "Garden", "time": random_15min_time((21, 24))}
    ],
    [
        {"text": f"Practicing dance steps in the Ballroom at {random_15min_time((21, 24))}.", "location": "Ballroom", "time": random_15min_time((21, 24))},
        {"text": f"Alone in the Solarium, reading at {random_15min_time((21, 24))}.", "location": "Solarium", "time": random_15min_time((21, 24))},
        {"text": f"Repairing a window in the Attic at {random_15min_time((21, 24))}.", "location": "Attic", "time": random_15min_time((21, 24))},
        {"text": f"Inspecting the Cellar at {random_15min_time((21, 24))}.", "location": "Cellar", "time": random_15min_time((21, 24))},
        {"text": f"Polishing silver in the Butler’s Pantry at {random_15min_time((21, 24))}.", "location": "Butler’s Pantry", "time": random_15min_time((21, 24))},
        {"text": f"Tuning the grand piano in the Music Room at {random_15min_time((21, 24))}.", "location": "Music Room", "time": random_15min_time((21, 24))},
        {"text": f"Arranging flowers in the Conservatory at {random_15min_time((21, 24))}.", "location": "Conservatory", "time": random_15min_time((21, 24))},
        {"text": f"Lighting candles in the Chapel Crypt at {random_15min_time((21, 24))}.", "location": "Chapel Crypt", "time": random_15min_time((21, 24))}
    ],
    [
        {"text": f"Walking in the Garden at {random_15min_time((21, 24))}.", "location": "Garden", "time": random_15min_time((21, 24))},
        {"text": f"Observing the stars in the Observatory at {random_15min_time((21, 24))}.", "location": "Observatory", "time": random_15min_time((21, 24))},
        {"text": f"Dining alone in the Dining Hall at {random_15min_time((21, 24))}.", "location": "Dining Hall", "time": random_15min_time((21, 24))},
        {"text": f"Smoking in the Smoking Room at {random_15min_time((21, 24))}.", "location": "Smoking Room", "time": random_15min_time((21, 24))},
        {"text": f"Sorting laundry in the Laundry Room at {random_15min_time((21, 24))}.", "location": "Laundry Room", "time": random_15min_time((21, 24))},
        {"text": f"Inspecting the Armory at {random_15min_time((21, 24))}.", "location": "Armory", "time": random_15min_time((21, 24))},
        {"text": f"Admiring paintings in the Portrait Gallery at {random_15min_time((21, 24))}.", "location": "Portrait Gallery", "time": random_15min_time((21, 24))},
        {"text": f"Reviewing maps in the Map Room at {random_15min_time((21, 24))}.", "location": "Map Room", "time": random_15min_time((21, 24))}
    ],
    [
        {"text": f"Feeding the horses in the Stable at {random_15min_time((21, 24))}.", "location": "Horse Stable", "time": random_15min_time((21, 24))},
        {"text": f"Fetching water from the Well House at {random_15min_time((21, 24))}.", "location": "Well House", "time": random_15min_time((21, 24))},
        {"text": f"Admiring paintings in the Gallery at {random_15min_time((21, 24))}.", "location": "Gallery", "time": random_15min_time((21, 24))},
        {"text": f"Resting in the East Bedchamber at {random_15min_time((21, 24))}.", "location": "East Bedchamber", "time": random_15min_time((21, 24))},
        {"text": f"Cleaning weapons in the Armory at {random_15min_time((21, 24))}.", "location": "Armory", "time": random_15min_time((21, 24))},
        {"text": f"Tending plants in the Greenhouse at {random_15min_time((21, 24))}.", "location": "Greenhouse", "time": random_15min_time((21, 24))},
        {"text": f"Writing letters in the Study at {random_15min_time((21, 24))}.", "location": "Study", "time": random_15min_time((21, 24))},
        {"text": f"Preparing tea in the Kitchen at {random_15min_time((21, 24))}.", "location": "Kitchen", "time": random_15min_time((21, 24))}
    ],
    [
        {"text": f"Hiding in the Attic at {random_15min_time((21, 24))}.", "location": "Attic", "time": random_15min_time((21, 24))},
        {"text": f"Praying alone in the Chapel at {random_15min_time((21, 24))}.", "location": "Chapel", "time": random_15min_time((21, 24))},
        {"text": f"Examining old maps in the Study at {random_15min_time((21, 24))}.", "location": "Study", "time": random_15min_time((21, 24))},
        {"text": f"Smoking in the Smoking Room at {random_15min_time((21, 24))}.", "location": "Smoking Room", "time": random_15min_time((21, 24))},
        {"text": f"Polishing armor in the Armory at {random_15min_time((21, 24))}.", "location": "Armory", "time": random_15min_time((21, 24))},
        {"text": f"Reading poetry in the West Bedchamber at {random_15min_time((21, 24))}.", "location": "West Bedchamber", "time": random_15min_time((21, 24))},
        {"text": f"Inspecting the Vault at {random_15min_time((21, 24))}.", "location": "Vault", "time": random_15min_time((21, 24))},
        {"text": f"Feeding the birds in the Garden at {random_15min_time((21, 24))}.", "location": "Garden", "time": random_15min_time((21, 24))}
    ],
    [
        {"text": f"Resting in the Guest Suite at {random_15min_time((21, 24))}.", "location": "Guest Suite", "time": random_15min_time((21, 24))},
        {"text": f"Dusting shelves in the Library at {random_15min_time((21, 24))}.", "location": "Library", "time": random_15min_time((21, 24))},
        {"text": f"Tending the fire in the Parlor at {random_15min_time((21, 24))}.", "location": "Parlor", "time": random_15min_time((21, 24))},
        {"text": f"Inspecting the Wine Cellar at {random_15min_time((21, 24))}.", "location": "Wine Cellar", "time": random_15min_time((21, 24))},
        {"text": f"Repairing a lantern in the Coach House at {random_15min_time((21, 24))}.", "location": "Coach House", "time": random_15min_time((21, 24))},
        {"text": f"Sweeping the Servant's Quarters at {random_15min_time((21, 24))}.", "location": "Servant's Quarters", "time": random_15min_time((21, 24))},
        {"text": f"Examining the clockwork in the Clock Tower at {random_15min_time((21, 24))}.", "location": "Clock Tower", "time": random_15min_time((21, 24))},
        {"text": f"Arranging flowers in the Conservatory at {random_15min_time((21, 24))}.", "location": "Conservatory", "time": random_15min_time((21, 24))}
    ],
    [
        {"text": f"Sharpening knives in the Kitchen at {random_15min_time((21, 24))}.", "location": "Kitchen", "time": random_15min_time((21, 24))},
        {"text": f"Cleaning the Nursery at {random_15min_time((21, 24))}.", "location": "Nursery", "time": random_15min_time((21, 24))},
        {"text": f"Playing billiards in the Billiards Room at {random_15min_time((21, 24))}.", "location": "Billiards Room", "time": random_15min_time((21, 24))},
        {"text": f"Inspecting the Master Bathroom at {random_15min_time((21, 24))}.", "location": "Master Bathroom", "time": random_15min_time((21, 24))},
        {"text": f"Reading in the Tower Room at {random_15min_time((21, 24))}.", "location": "Tower Room", "time": random_15min_time((21, 24))},
        {"text": f"Polishing silver in the Butler’s Pantry at {random_15min_time((21, 24))}.", "location": "Butler’s Pantry", "time": random_15min_time((21, 24))},
        {"text": f"Feeding the dogs in the Gamekeeper’s Lodge at {random_15min_time((21, 24))}.", "location": "Gamekeeper’s Lodge", "time": random_15min_time((21, 24))},
        {"text": f"Examining the Secret Laboratory at {random_15min_time((21, 24))}.", "location": "Secret Laboratory", "time": random_15min_time((21, 24))}
    ],
    [
        {"text": f"Resting in the West Bedchamber at {random_15min_time((21, 24))}.", "location": "West Bedchamber", "time": random_15min_time((21, 24))},
        {"text": f"Inspecting the Map Room at {random_15min_time((21, 24))}.", "location": "Map Room", "time": random_15min_time((21, 24))},
        {"text": f"Admiring the view from the Tower Room at {random_15min_time((21, 24))}.", "location": "Tower Room", "time": random_15min_time((21, 24))},
        {"text": f"Reading letters in the Servant's Quarters at {random_15min_time((21, 24))}.", "location": "Servant's Quarters", "time": random_15min_time((21, 24))},
        {"text": f"Cleaning the Portrait Gallery at {random_15min_time((21, 24))}.", "location": "Portrait Gallery", "time": random_15min_time((21, 24))},
        {"text": f"Arranging books in the Library at {random_15min_time((21, 24))}.", "location": "Library", "time": random_15min_time((21, 24))},
        {"text": f"Inspecting the Vault at {random_15min_time((21, 24))}.", "location": "Vault", "time": random_15min_time((21, 24))},
        {"text": f"Feeding the horses in the Stable at {random_15min_time((21, 24))}.", "location": "Horse Stable", "time": random_15min_time((21, 24))}
    ]
]

alibi_flavor_explanations = {
    "Praying in the Chapel at 10:15pm.": {
        "Zealotry": "A zealot would seek spiritual strength before or after committing a grave act.",
        "Guilt": "Seeking solace in prayer may be a sign of a guilty conscience.",
        "Fanaticism": "Fanatics often pray before or after forbidden rites.",
        "Remorse": "Prayer as penance for a terrible deed.",
        "Fear": "Hiding in the chapel, hoping for protection.",
        "Shame": "Shame drives one to seek forgiveness in sacred spaces.",
        "Loyalty": "A loyal soul prays for guidance before acting.",
        "Desperation": "Desperate for answers, one turns to prayer."
    },
    "Reading in the Library at 10:15pm.": {
        "Curiosity": "A curious mind seeks answers among the books.",
        "Obsession": "Obsessives lose themselves in research, even at odd hours.",
        "Guilt": "A guilty party may hide in study to avoid others.",
        "Remorse": "Remorseful suspects seek distraction in literature.",
        "Ambition": "Ambitious suspects research ways to advance their goals.",
        "Fear": "The library is a refuge from the chaos elsewhere."
    },
    "Tending the fire in the Parlor at 10:15pm.": {
        "Remorse": "Tending the fire is a meditative act for the remorseful.",
        "Guilt": "A guilty party seeks comfort in routine.",
        "Desperation": "Desperate suspects try to appear normal.",
        "Ambition": "Ambitious suspects may use the parlor to eavesdrop.",
        "Obsession": "Obsession with cleanliness or order brings one to the fire."
    },
    "Searching for a book in the Study at 10:15pm.": {
        "Curiosity": "A curious mind is always searching for new knowledge.",
        "Obsession": "Obsessives cannot rest until they find what they seek.",
        "Ambition": "Ambitious suspects look for secrets to use.",
        "Guilt": "A guilty party may search for ways to cover their tracks.",
        "Fear": "Searching for a book may be a cover for hiding."
    },
    "Practicing music in the Music Room at 10:15pm.": {
        "Remorse": "Music soothes a troubled conscience.",
        "Obsession": "Obsessives practice endlessly, seeking perfection.",
        "Desperation": "Desperate suspects try to distract themselves.",
        "Ambition": "Ambitious suspects may hope to impress others.",
        "Jealousy": "A jealous rival may practice to outshine someone."
    },
    "Inspecting the Greenhouse at 10:15pm.": {
        "Curiosity": "Curious minds are drawn to the exotic plants.",
        "Obsession": "Obsessives tend to the greenhouse at all hours.",
        "Desperation": "Desperate suspects may seek rare herbs for a purpose.",
        "Ambition": "Ambitious suspects may look for poisons or secrets.",
        "Fear": "The greenhouse is a quiet place to hide."
    },
    "Repairing the clock in the Clock Tower at 10:15pm.": {
        "Obsession": "Obsessives are drawn to the intricate workings of the clock.",
        "Ambition": "Ambitious suspects may use the height for surveillance.",
        "Curiosity": "Curious minds want to understand every mechanism.",
        "Desperation": "Desperate suspects may use the clock as an excuse.",
        "Fear": "The clock tower is a lonely, defensible place."
    },
    "Feeding birds in the Garden at 10:15pm.": {
        "Remorse": "Feeding birds is a gentle act for a troubled soul.",
        "Loyalty": "A loyal servant tends to the estate's creatures.",
        "Desperation": "Desperate suspects seek solace in routine.",
        "Obsession": "Obsessives repeat rituals to calm themselves.",
        "Fear": "The garden is open, but also a place to hide in plain sight."
    },
    "Practicing dance steps in the Ballroom at 10:15pm.": {
        "Ambition": "Ambitious suspects practice to impress.",
        "Jealousy": "A jealous rival tries to outshine others.",
        "Obsession": "Obsessives repeat steps endlessly.",
        "Remorse": "Dancing alone is a way to forget regret.",
        "Desperation": "Desperate suspects seek distraction."
    },
    "Alone in the Solarium, reading at 10:15pm.": {
        "Curiosity": "Curious minds seek solitude for study.",
        "Remorse": "Remorseful suspects hide away to reflect.",
        "Obsession": "Obsessives isolate themselves.",
        "Desperation": "Desperate suspects avoid others.",
        "Fear": "The solarium is a bright, safe place at night."
    },
    "Repairing a window in the Attic at 10:15pm.": {
        "Ambition": "Fixing the window could be a cover for spying or plotting.",
        "Desperation": "A desperate person might use any excuse to be alone.",
        "Obsession": "Obsessives fixate on small tasks to calm their nerves.",
        "Jealousy": "A jealous person might watch others from above.",
        "Fear": "The attic is a place to hide from danger."
    },
    "Inspecting the Cellar at 10:15pm.": {
        "Curiosity": "Curious minds are drawn to the cellar's secrets.",
        "Obsession": "Obsessives search for hidden things.",
        "Desperation": "Desperate suspects may seek a hiding place.",
        "Fear": "The cellar is a refuge for the frightened.",
        "Fanaticism": "Fanatics may use the cellar for rituals."
    },
    "Polishing silver in the Butler’s Pantry at 10:15pm.": {
        "Obsession": "Obsessives polish silver to perfection.",
        "Loyalty": "A loyal servant keeps the silver shining.",
        "Remorse": "Remorseful suspects lose themselves in chores.",
        "Desperation": "Desperate suspects try to appear useful.",
        "Shame": "Shame drives one to menial tasks."
    },
    "Tuning the grand piano in the Music Room at 10:15pm.": {
        "Obsession": "Obsessives tune and retune the piano.",
        "Ambition": "Ambitious suspects prepare for a performance.",
        "Remorse": "Music is a balm for regret.",
        "Desperation": "Desperate suspects seek distraction.",
        "Jealousy": "A jealous rival wants to outdo others musically."
    },
    "Arranging flowers in the Conservatory at 10:15pm.": {
        "Remorse": "Arranging flowers is a gentle act for a troubled soul.",
        "Obsession": "Obsessives arrange and rearrange endlessly.",
        "Curiosity": "Curious minds study the plants.",
        "Desperation": "Desperate suspects seek peace in beauty.",
        "Loyalty": "A loyal servant tends to the manor's appearance."
    },
    "Lighting candles in the Chapel Crypt at 10:15pm.": {
        "Zealotry": "A zealot lights candles for the dead or for forbidden rites.",
        "Fanaticism": "Fanatics perform rituals in the crypt.",
        "Remorse": "Lighting candles is an act of penance.",
        "Fear": "Candles keep the darkness at bay.",
        "Guilt": "A guilty party seeks forgiveness among the tombs."
    },
    "Walking in the Garden at 10:15pm.": {
        "Remorse": "A walk in the garden soothes a troubled mind.",
        "Obsession": "Obsessives pace the grounds.",
        "Curiosity": "Curious minds look for secrets among the flowers.",
        "Desperation": "Desperate suspects wander, lost in thought.",
        "Fear": "The garden is a place to escape prying eyes."
    },
    "Observing the stars in the Observatory at 10:15pm.": {
        "Obsession": "Obsessives chart the stars for meaning.",
        "Curiosity": "Curious minds seek cosmic answers.",
        "Fanaticism": "Fanatics look for omens in the heavens.",
        "Ambition": "Ambitious suspects seek inspiration.",
        "Remorse": "Stargazing is a way to forget earthly troubles."
    },
    "Dining alone in the Dining Hall at 10:15pm.": {
        "Remorse": "Eating alone is a sign of regret.",
        "Desperation": "Desperate suspects have lost their appetite for company.",
        "Guilt": "A guilty party avoids others.",
        "Obsession": "Obsessives keep to strict routines.",
        "Ambition": "Ambitious suspects plot over solitary meals."
    },
    "Smoking in the Smoking Room at 10:15pm.": {
        "Remorse": "Smoking calms a troubled mind.",
        "Obsession": "Obsessives indulge in ritual habits.",
        "Desperation": "Desperate suspects seek comfort.",
        "Ambition": "Ambitious suspects meet contacts here.",
        "Guilt": "A guilty party hides in smoke."
    },
    "Sorting laundry in the Laundry Room at 10:15pm.": {
        "Remorse": "Sorting laundry is a penance for the remorseful.",
        "Obsession": "Obsessives sort and resort endlessly.",
        "Desperation": "Desperate suspects try to appear useful.",
        "Shame": "Shame drives one to menial tasks.",
        "Loyalty": "A loyal servant keeps the house running."
    },
    "Inspecting the Armory at 10:15pm.": {
        "Ambition": "Ambitious suspects check the weapons for advantage.",
        "Fear": "Fearful suspects seek protection.",
        "Obsession": "Obsessives are drawn to the tools of violence.",
        "Curiosity": "Curious minds study the armory's contents.",
        "Desperation": "Desperate suspects look for a way out."
    },
    "Admiring paintings in the Portrait Gallery at 10:15pm.": {
        "Obsession": "Obsessives are drawn to the faces of the past.",
        "Remorse": "Remorseful suspects seek comfort in memories.",
        "Curiosity": "Curious minds study the family history.",
        "Ambition": "Ambitious suspects look for inspiration.",
        "Jealousy": "A jealous rival envies the ancestors."
    },
    "Reviewing maps in the Map Room at 10:15pm.": {
        "Curiosity": "Curious minds seek hidden paths.",
        "Obsession": "Obsessives memorize every detail.",
        "Ambition": "Ambitious suspects plan their next move.",
        "Desperation": "Desperate suspects look for escape routes.",
        "Fear": "Fearful suspects want to know every exit."
    },
    "Feeding the horses in the Stable at 10:15pm.": {
        "Loyalty": "A loyal servant cares for the animals.",
        "Remorse": "Feeding horses is a calming ritual.",
        "Desperation": "Desperate suspects seek comfort in routine.",
        "Obsession": "Obsessives tend to the horses meticulously.",
        "Fear": "The stable is a safe place to hide."
    },
    "Fetching water from the Well House at 10:15pm.": {
        "Remorse": "Fetching water is a humble, penitent act.",
        "Desperation": "Desperate suspects seek to be useful.",
        "Obsession": "Obsessives repeat chores endlessly.",
        "Curiosity": "Curious minds wonder what lies at the bottom.",
        "Fear": "The well house is isolated, a place to hide."
    },
    "Admiring paintings in the Gallery at 10:15pm.": {
        "Obsession": "Obsessives are drawn to the art.",
        "Remorse": "Remorseful suspects seek solace in beauty.",
        "Curiosity": "Curious minds study every detail.",
        "Ambition": "Ambitious suspects look for inspiration.",
        "Jealousy": "A jealous rival envies the subjects."
    },
    "Resting in the East Bedchamber at 10:15pm.": {
        "Remorse": "Rest is a refuge for the remorseful.",
        "Desperation": "Desperate suspects seek escape in sleep.",
        "Guilt": "A guilty party hides away.",
        "Obsession": "Obsessives cannot rest, even in bed.",
        "Fear": "The bedchamber is a safe haven."
    },
    "Cleaning weapons in the Armory at 10:15pm.": {
        "Ambition": "Ambitious suspects prepare for action.",
        "Obsession": "Obsessives polish weapons to perfection.",
        "Fear": "Fearful suspects want to be ready for danger.",
        "Remorse": "Cleaning weapons is a penance.",
        "Desperation": "Desperate suspects seek protection."
    },
    "Tending plants in the Greenhouse at 10:15pm.": {
        "Remorse": "Tending plants soothes a troubled mind.",
        "Obsession": "Obsessives care for every leaf.",
        "Curiosity": "Curious minds study the flora.",
        "Desperation": "Desperate suspects seek peace in nature.",
        "Loyalty": "A loyal servant keeps the greenhouse thriving."
    },
    "Writing letters in the Study at 10:15pm.": {
        "Remorse": "Writing letters is a way to confess or apologize.",
        "Obsession": "Obsessives write and rewrite endlessly.",
        "Ambition": "Ambitious suspects plot in correspondence.",
        "Desperation": "Desperate suspects reach out for help.",
        "Guilt": "A guilty party tries to explain themselves."
    },
    "Preparing tea in the Kitchen at 10:15pm.": {
        "Remorse": "Preparing tea is a calming ritual.",
        "Obsession": "Obsessives perfect every detail.",
        "Desperation": "Desperate suspects seek comfort.",
        "Loyalty": "A loyal servant tends to the household.",
        "Fear": "The kitchen is a safe, familiar place."
    },
    "Hiding in the Attic at 10:15pm.": {
        "Fear": "The attic is a refuge for the frightened.",
        "Desperation": "Desperate suspects hide from danger.",
        "Guilt": "A guilty party avoids discovery.",
        "Obsession": "Obsessives are drawn to hidden spaces.",
        "Remorse": "Hiding is a penance for regret."
    },
    "Praying alone in the Chapel at 10:15pm.": {
        "Zealotry": "A zealot seeks divine guidance in solitude.",
        "Remorse": "Prayer is a penance for wrongdoing.",
        "Fanaticism": "Fanatics pray before or after forbidden acts.",
        "Guilt": "A guilty party seeks forgiveness.",
        "Fear": "The chapel is a sanctuary from fear."
    },
    "Examining old maps in the Study at 10:15pm.": {
        "Curiosity": "Curious minds seek hidden knowledge.",
        "Obsession": "Obsessives pore over maps for hours.",
        "Ambition": "Ambitious suspects plan their next move.",
        "Desperation": "Desperate suspects look for escape routes.",
        "Fear": "Knowing the layout is a comfort to the fearful."
    },
    "Smoking in the Smoking Room at 10:15pm.": {
        "Remorse": "Smoking calms a troubled mind.",
        "Obsession": "Obsessives indulge in ritual habits.",
        "Desperation": "Desperate suspects seek comfort.",
        "Ambition": "Ambitious suspects meet contacts here.",
        "Guilt": "A guilty party hides in smoke."
    },
    "Polishing armor in the Armory at 10:15pm.": {
        "Duty": "A sense of duty keeps the armor shining.",
        "Obsession": "Obsessives polish armor to perfection.",
        "Remorse": "Polishing armor is a penance.",
        "Ambition": "Ambitious suspects prepare for action.",
        "Fear": "Armor is a comfort to the fearful."
    },
    "Reading poetry in the West Bedchamber at 10:15pm.": {
        "Remorse": "Poetry soothes a troubled soul.",
        "Obsession": "Obsessives memorize every line.",
        "Desperation": "Desperate suspects seek escape in verse.",
        "Curiosity": "Curious minds explore every stanza.",
        "Guilt": "A guilty party hides away with poetry."
    },
    "Inspecting the Vault at 10:15pm.": {
        "Greed": "Greedy suspects check the vault for valuables.",
        "Ambition": "Ambitious suspects seek secrets or leverage.",
        "Obsession": "Obsessives check the vault repeatedly.",
        "Fear": "The vault is a secure hiding place.",
        "Desperation": "Desperate suspects look for resources."
    },
    "Feeding the birds in the Garden at 10:15pm.": {
        "Remorse": "Feeding birds is a gentle act for a troubled soul.",
        "Loyalty": "A loyal servant tends to the estate's creatures.",
        "Desperation": "Desperate suspects seek solace in routine.",
        "Obsession": "Obsessives repeat rituals to calm themselves.",
        "Fear": "The garden is open, but also a place to hide in plain sight."
    },
    "Resting in the Guest Suite at 10:15pm.": {
        "Remorse": "Rest is a refuge for the remorseful.",
        "Desperation": "Desperate suspects seek escape in sleep.",
        "Guilt": "A guilty party hides away.",
        "Obsession": "Obsessives cannot rest, even in bed.",
        "Fear": "The guest suite is a safe haven."
    },
    "Dusting shelves in the Library at 10:15pm.": {
        "Loyalty": "A loyal servant keeps the library clean.",
        "Remorse": "Dusting is a penance for regret.",
        "Obsession": "Obsessives dust every shelf meticulously.",
        "Desperation": "Desperate suspects try to appear useful.",
        "Curiosity": "Curious minds find secrets while dusting."
    },
    "Inspecting the Wine Cellar at 10:15pm.": {
        "Remorse": "The wine cellar is a place to drown sorrows.",
        "Desperation": "Desperate suspects seek solace in drink.",
        "Obsession": "Obsessives check the cellar for rare bottles.",
        "Curiosity": "Curious minds look for hidden compartments.",
        "Fear": "The cellar is a refuge from prying eyes."
    },
    "Repairing a lantern in the Coach House at 10:15pm.": {
        "Obsession": "Obsessives fix every broken thing.",
        "Ambition": "Ambitious suspects prepare for a quick escape.",
        "Desperation": "Desperate suspects need light in the darkness.",
        "Loyalty": "A loyal servant keeps the house running.",
        "Fear": "A working lantern is a comfort in the dark."
    },
    "Sweeping the Servant's Quarters at 10:15pm.": {
        "Loyalty": "A loyal servant keeps the quarters clean.",
        "Remorse": "Sweeping is a penance for regret.",
        "Obsession": "Obsessives sweep every corner.",
        "Desperation": "Desperate suspects try to appear useful.",
        "Shame": "Shame drives one to menial tasks."
    },
    "Examining the clockwork in the Clock Tower at 10:15pm.": {
        "Obsession": "Obsessives are drawn to the intricate mechanisms.",
        "Curiosity": "Curious minds want to understand every gear.",
        "Ambition": "Ambitious suspects use the height for surveillance.",
        "Desperation": "Desperate suspects need to keep busy.",
        "Fear": "The clock tower is a lonely, defensible place."
    },
    "Arranging flowers in the Conservatory at 10:15pm.": {
        "Remorse": "Arranging flowers is a gentle act for a troubled soul.",
        "Obsession": "Obsessives arrange and rearrange endlessly.",
        "Curiosity": "Curious minds study the plants.",
        "Desperation": "Desperate suspects seek peace in beauty.",
        "Loyalty": "A loyal servant tends to the manor's appearance."
    },
    "Sharpening knives in the Kitchen at 10:15pm.": {
        "Ambition": "Ambitious suspects prepare for action.",
        "Obsession": "Obsessives sharpen knives to perfection.",
        "Fear": "Fearful suspects want to be ready for danger.",
        "Remorse": "Sharpening knives is a penance.",
        "Desperation": "Desperate suspects seek protection."
    },
    "Cleaning the Nursery at 10:15pm.": {
        "Remorse": "Cleaning the nursery is a penance for regret.",
        "Loyalty": "A loyal servant keeps the nursery tidy.",
        "Obsession": "Obsessives clean every toy and corner.",
        "Desperation": "Desperate suspects try to appear useful.",
        "Shame": "Shame drives one to menial tasks."
    },
    "Playing billiards in the Billiards Room at 10:15pm.": {
        "Ambition": "Ambitious suspects plot over games.",
        "Obsession": "Obsessives play to perfection.",
        "Remorse": "Games are a distraction from regret.",
        "Desperation": "Desperate suspects seek escape in play.",
        "Jealousy": "A jealous rival tries to outdo others."
    },
    "Inspecting the Master Bathroom at 10:15pm.": {
        "Remorse": "The bathroom is a place to wash away guilt.",
        "Obsession": "Obsessives check every detail.",
        "Desperation": "Desperate suspects seek solitude.",
        "Fear": "The bathroom is a safe, private space.",
        "Shame": "Shame drives one to hide."
    },
    "Reading in the Tower Room at 10:15pm.": {
        "Curiosity": "Curious minds seek solitude for study.",
        "Remorse": "Reading is a way to forget regret.",
        "Obsession": "Obsessives isolate themselves.",
        "Desperation": "Desperate suspects avoid others.",
        "Fear": "The tower is a safe, high place."
    },
    "Polishing silver in the Butler’s Pantry at 10:15pm.": {
        "Obsession": "Obsessives polish silver to perfection.",
        "Loyalty": "A loyal servant keeps the silver shining.",
        "Remorse": "Remorseful suspects lose themselves in chores.",
        "Desperation": "Desperate suspects try to appear useful.",
        "Shame": "Shame drives one to menial tasks."
    },
    "Feeding the dogs in the Gamekeeper’s Lodge at 10:15pm.": {
        "Loyalty": "A loyal servant cares for the animals.",
        "Remorse": "Feeding dogs is a calming ritual.",
        "Desperation": "Desperate suspects seek comfort in routine.",
        "Obsession": "Obsessives tend to the dogs meticulously.",
        "Fear": "The lodge is a safe place to hide."
    },
    "Examining the Secret Laboratory at 10:15pm.": {
        "Curiosity": "Curious minds are drawn to the unknown.",
        "Obsession": "Obsessives cannot resist forbidden experiments.",
        "Ambition": "Ambitious suspects seek power in secrets.",
        "Desperation": "Desperate suspects look for answers.",
        "Fear": "The laboratory is a place to hide from others."
    },
    "Resting in the West Bedchamber at 10:15pm.": {
        "Remorse": "Rest is a refuge for the remorseful.",
        "Desperation": "Desperate suspects seek escape in sleep.",
        "Guilt": "A guilty party hides away.",
        "Obsession": "Obsessives cannot rest, even in bed.",
        "Fear": "The bedchamber is a safe haven."
    },
    "Inspecting the Map Room at 10:15pm.": {
        "Curiosity": "Curious minds seek hidden paths.",
        "Obsession": "Obsessives memorize every detail.",
        "Ambition": "Ambitious suspects plan their next move.",
        "Desperation": "Desperate suspects look for escape routes.",
        "Fear": "Fearful suspects want to know every exit."
    },
    "Admiring the view from the Tower Room at 10:15pm.": {
        "Obsession": "Obsessives are drawn to the heights.",
        "Remorse": "The view is a way to forget regret.",
        "Curiosity": "Curious minds look for movement below.",
        "Ambition": "Ambitious suspects plot from above.",
        "Fear": "The tower is a safe, high place."
    },
    "Reading letters in the Servant's Quarters at 10:15pm.": {
        "Remorse": "Reading letters is a way to reconnect with the past.",
        "Obsession": "Obsessives read and reread correspondence.",
        "Desperation": "Desperate suspects seek comfort in words.",
        "Loyalty": "A loyal servant keeps in touch with family.",
        "Shame": "Shame drives one to hide away."
    },
    "Cleaning the Portrait Gallery at 10:15pm.": {
        "Loyalty": "A loyal servant keeps the gallery clean.",
        "Remorse": "Cleaning is a penance for regret.",
        "Obsession": "Obsessives dust every frame.",
        "Desperation": "Desperate suspects try to appear useful.",
        "Shame": "Shame drives one to menial tasks."
    },
    "Arranging books in the Library at 10:15pm.": {
        "Obsession": "Obsessives arrange books endlessly.",
        "Curiosity": "Curious minds find secrets while sorting.",
        "Remorse": "Arranging books is a calming ritual.",
        "Desperation": "Desperate suspects try to appear useful.",
        "Loyalty": "A loyal servant keeps the library in order."
    },
    "Inspecting the Vault at 10:15pm.": {
        "Greed": "Greedy suspects check the vault for valuables.",
        "Ambition": "Ambitious suspects seek secrets or leverage.",
        "Obsession": "Obsessives check the vault repeatedly.",
        "Fear": "The vault is a secure hiding place.",
        "Desperation": "Desperate suspects look for resources."
    },
    "Feeding the horses in the Stable at 10:15pm.": {
        "Loyalty": "A loyal servant cares for the animals.",
        "Remorse": "Feeding horses is a calming ritual.",
        "Desperation": "Desperate suspects seek comfort in routine.",
        "Obsession": "Obsessives tend to the horses meticulously.",
        "Fear": "The stable is a safe place to hide."
    }
}

clue_motives = {
    "A silver pendant etched with tentacles.": "Fanaticism",
    "Blood-stained prayer book.": "Fanaticism",
    "Footprints leading to a sealed hatch.": "Ambition",
    "A coded diary mentioning a 'Summoning'.": "Revenge",
    "A page torn from a forbidden tome.": "Blackmail",
    "A torn letter from the Bishop addressed to Lady Ashcroft.": "Forbidden Love",
    "A pawn ticket for a golden chalice, issued the day before the Bishop vanished.": "Desperation",
    "A threatening note warning the Bishop to abandon his 'awakening.'": "Fear"
}

means_pool = [
    "had access to the Bishop's private study.",
    "knows the secret passages of the manor.",
    "is an expert in poisons and rare herbs.",
    "possessed the chapel keys.",
    "was seen near the Bishop's quarters.",
    "had no known way to reach the Bishop.",
    "had a duplicate key to the crypt.",
    "was familiar with the manor's secret alarms."
]

means_flavor_explanations = {
    "had access to the Bishop's private study.": {
        "Ambition": "Ambitious suspects would use their access to further their own goals.",
        "Jealousy": "A jealous rival could exploit this access to confront the Bishop in private.",
        "Revenge": "Access allowed for a private moment to settle old scores.",
        "Forbidden Love": "Secret meetings in the study, away from prying eyes.",
        "Obsession": "The study was a place to search for forbidden knowledge.",
        "Fanaticism": "The study held sacred texts, tempting to a zealot.",
        "Desperation": "Access was a last chance to plead or threaten.",
        "Fear": "A fearful suspect might search the study for secrets to protect themselves.",
        "Blackmail": "Private access made it easier to uncover or threaten with secrets.",
        "Guilt": "A guilty party might return to the study to cover their tracks.",
        "Loyalty": "A loyal confidant could enter to protect or warn the Bishop.",
        "Resentment": "Resentment festers in private, where words are unguarded.",
        "Zealotry": "A zealot might seek to confront the Bishop over doctrine.",
        "Shame": "A shamed suspect might seek forgiveness or hide evidence.",
        "Manipulation": "Manipulators use private meetings to twist the Bishop’s will.",
        "Greed": "Access to valuables or documents could tempt the greedy.",
        "Remorse": "A remorseful soul might return to confess or undo harm.",
        "Hatred": "Hatred simmers in private, away from witnesses.",
        "Duty": "A sense of duty might bring someone to warn or confront the Bishop.",
        "Curiosity": "Curious minds search for secrets in the Bishop’s papers.",
        "Ambivalence": "Conflicted feelings might drive one to seek answers alone.",
        "Pride": "Prideful suspects demand private audience to assert themselves.",
        "Despair": "Despair might drive one to a final, desperate act in private.",
        "Envy": "Envious eyes covet what is seen only in the study."
    },
    "knows the secret passages of the manor.": {
        "Ambition": "Secret passages are tools for those who wish to move unseen and seize power.",
        "Jealousy": "A jealous person could spy on rivals or arrange secret meetings.",
        "Revenge": "Secret routes allow for ambush or escape after a crime.",
        "Forbidden Love": "Lovers use hidden ways to meet in secret.",
        "Obsession": "Obsessives map every hidden path, unable to let go.",
        "Fanaticism": "Secret passages are used for clandestine rituals.",
        "Desperation": "A desperate person uses any means to avoid detection.",
        "Fear": "Secret passages are a refuge for the frightened.",
        "Blackmail": "Blackmailers use hidden ways to deliver threats unseen.",
        "Guilt": "A guilty party hides their movements through secret ways.",
        "Loyalty": "A loyal servant might use passages to protect their master.",
        "Resentment": "Resentful suspects lurk in the shadows, unseen.",
        "Zealotry": "Zealots use hidden routes to gather or plot.",
        "Shame": "Shame drives one to avoid the main halls.",
        "Manipulation": "Manipulators move unseen, pulling strings from the dark.",
        "Greed": "Greedy hands seek treasures hidden in secret places.",
        "Remorse": "Remorseful souls wander the hidden corridors in regret.",
        "Hatred": "Hatred festers in the darkness of secret halls.",
        "Duty": "Duty may require secret vigilance.",
        "Curiosity": "Curious minds cannot resist exploring every hidden way.",
        "Ambivalence": "Uncertain suspects wander the passages, unsure of their purpose.",
        "Pride": "Prideful suspects may use secret ways to avoid humiliation.",
        "Despair": "Despair leads one to hide from the world.",
        "Envy": "Envy drives one to spy on those more fortunate."
    },
    "is an expert in poisons and rare herbs.": {
        "Ambition": "An ambitious suspect might use poison to remove obstacles.",
        "Jealousy": "A jealous rival could poison a competitor.",
        "Revenge": "Poison is the weapon of those who seek vengeance from the shadows.",
        "Forbidden Love": "A lover might use herbs to heal or harm in secret.",
        "Obsession": "Obsession with toxins leads to dangerous knowledge.",
        "Fanaticism": "A zealot may use poison in ritual or punishment.",
        "Desperation": "Desperate measures call for subtle means.",
        "Fear": "Fearful suspects use poison to defend themselves.",
        "Blackmail": "Blackmailers threaten with knowledge of rare toxins.",
        "Guilt": "A guilty party may use herbs to cover up a crime.",
        "Loyalty": "A loyal servant might use antidotes to protect.",
        "Resentment": "Resentment festers, and poison is a silent tool.",
        "Zealotry": "Zealots may see poison as divine justice.",
        "Shame": "Shame leads to secret use of harmful substances.",
        "Manipulation": "Manipulators use poison to control outcomes.",
        "Greed": "Greedy suspects may sell rare herbs for profit.",
        "Remorse": "Remorseful suspects may seek to heal what they have harmed.",
        "Hatred": "Hatred finds expression in deadly concoctions.",
        "Duty": "Duty may require knowledge of both healing and harm.",
        "Curiosity": "Curious minds experiment with dangerous substances.",
        "Ambivalence": "Uncertain suspects may use poison without conviction.",
        "Pride": "Prideful experts boast of their skills.",
        "Despair": "Despair may drive one to use poison on themselves or others.",
        "Envy": "Envy poisons the heart—and sometimes the cup."
    },
    "possessed the chapel keys.": {
        "Ambition": "Ambitious suspects use the keys to access sacred secrets.",
        "Jealousy": "A jealous rival might lock out others or arrange secret meetings.",
        "Revenge": "Keys allow for private vengeance in holy places.",
        "Forbidden Love": "Lovers meet in the chapel, away from prying eyes.",
        "Obsession": "Obsession with the sacred leads to constant visits.",
        "Fanaticism": "A zealot guards the chapel for ritual or punishment.",
        "Desperation": "Desperate suspects seek sanctuary or escape.",
        "Fear": "Fearful suspects lock themselves away for safety.",
        "Blackmail": "Blackmailers use the keys to plant or retrieve evidence.",
        "Guilt": "A guilty party may seek forgiveness in the chapel.",
        "Loyalty": "Loyal servants guard the chapel for their master.",
        "Resentment": "Resentful suspects may desecrate or defile the sacred.",
        "Zealotry": "Zealots see the keys as a symbol of divine authority.",
        "Shame": "Shame drives one to seek solace in prayer.",
        "Manipulation": "Manipulators use the keys to control access.",
        "Greed": "Greedy suspects may steal offerings or relics.",
        "Remorse": "Remorseful suspects pray for forgiveness.",
        "Hatred": "Hatred may lead to sacrilege.",
        "Duty": "Duty requires guarding the sacred.",
        "Curiosity": "Curious minds search for secrets in the chapel.",
        "Ambivalence": "Ambivalent suspects are unsure why they hold the keys.",
        "Pride": "Prideful suspects flaunt their authority.",
        "Despair": "Despair leads one to seek comfort in the sacred.",
        "Envy": "Envy of the Bishop's spiritual authority."
    },
    "was seen near the Bishop's quarters.": {
        "Ambition": "Ambitious suspects keep close to power.",
        "Jealousy": "A jealous rival lurks near the Bishop's rooms.",
        "Revenge": "A vengeful suspect waits for the right moment.",
        "Forbidden Love": "A lover visits in secret.",
        "Obsession": "Obsession draws one to the Bishop's presence.",
        "Fanaticism": "A zealot seeks to confront or protect the Bishop.",
        "Desperation": "Desperate suspects plead for help.",
        "Fear": "Fearful suspects seek protection or information.",
        "Blackmail": "Blackmailers deliver threats in person.",
        "Guilt": "A guilty party checks on the Bishop's well-being.",
        "Loyalty": "Loyal servants stand guard.",
        "Resentment": "Resentful suspects watch for a chance to strike.",
        "Zealotry": "Zealots seek to convert or confront.",
        "Shame": "Shame keeps one lurking in the shadows.",
        "Manipulation": "Manipulators gather information.",
        "Greed": "Greedy suspects look for valuables.",
        "Remorse": "Remorseful suspects seek forgiveness.",
        "Hatred": "Hatred keeps one close to their enemy.",
        "Duty": "Duty requires vigilance.",
        "Curiosity": "Curious minds seek answers.",
        "Ambivalence": "Ambivalent suspects are drawn but uncertain.",
        "Pride": "Prideful suspects assert their presence.",
        "Despair": "Despair brings one to the Bishop's door.",
        "Envy": "Envy of the Bishop's comfort and status."
    },
    "had no known way to reach the Bishop.": {
        "Ambition": "Ambition is frustrated by lack of access.",
        "Jealousy": "Jealousy festers when kept at a distance.",
        "Revenge": "A vengeful suspect may seek other means.",
        "Forbidden Love": "A lover is kept apart, fueling longing.",
        "Obsession": "Obsession grows when denied contact.",
        "Fanaticism": "A zealot may see this as a test of faith.",
        "Desperation": "Desperate suspects may try to force entry.",
        "Fear": "Fearful suspects avoid the Bishop intentionally.",
        "Blackmail": "Blackmailers may use intermediaries.",
        "Guilt": "A guilty party avoids the Bishop out of shame.",
        "Loyalty": "Loyal servants are kept away for their own good.",
        "Resentment": "Resentment grows when excluded.",
        "Zealotry": "Zealots may see exclusion as persecution.",
        "Shame": "Shame keeps one away.",
        "Manipulation": "Manipulators work from afar.",
        "Greed": "Greedy suspects are denied opportunity.",
        "Remorse": "Remorseful suspects avoid confrontation.",
        "Hatred": "Hatred simmers in isolation.",
        "Duty": "Duty may require keeping a distance.",
        "Curiosity": "Curious minds are frustrated by barriers.",
        "Ambivalence": "Ambivalent suspects make no effort to approach.",
        "Pride": "Prideful suspects refuse to beg for entry.",
        "Despair": "Despair keeps one isolated.",
        "Envy": "Envy grows when kept outside."
    },
    "had a duplicate key to the crypt.": {
        "Ambition": "Ambitious suspects use the crypt for secret meetings or schemes.",
        "Jealousy": "A jealous rival may desecrate the crypt.",
        "Revenge": "A vengeful suspect hides evidence in the crypt.",
        "Forbidden Love": "Lovers meet in secret among the dead.",
        "Obsession": "Obsession with the occult draws one to the crypt.",
        "Fanaticism": "A zealot uses the crypt for forbidden rites.",
        "Desperation": "Desperate suspects seek sanctuary or escape.",
        "Fear": "Fearful suspects hide in the crypt.",
        "Blackmail": "Blackmailers hide secrets among the tombs.",
        "Guilt": "A guilty party seeks forgiveness among the dead.",
        "Loyalty": "Loyal servants guard the crypt.",
        "Resentment": "Resentful suspects desecrate the crypt.",
        "Zealotry": "Zealots perform rituals in the crypt.",
        "Shame": "Shame drives one to hide in darkness.",
        "Manipulation": "Manipulators use the crypt for clandestine meetings.",
        "Greed": "Greedy suspects search for buried treasures.",
        "Remorse": "Remorseful suspects mourn among the tombs.",
        "Hatred": "Hatred leads to desecration.",
        "Duty": "Duty requires guarding the crypt.",
        "Curiosity": "Curious minds explore forbidden places.",
        "Ambivalence": "Ambivalent suspects wander the crypt aimlessly.",
        "Pride": "Prideful suspects claim the crypt as their domain.",
        "Despair": "Despair leads one to the crypt's darkness.",
        "Envy": "Envy of the Bishop's eternal rest."
    },
    "was familiar with the manor's secret alarms.": {
        "Ambition": "Ambitious suspects disable alarms to move unseen.",
        "Jealousy": "A jealous rival uses alarms to catch others in the act.",
        "Revenge": "A vengeful suspect triggers alarms to frame others.",
        "Forbidden Love": "Lovers avoid alarms to meet in secret.",
        "Obsession": "Obsession with security leads to mastery of alarms.",
        "Fanaticism": "A zealot disables alarms for forbidden rites.",
        "Desperation": "Desperate suspects use alarms to call for help.",
        "Fear": "Fearful suspects set alarms for protection.",
        "Blackmail": "Blackmailers use alarms to threaten or control.",
        "Guilt": "A guilty party disables alarms to cover their tracks.",
        "Loyalty": "Loyal servants use alarms to protect the Bishop.",
        "Resentment": "Resentful suspects sabotage alarms.",
        "Zealotry": "Zealots use alarms to gather followers.",
        "Shame": "Shame leads one to avoid detection.",
        "Manipulation": "Manipulators use alarms to control movement.",
        "Greed": "Greedy suspects disable alarms to steal.",
        "Remorse": "Remorseful suspects reset alarms after the fact.",
        "Hatred": "Hatred leads to sabotage.",
        "Duty": "Duty requires vigilance over security.",
        "Curiosity": "Curious minds study the alarm system.",
        "Ambivalence": "Ambivalent suspects forget to reset alarms.",
        "Pride": "Prideful suspects boast of their knowledge.",
        "Despair": "Despair leads one to ignore alarms.",
        "Envy": "Envy of those with unrestricted access."
    }
}

knowledge_pool = [
    "mentions the ritual circle in the cellar.",
    "knows about the Bishop's last sermon.",
    "saw the Bishop after midnight.",
    "heard strange chanting from the chapel.",
    "claims ignorance of the crime details.",
    "describes a detail only the culprit would know.",
    "recalls the Bishop's argument with a guest.",
    "mentions a hidden passage behind the altar."
]

witnesses_pool = [
    "I was seen by the maid, who can vouch for my whereabouts. She was dusting the hallway as I passed.\" Their eyes dart with a mixture of hope and anxiety, as if clinging to this alibi for safety.",
    "I was alone, and no one can confirm my whereabouts. I realize how suspicious that sounds.\" Their posture is tense, shoulders hunched defensively, betraying a deep discomfort.",
    "I saw another suspect nearby, though I can't be sure of the time. They seemed in a hurry.\" Their voice wavers, uncertain, and they avoid your gaze as if afraid of implicating themselves.",
    "No one can confirm where I was. I kept to myself that night.\" Their hands fidget restlessly, and a shadow of doubt crosses their face.",
    "I was with a group in the parlor, sharing drinks and stories. Several people can confirm this.\" Their tone is confident, but a flicker of nervousness betrays a need for validation.",
    "The butler saw me in the corridor. He can confirm I was there.\" They stand a bit straighter, as if the memory of a witness offers some protection.",
    "The gardener saw me outside, tending to the roses. I waved to them as I passed.\" Their expression is earnest, but a hint of worry lingers in their eyes.",
    "The cook can vouch for me—I was in the kitchen helping with supper. We spoke for several minutes.\" Their lips press together, as if replaying the memory for reassurance."
]

financial_pool = [
    "He owed me a great deal of money. I was desperate to collect my debts.\" Their jaw clenches, and a flicker of resentment passes over their features.",
    "I have no interest in his wealth. Money has never motivated me.\" Their voice is steady, but their eyes narrow, as if daring you to doubt their sincerity.",
    "I needed the Bishop's inheritance to pay off my creditors. It was my only hope.\" Their hands tremble slightly, betraying the strain of financial hardship.",
    "I am not motivated by money. My needs are simple.\" They shrug, but a faint blush suggests embarrassment or perhaps a hidden truth.",
    "I was desperate for funds after a string of bad luck. The Bishop's fortune was tempting.\" Their shoulders sag, and a weary sigh escapes them.",
    "I am well-off and had no financial motive. My affairs are in order.\" They speak with calm assurance, but their gaze flickers to the side, as if recalling past temptations.",
    "I lost a fortune in the war. The Bishop knew of my troubles.\" Their eyes darken with old grief, and their voice drops to a whisper.",
    "I was promised a generous donation if I helped him. I never saw a penny.\" Their lips curl in frustration, and they cross their arms defensively."
]

secret_relationship_pool = [
    "We were lovers, though we kept it hidden from everyone. Our bond was forbidden.\" Their cheeks flush, and they glance away, torn between shame and longing.",
    "He threatened to expose my secret if I didn't comply. I was terrified.\" Their hands clench into fists, and a tremor runs through their voice.",
    "We shared a forbidden bond, one that would ruin us both if revealed. I had no choice but to keep it secret.\" Their eyes dart nervously, and they swallow hard, haunted by the weight of secrecy.",
    "There was nothing between us, I swear. Any rumors are lies.\" Their tone is defensive, and their jaw sets stubbornly.",
    "He was like family to me. I would never harm him.\" Their expression softens, but a shadow of sorrow lingers.",
    "We had a professional relationship only. Nothing more.\" Their words are clipped, and they maintain rigid posture, as if hiding discomfort.",
    "He was my mentor, guiding me through difficult times. I owe him everything.\" Their gaze grows distant, and a note of regret colors their words.",
    "We quarreled over a personal matter, but it was resolved. I bear no grudge.\" Their lips press into a thin line, and they shift uneasily."
]

blackmail_pool = [
    "The Bishop was hiding something far worse than you know. I warned him, but he wouldn't listen.\" Their eyes flicker with fear, and their voice drops to a conspiratorial whisper.",
    "Secrets are dangerous in this house. I have my own to protect.\" Their shoulders tense, and they scan the room as if expecting eavesdroppers.",
    "I know nothing of blackmail. That's not my way.\" Their tone is flat, but their fingers drum nervously on the table.",
    "He was being threatened by someone, but he never told me who. I wish I could help.\" Their brow furrows with concern, and they sigh heavily.",
    "I warned him about his secrets. Some things are better left buried.\" Their gaze grows distant, and a shiver runs through them.",
    "Blackmail is a dangerous game. I try to stay out of such affairs.\" Their lips twist in distaste, and they cross their arms protectively.",
    "He confided in me about a blackmailer. I told him to go to the authorities.\" Their voice is earnest, but their eyes betray a flicker of guilt.",
    "I received an anonymous threat as well. It frightened me deeply.\" Their hands shake, and they glance over their shoulder, visibly unsettled."
]

confession_pool = [
    "I would never harm the Bishop! You have to believe me.\" Their voice cracks with desperation, and their eyes plead for understanding.",
    "You have no proof! This is a witch hunt.\" Their face flushes with anger, and they clench their fists in frustration.",
    "Fine, I admit it! I did what had to be done.\" Their shoulders slump in resignation, and a haunted look settles in their eyes.",
    "This is absurd! I demand to speak to my solicitor.\" Their tone is indignant, but a bead of sweat betrays their anxiety.",
    "I am innocent! I swear on my life.\" Their hands tremble, and their breathing quickens with panic.",
    "You can't prove anything! Your case is full of holes.\" Their lips curl in defiance, but their gaze flickers with uncertainty.",
    "I demand a lawyer! I won't say another word.\" Their jaw sets stubbornly, and they cross their arms in a show of resistance.",
    "You don't understand what really happened! There's more to this than you know.\" Their voice is strained, and a shadow of fear passes over their features."
]

clue_locations = {}

elder_sign = {
    "name": "Elder Sign",
    "effect": "faith",
    "amount": 3,
    "desc": (
        "A strange, star-shaped talisman carved from ancient stone. "
        "Its lines twist in impossible angles, and the air around it feels subtly warped. "
        "Legends say it wards off the Old Ones and brings strength to the faithful."
    )
}

scrying_lens = {
    "name": "Scrying Lens",
    "desc": (
        "A cloudy crystal lens set in tarnished silver. When held to the eye, it reveals the hidden movements of those who dwell within the manor."
    )
}

artifact_pool = [
    {
        "name": "Loaded Webley .45",
        "desc": "My, it's a big one. A heavy revolver, fully loaded. Its cold steel promises deadly force.",
        "effect": "combat",
        "amount": "+9",
        "bullets": 6      # Number of bullets
    },
    {
        "name": "Silver Crucifix",
        "desc": "An ornate cross, tarnished with age. It seems to pulse with a faint warmth.",
        "effect": "faith",
        "amount": "+1"
    },
    {
        "name": "Silver Ornate Key",
        "desc": "A beautifully crafted silver key, cold to the touch. It looks important.",
        "effect": "unlock",
        "amount": 1  # Unlocks a special door 
    },
    {
        "name": "Abraxas Amulet",
        "desc": "A dark, ornate amulet that seems to absorb light.",
        "effect": "darkness",
        "amount": "+1"
    },
    {
        "name": "Occult Grimoire",
        "desc": "A leather-bound tome filled with forbidden rites and sigils.",
        "effect": "perception",
        "amount": "+1",
        "side_effect": ("sanity", -1)
    },
    {
        "name": "Monocle of Insight",
        "desc": "A finely crafted monocle that seems to shimmer with hidden knowledge.",
        "effect": "perception",
        "amount": "+2"
    },
    {
        "name": "Vial of Laudanum",
        "desc": "A small bottle of opiate tincture, used to calm nerves.",
        "effect": "sanity",
        "amount": "+3",
        "side_effect": ("perception", -1)
    },
    {
        "name": "Silver Dagger",
        "desc": "A ritual blade, cold to the touch.",
        "effect": "strength",
        "amount": "+2"
    },
    {
        "name": "Brass Spyglass",
        "desc": "An extendable spyglass, engraved with arcane symbols.",
        "effect": "clue",
        "amount": 1  # Reveal a random clue
    },
    {
        "name": "Sealed Letter",
        "desc": "A wax-sealed envelope, addressed in a trembling hand.",
        "effect": "quest",
        "amount": 1  # Triggers a side quest or clue
    },
    {
        "name": "Tarot Deck",
        "desc": "A deck of cards with unsettling illustrations.",
        "effect": "hint",
        "amount": 1,  # Gain a hint, risk sanity
        "side_effects": ("sanity", -1)
    },
    {
        "name": "Ritual Candle",
        "desc": "A black candle that never seems to burn down.",
        "effect": "secret",
        "amount": 1  # Reveal a secret
    },
    {
        "name": "Whispering Skull",
        "desc": "A small skull that sometimes murmurs in forgotten tongues.",
        "effect": "random",
        "amount": 1  # Random effect: clue, sanity loss, or hint
    },
    {
        "name": "Tattered Map",
        "desc": "A hand-drawn map with cryptic markings.",
        "effect": "shortcut",
        "amount": 1  # Reveals a hidden room or shortcut
    },
    {
        "name": "Bishop’s Signet Ring",
        "desc": "A heavy gold ring engraved with ecclesiastical symbols.",
        "effect": "puzzle",
        "amount": 1  # Needed for certain endings or puzzles
    },
    {
        "name": "Phial of Holy Water",
        "desc": "A glass vial filled with water that glows faintly.",
        "effect": "repel",
        "amount": 1  # Repel or weaken supernatural enemies
    },
    {
        "name": "Pocket Watch",
        "desc": "An elegant watch that ticks erratically in certain rooms.",
        "effect": "warn",
        "amount": 1  # Warns of danger or time-sensitive events
    },
    {
        "name": "Candle Snuffer",
        "desc": "A silver tool for extinguishing candles, oddly cold to the touch.",
        "effect": "ritual",
        "amount": 1  # Use in rituals or to solve a puzzle
    },
    {
        "name": "Bloodstained Handkerchief",
        "desc": "Monogrammed, with a faint scent of perfume.",
        "effect": "clue",
        "amount": 1  # Clue or evidence for a suspect
    },
    {
        "name": "Strange Key",
        "desc": "An oddly-shaped key that doesn’t fit any known lock.",
        "effect": "unlock",
        "amount": 1  # Opens a secret passage or room
    },
    {
        "name": "First Fragment of the Eibon Manuscript",
        "desc": "A brittle, yellowed page inked with spiraling glyphs. The words seem to shift when you look away."
    },
    {
        "name": "Second Fragment of the Eibon Manuscript",
        "desc": "A torn vellum leaf, its margins scorched. Faded diagrams hint at forbidden rituals beneath the surface."
    },
    {
        "name": "Third Fragment of the Eibon Manuscript",
        "desc": "A page stained with something dark. The script is cramped and frantic, ending in a spiral that draws the eye inward."
    }
]

# Exclude keys and chests from artifacts
excluded_artifacts = {"Silver Ornate Key", "Strange Key", "Bent Key"}
available_artifacts = [a for a in artifact_pool if a["name"] not in excluded_artifacts and "chest" not in a["name"].lower()]
available_clues = [c for c in game_state.get("clue_pool", [])]

# Pick up to 3 random clues and 3 random artifacts for chests
chest_contents = []
if available_clues:
    chest_contents += random.sample(available_clues, min(3, len(available_clues)))
if available_artifacts:
    chest_contents += [a["name"] for a in random.sample(available_artifacts, min(3, len(available_artifacts)))]

chest_pool = [
    {"name": "Locked Chest", "desc": "A sturdy wooden chest with a heavy iron lock. It looks like it could contain something valuable."},
    {"name": "Ornate Chest", "desc": "An ornate chest inlaid with silver filigree. The lock is intricate and old."},
    {"name": "Dusty Chest", "desc": "A dusty chest tucked away in the corner. Its lock is rusted but still secure."}
]

def motive_probability(perception):
    # 18 = 100%, 15 = 90%, 12 = 75%, 10 = 60%, 8 = 50%, <8 = 35%
    if perception >= 18:
        return 100
    elif perception >= 15:
        return 90
    elif perception >= 12:
        return 75
    elif perception >= 10:
        return 60
    elif perception >= 8:
        return 50
    else:
        return 35
    
def assign_elder_sign_to_room():
    """Assign the Elder Sign to a random unique room at game start."""
    possible_rooms = list(room_templates.keys())
    random.shuffle(possible_rooms)
    # Avoid placing in Foyer or starting room
    for room in possible_rooms:
        if room != "Foyer":
            game_state["elder_sign_room"] = room
            break

def assign_scrying_lens_to_room():
    possible_rooms = list(room_templates.keys())
    random.shuffle(possible_rooms)
    for room in possible_rooms:
        if room != "Foyer" and room != game_state.get("elder_sign_room"):
            game_state["scrying_lens_room"] = room
            break

def auto_generate_walls():
    """
    After passages are generated, add a wall for every non-passage between adjacent rooms.
    """
    game_state["walls"] = set()
    for (x, y), exits in game_state["passages"].items():
        for dir_name, (dx, dy) in moves.items():
            nx, ny = x + dx, y + dy
            neighbor = (nx, ny)
            if dir_name in {"n", "s", "e", "w"} and MAP_MIN <= nx <= MAP_MAX and MAP_MIN <= ny <= MAP_MAX:
                if dir_name not in exits:
                    game_state["walls"].add(((x, y), neighbor))
                    game_state["walls"].add((neighbor, (x, y)))
                    
# Potions to be scattered

def check_for_chest():
    room = game_state["location"]
    # Example: chest_locations should map room names to chest info and reward
    chest_info = chest_locations.get(room)
    if chest_info and not chest_info.get("opened", False):
        print(f"\nYou spot a chest here: {chest_info['chest']['desc']}")
        has_key = any(key in game_state["inventory"] for key in ["Strange Key", "Bent Key", "Silver Ornate Key"])
        if has_key:
            print(f"{ORANGE}[U] Use a key to open the chest{RESET}")
        else:
            print("You need a key to open this chest.")
        print("[L] Leave the chest alone")
        choice = input("> ").strip().lower()
        if choice == "u" and has_key:
            # Remove the first key found
            for key in ["Strange Key", "Bent Key", "Silver Ornate Key"]:
                if key in game_state["inventory"]:
                    game_state["inventory"].remove(key)
                    break
            chest_info["opened"] = True
            reward = chest_info["content"]
            print(f"You unlock the chest and find: {reward}!")
            game_state["inventory"].append(reward)
            game_state["journal"].append(f"Opened chest in {room}: {reward}")
            game_state["score"] += 15
            wait_for_space()

            if all(c.get("opened", False) for c in chest_locations.values()):
                if "Opened every chest" not in game_state["achievements"]:
                    game_state["achievements"].add("Opened every chest")
                    game_state["score"] += ACHIEVEMENT_SCORE
                    print(f"{CYAN}Achievement unlocked: {ACHIEVEMENTS['Opened every chest']} (+{ACHIEVEMENT_SCORE} points){RESET}")

        elif choice == "l":
            print("You leave the chest locked for now.")
            wait_for_space()
        else:
            print("You don't have a key or chose not to use it.")
            wait_for_space()

potion_pool = [
    {"name": "Potion of Strength", "effect": "strength", "amount": 2, "desc": "A crimson tonic that invigorates the muscles."},
    {"name": "Potion of Stamina", "effect": "stamina", "amount": 2, "desc": "A cloudy elixir that fortifies your endurance."},
    {"name": "Potion of Perception", "effect": "perception", "amount": 2, "desc": "A clear liquid that heightens your senses."},
    {"name": "Potion of Agility", "effect": "agility", "amount": 2, "desc": "A sparkling draught that sharpens your reflexes."},
    # {"name": "Potion of Insight", "effect": "perception", "amount": 2, "desc": "A shimmering draught that sharpens your mind."},
    # {"name": "Potion of Endurance", "effect": "stamina", "amount": 2, "desc": "A bitter tonic that steels your body against fatigue."},
    # {"name": "Potion of Zeal", "effect": "faith", "amount": 2, "desc": "A fiery potion that emboldens your spirit."},
    # {"name": "Potion of Might", "effect": "strength", "amount": 2, "desc": "A thick, iron-tasting brew that fills you with raw power."}
]
potion_locations = {}

# Potions to be scattered
def assign_potions_to_rooms():
    """Assign each potion to a random unique room at game start."""
    global potion_locations
    potion_locations = {}
    possible_rooms = list(room_templates.keys())
    random.shuffle(possible_rooms)
    for potion, room in zip(potion_pool, possible_rooms):
        potion_locations[room] = potion

def assign_clues_to_rooms():
    """Assign each clue to a random unique room at game start."""
    global clue_locations
    clue_locations = {}
    # Use all visited_locations at start, or generate a pool of possible rooms
    possible_rooms = list(room_templates.keys())
    random.shuffle(possible_rooms)
    for clue, room in zip(game_state["clue_pool"], possible_rooms):
        clue_locations[room] = clue

def assign_artifacts_to_rooms():
    possible_rooms = [r for r in room_templates.keys() if r != "Foyer"]
    random.shuffle(possible_rooms)
    # Always include the three Eibon Pages, plus 3 random other artifacts
    Eibon_pages = [a for a in artifact_pool if a["name"] in {
    "First Fragment of the Eibon Manuscript",
    "Second Fragment of the Eibon Manuscript",
    "Third Fragment of the Eibon Manuscript"
}]
    other_artifacts = [a for a in artifact_pool if a["name"] not in {
    "First Fragment of the Eibon Manuscript",
    "Second Fragment of the Eibon Manuscript",
    "Third Fragment of the Eibon Manuscript"
}]
    available_artifacts = Eibon_pages + random.sample(other_artifacts, 3)
    artifact_locations = {}
    for artifact, room in zip(available_artifacts, possible_rooms):
        artifact_locations[room] = artifact
    game_state["artifact_locations"] = artifact_locations

def reset_game_state():
    # Clear all mutable game state for a fresh start
    game_state["inventory"] = []
    game_state["quests"] = []
    game_state["clues"] = []
    game_state["journal"] = []
    game_state["suspects"] = []
    game_state["location"] = ""
    game_state["turns"] = 0
    game_state["visited_locations"] = {}
    game_state["position"] = (0, 0)
    for stat in ["health", "faith", "sanity", "perception", "strength", "stamina", "agility", "comeliness"]:
        game_state[stat] = 0
    game_state["name"] = ""
    game_state["gender"] = ""
    game_state["background"] = ""

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def delay_print(s, speed=0.01):
    """Prints text slowly, but finishes instantly if the user presses space or if speed=0."""
    # import msvcrt  Windows only; for cross-platform, use 'getch' from 'getch' package
    import threading

    if speed == 0:
        print(s)
        return

    stop = [False]

    def check_space():
        while not stop[0]:
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key == b' ':
                    stop[0] = True
                    break

    thread = threading.Thread(target=check_space, daemon=True)
    thread.start()

    for i, c in enumerate(s):
        if stop[0]:
            print(s[i:], end='', flush=True)
            break
        print(c, end='', flush=True)
        time.sleep(speed)
    print()
    stop[0] = True
    thread.join(timeout=0.1)  # Clean up the thread

def to_tuple(obj):
    if isinstance(obj, list):
        return tuple(to_tuple(i) for i in obj)
    return obj

def convert_sets(obj):
    if isinstance(obj, set):
        return list(obj)
    elif isinstance(obj, dict):
        return {k: convert_sets(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_sets(i) for i in obj]
    else:
        return obj

def save_game():
    try:
        game_state_copy = convert_sets(game_state)

        # Convert tuple keys in visited_locations to strings for JSON
        visited_serializable = {str(k): v for k, v in game_state["visited_locations"].items()}
        game_state_copy["visited_locations"] = visited_serializable

        # Convert tuple keys in room_flavor_used to strings for JSON
        if "room_flavor_used" in game_state:
            flavor_serializable = {str(k): v for k, v in game_state["room_flavor_used"].items()}
            game_state_copy["room_flavor_used"] = flavor_serializable

        # Convert sets to lists for JSON serialization
        for key in ["breadcrumbs", "persuasion_targets", "walls", "locked_doors", "suspects_interrogated", "searched_rooms"]:
            if key in game_state_copy and isinstance(game_state_copy[key], set):
                # Convert tuples inside the set to lists for JSON
                game_state_copy[key] = [list(item) if isinstance(item, tuple) else item for item in game_state_copy[key]]

        # Convert passages dict of sets to dict of lists
        if "passages" in game_state_copy:
            game_state_copy["passages"] = {str(k): list(v) for k, v in game_state_copy["passages"].items()}

        with open("savegame.json", "w") as f:
            json.dump(game_state_copy, f)

        print("Game saved.")
    except Exception as e:
        print(f"Error saving game: {e}")
    wait_for_space()
    # title_screen()

def load_game():
    global game_state, previous_menu_function
    try:
        if os.path.exists("savegame.json"):
            with open("savegame.json", "r") as f:
                loaded_state = json.load(f)

            # Convert string keys back into tuples for visited_locations
            visited = {}
            for key, value in loaded_state.get("visited_locations", {}).items():
                if isinstance(key, str) and key.startswith("(") and "," in key:
                    x, y = map(int, key.strip("()").split(","))
                    visited[(x, y)] = value
                elif isinstance(key, tuple):
                    visited[key] = value
            loaded_state["visited_locations"] = visited

            # Convert string keys back into tuples and values to sets for passages
            if "passages" in loaded_state:
                passages = {}
                for key, value in loaded_state["passages"].items():
                    if isinstance(key, str) and key.startswith("(") and "," in key:
                        x, y = map(int, key.strip("()").split(","))
                        passages[(x, y)] = set(value)
                    elif isinstance(key, tuple):
                        passages[key] = set(value)
                loaded_state["passages"] = passages

            # Convert string keys back into tuples for room_flavor_used
            if "room_flavor_used" in loaded_state:
                flavor = {}
                for key, value in loaded_state["room_flavor_used"].items():
                    if isinstance(key, str) and key.startswith("(") and "," in key:
                        x, y = map(int, key.strip("()").split(","))
                        flavor[(x, y)] = value
                    elif isinstance(key, tuple):
                        flavor[key] = value
                loaded_state["room_flavor_used"] = flavor

            # Convert lists back to sets of tuples for breadcrumbs, persuasion_targets, walls, locked_doors
            for key in ["breadcrumbs", "persuasion_targets", "walls", "locked_doors"]:
                if key in loaded_state:
                    if isinstance(loaded_state[key], list):
                        loaded_state[key] = set(to_tuple(item) for item in loaded_state[key])
                    elif isinstance(loaded_state[key], set):
                        loaded_state[key] = set(to_tuple(item) for item in loaded_state[key])
                    else:
                        loaded_state[key] = set()
                else:
                    loaded_state[key] = set()

            # Ensure searched_rooms is a set of tuples
            if "searched_rooms" in loaded_state:
                loaded_state["searched_rooms"] = set(to_tuple(item) for item in loaded_state["searched_rooms"])
            else:
                loaded_state["searched_rooms"] = set()

            # Convert position from list to tuple
            if "position" in loaded_state and isinstance(loaded_state["position"], list):
                loaded_state["position"] = tuple(loaded_state["position"])

            game_state.update(loaded_state)

            # Ensure every suspect has a relationship field and asked field is a set
            for suspect in game_state.get("suspects", []):
                if "relationship" not in suspect:
                    suspect["relationship"] = random.choice(relationship_responses)
                if "asked" in suspect and isinstance(suspect["asked"], list):
                    suspect["asked"] = set(suspect["asked"])

                        # Ensure achievements is a set after loading
            if "achievements" in game_state:
                if isinstance(game_state["achievements"], list):
                    game_state["achievements"] = set(game_state["achievements"])
                elif not isinstance(game_state["achievements"], set):
                    game_state["achievements"] = set()
            else:
                game_state["achievements"] = set()

            # Ensure suspects_interrogated is a set of strings (fixes .add() error)
            if "suspects_interrogated" in game_state:
                if isinstance(game_state["suspects_interrogated"], list):
                    game_state["suspects_interrogated"] = set(game_state["suspects_interrogated"])
                elif not isinstance(game_state["suspects_interrogated"], set):
                    game_state["suspects_interrogated"] = set()
            else:
                game_state["suspects_interrogated"] = set()

            # Ensure set-like keys are always sets after loading
            set_keys = [
                "searched_rooms",
                "breadcrumbs",
                # "suspects_interrogated",  # Do NOT include here
                "walls",
                "locked_doors",
                "persuasion_targets"
            ]
            for key in set_keys:
                if key in game_state:
                    if isinstance(game_state[key], list):
                        game_state[key] = set(tuple(item) if isinstance(item, list) else item for item in game_state[key])
                    elif not isinstance(game_state[key], set):
                        game_state[key] = set()
                else:
                    game_state[key] = set()

            print("Game loaded.")
            wait_for_space()

            if game_state.get("location"):
                previous_menu_function = describe_room
                describe_room()
            else:
                title_screen()
        else:
            print("No save file found.")
            wait_for_space()
            title_screen()
    except Exception as e:
        print(f"Error loading game: {e}")
        wait_for_space()
        title_screen()
                             
def faith_check(difficulty=10):
    """Returns True if faith check passes (difficulty 1-18)."""
    return random.randint(1, 18) <= max(1, game_state["faith"] - difficulty + 10)

def pick_unique_initial_rooms(room_list, count, fixed_rooms):
    """Pick up to `count` rooms from room_list, no two sharing the same first letter with each other or with fixed_rooms."""
    used_letters = {room[0].upper() for room in fixed_rooms}
    selected = []
    for room in random.sample(room_list, len(room_list)):
        first = room[0].upper()
        if first not in used_letters:
            selected.append(room)
            used_letters.add(first)
        if len(selected) == count:
            break
    return selected

def move_to_new_room(direction=None, show_room=True):
    x, y = game_state["position"]
    moves = {
        "n": (0, -1),
        "s": (0, 1),
        "e": (1, 0),
        "w": (-1, 0)
    }
    if direction not in moves:
        direction = random.choice(list(moves.keys()))
    dx, dy = moves[direction]
    new_x, new_y = x + dx, y + dy

    # Check map bounds
    if not (MAP_MIN <= new_x <= MAP_MAX and MAP_MIN <= new_y <= MAP_MAX):
        delay_print("You sense an unnatural barrier. The manor does not extend further in that direction.")
        wait_for_space()
        show_map()
        return

    pos = (x, y)
    new_pos = (new_x, new_y)
    walls = game_state.get("walls", set())

    # Check for wall
    if ((pos, new_pos) in walls):
        delay_print("A wall blocks your way.")
        # wait_for_space()
        show_map()
        return

    # Check for passage
    allowed_dirs = game_state["passages"].get((x, y), set())
    if direction not in allowed_dirs:
        delay_print("A wall blocks your way.")
        # wait_for_space()
        show_map()
        return

    # Move to new position
    game_state["position"] = new_pos

    # Mark this room as visited in breadcrumbs
    if "breadcrumbs" not in game_state or not isinstance(game_state["breadcrumbs"], set):
        game_state["breadcrumbs"] = set()
    game_state["breadcrumbs"].add(new_pos)

    # Assign a new or existing location name for new_pos
    if new_pos not in game_state["visited_locations"]:
        new_location = random.choice(list(room_templates.keys()))
        game_state["visited_locations"][new_pos] = new_location
    game_state["location"] = game_state["visited_locations"][new_pos]

    # Move suspects after player moves
    move_suspects()

    if show_room:
        game_state["score"] += 1 # Increment score for exploring a new room

def move_suspects():
    for suspect in game_state["suspects"]:
        # Halt movement if suspect is in the same room as the player
        if suspect.get("position") == game_state["position"]:
            continue  # Do not move this suspect this turn

        # Initialize suspect position if not set (start at random valid position)
        if "position" not in suspect or suspect["position"] is None:
            while True:
                pos = (random.randint(MAP_MIN, MAP_MAX), random.randint(MAP_MIN, MAP_MAX))
                if pos != game_state["position"]:
                    suspect["position"] = pos
                    suspect["wait_turns"] = 0
                    break

        # If the suspect is a transformed monstrosity and is chasing the player, move toward player
        if suspect.get("transformed", False) and suspect.get("chasing_player", False):
            # --- Movement speed based on difficulty ---
            if game_state.get("difficulty") == "easy":
                # Move every other turn (use a cooldown)
                if "move_cooldown" not in suspect:
                    suspect["move_cooldown"] = 0
                suspect["move_cooldown"] += 1
                if suspect["move_cooldown"] % 2 != 1:
                    continue  # Skip movement this turn
            # On hard, move every turn (no cooldown needed)

            sx, sy = suspect["position"]
            px, py = game_state["position"]
            dx = 1 if px > sx else -1 if px < sx else 0
            dy = 1 if py > sy else -1 if py < sy else 0
            next_pos = (sx + dx, sy + dy)
            walls = game_state.get("walls", set())
            locked_doors = game_state.get("locked_doors", set())
            # Only move if not blocked by wall/door and within bounds
            if (
                MAP_MIN <= next_pos[0] <= MAP_MAX and MAP_MIN <= next_pos[1] <= MAP_MAX
                and ((sx, sy), next_pos) not in walls
                and ((sx, sy), next_pos) not in locked_doors
            ):
                suspect["position"] = next_pos
            continue  # Skip normal movement for chasing suspect

        # Handle waiting (standing still)
        if suspect.get("wait_turns", 0) > 0:
            suspect["wait_turns"] -= 1
            continue  # Skip movement this turn

        # 1 in 3 chance to stand still for 1 or 2 turns
        if random.random() < 1/3:
            suspect["wait_turns"] = random.choice([1, 2])
            continue

        # Get all adjacent positions within map bounds (visited or not)
        x, y = suspect["position"]
        walls = game_state.get("walls", set())
        locked_doors = game_state.get("locked_doors", set())
        adjacent = []
        for dx, dy in [
            (0, 1), (0, -1), (1, 0), (-1, 0),  # N, S, E, W
        ]:
            nx, ny = x + dx, y + dy
            if MAP_MIN <= nx <= MAP_MAX and MAP_MIN <= ny <= MAP_MAX:
                # Only add if not blocked by wall or locked door
                if ((x, y), (nx, ny)) not in walls and ((x, y), (nx, ny)) not in locked_doors:
                    adjacent.append((nx, ny))

        # Move to a random adjacent visited room if possible
        if adjacent:
            suspect["position"] = random.choice(adjacent)
        # else: no move (surrounded by unvisited rooms or walls)

def show_stats(from_combat=False):
    clear()
    delay_print(f"Name: {game_state['name']}")
    print(f"Gender: {game_state['gender']}")
    print(f"Background: {game_state['background']}")
    for stat in ["faith", "sanity", "perception", "strength", "stamina", "agility", "comeliness"]:
        print(f"{stat.capitalize()}: {game_state[stat]}")
    wait_for_space()
    if from_combat:
        return  # Just return to combat loop
    if previous_menu_function:
        previous_menu_function()
    else:
        title_screen()

def show_journal():
    clear()
    show_hints = game_state.get("show_suspicion_hints", True)

    delay_print("Journal Entries:")
    clues = [entry for entry in game_state["journal"] if entry.startswith("CLUE FOUND")]
    artifacts = [entry for entry in game_state["journal"] if entry.startswith("ARTIFACT FOUND")]
    responses = [entry for entry in game_state["journal"] if not entry.startswith("CLUE FOUND") and not entry.startswith("ARTIFACT FOUND")]

    if clues:
        print("\n--- Clues Discovered ---")
        for entry in clues:
            print(entry)
    if artifacts:
        print("\n--- Artifacts Discovered ---")
        for entry in artifacts:
            print(entry)
    if responses:
        print("\n--- Suspect Responses ---")
        last_suspect = None
        for entry in responses:
            # Extract suspect name from entry if possible
            if "Testimony from " in entry:
                suspect_name = entry.split("Testimony from ")[1].split(" at ")[0]
            else:
                suspect_name = None
            # Print a separator and pause if moving to a new suspect
            if last_suspect and suspect_name and suspect_name != last_suspect:
                delay_print(f"{YELLOW}--- Next Suspect ---{RESET}", speed=0.01)
            print(entry)
            last_suspect = suspect_name
        print("-----------------------------")

    print("\n--- THINGS TO DO ---")
    for quest in game_state["quests"]:
        if not quest.startswith("\033[9m"):
            print(quest)

    if not clues and not artifacts and not responses:
        delay_print("Your journal is empty.")

    print(f"\nHints are currently {'ON' if show_hints else 'OFF'}.")
    if show_hints:
        for s in game_state["suspects"]:
            if s["name"] in game_state.get("suspects_interrogated", set()):
                opp = s.get("opportunity", "uncertain")
                if opp == "strong":
                    print(f"{YELLOW}Hint: {s['name']} had strong opportunity.{RESET}")
                elif opp == "weak":
                    print(f"{ORANGE}Hint: {s['name']} had weak opportunity.{RESET}")
                else:
                    print(f"{GREY}Hint: {s['name']}'s opportunity is uncertain.{RESET}")

    interviewed = [s for s in game_state["suspects"] if s["name"] in game_state.get("suspects_interrogated", set())]

    # Menu options
    print("\n[T] Toggle suspicion hints   [M] Murder Board   [P] Suspect Patterns Table", end="")
    if interviewed:
        print("   [D] Deduction tree for an interviewed suspect", end="")
    print("   [Enter] Continue\n")

    choice = input("> ").strip().lower()
    if choice == "t":
        game_state["show_suspicion_hints"] = not show_hints
        show_journal()
        return
    elif choice == "m":
        show_murder_board()
        show_journal()
        return
    elif choice == "p":
        show_suspect_patterns()
        show_journal()
        return
    elif choice == "d" and interviewed:
        print("\nEnter the suspect's name (or number) for deduction tree:")
        for idx, s in enumerate(interviewed, 1):
            print(f"[{idx}] {s['name']}")
        suspect_input = input("> ").strip()
        if suspect_input.isdigit():
            idx = int(suspect_input) - 1
            if 0 <= idx < len(interviewed):
                suspect_name = interviewed[idx]["name"]
            else:
                print("Invalid number.")
                wait_for_space()
                show_journal()
                return
        else:
            suspect_name = suspect_input
        deduction_tree_for_suspect(suspect_name)
        show_journal()
        return

    if previous_menu_function:
        previous_menu_function()
    else:
        title_screen()

def build_timeline_data():
    """Builds a timeline of all suspects' whereabouts."""
    timeline = {}
    for s in game_state["suspects"]:
        alibi = s.get("alibi", {})
        time = alibi.get("time", "Unknown")
        loc = alibi.get("location", "Unknown")
        if time not in timeline:
            timeline[time] = {}
        if loc not in timeline[time]:
            timeline[time][loc] = []
        timeline[time][loc].append(s["name"])
    return timeline

def show_murder_board():
    clear()
    print(f"{YELLOW}=== MURDER BOARD: Suspect Whereabouts ==={RESET}\n")
    # Only include interrogated suspects
    interrogated_names = set(game_state.get("suspects_interrogated", set()))
    timeline = {}
    for s in game_state["suspects"]:
        if s["name"] not in interrogated_names:
            continue
        alibi = s.get("alibi", {})
        time = alibi.get("time", "Unknown")
        loc = alibi.get("location", "Unknown")
        if time not in timeline:
            timeline[time] = {}
        if loc not in timeline[time]:
            timeline[time][loc] = []
        timeline[time][loc].append(s["name"])
    if not timeline:
        print("No suspects have been interrogated yet.")
        wait_for_space()
        return
    times = sorted(timeline.keys())
    # Gather all unique locations
    locations = set()
    for t in timeline.values():
        locations.update(t.keys())
    locations = sorted(locations)

    # Determine max suspect name length among interrogated suspects
    max_name_len = max((len(s["name"]) for s in game_state["suspects"] if s["name"] in interrogated_names), default=10)
    col_width = max(max_name_len + 2, 12)  # Add padding, minimum 12

    # Print header
    print("Time      | " + " | ".join(f"{loc[:col_width]:<{col_width}}" for loc in locations))
    print("-" * (11 + len(locations) * (col_width + 3)))
    for time in times:
        row = f"{time:<9} | "
        row += " | ".join(
            ", ".join(timeline[time].get(loc, []))[:col_width].ljust(col_width)
            if timeline[time].get(loc) else " " * col_width
            for loc in locations
        )
        print(row)
    print("\nLegend: Each cell shows interrogated suspects who claim to be in that room at that time.")
    print("Look for overlaps, corroborations, or contradictions!")
    wait_for_space()

def check_alibi_corroboration(suspect):
    """Returns a tuple (corroborators, contradictors, alone) for a suspect's alibi."""
    alibi = suspect.get("alibi", {})
    time = alibi.get("time", None)
    loc = alibi.get("location", None)
    corroborators = []
    contradictors = []
    for s in game_state["suspects"]:
        if s["name"] == suspect["name"]:
            continue
        other_alibi = s.get("alibi", {})
        if other_alibi.get("time") == time and other_alibi.get("location") == loc:
            corroborators.append(s["name"])
        elif other_alibi.get("time") == time and other_alibi.get("location") != loc:
            contradictors.append(s["name"])
    alone = not corroborators
    return corroborators, contradictors, alone

def show_suspect_patterns():
    clear()
    print(f"{CYAN}=== SUSPECT PATTERNS: Interviewed Suspects ==={RESET}\n")
    interviewed = [s for s in game_state["suspects"] if s["name"] in game_state.get("suspects_interrogated", set())]
    if not interviewed:
        print("No suspects have been interviewed yet.")
        wait_for_space()
        return

    # Find the maximum alibi text length from all alibi_pools
    max_alibi_len = 40  # Default minimum
    for pool in alibi_pools:
        for alibi in pool:
            max_alibi_len = max(max_alibi_len, len(alibi.get("text", "")))

    print(f"{'Suspect':<18} {'Alibi':<{max_alibi_len}} {'Corroborated':<15} {'Contradicted':<15} {'Alone':<8}")
    print("-" * (18 + max_alibi_len + 15 + 15 + 8 + 4))
    for s in interviewed:
        alibi = s.get("alibi", {})
        alibi_text = alibi.get("text", "No alibi")
        corroborators, contradictors, alone = check_alibi_corroboration(s)
        print(f"{s['name']:<18} {alibi_text[:max_alibi_len]:<{max_alibi_len}} "
              f"{(', '.join(corroborators) if corroborators else '-'):15} "
              f"{(', '.join(contradictors) if contradictors else '-'):15} "
              f"{'Yes' if alone else 'No':<8}")
    print("\nLook for suspects who are always alone, never seen, or whose stories overlap/contradict.")
    wait_for_space()



def show_quests():
    clear()
    delay_print("Active Mysteries:")
    awarded = set()
    score_award = 0

    # Award points for completed quests
    for quest in game_state["quests"]:
        # Award 15 points for these quests
        if (
            "Assemble the Book of Eibon by finding all three manuscript fragments." in quest
            or "Obtain the -incomplete- Book of Eibon." in quest
            or "Assemble the Book of Eibon and open the portal to the Elder Ones' realm." in quest
            or "Pray for guidance in the chapel." in quest
            or "Successfully evade an underworld monstrosity" in quest
        ):
            if quest not in awarded:
                score_award += 15
                awarded.add(quest)
        # Award 25 points for Bishop investigation and banishing Azathoth
        if (
            "Investigate the disappearance of the Bishop." in quest
            or "Banish Azathoth back to the Elder Ones' domain." in quest
        ):
            if quest not in awarded:
                score_award += 25
                awarded.add(quest)
        # Do not award for searching for Eibon pages (redundant)
        if "You must search the manor for the missing pages of the Book of Eibon." in quest:
            continue

        delay_print(f"- {quest}")

    if score_award > 0:
        game_state["score"] += score_award
        print(f"{YELLOW}Quest completion bonus: +{score_award} points!{RESET}")

    wait_for_space()

    suspects_here = [
        s for s in game_state["suspects"]
        if s.get("position") == game_state["position"]
    ]

    if previous_menu_function:
        previous_menu_function()
    else:
        title_screen()

    print("\nWhat would you like to do?")
    print("[1] Search the room")
    print("[2] Move to another location")
    print("[3] Show map")
    print("[4] Check journal")
    print("[5] Check inventory")
    if suspects_here:
        suspect_names = ", ".join(s["name"] for s in suspects_here)
        print(f"[6] Interrogate suspect ({suspect_names})")
    print("[7] Attempt case resolution")
    print("[8] Save game")
    print("[9] Quit to title")

    x, y = game_state["position"]
    available_exits = [d.upper() for d in game_state["passages"].get((x, y), set())]
    
    if available_exits:
        print(f"\nThere are exits: {', '.join(available_exits)}")
    else:
        print("\nThere are no available exits from this room.")

    user_input = input("> ").strip().lower()
    if user_input == "1":
        add_random_clue()
        # describe_room()
    elif user_input == "2":
        clear()
        print("Where would you like to go? (N, S, E, W)")
        dir_input = input("> ").strip().lower()
        if dir_input in ["n","s","e","w","ne","nw","se","sw"]:
            move_to_new_room(dir_input)
        else:
            delay_print("Unknown direction. Please enter a valid compass direction.")
            wait_for_space()
            describe_room()
    elif user_input == "3":
        show_map()
        # describe_room()
    elif user_input == "4" or user_input == "journal" or user_input == "j":
        show_journal()
    elif user_input == "5" or user_input == "inventory" or user_input == "i":
        show_inventory()
    elif user_input == "6" and suspects_here:
        interrogate_suspect()
    elif user_input == "7":
        case_resolution()
    elif user_input == "8" or user_input == "save":
        save_game()
        wait_for_space("Press SPACE to continue.")
        describe_room()
    elif user_input == "9" or user_input == "quit":
        title_screen()
    else:
        handle_input(user_input, describe_room)


def show_map():
    global last_alerted_position
    clear()
    location = game_state["location"]
    pos = game_state["position"]
    print(f"{YELLOW}Current Location: {location} at {pos}{RESET}")
    look_around(pause=False, instant=True)  # Show short description under current location

    delay_print("\nMap:", speed=0)

    # Only ask for fog of war toggle once per session
    if "fog_of_war" not in game_state:
        choice = input("Show only visited rooms/walls on map (fog of war)? (Y/N): ").strip().lower()
        game_state["fog_of_war"] = (choice == "y")

    # --- Add this block for NPC visibility toggle ---
    if "can_see_npcs" not in game_state or game_state.get("debug_npc_toggle", True):
        npc_choice = input("Show NPCs (suspects) on map? (Y/N): ").strip().lower()
        game_state["can_see_npcs"] = (npc_choice == "y")
        game_state["debug_npc_toggle"] = False  # Only ask once per session

    show_npcs = game_state.get("can_see_npcs", False)
    render_map(show_npcs, fog_of_war=game_state.get("fog_of_war", False))
   
    if "last_alerted_position" not in globals():
        last_alerted_position = None

    while True:
        key = msvcrt.getch()
        moved = False
        prev_pos = game_state["position"]

        # Arrow keys: first byte is b'\xe0', second byte is direction
        if key == b'\xe0':
            arrow = msvcrt.getch()
            if arrow == b'H':  # Up
                move_to_new_room('n', show_room=False)
                moved = True
            elif arrow == b'P':  # Down
                move_to_new_room('s', show_room=False)
                moved = True
            elif arrow == b'K':  # Left
                move_to_new_room('w', show_room=False)
                moved = True
            elif arrow == b'M':  # Right
                move_to_new_room('e', show_room=False)
                moved = True
        elif key in [b'n', b'N']:
            move_to_new_room('n', show_room=False)
            moved = True
        elif key in [b's', b'S']:
            move_to_new_room('s', show_room=False)
            moved = True
        elif key in [b'e', b'E']:
            move_to_new_room('e', show_room=False)
            moved = True
        elif key in [b'w', b'W']:
            move_to_new_room('w', show_room=False)
            moved = True
        elif key in [b'\r', b'\n']:  # Enter key
            last_alerted_position = None
            if previous_menu_function:
                previous_menu_function()
            else:
                describe_room()
            return
        # Ignore other keys

        if moved:
            new_pos = game_state["position"]
            suspects_here = [
                s for s in game_state["suspects"]
                if s.get("position") == new_pos
            ]
            # Only alert if entering a suspect's space and haven't alerted for this position yet
            if suspects_here and (last_alerted_position != new_pos):
                names = ', '.join(s["name"] for s in suspects_here)
                delay_print(f"{ORANGE}You see someone here: {names}{RESET}")
                wait_for_space("Press SPACE to continue.")
                last_alerted_position = new_pos
                interrogate_suspect()  # <-- Go directly to interrogation menu
                return
            else:
                # Reset alert if no suspects here
                if not suspects_here:
                    last_alerted_position = None
            show_map()
            return

def deduction_tree_for_suspect(suspect_name):
    suspect = next((s for s in game_state["suspects"] if s["name"].lower() == suspect_name.lower()), None)
    if not suspect:
        print(f"No suspect named '{suspect_name}' found.")
        wait_for_space()
        return

    asked = suspect.get("asked", set())
    print(f"\nDeduction Tree for {suspect['name']} ({suspect.get('trait', 'Unknown')}):")
    print("Start")
    print("│")

    # Motive (always show)
    print(f"├─ Motive: {suspect.get('motive', 'Unknown')}")
    # Alibi (always show)
    alibi = suspect.get("alibi", {})
    alibi_text = alibi.get("text", "No alibi given.")
    print(f"├─ Alibi: {alibi_text}")
    # Corroboration/Contradiction (always show)
    corroborators, contradictors, alone = check_alibi_corroboration(suspect)
    if corroborators:
        print(f"│   ├─ {YELLOW}Corroborated by: {', '.join(corroborators)}{RESET}")
    if contradictors:
        print(f"│   ├─ {RED}Contradicted by: {', '.join(contradictors)}{RESET}")
    if alone:
        print(f"│   ├─ {GREY}No one corroborates this alibi.{RESET}")

    # Additional fields (only if asked)
    if "relationship" in asked:
        print(f"├─ Relationship: {suspect.get('relationship', 'Unknown')}")
    if "means" in asked:
        print(f"├─ Means: {suspect.get('means', 'Unknown')}")
    if "knowledge" in asked:
        print(f"├─ Knowledge: {suspect.get('knowledge', 'Unknown')}")
    if "witnesses" in asked:
        print(f"├─ Witnesses: {suspect.get('witnesses', 'Unknown')}")
    if "financial" in asked:
        print(f"├─ Financial: {suspect.get('financial', 'Unknown')}")
    if "secret_relationship" in asked:
        print(f"├─ Secret Relationship: {suspect.get('secret_relationship', 'Unknown')}")
    if "blackmail" in asked:
        print(f"├─ Blackmail/Occult: {suspect.get('blackmail', 'Unknown')}")
    if "confession" in asked:
        print(f"├─ Confession: {suspect.get('confession', 'Unknown')}")

    # Opportunity (always show)
    opportunity = suspect.get("opportunity", "uncertain")
    if opportunity == "strong":
        print("├─ ✓ Had strong opportunity to commit the crime.")
    elif opportunity == "weak":
        print("├─ ? Had weak opportunity to commit the crime.")
    else:
        print("├─ ✗ Opportunity is uncertain or unlikely.")

    print("└─ (Gather more evidence for a stronger deduction.)\n")
    wait_for_space()
def render_map(show_npcs=False, fog_of_war=False):
    """
    Render the entire map grid (not just a window around the player).
    Shows all rooms from MAP_MIN to MAP_MAX in both x and y, with a perimeter wall.
    """
    px, py = game_state["position"]

    suspect_positions = {}
    if show_npcs:
        for idx, s in enumerate(game_state["suspects"], 1):
            pos = s.get("position")
            if pos:
                pos = tuple(pos)
                suspect_positions.setdefault(pos, []).append(str(idx))

    # Unicode box-drawing characters
    VERT_WALL = "│"
    HORZ_WALL = "─"
    VERT_DOOR = "║"
    HORZ_DOOR = "═"
    SPACE = " "

    sanity = game_state["sanity"]
    breadcrumbs = set(game_state.get("breadcrumbs", []))
    breadcrumbs.add((px, py))

    # --- LEGEND: Unique abbreviations, using first letter, then first+last if needed ---
    legend = {}
    used_abbrevs = set()
    for room in set(game_state["visited_locations"].values()):
        abbrev = room[0].upper()
        if abbrev not in used_abbrevs:
            legend[abbrev] = room
            used_abbrevs.add(abbrev)
        else:
            # Use first and last letter, capitalized
            two_letter = (room[0] + room[-1]).capitalize()
            if two_letter not in used_abbrevs:
                legend[two_letter] = room
                used_abbrevs.add(two_letter)
            else:
                # If still not unique, use first and last letter, capitalized
                alt_abbrev = (room[0] + room[-1]).capitalize()
                if alt_abbrev not in used_abbrevs:
                    legend[alt_abbrev] = room
                    used_abbrevs.add(alt_abbrev)
                else:
                    # As a last resort, use only the first letter (may duplicate)
                    legend[abbrev] = room

    legend_items = [f"{abbr} = {room}" for abbr, room in sorted(legend.items())]
    col_count = 4
    row_len = (len(legend_items) + col_count - 1) // col_count
    legend_lines = []
    for i in range(row_len):
        cols = []
        for j in range(col_count):
            idx = i + j * row_len
            if idx < len(legend_items):
                cols.append(f"{legend_items[idx]:<25}")
        legend_lines.append(" ".join(cols))

    walls = game_state.get("walls", set())
    locked_doors = game_state.get("locked_doors", set())
    visited = set(game_state["visited_locations"].keys())

    # Use the full map bounds
    min_x, max_x = MAP_MIN, MAP_MAX
    min_y, max_y = MAP_MIN, MAP_MAX
    grid_size = MAP_SIZE

    # --- Draw top perimeter wall ---
    top_row = ""
    for x in range(min_x, max_x + 1):
        top_row += HORZ_WALL * 3
    print(f"   {top_row}")

    for row_idx, y in enumerate(range(min_y, max_y + 1)):
        row = ""
        # Left perimeter wall
        row += VERT_WALL
        for x in range(min_x, max_x + 1):
            pos = (x, y)
            char = "   "
            color = ""
            unexplored = fog_of_war and pos not in breadcrumbs

            # Cell rendering
            if unexplored:
                char = "   "
                color = ""
            elif pos == (px, py):
                char = " @ "
                color = CYAN
                if sanity < 4 and random.random() < 0.5:
                    char = " # "
            elif show_npcs and pos in suspect_positions and (
                    (not fog_of_war and pos in game_state["visited_locations"]) or
                    (fog_of_war and pos in breadcrumbs)
                ):
                # If any suspect at this position is transformed, mark RED
                suspects_here = [s for s in game_state["suspects"] if s.get("position") == pos]
                if any(s.get("transformed", False) for s in suspects_here):
                    char = " " + "".join(suspect_positions[pos]) + " "
                    color = RED
                else:
                    char = " " + "".join(suspect_positions[pos]) + " "
                    color = ORANGE
                if sanity < 4 and random.random() < 0.4:
                    char = " ? "
            elif not fog_of_war and pos in game_state["visited_locations"]:
                loc = game_state["visited_locations"].get(pos, "Empty Room")
                searched = "searched_rooms" in game_state and pos in game_state["searched_rooms"]
                if loc == "Empty Room":
                    char = " ◉ "
                    color = GREY if searched else GREEN
                else:
                    # Use the same abbreviation as the legend
                    abbr = None
                    for key, value in legend.items():
                        if value == loc:
                            abbr = key
                            break
                    if abbr is None:
                        abbr = loc[0].upper()
                    # Pad abbreviation to fit cell width (3 chars)
                    char = f" {abbr:<2}" if len(abbr) == 1 else f"{abbr[:2]:<3}"
                    color = GREY if searched else YELLOW
                if sanity < 4 and random.random() < 0.2:
                    char = random.choice([" ~ ", " * ", " % ", " $ "])
            elif fog_of_war and pos in breadcrumbs:
                loc = game_state["visited_locations"].get(pos, "Empty Room")
                searched = "searched_rooms" in game_state and pos in game_state["searched_rooms"]
                if loc == "Empty Room":
                    char = " ◉ "
                    color = GREY if searched else GREEN
                else:
                    abbr = None
                    for key, value in legend.items():
                        if value == loc:
                            abbr = key
                            break
                    if abbr is None:
                        abbr = loc[0].upper()
                    char = f" {abbr:<2}" if len(abbr) == 1 else f"{abbr[:2]:<3}"
                    color = GREY if searched else YELLOW
            row += f"{color}{char}{RESET}"

            # Only add vertical wall/space if not the last cell in the row
            if x < max_x:
                right_pos = (x + 1, y)
                if fog_of_war:
                    if (not unexplored or right_pos in breadcrumbs):
                        if ((pos, right_pos) in locked_doors):
                            row += VERT_DOOR
                        elif ((pos, right_pos) in walls):
                            row += VERT_WALL
                        else:
                            row += SPACE
                    else:
                        row += SPACE
                else:
                    if ((pos, right_pos) in locked_doors):
                        row += VERT_DOOR
                    elif ((pos, right_pos) in walls):
                        row += VERT_WALL
                    else:
                        row += SPACE
        # Right perimeter wall
        row += VERT_WALL

        # Print the map row with the corresponding legend line (if any)
        if row_idx < len(legend_lines):
            print(f"{row}   {legend_lines[row_idx]}")
        else:
            print(row)

        # Draw horizontal walls/doors below this row (unless last row)
        if y < max_y:
            wall_row = VERT_WALL  # Left perimeter
            for x in range(min_x, max_x + 1):
                pos = (x, y)
                below_pos = (x, y + 1)
                if fog_of_war:
                    if pos in breadcrumbs or below_pos in breadcrumbs:
                        if ((pos, below_pos) in locked_doors):
                            wall_row += HORZ_DOOR * 3
                        elif ((pos, below_pos) in walls):
                            wall_row += HORZ_WALL * 3
                        else:
                            wall_row += SPACE * 3
                    else:
                        wall_row += SPACE * 3
                else:
                    if ((pos, below_pos) in locked_doors):
                        wall_row += HORZ_DOOR * 3
                    elif ((pos, below_pos) in walls):
                        wall_row += HORZ_WALL * 3
                    else:
                        wall_row += SPACE * 3
                # Only add vertical wall/space if not the last cell in the row
                if x < max_x:
                    right_pos = (x + 1, y)
                    if fog_of_war:
                        if pos in breadcrumbs and right_pos in breadcrumbs:
                            if ((pos, right_pos) in locked_doors):
                                wall_row += VERT_DOOR
                            elif ((pos, right_pos) in walls):
                                wall_row += VERT_WALL
                            else:
                                wall_row += SPACE
                        else:
                            wall_row += SPACE
                    else:
                        if ((pos, right_pos) in locked_doors):
                            wall_row += VERT_DOOR
                        elif ((pos, right_pos) in walls):
                            wall_row += VERT_WALL
                        else:
                            wall_row += SPACE
            wall_row += VERT_WALL  # Right perimeter
            print(f"{wall_row}")

    # --- Draw bottom perimeter wall ---
    bottom_row = ""
    for x in range(min_x, max_x + 1):
        bottom_row += HORZ_WALL * 3
    print(f"   {bottom_row}")
    print(f"\n{YELLOW}Tip: Use arrow keys or N/S/E/W to move.To SEARCH a room, press ENTER to return to the action menu.{RESET}")

    print("\nSuspects:")
    num_to_show = len(game_state.get("suspects", []))
    for idx, s in enumerate(game_state["suspects"][:num_to_show], 1):
        name = s["name"]
        if name in game_state.get("suspects_interrogated", set()):
            color = YELLOW
        else:
            color = GREY
        print(f"{color}{idx}. {name}{RESET}")

def show_map_flow():
    """
    Print a simplified ASCII map flow based on the current generated manor.
    Shows only key rooms and their connections.
    """
    pos_by_room = {v: k for k, v in game_state["visited_locations"].items()}
    foyer = pos_by_room.get("Foyer")
    main_hall = pos_by_room.get("Main Hall")
    manor_grounds = pos_by_room.get("Manor Grounds")
    atrium = pos_by_room.get("Atrium")
    solarium = pos_by_room.get("Solarium")
    cellar = pos_by_room.get("Cellar")
    garden = pos_by_room.get("Garden")
    observatory = pos_by_room.get("Observatory")
    well_house = pos_by_room.get("Well House")
    stable = pos_by_room.get("Horse Stable")

    print("\n--- Manor Map Flow (Key Rooms) ---\n")
    print("         [{0}]".format("Observatory" if observatory else "??"))
    print("             |")
    print("         [{0}]".format("Solarium" if solarium else "??"))
    print("             |")
    print("[{0}]--[{1}]--[{2}]--[{3}]--[{4}]--[{5}]".format(
        "Garden" if garden else "??",
        "Atrium" if atrium else "??",
        "Main Hall" if main_hall else "??",
        "Foyer" if foyer else "??",
        "Manor Grounds" if manor_grounds else "??",
        "Horse Stable" if stable else "??"
    ))
    print("             |")
    print("         [{0}]".format("Cellar" if cellar else "??"))
    print("             |")
    print("         [{0}]".format("Well House" if well_house else "??"))
    print()
    wait_for_space()
    if previous_menu_function:
        previous_menu_function()
    else:
        title_screen()

def show_inventory():
    clear()
    delay_print("Inventory:")
    if game_state["inventory"]:
        for idx, item in enumerate(game_state["inventory"], 1):
            print(f"[{idx}] {distort_text(item, game_state['sanity'])}")
        print(f"[{len(game_state['inventory'])+1}] Use an item")
        print(f"[{len(game_state['inventory'])+2}] Return")
        choice = input("\nSelect an item to inspect, use, or RETURN to action menu: ")

        # Allow pressing Enter to return to action menu
        if choice.strip() == "":
            if previous_menu_function:
                previous_menu_function()
            else:
                describe_room()
            return
        elif choice.strip() == "":
            # User pressed only spaces (e.g., spacebar), ignore and ask again
            show_inventory()
            return

        if choice.isdigit():
            idx = int(choice) - 1
            if idx == len(game_state["inventory"]):  # Use an item
                if previous_menu_function:
                    use_item(previous_menu_function)
                else:
                    use_item(describe_room)
                return
            elif idx == len(game_state["inventory"]) + 1:  # Return
                if previous_menu_function:
                    previous_menu_function()
                else:
                    describe_room()
                return
            elif 0 <= idx < len(game_state["inventory"]):
                item = game_state["inventory"][idx]
                if item == "Envelope from the Commissioner":
                    delay_print(
                        f"""
I hope this finds you well, {game_state['name']}.
Bishop Alaric Greaves—a powerful, controversial cleric known for firebrand sermons and rumored secret rites—is missing from his chapel. No one saw him die, yet all the suspects were seen gathering at the mansion you now occupy. His final sermon spoke of a great awakening, and since then, strange phenomena have crept through the manor grounds and the city itself.

You, {game_state['name']}, are to be my cloaked investigator. Unravel the truth—was it murder, madness, or something... worse?

— Commissioner of Police of the Metropolis
                    """)
                    wait_for_space()
                elif item == "Elder Sign":
                    delay_print(
                        "Elder Sign: A strange, star-shaped talisman carved from ancient stone. "
                        "Its lines twist in impossible angles, and the air around it feels subtly warped. "
                        "Legends say it wards off the Old Ones and brings strength to the faithful."
                    )
                    wait_for_space()
                elif item == "Scrying Lens":
                    delay_print(
                        "Scrying Lens: A cloudy crystal lens set in tarnished silver. When held to the eye, it reveals the hidden movements of those who dwell within the manor."
                    )
                    wait_for_space()
                else:
                    delay_print(f"You inspect the {item} but it does not demonstrate any special properties for immediate use.")
                    wait_for_space()
                # FIX: Always return to previous menu or action menu after inspecting
                if previous_menu_function:
                    previous_menu_function()
                else:
                    describe_room()
                return
            else:
                show_inventory()
                return
        else:
            show_inventory()
            return
    else:
        delay_print(distort_text("Your inventory is empty.", game_state["sanity"]))
        wait_for_space()
        if previous_menu_function:
            previous_menu_function()
        else:
            describe_room()
        return

def use_item(context=None, return_func=None):
    # Detect if called from combat by checking the return_func (lambda: None is used in combat)
    from_combat = context is not None and hasattr(context, "suspect")

    suspect = None 
    is_monstrosity = False 
    if from_combat and hasattr(context, "suspect"):
        suspect = context.suspect
        is_monstrosity = suspect and suspect.get("transformed", False)

    # Only highlight the Webley if it's in inventory and not yet used in this combat
    webley_in_inventory = "Loaded Webley .45" in game_state["inventory"]
    amulet_in_inventory = "Abraxas Amulet" in game_state["inventory"]

    # Highlight logic: Only orange if appropriate target and first use in combat
    combat_highlight = set()
    if from_combat and webley_in_inventory and (is_monstrosity or suspect):
        combat_highlight.add("Loaded Webley .45")
    if from_combat and amulet_in_inventory and is_monstrosity:
        combat_highlight.add("Abraxas Amulet")

    usable = [item for item in game_state["inventory"] if item in [a["name"] for a in artifact_pool + potion_pool]]
    if not usable:
        delay_print("You have no usable items.")
        wait_for_space()
        if callable(return_func):
            return_func()
        else:
            show_inventory()
        return

    print("\nWhich item would you like to use?")
    for idx, name in enumerate(usable, 1):
        if name in combat_highlight:
            print(f"{ORANGE}[{idx}] {name}{RESET}")
        else:
            print(f"[{idx}] {name}")
    print(f"[{len(usable)+1}] Return")
    choice = input("> ").strip()
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(usable):
            item_name = usable[idx]
            artifact = next((a for a in artifact_pool if a["name"] == item_name), None)
            potion = next((p for p in potion_pool if p["name"] == item_name), None)
            if artifact:
                # Apply main effect
                if artifact["name"] == "Loaded Webley .45":
                    bullets = artifact.get("bullets", 6)
                    if from_combat and suspect:
                        if is_monstrosity:
                            if bullets > 0:
                                delay_print(f"{YELLOW}You fire the Webley .45 at the monstrosity!{RESET}")
                                delay_print(f"{ORANGE}The revolver roars! ({bullets-1} bullets remaining){RESET}")
                                artifact["bullets"] -= 1
                                suspect["stamina"] = 0  # Instantly kill the monstrosity
                                delay_print(f"{RED}The bullet strikes true! The monstrosity collapses, slain by mortal steel!{RESET}")
                            else:
                                delay_print(f"{RED}The Webley .45 is empty!{RESET}")
                        else:
                            if bullets > 0:
                                delay_print(f"{YELLOW}You fire the Webley .45 at your foe!{RESET}")
                                artifact["bullets"] -= 1
                                delay_print(f"{ORANGE}The revolver roars! ({artifact['bullets']} bullets remaining){RESET}")
                                suspect["stamina"] = max(0, suspect.get("stamina", 0) - 8)  # Deal 8 damage
                                delay_print(f"{RED}The bullet strikes {suspect['name']}! ({suspect['stamina']} stamina remaining){RESET}")
                                # --- Sync enemy_stamina for combat loop ---
                                if from_combat:
                                    # Find and update the local variable in the combat function
                                    # You must update enemy_stamina in skill_check_combat after use_item returns:
                                    game_state["sync_stamina"] = suspect["stamina"]
                            else:
                                delay_print(f"{RED}The Webley .45 is empty!{RESET}")
                    else:
                        delay_print(f"{RED}You brandish the Webley .45, but there is no foe to fire upon.{RESET}")
                    wait_for_space()
                    # Using an item spends a melee round
                    game_state["combat_rounds_used"] = game_state.get("combat_rounds_used", 0) + 1
                    if callable(return_func):
                        return_func()
                    else:
                        show_inventory()
                    return
                if artifact["name"] == "Abraxas Amulet":
                    if from_combat and suspect:
                        if is_monstrosity:
                            delay_print(f"{ORANGE}You clutch the Abraxas Amulet. A protective aura surrounds you, warding off the monstrosity!{RESET}")
                        else:
                            delay_print(f"{YELLOW}You clutch the Abraxas Amulet, but nothing happens. Its power only wards off supernatural horrors, not ordinary humans.{RESET}")
                    else:
                        delay_print(f"{YELLOW}You clutch the Abraxas Amulet, but nothing happens.{RESET}")
                    wait_for_space()
                    # Using an item spends a melee round
                    game_state["combat_rounds_used"] = game_state.get("combat_rounds_used", 0) + 1
                    if callable(return_func):
                        return_func()
                    else:
                        show_inventory()
                    return
                # Normal artifact logic
                if artifact.get("effect") in game_state:
                    amt = artifact["amount"]
                    if isinstance(amt, str) and amt.startswith("+"):
                        amt = int(amt)
                    game_state[artifact["effect"]] = min(18, game_state[artifact["effect"]] + int(amt))
                    delay_print(f"You use the {artifact['name']}. {artifact['desc']} (+{amt} {artifact['effect'].capitalize()})")
                # Apply side effect if any
                if "side_effects" in artifact:
                    side_effects = artifact["side_effects"]
                    if isinstance(side_effects, tuple) and len(side_effects) == 2 and isinstance(side_effects[0], str):
                        side_effects = [side_effects]
                    for stat, amt in side_effects:
                        game_state[stat] = max(0, min(18, game_state[stat] + amt))
                        delay_print(f"Side effect: {stat.capitalize()} {'+' if amt > 0 else ''}{amt}")
                # Remove after use (permanent effect)
                game_state["inventory"].remove(item_name)
                wait_for_space()
                if callable(return_func):
                    return_func()
                else:
                    show_inventory()
                return

            elif potion:
                game_state[potion["effect"]] = min(18, game_state[potion["effect"]] + potion["amount"])
                delay_print(f"You drink the {potion['name']}. {potion['desc']} (+{potion['amount']} {potion['effect'].capitalize()})")
                game_state["inventory"].remove(potion["name"])
                wait_for_space()
                if callable(return_func):
                    return_func()
                else:
                    show_inventory()
                return
        elif idx == len(usable):  # Return option
            if callable(return_func):
                return_func()
            else:
                show_inventory()
            return
        else:
            show_inventory()
            return
                
def skill_check_combat(enemy_name, enemy_difficulty=None, stat=None):
    import time
    import msvcrt
    clear()
    suspect = next((s for s in game_state["suspects"] if s["name"] == enemy_name), None)
    delay_print(f"You face off against {enemy_name}. The air crackles with tension.")
    wait_for_space()

    player_stamina = game_state["stamina"]
    player_strength = game_state["strength"]
    player_agility = game_state["agility"]

    if suspect:
        enemy_stamina = suspect.get("stamina", 10)
        enemy_strength = suspect.get("strength", 8)
        enemy_agility = suspect.get("agility", 8)
        enemy_name = suspect["name"]
        transformed = suspect.get("transformed", False)
    else:
        enemy_stamina = enemy_difficulty if enemy_difficulty is not None else 10
        enemy_strength = 8
        enemy_agility = 8
        transformed = False

    round_num = 1
    sanity_lost = 0

    while player_stamina > 0 and enemy_stamina > 0:
        time.sleep(2.7)
        clear()
        delay_print(f"--- Melee Round {round_num} ---", speed=0)
        delay_print(f"Your Stamina: {player_stamina} | {enemy_name}'s Stamina: {enemy_stamina}", speed=0)
        if transformed:
            delay_print(f"Your Sanity: {game_state['sanity']}", speed=0)
        if game_state["sanity"] < 4:
            delay_print(RED + "WARNING: Your sanity is dangerously low!" + RESET, speed=0)
        if player_agility < 4:
            delay_print(RED + "WARNING: Your agility is dangerously low!" + RESET, speed=0)
        if player_strength < 4:
            delay_print(RED + "WARNING: Your strength is dangerously low!" + RESET, speed=0)
        if player_stamina < 4:
            delay_print(RED + "WARNING: Your stamina is dangerously low!" + RESET, speed=0)

        print("[A] Attack  [U] Use item  [F] Flee  [S] Show stats (press key to interrupt, or wait for auto-advance)")

        # Default action is attack if no key pressed
        action = "a"
        start_time = time.time()
        while time.time() - start_time < 1:
            if msvcrt.kbhit():
                key = msvcrt.getch().decode('utf-8').lower()
                if key in ['a', 'u', 'f', 's']:
                    action = key
                    break
            time.sleep(0.05)

        if action == "u":
            class CombatContext:
                def __init__(self, suspect):
                    self.suspect = suspect

            def combat_return():
                pass  # Placeholder to return to the combat loop

            use_item(CombatContext(suspect), combat_return)
            player_stamina = game_state["stamina"]
            player_strength = game_state["strength"]
            player_agility = game_state["agility"]
            if "sync_stamina" in game_state:
                enemy_stamina = game_state.pop("sync_stamina")
            round_num += 1
            continue
        elif action == "s":
            show_stats(from_combat=True)
            continue
        elif action == "f":
            if transformed:
                print(f"{ORANGE}[F] Flee for your life!{RESET} or press Enter to stand your ground.")
                flee_choice = input("> ").strip().lower()
                if flee_choice == "f":
                    escaped = timing_bullseye_chase()
                    if escaped:
                        delay_print("You manage to escape the horror and slam the door behind you!")
                        game_state["stamina"] = player_stamina
                        describe_room()
                        return
                    else:
                        delay_print("The horror catches you! You are forced to fight for your life!")
            else:
                player_agility_score = game_state["agility"] + roll_fudge()
                enemy_agility_score = enemy_agility + roll_fudge()
                delay_print(f"Your escape roll: {game_state['agility']} + die roll = {YELLOW}{player_agility_score}{RESET}")
                delay_print(f"{enemy_name}'s pursuit roll: {enemy_agility} + die roll = {YELLOW}{enemy_agility_score}{RESET}")
                if player_agility_score >= enemy_agility_score:
                    delay_print(f"{YELLOW}You slip away before your opponent can react!{RESET}")
                    game_state["stamina"] = player_stamina
                    wait_for_space()
                    describe_room()
                    return
                else:
                    delay_print(RED + "You try to flee, but your opponent catches you with a parting blow! (Stamina -2, Score -10)" + RESET)
                    game_state["stamina"] = max(0, game_state["stamina"] - 2)
                    game_state["score"] -= 10
                    wait_for_space()
                    describe_room()
                    return

        # Combat logic (attack)
        player_base = (player_strength + player_stamina + player_agility) // 3
        combat_bonus = game_state.pop("combat_bonus", 0)
        player_roll = player_base + roll_fudge() + (player_agility - enemy_agility) // 2 + combat_bonus

        enemy_base = (enemy_strength + enemy_stamina + enemy_agility) // 3
        enemy_roll = enemy_base + roll_fudge() + (enemy_agility - player_agility) // 2

        delay_print(f"Your combat score: {player_base} + die roll + agility mod = {YELLOW}{player_roll}{RESET}", speed=0)
        delay_print(f"Enemy combat score: {enemy_base} + die roll + agility mod = {YELLOW}{enemy_roll}{RESET}", speed=0)

        if player_roll >= enemy_roll:
            player_damage = max(1, 1 + (player_strength - enemy_strength) // 4)
            delay_print(YELLOW + f"You strike {enemy_name} for {player_damage} damage!" + RESET)
            enemy_stamina -= player_damage
        else:
            damage = max(1, 1 + (enemy_strength - player_strength) // 4)
            if transformed and "Abraxas Amulet" in game_state["inventory"]:
                delay_print(f"{ORANGE}The Abraxas Amulet glows! The monstrosity cannot harm you while you possess it.{RESET}", speed=0)
                damage = 0
            elif transformed and game_state["faith"] >= 14:
                delay_print(f"{ORANGE}Your faith shields you from the worst of the supernatural assault! (Damage halved){RESET}", speed=0)
                damage = max(1, damage // 2)
            elder_god_twist = False
            if suspect and random.random() < 0.15 and sanity_lost == 0:
                elder_god_twist = True
            if elder_god_twist:
                if not transformed:
                    delay_print(RED + "The suspect's body contorts and transforms into a monstrous horror! A hideous, wet cracking echoes through the room as the suspect's flesh ripples and splits. Limbs elongate, bones twist, and eyes bloom like fungus across their writhing form. What once was human is now a blasphemous shape, a thing of nightmare and cosmic dread, shrieking in a chorus of voices not meant for mortal ears." + RESET)
                    enemy_strength += 2
                    if suspect:
                        suspect["strength"] = enemy_strength
                        suspect["transformed"] = True
                        suspect["position"] = game_state["position"]
                    transformed = True
                    if "Abraxas Amulet" in game_state["inventory"]:
                        delay_print(f"{ORANGE}The Abraxas Amulet glows with a fierce light! The horror recoils and cannot approach you while you wear it.{RESET}")
                        delay_print(f"{ORANGE}You are protected from the monstrosity's attacks as long as you possess the Amulet.{RESET}")
                        round_num += 1
                        continue
                    print(f"{ORANGE}[F] Flee for your life!{RESET} or press Enter to stand your ground.")
                    flee_choice = input("> ").strip().lower()
                    if flee_choice == "f":
                        escaped = timing_bullseye_chase()
                        if escaped:
                            describe_room()
                            return
                        else:
                            delay_print("The horror catches you! You are forced to fight for your life!")
                delay_print(f"Your Sanity: {game_state['sanity']}")
                delay_print(ORANGE + random.choice([
                    f"The monstrosity tries to rend the flesh from your bones!",
                    f"With a guttural roar, the creature's claws slash at your throat, spraying blood across the walls.",
                    f"The abomination lunges, jaws distending to snap at your face.",
                    f"Tentacles burst from its torso, writhing and seeking to strangle you.",
                    f"Your skin burns as acidic saliva drips from its fangs.",
                    f"It hammers you with inhuman strength, bones creaking under the impact.",
                    f"Eyes blink open across its body, all fixed hungrily on you.",
                    f"The thing's claws rake deep gouges into your side, hot blood pouring down.",
                    f"It shrieks, a sound that makes your vision blur and your heart pound with terror.",
                    f"With a sickening crunch, it bites into your shoulder, tearing flesh and muscle.",
                    f"Black ichor sprays as the beast's claws rip through your defenses.",
                    f"The horror's jaws snap shut inches from your face, spattering you with foul saliva.",
                    f"Your vision swims as the creature's tentacles squeeze the breath from your lungs.",
                    f"Bone and sinew snap as the abomination slams you against the wall.",
                    f"A dozen eyes blink open across its chest, all staring hungrily at you."
                ]) + RESET)
                delay_print(f"You lose {damage} stamina.")
                delay_print("\n" + random.choice([
                    f"As {enemy_name} strikes you, their flesh ripples and splits, revealing writhing tentacles and lidless, unblinking eyes.",
                    f"{enemy_name}'s mouth distends impossibly wide, emitting a chorus of whispers in a language not meant for human ears.",
                    f"Your attacker’s skin sloughs away, replaced by a mass of chitinous plates and twitching, alien appendages.",
                    f"With a sickening crack, {enemy_name}'s limbs elongate and bend backwards, their face melting into a mass of wriggling feelers.",
                    f"The corpse of {enemy_name} convulses, sprouting glistening, phosphorescent tendrils that thrash blindly at the air."
                ]))
                delay_print("You reel in terror as the truth is revealed: this was no mere mortal, but a servant of some higher unspeakable evil from some other upside down plane of existence!")
                game_state["sanity"] = max(0, game_state["sanity"] - 1)
                sanity_lost = 2
            else:
                if transformed:
                    delay_print(ORANGE + random.choice([
                        f"The monstrosity tries to rend the flesh from your bones!",
                        f"With a guttural roar, the creature's claws slash at your throat, spraying blood across the walls.",
                        f"The abomination lunges, jaws distending to snap at your face.",
                        f"Tentacles burst from its torso, writhing and seeking to strangle you.",
                        f"Your skin burns as acidic saliva drips from its fangs.",
                        f"It hammers you with inhuman strength, bones creaking under the impact.",
                        f"Eyes blink open across its body, all fixed hungrily on you.",
                        f"The thing's claws rake deep gouges into your side, hot blood pouring down.",
                        f"It shrieks, a sound that makes your vision blur and your heart pound with terror.",
                        f"With a sickening crunch, it bites into your shoulder, tearing flesh and muscle.",
                        f"Black ichor sprays as the beast's claws rip through your defenses.",
                        f"The horror's jaws snap shut inches from your face, spattering you with foul saliva.",
                        f"Your vision swims as the creature's tentacles squeeze the breath from your lungs.",
                        f"Bone and sinew snap as the abomination slams you against the wall.",
                        f"A dozen eyes blink open across its chest, all staring hungrily at you."
                    ]) + RESET)
                    delay_print(f"You lose {damage} stamina.")
                    delay_print("\n" + random.choice([
                        f"As {enemy_name} strikes you, their flesh ripples and splits, revealing writhing tentacles and lidless, unblinking eyes.",
                        f"{enemy_name}'s mouth distends impossibly wide, emitting a chorus of whispers in a language not meant for human ears.",
                        f"Your attacker’s skin sloughs away, replaced by a mass of chitinous plates and twitching, alien appendages.",
                        f"With a sickening crack, {enemy_name}'s limbs elongate and bend backwards, their face melting into a mass of wriggling feelers.",
                        f"The corpse of {enemy_name} convulses, sprouting glistening, phosphorescent tendrils that thrash blindly at the air."
                    ]))
                else:
                    delay_print(ORANGE + random.choice([
                        f"{enemy_name} lands a heavy blow to your ribs.",
                        f"{enemy_name} slams a fist into your shoulder.",
                        f"{enemy_name} catches you off guard with a quick punch.",
                        f"{enemy_name} drives you back with a sudden shove.",
                        f"{enemy_name} lands a glancing blow to your cheek.",
                        f"{enemy_name} strikes you with surprising force.",
                        f"{enemy_name}'s fingernails rip into your throat, leaving burning scratches.",
                        f"{enemy_name} grabs your hair and slams your head against the wall."
                    ]) + RESET)
                    delay_print(f"You lose {damage} stamina.")
                player_stamina -= damage

        delay_print(f"Your Stamina: {player_stamina} | {enemy_name}'s Stamina: {enemy_stamina}", speed=0)
        round_num += 1

    game_state["stamina"] = player_stamina
    if suspect:
        suspect["stamina"] = enemy_stamina

    # Prevent defeating monstrosity by melee
    if suspect and transformed and player_stamina > 0 and enemy_stamina <= 0:
        used_webley = game_state.get("combat_bonus", 0) >= 10
        used_amulet = "Abraxas Amulet" in game_state["inventory"]
        if not used_webley and not used_amulet:
            delay_print(f"{RED}Your attacks seem to do nothing! The monstrosity shrugs off mortal wounds and rises again, unkillable by ordinary force!{RESET}")
            suspect["stamina"] = max(1, suspect.get("stamina", 10))
            enemy_stamina = suspect["stamina"]
            round_num += 1
            wait_for_space()
            return
        else:
            suspect["stamina"] = 0
            if suspect in game_state["suspects"]:
                game_state["suspects"].remove(suspect)
                wait_for_space()

    if player_stamina > 0:
        if suspect and transformed:
            delay_print(f"{RED}The monstrous remains of {enemy_name} collapse, oozing ichor and twitching as the unnatural life leaves them. The horror is over—for now.{RESET}")
            print("P̴̧̧͔̦̲͙͉̘̰̜͎̤̻̹̤͋̀̈́̄́̂͐͂̈́̓͐͒͜͝h̴̡̡̡̲͓̜̬͎̖̟̞̦͙̑̀͊̎̌̐̆̽̆̈́̆͌̕ͅ'̶̜̟͛̉̎̅̿̊n̴͇̟͋g̴̥̦̟̘̝̱͉̲̤͙͇͋̄̐̏͊̔͌́͛̇l̶̡͙̻̗̩̬̣̰͚̯̲̉̃̒́͛͆͋̀͛͆̃͜͝ụ̷̧̧͎̯̜͕̻̘̬̙̱͈͛͐ͅi̴̖͓̥͔͕͍̮͇̼͚̗̭̻͌̈́̈́̈́͊̿̀͆͋̀͌̍̀̍͜͠͠͝ ̵̢̩̟̫̣̪̬͍̳̞̰͕̝͚̣͗͛̈́͘̚m̷̛͔̱̎̐̊̀͐̑͆̑̈́͛͘͝g̸̡̨͛͒̈͆͝l̸̡̨͕̣͎̙͕̥͛̎͆̊͛̋̍̿͐̅̄̋̔̈́̓̕͝w̵̧̖̟̠̼̠̼̗̜̱͈̮̩͆'̴͕̟̹͙̝̼͖̟̈̃̈́̉͛̀͛̂͘͝n̸̲̜̭̪̩̅͌̀̏͛̅̎̋͑͐̏̈́̽̌͝͝a̵̡̫͙̻͓͉͈͈͉̙͑͗͗͝f̵̨̖̯̳̮̳̼̺̠̰̘̘̙̗͍͖͆͑̀͂͋̈̑̈͜͝h̸͏̡̛͈̱͇͉̯̹̘͋̄̾̽͋́͂͛̊̕͝ ̸̧̣̫̳̥̥̲̖̻̭̾̅̎́̀̓̉́̇̕͝͝ͅͅw̴̨͖̼͕͉͍̺͐́̈̈́ģ̴̛̫͎̼̥͕̦̮͈̩̺̈́̃̇a̶̛̱͔̩̦͙͇̖͚̲̙͖͚͎͈̓͑̀͒ḩ̶̨̝̺͚͎̺̙͕̞̂͐̂́̈́̍͛͝ͅ'̵͚̝̝̩̗̭̦̇̐̈́̃̊̌̔́̌͝͝͝ͅņ̴̗͕̬̞̻̼̜̥͈̣̬͇̦̻͖̏́̓͒̈́͐́͠ͅa̸̹̟̯͈̣͖͙͝g̴̨̼̤̜̥̼̰͈̞̪̙̭̅̃͛̆l̸͚̗͉̖̰̿̊͐͌̈́̃ͅ ̷̟͇͕̘̰̤͖̰̜̝̰̗̼̟̱͖̂̈̈́̔̌̊̕͜f̸̧̲̬̤͍̙̰͎̲͖̭̜̖̫̅̒́̃͜h̴̛̩̫͕̣̻͛́́̏̈́̐ẗ̵̨̛̛̻̻͉̗̲̙̠̦̜̔̾͒̑͂̈́͑̏̈͊̊͋ͅa̷̢̰͍̞̭̗̜̣̒̔͑ǧ̴̨̱̘̣͕͙̘̺͍̦̒͌́̓̎͋n̴͍͔͔͙̰͐͜!")
            game_state["score"] -= 15
            delay_print("You have taken a life in self-defense. The weight of this act will haunt you. (-15 Score)")
            wait_for_space()
            suspect["stamina"] = 0
            if suspect in game_state["suspects"]:
                game_state["suspects"].remove(suspect)
        else:
            delay_print(f"You overcome the threat posed by {enemy_name}! You live to investigate another day.")
            game_state["journal"].append(f"Survived combat against {enemy_name}.")
            if suspect:
                suspect["stamina"] = 0
                if suspect in game_state["suspects"]:
                    game_state["suspects"].remove(suspect)
    else:
        delay_print(f"The encounter with {enemy_name} overwhelms you...")
        game_state["journal"].append(f"Defeated by {enemy_name}. Survived, but barely.")

    if suspect and suspect.get("is_murderer") and player_stamina > 0:
        game_state["score"] -= 25
        delay_print(f"As {suspect['name']} falls, the truth is revealed: {suspect['name']} was the murderer all along!")
        delay_print("But justice through violence is not justice at all. The Commissioner is furious at your methods.")
        delay_print("You have failed to solve the mystery through deduction. The case is closed in disgrace.")
        print(RED + r"""
 __     __           _                    
 \ \   / /          | |                   
  \ \_/ /__  _   _  | |     ___  ___  ___ 
   \   / _ \ '__/ __| | | |/ _` / __|/ _ \
    | | (_) | |_| | | |___| (_) \__ \  __/
    |_|\___/ \__,_| |______\___/|___/\___|
    """ + RESET)
        delay_print("Sorry!")
        wait_for_space()
        show_score()
        wait_for_space()
        title_screen()
        return

    if player_stamina <= 0:
        delay_print("You have succumbed to your death. The investigation ends here. Better luck next time")
        game_state["score"] -= 35
        show_score()
        print(RED + "You are overwhelmed! Your vision fades as your strength fails..." + RESET)
        print(RED + r"""
     __     __           _____  _          _ 
     \ \   / /          |  __ \(_)        | |
      \ \_/ /__  _   _  | |  | |_  ___  __| |
       \   / _ \| | | | | |  | | |/ _ \/ _` |
        | | (_) | |_| | | |__| | |  __/ (_| |
        |_|\___/ \__,_| |_____/|_|\___|\__,_|
        """ + RESET)
        wait_for_space()
        title_screen()
    else:
        wait_for_space()

def handle_input(user_input, return_function):
    global previous_menu_function

     # --- DEBUG: Instantly add all clues (SHERLOCK cheat) ---
    if user_input.strip().lower() == "sherlock":
        all_clues = []
        for pool in clue_pools:
            all_clues.extend(pool)
        added = 0
        for clue in all_clues:
            if clue not in game_state["clues"]:
                game_state["clues"].append(clue)
                game_state["journal"].append(f"CLUE FOUND (SHERLOCK): {clue}")
                added += 1
        print(f"{YELLOW}SHERLOCK MODE: Added {added} clues to your case!{RESET}")
        wait_for_space()
        if callable(return_function):
            return_function()
        return
    
    if user_input in valid_moves:
        move_to_new_room(user_input)
        return  # Prevent falling through to other cases
    elif user_input == "santa":
        debug_add_artifact()
        return_function()
        return
    elif user_input == "score":
        show_score()
        wait_for_space()
        return_function()
    elif user_input == "help":
        show_help()
    elif user_input == "look" or user_input == "l":
        look_around()
        return_function()
    elif user_input == "save":
        save_game()
        return_function()
    elif user_input == "load":
        load_game()
    elif user_input == "quit" or user_input == "qq" or user_input == "exit":
        exit()
    elif user_input == "back" or user_input == "menu":
        if previous_menu_function:
            previous_menu_function()
        else:
            title_screen()
    elif user_input == "title":
        title_screen()
    elif user_input == "inventory" or user_input == "i":
        show_inventory()
    elif user_input == "journal" or user_input == "j":
        show_journal()
    elif user_input == "quests" or user_input == "mystery":
        show_quests()
    elif user_input == "map" or user_input == "m":
        show_map()
    elif user_input == "stats":
        show_stats()
    elif user_input == "flow":    
        show_map_flow()
    elif user_input == "fight":
        suspects = [s for s in game_state["suspects"] if s.get("stamina", 0) > 0]
        if not suspects:
            delay_print("There are no suspects available for a brawl.")
            return_function()
            return
        print("\nChoose a suspect to brawl with:")
        for i, s in enumerate(suspects, 1):
            print(f"[{i}] {s['name']}")
        choice = input("> ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(suspects):
                skill_check_combat(suspects[idx]["name"])
                if previous_menu_function:
                    previous_menu_function()
                else:
                    describe_room()
                return
        delay_print("Invalid choice.")
        if previous_menu_function:
            previous_menu_function()
        else:
            describe_room()
        return
    else:
        
        delay_print("Unknown command. Type 'help' for available options.")
        print("Available commands: help, look, save, load, quit, back, menu, title, inventory, journal, quests, stats, map, flow, score, fight, n/s/e/w/ne/nw/se/sw")
        # Just return to the previous menu or show help, but do NOT call handle_input recursively with 'choice'
    if callable(return_function):
        return_function()
  
def show_help():
    print("Available commands:")
    print("- help: Show this help message")
    print("- look [l]: Look around the current location")
    print("- save: Save your game")
    print("- load: Load a previous save")
    print("- quit: Quit the game")
    print("- back/menu: Return to the previous menu")
    print("- title: Return to the title screen")
    print("- inventory [i]: Show your inventory")
    print("- journal [j]: Show your journal entries")
    print("- quests/mystery: Show active mysteries")
    print("- stats: Show character stats")
    print("- map [m]: Show the current map")
    print("- flow: Show a simplified map flow of key rooms")
    print("- score: Show your current score and scoring breakdown")
    print("- fight: Start a combat encounter with any suspect (debug)")
    print("- n/s/e/w/ne/nw/se/sw: Move in that direction from any screen")
    wait_for_space("Press SPACE to continue.")

    if previous_menu_function:
        previous_menu_function()
    else:
        title_screen()

def look_around(pause=True, instant=False):
    room = game_state["location"]
    descriptions = room_templates.get(room, ["You see nothing remarkable, an empty corridor or room."])
    first_sentence = descriptions[0].split(".")[0] + "."
    delay_print(first_sentence, speed=0 if instant else 0.01)
    if pause:
        wait_for_space()

def title_screen():
    global previous_menu_function
    previous_menu_function = title_screen
    clear()
    print(YELLOW +r"""
  _____                              _             
 |  __ \                            (_)            
 | |__) |__ _ __ ___ _   _  __ _ ___ _  ___  _ __  
 |  ___/ _ \ '__/ __| | | |/ _` / __| |/ _ \| '_ \ 
 | |  |  __/ |  \__ \ |_| | (_| \__ \ | (_) | | | |
 |_|   \___|_|  |___/\__,_|\__,_|___/_|\___/|_| |_|
                                                  
    
    """ + RESET)
    delay_print("A Victorian Roguelike Mystery!")

    print("[1] Begin New Investigation")
    print("[2] On the Art of Persuasion")
    print("[3] Instructions")
    print("[4] The Setting")
    print("[5] The Mystery")
    print("[6] Load Game")
    print("[7] Quit")

    user_input = input("\n> ").strip().lower()

    if user_input == "1":
        dream_flashback()
    elif user_input == "2":
        show_persuasion_lore()
        title_screen()
    elif user_input == "3":
        instructions()
    elif user_input == "4":
        show_setting()
        title_screen()
    elif user_input == "5":
        show_mystery()
        title_screen()
    elif user_input == "6":
        load_game()
    elif user_input == "7" or user_input == "quit" or user_input == "q" or user_input == "exit":
        delay_print("Thank you for playing! Goodbye.")
        exit()
    else:
        handle_input(user_input, title_screen)

def instructions():
    global previous_menu_function
    previous_menu_function = instructions
    clear()
    delay_print("Navigate using number keys. Choices shape sanity, stats, and storyline.")
    delay_print("You play an investigator in a dark Victorian world of cults and mysteries.")
    delay_print("Global commands can be entered anytime (help, save, load, quit, back, menu, title).")
    delay_print("Optional commands include: journal, map, stats, quests, inventory.")
    wait_for_space()
    title_screen()

def distort_text(text, sanity):
    import random

    def jumble_word(word):
        if len(word) <= 3:
            return word
        mid = list(word[1:-1])
        random.shuffle(mid)
        return word[0] + ''.join(mid) + word[-1]

    def zalgo(text):
        zalgo_marks = [chr(i) for i in range(0x300, 0x36F)]
        out = ""
        for c in text:
            out += c
            if c.isalpha() and random.random() < 0.7:
                out += ''.join(random.choice(zalgo_marks) for _ in range(random.randint(1, 3)))
        return out

    if sanity >= 6:
        return text  # Clear
    elif sanity >= 5:
        # Mild distortion: jumble some words
        words = text.split()
        for i in range(len(words)):
            if random.random() < 0.3:
                words[i] = jumble_word(words[i])
        return ' '.join(words)
    elif sanity >= 4:
        # Severe distortion: reverse words and jumble
        words = text.split()
        words = [jumble_word(w) for w in words[::-1]]
        return ' '.join(words)
    else:
        # Zalgo/unicode glitch
        return zalgo(text)

def lock_all_doors():
    game_state["locked_doors"] = set()
    for pos, exits in game_state["passages"].items():
        for dir_name in exits:
            dx, dy = moves[dir_name]
            neighbor = (pos[0] + dx, pos[1] + dy)
            # Lock both moves
            game_state["locked_doors"].add((pos, neighbor))
            game_state["locked_doors"].add((neighbor, pos))

def place_silver_key():
    possible_rooms = [r for r in room_templates.keys() if r != "Foyer"]
    key_room = random.choice(possible_rooms)
    game_state.setdefault("artifact_locations", {})[key_room] = next(a for a in artifact_pool if a["name"] == "Silver Ornate Key")

def add_random_clue():
    room = game_state["location"]
    found_something = False
    pos = game_state["position"]
    if "searched_rooms" not in game_state:
        game_state["searched_rooms"] = set()
    game_state["searched_rooms"].add(pos)

    # Clue logic (as before)
    clue = clue_locations.get(room)
    if clue and clue not in game_state["clues"]:
        if random.random() < 0.98: 
            game_state["clues"].append(clue)
            delay_print(f"Clue discovered: {clue}")
            game_state["journal"].append(f"CLUE FOUND at {game_state['location']}: {clue}")
            game_state["score"] += 10  # Add to score for finding a clue
            game_state["score_log"].append(f"Clue: {clue} [+10]")
            # print(f"[DEBUG] Score after finding clue: {game_state['score']}")
            found_something = True

    # Scrying Lens logic
    if (
        "scrying_lens_room" in game_state
        and room == game_state["scrying_lens_room"]
        and "Scrying Lens" not in game_state["inventory"]
    ):
        game_state["inventory"].append("Scrying Lens")
        game_state["can_see_npcs"] = True
        delay_print(
            "You discover a cloudy crystal lens set in tarnished silver: the Scrying Lens.\n"
            "When you peer through it, the locations of others in the manor shimmer into view on your map."
        )
        found_something = True

    # Potion logic
    potion = potion_locations.get(room)
    if potion and potion["name"] not in game_state["inventory"]:
        if random.random() < 0.8:
            game_state["inventory"].append(potion["name"])
            delay_print(f"You found a {potion['name']}! {potion['desc']}")
            # Remove this potion from all other rooms so it can't be found again
            for r in list(potion_locations.keys()):
                if potion_locations[r]["name"] == potion["name"] and r != room:
                    del potion_locations[r]
            found_something = True

    # Artifact logic

    # After adding an artifact to inventory in add_random_clue()

    artifact = game_state.get("artifact_locations", {}).get(room)
    if artifact and artifact["name"] not in game_state["inventory"]:
        game_state["inventory"].append(artifact["name"])
        delay_print(f"You found {artifact['name']}! {artifact['desc']}")
        game_state["score"] += 20  # Add to score for finding an artifact
        # print(f"[DEBUG] Score after finding artifact: {game_state['score']}")
        game_state["journal"].append(f"ARTIFACT FOUND at {game_state['location']}: {artifact['name']}")
        game_state["score_log"].append(f"Artifact: {artifact['name']} [+20]") 
        # Remove this artifact from all other rooms so it can't be found again
        for r in list(game_state["artifact_locations"].keys()):
            if game_state["artifact_locations"][r]["name"] == artifact["name"] and r != room:
                del game_state["artifact_locations"][r]
        found_something = True

        # --- Place achievement unlock logic here ---
        # Check if all artifacts have been found
        if all(a["name"] in game_state["inventory"] for a in artifact_pool):
            if "Found all artifacts" not in game_state["achievements"]:
                game_state["achievements"].add("Found all artifacts")
                game_state["score"] += ACHIEVEMENT_SCORE
                print(f"{CYAN}Achievement unlocked: {ACHIEVEMENTS['Found all artifacts']} (+{ACHIEVEMENT_SCORE} points){RESET}")

        # --- Add Eibon quest if first fragment is found ---
        if artifact["name"] in {
            "First Fragment of the Eibon Manuscript",
            "Second Fragment of the Eibon Manuscript",
            "Third Fragment of the Eibon Manuscript"
        }:
            quest_text = "Assemble the Book of Eibon by finding all three manuscript fragments."
            if quest_text not in game_state["quests"]:
                game_state["quests"].append(quest_text)
                delay_print(f"{YELLOW}Quest added: {quest_text}{RESET}")
         
    # Elder Sign logic
    if (
        "elder_sign_room" in game_state
        and room == game_state["elder_sign_room"]
        and "Elder Sign" not in game_state["inventory"]
    ):
        game_state["inventory"].append("Elder Sign")
        game_state["faith"] = min(18, game_state["faith"] + 3)
        delay_print(
            "You discover a strange, star-shaped talisman: the Elder Sign.\n"
            "Its lines twist in impossible angles, and the air around it feels subtly warped.\n"
            "You feel a surge of holy power (+3 Faith)."
        )
        found_something = True

    if not found_something:
        delay_print("You search carefully, but find nothing new.")
    # input("Press Enter to continue.")
    # room = game_state["location"]
    # found_something = False

def show_epilogue_awaken_in_manor():
    delay_print("You stare blindly at the walls of the manor, forever questioning what you have seen tonight.")
    print(YELLOW + r"""
      _______ _            ______           _ 
     |__   __| |          |  ____|         | |
        | |  | |__   ___  | |__   _ __   __| |
        | |  | '_ \ / _ \ |  __| | '_ \ / _` |
        | |  | | | |  __/ | |____| | | | (_| |
        |_|  |_| |_|\___| |______|_| |_|\__,_|
        """ + RESET)
    wait_for_space()

def show_accusation_breakdown(accused, correct_culprit, clue_motives, player_clues):
    print("\n--- Accusation Breakdown ---")
    if accused["name"] == correct_culprit["name"]:
        print(f"{YELLOW}The following evidence proves {accused['name']} is the culprit:{RESET}")
    else:
        print(f"{RED}Here's why {accused['name']} is NOT the culprit:{RESET}")

    # Motive
    accused_motive = accused.get("motive", "Unknown")
    culprit_motive = correct_culprit.get("motive", "Unknown")
    motive_long = ""
    for pool in motive_pools:
        for m in pool:
            if m["short"] == accused_motive:
                motive_long = m.get("long", "")
                break
    if accused_motive == culprit_motive:
        print(f"- Motive: {YELLOW}{accused_motive}{RESET} {GREY}{motive_long}{RESET}")
    else:
        print(f"- Motive: {RED}{accused_motive}{RESET} (real culprit's motive: {YELLOW}{culprit_motive}{RESET}) {GREY}{motive_long}{RESET}")
        print(f"    {GREY}(This motive does not fit the true crime.){RESET}")

    # Means
    accused_means = accused.get("means", "Unknown")
    culprit_means = correct_culprit.get("means", "Unknown")
    means_flavor = means_flavor_explanations.get(accused_means, {}).get(accused_motive)
    if accused_means == culprit_means:
        if means_flavor:
            print(f"- Means: {YELLOW}{accused_means}{RESET} {GREY}{means_flavor}{RESET}")
        else:
            print(f"- Means: {YELLOW}{accused_means}{RESET} (suspect had the necessary means to commit the crime)")
    else:
        print(f"- Means: {RED}{accused_means}{RESET} (real culprit's means: {YELLOW}{culprit_means}{RESET})")
        print(f"    {GREY}(Means do not match the real culprit's method.){RESET}")

    # Alibi
    accused_alibi = accused.get("alibi", {})
    culprit_alibi = correct_culprit.get("alibi", {})
    accused_alibi_text = accused_alibi.get("text") if isinstance(accused_alibi, dict) else str(accused_alibi)
    culprit_alibi_text = culprit_alibi.get("text") if isinstance(culprit_alibi, dict) else str(culprit_alibi)
    alibi_flavor = alibi_flavor_explanations.get(accused_alibi_text, {}).get(accused_motive)
    if accused_alibi_text == culprit_alibi_text:
        if alibi_flavor:
            print(f"- Alibi: {YELLOW}{accused_alibi_text}{RESET} {GREY}{alibi_flavor}{RESET}")
        else:
            print(f"- Alibi: {YELLOW}{accused_alibi_text}{RESET}")
    else:
        print(f"- Alibi: {RED}{accused_alibi_text}{RESET} (real culprit's alibi: {YELLOW}{culprit_alibi_text}{RESET})")
        print(f"    {GREY}(Alibi does not match the real culprit's opportunity.){RESET}")

    # Clues
    matching_clues = []
    for clue in player_clues:
        clue_motive = clue_motives.get(clue)
        if clue_motive == accused_motive:
            matching_clues.append(clue)
    if matching_clues:
        print(f"- Clues linking to {accused['name']}:")
        for clue in matching_clues:
            flavor = clue_flavor_explanations.get(clue, {}).get(accused_motive)
            if flavor:
                print(f"    {YELLOW}{clue}{RESET} {GREY}— {flavor}{RESET}")
            else:
                print(f"    {YELLOW}{clue}{RESET}")
        if accused_motive != culprit_motive:
            print(f"    {GREY}(However, these clues do not point to the true motive or means.){RESET}")
    else:
        print(f"- No clues directly link {accused['name']} to the crime.")

    # If the accusation was false, end the game with "The End" epilogue
    if accused["name"] != correct_culprit["name"]:
        print(f"\n{RED}Your accusation has failed. The true culprit remains at large...{RESET}")
        show_epilogue_awaken_in_manor()
        delay_print("You have failed to solve the case. The shadows of the manor seem to deepen. The investigation ends here.")
        show_score()
        wait_for_space()
        title_screen()

def final_boss_sequence():
    clear()
    delay_print(f"{RED}The portal yawns wide, swirling with impossible colors and the sound of distant, maddening flutes.{RESET}")
    delay_print("Do you dare to step through and confront the source of all this horror?")
    print(f"{ORANGE}Enter the portal to the Elder Ones' realm? (Y/N){RESET}")
    choice = input("> ").strip().lower()
    if choice != "y":
        show_epilogue_awaken_in_manor()
        delay_print("You step back from the brink. The portal closes, leaving you trembling but alive.")
        delay_print(f"Final Score: {game_state['score']}")
        # save_game()
        wait_for_space()
        title_screen()
        return

    # --- Narration: Arrival in R'lyeh ---
    clear()
    delay_print(f"{RED}You step through the portal. Reality twists and shudders. You find yourself in R'lyeh, the sunken city of the Elder Ones.{RESET}")
    delay_print("Cyclopean towers rise at impossible angles, and the sky churns with colors that have no name. The air is thick with the scent of brine and blood.")
    delay_print("At the heart of the city, you see Azathoth—the Blind Idiot God, the center of all chaos—writhing in a mass of tentacles and eyes.")
    delay_print("Between you and Azathoth lies the mutilated corpse of the Bishop, splayed open upon a slab of black stone. His chest is hollowed, ribs cracked wide, and his face is frozen in a rictus of agony. Blood and ichor pool at your feet, seeping into the cracks of the alien pavement.")
    delay_print(f"{RED}Azathoth's voice booms in your mind, a cacophony of flutes and screams:{RESET}")
    delay_print(
        "\"The Bishop's flesh was the key. His soul, the price. Only by restoring the dreaming center of reality can both our realms persist.\"\n"
        "\"You, little spark, are a threat to the balance. But I have need of you yet...\""
    )
    delay_print("Azathoth's form surges forward, a tidal wave of madness and power. You ready yourself for the final confrontation.")

    amulet_events_left = amulet_azathoth_events.copy()

    # --- Boss Fight Setup ---
    player_stamina = max(1, game_state.get("stamina", 10))
    # Set Azathoth's stamina based on difficulty
    if game_state.get("difficulty") == "easy":
        azathoth_stamina = 4
    else:
        azathoth_stamina = 7
    has_amulet = "Abraxas Amulet" in game_state["inventory"]

    while player_stamina > 1 and azathoth_stamina > 0:
        clear()
        delay_print(f"{RED}Azathoth looms before you, a storm of chaos and hunger!{RESET}")
        delay_print(f"Your Stamina: {player_stamina} | Azathoth's Power: {azathoth_stamina}")
        print("\nWhat will you do?")
        print("[A] Attack")
        if has_amulet:
            print(f"{ORANGE}[U] Use Abraxas Amulet{RESET}")
        else:
            print("[U] Use an item")
        print("[F] Flee (impossible)")
        action = input("> ").strip().lower()

        if action == "u" and has_amulet:
            delay_print(f"{ORANGE}You brandish the Abraxas Amulet. It blazes with a blinding light, momentarily holding Azathoth at bay!{RESET}")
            delay_print("To strike a blow, you must time your attack perfectly...")
            hit = timing_bullseye_chase(mode="boss")
            if hit:
                azathoth_stamina -= 1
                if amulet_events_left:
                    event = random.choice(amulet_events_left)
                    amulet_events_left.remove(event)
                    delay_print(event)
                else:
                    delay_print(f"{YELLOW}The amulet's power sears Azathoth again, but the effect seems to diminish...{RESET}")
                if azathoth_stamina == 0:
                    break
            else:
                delay_print(random.choice(azathoth_lashouts))
                player_stamina = max(1, player_stamina - 4)
        elif action == "a":
            delay_print(f"{RED}You strike at Azathoth, but your attack passes through empty chaos. It is utterly futile!{RESET}")
            delay_print(random.choice(azathoth_lashouts))
            player_stamina = max(1, player_stamina - 4)
        elif action == "u":
            if "Loaded Webley .45" in game_state["inventory"]:
                delay_print(f"{YELLOW}You fire the Loaded Webley .45 at Azathoth!{RESET}")
                delay_print(f"{RED}The bullets streak toward the monstrous form, but are swallowed by writhing tentacles or ricochet harmlessly off its chitinous thorax. Azathoth does not even notice your attack.{RESET}")
                delay_print(random.choice(azathoth_lashouts))
            else:
                delay_print(f"{RED}You use an item, but nothing in your possession can harm Azathoth!{RESET}")
                delay_print(random.choice(azathoth_lashouts))
            player_stamina = max(1, player_stamina - 4)
        elif action == "f":
            delay_print(f"{RED}There is no escape from R'lyeh. The city closes in around you!{RESET}")
            player_stamina = max(1, player_stamina - 4)
        else:
            delay_print("You hesitate, and Azathoth's power batters your mind and body!")
            player_stamina = max(1, player_stamina - 4)
        wait_for_space()

    # --- Endings ---
    if azathoth_stamina == 0:
        delay_print(f"{YELLOW}With a final, perfect strike, the Abraxas Amulet unleashes a torrent of light!{RESET}")
        delay_print(f"{RED}Azathoth howls, his form unraveling into a storm of darkness and sound. The city trembles as the Blind Idiot God is banished into exile, his presence torn from both realms!{RESET}")
        delay_print("The portal snaps shut behind you. You collapse, gasping, back in the manor, the Book of Eibon pulsing with spent power in your hands.")
        delay_print(f"{YELLOW}You have defeated Azathoth and saved both worlds—for now. Your legend will echo through the ages!{RESET}")
        mark_quest_completed("Banish Azathoth back to the Elder Ones' domain.")
        game_state["score"] += 15
        delay_print(f"Final Score: {game_state['score']}")
        wait_for_space()
        # save_game()
        title_screen()
        return
    else:
        delay_print(f"{RED}Azathoth's power overwhelms you. You collapse, barely clinging to life. The Blind Idiot God looms over you, but does not strike the final blow.{RESET}")
        delay_print(
            "\"You will live, little spark. I have need of you yet. There are other doors to open, other worlds to shatter. Rest now, and await my call...\""
        )
        show_epilogue_awaken_in_manor()
                
        delay_print(f"Final Score: {game_state['score']}")
        # save_game()
        wait_for_space()
        title_screen()
        return

# --- Insert this call in case_resolution() and interrogate_suspect() after the portal is opened and all Eibon pages are collected ---

   
def show_score():
    clear()
    delay_print(f"Final Score: {game_state['score']}")
    print("\n--- Score Breakdown ---")

    clues = [entry for entry in game_state["score_log"] if entry.startswith("Clue:")]
    artifacts = [entry for entry in game_state["score_log"] if entry.startswith("Artifact:")]
    interrogations = [entry for entry in game_state["score_log"] if entry.startswith("Interrogated:")]
    solved = [entry for entry in game_state["score_log"] if entry.startswith("Case Solved")]
    turns = [entry for entry in game_state["score_log"] if entry.startswith("5 turns taken")]
    penalties = [entry for entry in game_state["score_log"] if entry not in clues + artifacts + interrogations + solved + turns]

    if game_state["sanity"] > 10:
        if "Kept sanity above 10" not in game_state["achievements"]:
            game_state["achievements"].add("Kept sanity above 10")
            game_state["score"] += ACHIEVEMENT_SCORE
            print(f"{CYAN}Achievement unlocked: {ACHIEVEMENTS['Kept sanity above 10']} (+{ACHIEVEMENT_SCORE} points){RESET}")
    if game_state["faith"] >= 5:
        if "Never dropped below 5 faith" not in game_state["achievements"]:
            game_state["achievements"].add("Never dropped below 5 faith")
            game_state["score"] += ACHIEVEMENT_SCORE
            print(f"{CYAN}Achievement unlocked: {ACHIEVEMENTS['Never dropped below 5 faith']} (+{ACHIEVEMENT_SCORE} points){RESET}")
    if clues:
        print(f"Clues found: {len(clues)} x +10 = +{len(clues)*10}")
        for entry in clues:
            print("  " + entry)
    if artifacts:
        print(f"Artifacts found: {len(artifacts)} x +20 = +{len(artifacts)*20}")
        for entry in artifacts:
            print("  " + entry)
    if interrogations:
        print(f"Suspects interrogated: {len(interrogations)} x +15 = +{len(interrogations)*15}")
        for entry in interrogations:
            print("  " + entry)
    if solved:
        print(f"Case solved: +100")
        for entry in solved:
            print("  " + entry)
    if turns:
        print(f"Turn penalties: {len(turns)} x -1 = {len(turns)*-1}")
        for entry in turns:
            print("  " + entry)
    if game_state.get("achievements"):
        print("\n--- Achievements Unlocked ---")
        for achievement in game_state["achievements"]:
            print(f"{YELLOW}{achievement}{RESET}")
    for entry in penalties:
        print(entry)

    print("\n--- Scoring Rules ---")
    print("Clues found: +10 each")
    print("Suspects interrogated: +15 each")
    print("Artifacts found: +20 each")
    print("Case solved: +100")
    print("Each 5 turns taken: +1")
    print("Stamina dropped to 0: -25")
    print("Sanity dropped to 0: -50")
    print("Killing any suspect: -30")
    # wait_for_space("Press SPACE to continue.")
    if game_state.get("achievements"):
        print("\n--- ACHIEVEMENTS Unlocked ---")
        for achievement in game_state["achievements"]:
            desc = ACHIEVEMENTS.get(achievement, "")
            print(f"{YELLOW}{achievement}{RESET}: {desc}")

def case_resolution():
    # If called from a forced confession, use that suspect as the accused
    forced_accused_name = game_state.pop("forced_accused", None)
    accused = None
    if forced_accused_name:
        accused = next((s for s in game_state["suspects"] if s["name"] == forced_accused_name), None)
        if not accused:
            delay_print("Error: Accused suspect not found.")
            title_screen()
            return
    else:
        delay_print("You gather your thoughts, and the suspects around, and review the case... Pages of notes flicker in your mind like a shuffled deck of ghosts.")
        if len(game_state["clues"]) >= game_state.get("required_clues", 5):
            # List suspects for accusation
            print("\nWho do you accuse of the Bishop's disappearance?")
            for idx, suspect in enumerate(game_state["suspects"], 1):
                name = suspect['name']
                if name in game_state.get("suspects_interrogated", set()):
                    print(f"{YELLOW}[{idx}] {name} (interrogated){RESET}")
                else:
                    print(f"[{idx}] {name}")
            print(f"[{len(game_state['suspects'])+1}] Cancel")
            while True:
                choice = input("> ").strip()
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(game_state["suspects"]):
                        accused = game_state["suspects"][idx]
                        break
                    elif idx == len(game_state["suspects"]):
                        describe_room()
                        return
                print("Please select a valid suspect number or cancel.")
        else:
            delay_print("There are still missing pieces. They flit just beyond comprehension like shadows behind stained glass.")
            return

    # Reveal the outcome
    if accused and accused.get("is_murderer"):
        crime = game_state.get("crime_type", "disappearance")
        delay_print(f"{YELLOW}You accuse {accused['name']}... and the evidence is overwhelming! The culprit breaks down and confesses!{RESET}")
        # Reveal the true fate of the Bishop based on crime_type
        if crime == "murder":
            delay_print(f"The truth is revealed: {accused['name']} murdered the Bishop in a fit of {accused['motive'].lower()}.")
        elif crime == "kidnapping":
            delay_print(f"{accused['name']} kidnapped the Bishop, driven by {accused['motive'].lower()}.")
        elif crime == "ritual sacrifice":
            delay_print(f"{accused['name']} performed a forbidden ritual, sacrificing the Bishop for {accused['motive'].lower()} reasons.")
        elif crime == "blackmail":
            delay_print(f"{accused['name']} blackmailed the Bishop, forcing his disappearance out of {accused['motive'].lower()}.")
        elif crime == "forced exile":
            delay_print(f"{accused['name']} orchestrated the Bishop's exile, motivated by {accused['motive'].lower()}.")
        else:
            delay_print(f"{accused['name']} is the culprit, the one responsible for the Bishop's disappearance.")
        delay_print("Justice is served. The Bishop's fate is finally known.")
        correct_culprit = accused
        show_accusation_breakdown(accused, correct_culprit, game_state.get("clue_motives", {}), game_state.get("clues", []))
        wait_for_space()
        mark_quest_completed("Investigate the disappearance of the Bishop.")

        if "Survived combat against" not in " ".join(game_state["journal"]):
            if "Solved without violence" not in game_state["achievements"]:
                game_state["achievements"].add("Solved without violence")
                game_state["score"] += ACHIEVEMENT_SCORE
                print(f"{CYAN}Achievement unlocked: {ACHIEVEMENTS['Solved without violence']} (+{ACHIEVEMENT_SCORE} points){RESET}")

        if game_state.get("difficulty") == "hard":
            if "Solved the case on hard mode" not in game_state["achievements"]:
                game_state["achievements"].add("Solved the case on hard mode")
                game_state["score"] += ACHIEVEMENT_SCORE
                print(f"{CYAN}Achievement unlocked: {ACHIEVEMENTS['Solved the case on hard mode']} (+{ACHIEVEMENT_SCORE} points){RESET}")

        delay_print("You hear a rush of people. As the constables move in to apprehend the culprit, a heavy tome falls from their coat and lands at your feet.")
        delay_print(f"{ORANGE}It is the legendary Book of Eibon!{RESET}")
        delay_print(
            f"{accused['name']} laughs maniacally: "
            "'Futile, futile! The pages are scattered—you are but a child before its cosmic design! "
            "Its power is not meant for mortal minds, and your sanity would shatter should you glimpse its truth! Cahf ah nafl mglw'nafh hh' ahor syha'h ah'legeth, ng llll or'azath syha'hnahh n'ghftephai n'gha ahornah ah'mglw'nafh'"
            "...and with that, the suspect vanishes into thin air, leaving only the Book of Eibon behind in your possession."
        )
        # Add Book of Eibon to inventory if not present
        if "Book of Eibon" not in game_state["inventory"]:
            game_state["inventory"].append("Book of Eibon")
            game_state["journal"].append("Obtain the -incomplete- Book of Eibon.")
            mark_quest_completed("Obtain the -incomplete- Book of Eibon.")

        # --- Check if all three pages are present; if not, show missing pages and offer C/Q ---
        required_pages = {
            "First Fragment of the Eibon Manuscript",
            "Second Fragment of the Eibon Manuscript",
            "Third Fragment of the Eibon Manuscript"
        }
        player_pages = set(item for item in game_state["inventory"] if "Fragment of the Eibon Manuscript" in item)
        if not required_pages.issubset(player_pages):
            missing = required_pages - player_pages
            delay_print(f"{ORANGE}You are missing the following pages: {', '.join(sorted(missing))}.{RESET}")
            delay_print("You sense that if you can find the missing pages and return, the Book of Eibon will reveal its true power...")
            game_state["journal"].append("You must search the manor for the missing pages of the Book of Eibon.")
            # Add quest to logbook if not already present
            quest_text = "Assemble the Book of Eibon by finding all three manuscript fragments."
            if quest_text not in game_state["quests"]:
                game_state["quests"].append(quest_text)
            delay_print("You may continue your investigation to seek out the missing pages, or quit to the title screen.")
            while True:
                print("[C] Continue searching for the missing pages")
                print("[Q] Quit to title")
                choice = input("> ").strip().lower()
                if choice == "c":
                    # Remove the accused from suspects so they can't be interrogated anymore
                    if accused in game_state["suspects"]:
                        game_state["suspects"].remove(accused)
                    describe_room()
                    return
                elif choice == "q":
                    title_screen()
                    return
                else:
                    print("Please select C or Q.")

    elif accused:
        delay_print(f"{RED}You accuse {accused['name']}, but the evidence does not hold. The real culprit remains at large...{RESET}")
        game_state["score"] -= 30
        game_state["journal"].append(f"Case failed: Wrongly accused {accused['name']}.")
        delay_print("You have failed to solve the case. The shadows of the manor seem to deepen.")
        # Show breakdown
        correct_culprit = next(s for s in game_state["suspects"] if s.get("is_murderer"))
        show_accusation_breakdown(accused, correct_culprit, game_state.get("clue_motives", {}), game_state.get("clues", []))
        wait_for_space()
def describe_room():
    global previous_menu_function
    previous_menu_function = describe_room
    clear()
    room = game_state["location"]

    # Always assign this at the top
    main_quest_stricken = any(
        q.replace("\033[9m", "").replace("\033[0m", "") == "Investigate the disappearance of the Bishop."
        for q in game_state.get("quests", [])
    )
    interrogated_count = len(game_state.get("suspects_interrogated", set()))

    # --- UNIVERSAL PORTAL CHECK: If you have all three pages and the Book, trigger the final boss ---
    required_pages = {
        "First Fragment of the Eibon Manuscript",
        "Second Fragment of the Eibon Manuscript",
        "Third Fragment of the Eibon Manuscript"
    }
    player_pages = set(item for item in game_state["inventory"] if "Fragment of the Eibon Manuscript" in item)
    if required_pages.issubset(player_pages) and "Book of Eibon" in game_state["inventory"]:
        # Only trigger if not already completed
        if "Assemble the Book of Eibon and open the portal to the Elder Ones' realm." not in [
            q.replace("\033[9m", "").replace("\033[0m", "") for q in game_state.get("quests", [])
        ]:
            delay_print(f"{YELLOW}You have assembled all three missing pages of the Book of Eibon!{RESET}")
            delay_print("The Book pulses with power. A portal begins to open...")
            game_state["journal"].append("Assemble the Book of Eibon and open the portal to the Elder Ones' realm.")
            mark_quest_completed("Assemble the Book of Eibon by finding all three manuscript fragments.")
            mark_quest_completed("Assemble the Book of Eibon and open the portal to the Elder Ones' realm.")
            final_boss_sequence()
            return

    # --- Suspect alert: always show if someone is here ---
    suspects_here = [
        s for s in game_state["suspects"]
        if s.get("position") == game_state["position"]
    ]
    if suspects_here:
        names = ', '.join(s["name"] for s in suspects_here)
        delay_print(f"You see someone here: {names}")

    # --- Show 'enough evidence' message if appropriate ---
    if (
        len(game_state["clues"]) >= game_state.get("required_clues", 2)
        and interrogated_count >= game_state.get("min_suspects_interrogated", 3)
        and not main_quest_stricken
    ):
        print(f"{ORANGE}You feel you have gathered enough evidence to make an accusation. The truth is within your grasp...{RESET}")

    # --- Show room name at the top in GREEN ---
    print(f"\n{GREEN}=== {room} ==={RESET}\n")
    descriptions = room_templates.get(room, ["It's a bare and quiet room."])
    desc = random.choice(descriptions)
    distorted = distort_text(desc, game_state["sanity"])

    # --- Supernatural Event/Cut Scene ---
    if "supernatural_rooms" not in game_state:
        all_rooms = list(room_templates.keys())
        game_state["supernatural_rooms"] = random.sample(all_rooms, 5)
    supernatural_rooms = game_state["supernatural_rooms"]

    if game_state["location"] in supernatural_rooms:
        event_key = f"faith_event_{game_state['location']}"
        if not game_state.get(event_key, False):
            if faith_check(12):
                delay_print(f"{ORANGE}Your faith shields you from the unnatural influence in this place.{RESET}")
                wait_for_space()
            else:
                horror_scenes = [
                    "The shadows in the corners of the room begin to writhe and pulse, stretching into impossible shapes. A cold, invisible hand brushes your neck, and you hear a whisper in a language you cannot understand.",
                    "The walls seem to breathe, exhaling a chill that fogs your vision. For a moment, you glimpse a figure with too many eyes watching from the darkness, its gaze burrowing into your soul.",
                    "A sudden, suffocating silence falls. The air thickens, and you feel as if you are being submerged in icy water. Something ancient and hungry stirs just beyond the edge of sight.",
                    "The floorboards groan beneath you, and a chorus of ghostly voices rises in a mournful chant. The temperature plummets, and your breath crystallizes in the air.",
                    "A flicker of movement draws your eye—a shadow detaches itself from the wall and crawls across the ceiling, vanishing when you try to focus on it. Your heart pounds as you realize you are not alone."
                ]
                delay_print(f"{RED}{random.choice(horror_scenes)}{RESET}")
                delay_print(f"{RED}A chill runs through you. You lose 1 sanity.{RESET}")
                game_state["sanity"] = max(0, game_state["sanity"] - 1)
                wait_for_space()
            game_state[event_key] = True
            describe_room()  # Re-enter the room, now with the event marked as seen
            return
        delay_print(distorted)
    else:
        delay_print(distorted)

    # --- Flavor text logic ---
    pos = game_state["position"]
    used = game_state.setdefault("room_flavor_used", {})
    used_indices = used.get(pos, [])
    available_indices = [i for i in range(len(flavor_text_pool)) if i not in used_indices]

    # Guarantee flavor text on first entry to Foyer at (0, 0)
    if pos == (0, 0) and room == "Foyer" and not used_indices:
        idx = random.choice(available_indices)
        flavor = flavor_text_pool[idx]
        delay_print(distort_text(flavor, game_state["sanity"]))
        used.setdefault(pos, []).append(idx)
        game_state["room_flavor_used"] = used
        if not game_state.get("inventory_tip_shown"):
            print("\nCheck your inventory (press '5' or 'i') to see your list of belongings.")
            game_state["inventory_tip_shown"] = True
    elif available_indices and random.random() < 0.40:
        idx = random.choice(available_indices)
        flavor = flavor_text_pool[idx]
        delay_print(distort_text(flavor, game_state["sanity"]))
        used.setdefault(pos, []).append(idx)
        game_state["room_flavor_used"] = used
    elif not available_indices:
        used[pos] = []

    # Check if any suspect is present in the current room
    suspects_here = [
        s for s in game_state["suspects"]
        if s.get("position") == game_state["position"]
    ]

    # Count interrogated suspects (by set)
    interrogated_count = len(game_state.get("suspects_interrogated", set()))

    print("\nWhat would you like to do?")
    print("[1] Search the room")
    print("[2] Move to another location")
    print("[3] Show map")
    print("[4] Check journal")
    print("[5] Check inventory")

    # Chapel prayer option
    if room == "Chapel":
        print(f"{ORANGE}[P] Pray for guidance{RESET}")
    if suspects_here:
        suspect_names = ", ".join(s["name"] for s in suspects_here)
        print(f"{ORANGE}[6] Interrogate suspect ({suspect_names}){RESET}")
    # Only show case resolution if at least required clues and suspects interrogated
    main_quest_stricken = any(
        q.startswith("\033[9mInvestigate the disappearance of the Bishop.") for q in game_state.get("quests", [])
    )
    if (
        len(game_state["clues"]) >= game_state.get("required_clues", 2)
        and interrogated_count >= game_state.get("min_suspects_interrogated", 3)
        and not main_quest_stricken
    ):
        print(f"{ORANGE}[7] ATTEMPT CASE RESOLUTION{RESET}")
        case_resolution_available = True
    else:
        case_resolution_available = False
    print("[8] Save game")
    print("[9] Quit to title")

    x, y = game_state["position"]
    available_exits = [d.upper() for d in game_state["passages"].get((x, y), set())]
    if available_exits:
        print(f"\nThere are exits: {', '.join(available_exits)}")
    else:
        print("\nThere are no available exits from this room.")

    # Sanity penalty: only apply once
    if game_state["sanity"] <= 0 and not game_state.get("sanity_zero_penalized", False):
        game_state["score"] -= 25
        game_state["score_log"].append("Sanity dropped to 0 [-25]")
        game_state["sanity_zero_penalized"] = True

    # Announce Bishop's last known location and time ONCE, in ORANGE, and add to journal
    if not game_state.get("bishop_location_announced", False):
        last_loc = game_state.get("bishop_last_location", "an unknown location")
        last_time = game_state.get("bishop_last_time", "an unknown time")
        announcement = f"{ORANGE}The Bishop was last seen in the {last_loc} at {last_time}.{RESET}"
        print(announcement)
        journal_entry = f"{ORANGE}Bishop last seen: {last_loc} at {last_time}.{RESET}"
        if journal_entry not in game_state["journal"]:
            game_state["journal"].append(journal_entry)
        game_state["bishop_location_announced"] = True

    print("\n(You can use N/S/E/W keys to move when prompted for a direction, and arrow keys in the 'Map' option.)")
    user_input = input("> ").strip().lower()
    if user_input in ["n", "s", "e", "w"]:
        move_to_new_room(user_input)
        game_state["turns"] += 1
        if game_state["turns"] % 15 == 0:
            game_state["score"] += 1
            game_state["score_log"].append("15 turns taken [+1]")
        describe_room()
        return
    elif user_input == "1":
        add_random_clue()
        game_state["turns"] += 1
        if game_state["turns"] % 15 == 0:
            game_state["score"] += 1
            game_state["score_log"].append("15 turns taken [-1]")
        wait_for_space()
        describe_room()
        return
    elif user_input == "2":
        clear()
        print("Where would you like to go? (N, S, E, W)")
        print("You can also use arrow keys.")
        dir_input = input("> ").strip().lower()
        if dir_input in ["n", "s", "e", "w"]:
            move_to_new_room(dir_input)
            game_state["turns"] += 1
            if game_state["turns"] % 15 == 0:
                game_state["score"] += 1
                game_state["score_log"].append("15 turns taken [+1]")
        else:
            print("Press an arrow key to move, or Enter to return.")
            if msvcrt.kbhit():
                direction = get_direction_from_arrow()
                if direction:
                    move_to_new_room(direction)
                    game_state["turns"] += 1
                    if game_state["turns"] % 15 == 0:
                        game_state["score"] += 1
                        game_state["score_log"].append("15 turns taken [-1]")
                    return
            delay_print("Unknown direction. Please enter a valid compass direction or use arrow keys.")
            wait_for_space()
            describe_room()
    elif user_input == "3":
        show_map()
        return
    elif user_input == "4":
        show_journal()
    elif user_input == "5":
        show_inventory()
    elif user_input == "6" and suspects_here:
        interrogate_suspect()
    elif user_input == "7" and case_resolution_available:
        case_resolution()
    elif user_input == "8" or user_input == "save":
        save_game()
        describe_room()
    elif user_input == "9" or user_input == "quit":
        title_screen()
    elif user_input == "p" and room == "Chapel":
        if game_state.get("chapel_pray_cooldown", 0) > 0:
            delay_print(f"You sense the sacred silence has not yet returned. You must wait {game_state['chapel_pray_cooldown']} more turns before praying again.")
        else:
            delay_print("You kneel and pray. A sense of calm washes over you.")
            before_sanity = game_state["sanity"]
            before_health = game_state["health"]
            game_state["sanity"] = min(game_state.get("max_sanity", 10), game_state["sanity"] + 1)
            if game_state["faith"] >= 14:
                game_state["health"] = min(18, game_state["health"] + 1)
                delay_print(f"(Sanity restored: +{game_state['sanity'] - before_sanity}, Health restored: +{game_state['health'] - before_health})")
            else:
                delay_print(f"(Sanity restored: +{game_state['sanity'] - before_sanity})")
            game_state["journal"].append("Pray for guidance in the chapel.")
            mark_quest_completed("Pray for guidance in the chapel.")
            game_state["chapel_pray_cooldown"] = 5  # 5 turns cooldown
        wait_for_space()
        describe_room()
        return
    elif user_input == "f":
        print("\nChoose a suspect to fight:(DEBUG)")
        for i, s in enumerate(game_state["suspects"], 1):
            print(f"[{i}] {s['name']}")
        choice = input("> ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(game_state["suspects"]):
                skill_check_combat(game_state["suspects"][idx]["name"])
                describe_room()
                return
        print("Invalid choice.")
        describe_room()
        return
    else:
        handle_input(user_input, describe_room)

def interrogate_suspect():
    global previous_menu_function
    previous_menu_function = interrogate_suspect
    if not isinstance(game_state.get("suspects_interrogated"), set):
        game_state["suspects_interrogated"] = set(game_state.get("suspects_interrogated", []))
    suspects_here = [
        s for s in game_state["suspects"]
        if s.get("position") == game_state["position"]
    ]
    # If any suspect here is transformed, start combat immediately
    for suspect in suspects_here:
        if suspect.get("transformed", False):
            delay_print(f"{RED}A monstrous horror stands before you!{RESET}")
            skill_check_combat(suspect["name"])
            return
        
    if not suspects_here:
        delay_print("There is no one here to interrogate.")
        wait_for_space()
        describe_room()
        return

    while True:
        clear()
        print("\nChoose someone to interrogate:")
        for i, s in enumerate(suspects_here):
            print(f"[{i+1}] {s['name']}")
        print(f"[{len(suspects_here)+1}] Return")

        user_input = input("> ").strip().lower()
        if user_input == "" or user_input == "r" or (user_input.isdigit() and int(user_input) == len(suspects_here) + 1):
            describe_room()
            return

        if user_input.isdigit():
            idx = int(user_input) - 1
            if 0 <= idx < len(suspects_here):
                suspect = suspects_here[idx]
                # print("[DEBUG] suspects_interrogated type:", type(game_state["suspects_interrogated"]))
                
                if isinstance(game_state["suspects_interrogated"], list):
                    game_state["suspects_interrogated"] = set(game_state["suspects_interrogated"])
                elif not isinstance(game_state["suspects_interrogated"], set):
                    game_state["suspects_interrogated"] = set()
                game_state["suspects_interrogated"].add(suspect["name"])
                if len(game_state["suspects_interrogated"]) == len(game_state["suspects"]):
                    if "Interrogated every suspect" not in game_state["achievements"]:
                        game_state["achievements"].add("Interrogated every suspect")
                        game_state["score"] += ACHIEVEMENT_SCORE
                        print(f"{CYAN}Achievement unlocked: {ACHIEVEMENTS['Interrogated every suspect']} (+{ACHIEVEMENT_SCORE} points){RESET}")
                clear()
                # Show long flavor text on first encounter, short on subsequent
                if not suspect.get("flavor_text_shown", False):
                    desc = suspect.get("flavor_text")
                    suspect["flavor_text_shown"] = True
                else:
                    desc = motive_descriptions.get(suspect.get("motive"), "")
                if desc:
                    delay_print(desc)

                delay_print(f"You confront {suspect['name']}.")
                game_state["journal"].append(f"You confront {suspect['name']}")
                asked_question = False
                info_shown = False

                response_count = 0  # Track number of responses since last clear

                while True:
                    if response_count and response_count % 2 == 0:
                        clear()
                        print(f"{ORANGE}(You pause to gather your thoughts before continuing the interrogation...){RESET}")

                    print("\nOptions:")
                    options = set()
                    print("[1] Observe body language")
                    options.add("1")
                    print("[2] Ask about their relationship to the Bishop")
                    options.add("2")
                    print("[3] Ask where they were at the time of the crime")
                    options.add("3")
                    print("[4] Ask who they suspect")
                    options.add("4")
                    print("[5] Ask about their knowledge of the crime")
                    options.add("5")
                    print("[6] Ask about their means/access")
                    options.add("6")
                    print("[7] Ask about witnesses")
                    options.add("7")
                    print("[8] Ask about financial motive")
                    options.add("8")
                    print("[9] Ask about secret relationships")
                    options.add("9")
                    print("[10] Ask about blackmail or occult matters")
                    options.add("10")
                    print("[11] Direct accusation")
                    options.add("11")
                    if game_state["faith"] >= 14:
                        print(f"{ORANGE}[12] Bless or rebuke the suspect (Faith){RESET}")
                        options.add("12")
                    if not game_state.get("persuasion_active", False) and (game_state.get("comeliness", 0) >= 14 or game_state.get("perception", 0) >= 14):
                        print(f"{ORANGE}[13] Attempt Persuasion{RESET}")
                        options.add("13")
                    if game_state.get("clues"):
                        print(f"{ORANGE}[14] Present a clue as evidence{RESET}")
                        options.add("14")
                    print("[0 or RETURN] Return to action menu")
                    options.add("0")

                    choice = input("> ").strip().lower()

                    def check_tolerance():
                        if "tolerance" not in suspect:
                            suspect["tolerance"] = game_state.get("suspect_tolerance", 5)
                        suspect["tolerance"] -= 1
                        if suspect["tolerance"] == 2:
                            delay_print(f"{suspect['name']} is growing agitated. You sense danger.")
                        if suspect["tolerance"] <= 0:
                            if random.random() < 0.5:
                                delay_print(f"{suspect['name']} snaps! They attack you in a fit of rage!")
                                wait_for_space()
                                skill_check_combat(suspect["name"])
                                # --- Exit interrogation if suspect is gone ---
                                if suspect not in game_state["suspects"]:
                                    delay_print(f"{suspect['name']} is no longer present.")
                                    describe_room()
                                    return True
                            else:
                                delay_print(f"{suspect['name']}'s eyes narrow, but they hold their composure... for now.")
                        return False

                    if choice == "1":
                        roll = game_state["perception"] + roll_fudge()
                        if roll >= 12:
                            delay_print(f"(Observation check: Perception + die roll = {roll})")
                            delay_print("You notice a nervous tic. The suspect is definitely hiding something.")
                            game_state["journal"].append(
                                f"Observed {suspect['name']}'s body language at {game_state['location']}: hiding something."
                            )
                        else:
                            delay_print("You can't read their body language this time.")
                        asked_question = True
                        wait_for_space()
                        response_count += 1
                        continue

                    elif choice == "2":
                        rel = suspect['relationship']
                        delay_print(f"{suspect['name']} says: '{rel}'")
                        suspect.setdefault("asked", set()).add("relationship")
                        game_state["journal"].append(
                            f"Testimony from {suspect['name']} at {game_state['location']}: Relationship: {rel}"
                        )
                        asked_question = True
                        if check_tolerance():
                            return
                        wait_for_space()
                        response_count += 1
                        continue

                    elif choice == "3":
                        alibi = suspect.get('alibi', 'I was alone, and no one can confirm my whereabouts.')
                        if isinstance(alibi, dict):
                            alibi_text = alibi.get("text", str(alibi))
                        else:
                            alibi_text = str(alibi)
                        delay_print(f"{suspect['name']} says: '{alibi_text}'")
                        suspect.setdefault("asked", set()).add("alibi")
                        game_state["journal"].append(
                            f"Testimony from {suspect['name']} at {game_state['location']}: Alibi: {alibi_text}"
                        )
                        asked_question = True
                        if check_tolerance():
                            return
                        wait_for_space()
                        response_count += 1
                        continue

                    elif choice == "4":
                        other_name = random.choice([s['name'] for s in game_state['suspects'] if s['name'] != suspect['name']])
                        delay_print(f"{suspect['name']} says: 'If you ask me, {other_name} seemed suspicious.'")
                        game_state["journal"].append(
                            f"Testimony from {suspect['name']} at {game_state['location']}: Suspects: {other_name}"
                        )
                        asked_question = True
                        if check_tolerance():
                            return
                        wait_for_space()
                        response_count += 1
                        continue

                    elif choice == "5":
                        delay_print(f"{suspect['name']} {suspect.get('knowledge', 'I know nothing about that.')}")
                        suspect.setdefault("asked", set()).add("knowledge")
                        game_state["journal"].append(
                            f"Testimony from {suspect['name']} at {game_state['location']}: Knowledge: {suspect.get('knowledge', '')}"
                        )
                        asked_question = True
                        if check_tolerance():
                            return
                        wait_for_space()
                        response_count += 1
                        continue

                    elif choice == "6":
                        delay_print(f"{suspect['name']} {suspect.get('means', 'I had no special access.')}")
                        suspect.setdefault("asked", set()).add("means")
                        game_state["journal"].append(
                            f"Testimony from {suspect['name']} at {game_state['location']}: Means: {suspect.get('means', '')}"
                        )
                        asked_question = True
                        if check_tolerance():
                            return
                        wait_for_space()
                        response_count += 1
                        continue

                    elif choice == "7":
                        delay_print(f"{suspect['name']} says: '{suspect.get('witnesses', 'No one saw me.')}'")
                        suspect.setdefault("asked", set()).add("witnesses")
                        game_state["journal"].append(
                            f"Testimony from {suspect['name']} at {game_state['location']}: Witnesses: {suspect.get('witnesses', '')}"
                        )
                        asked_question = True
                        if check_tolerance():
                            return
                        wait_for_space()
                        response_count += 1
                        continue

                    elif choice == "8":
                        delay_print(f"{suspect['name']} says: '{suspect.get('financial', 'I have no financial motive.')}'")
                        suspect.setdefault("asked", set()).add("financial")
                        game_state["journal"].append(
                            f"Testimony from {suspect['name']} at {game_state['location']}: Financial: {suspect.get('financial', '')}"
                        )
                        asked_question = True
                        if check_tolerance():
                            return
                        wait_for_space()
                        response_count += 1
                        continue

                    elif choice == "9":
                        delay_print(f"{suspect['name']} says: '{suspect.get('secret_relationship', 'Nothing to confess.')}'")
                        suspect.setdefault("asked", set()).add("secret_relationship")
                        game_state["journal"].append(
                            f"Testimony from {suspect['name']} at {game_state['location']}: Secret Relationship: {suspect.get('secret_relationship', '')}"
                        )
                        asked_question = True
                        if check_tolerance():
                            return
                        wait_for_space()
                        response_count += 1
                        continue

                    elif choice == "10":
                        delay_print(f"{suspect['name']} says: '{suspect.get('blackmail', 'No comment.')}'")
                        suspect.setdefault("asked", set()).add("blackmail")
                        game_state["journal"].append(
                            f"Testimony from {suspect['name']} at {game_state['location']}: Blackmail/Occult: {suspect.get('blackmail', '')}"
                        )
                        asked_question = True
                        if check_tolerance():
                            return
                        wait_for_space()
                        response_count += 1
                        continue

                    elif choice == "11":
                        confession = suspect.get('confession', 'I have nothing to say.')
                        delay_print(f"{suspect['name']} says: '{confession}'")
                        suspect.setdefault("asked", set()).add("confession")
                        game_state["journal"].append(
                            f"Testimony from {suspect['name']} at {game_state['location']}: Confession: {confession}"
                        )
                        asked_question = True
                        wait_for_space()
                        response_count += 1
                        # If the suspect confesses, jump to case resolution
                        if "admit" in confession.lower():
                            # Check if minimum requirements are met
                            if (
                                len(game_state["clues"]) >= game_state.get("required_clues", 5)
                                and len(game_state.get("suspects_interrogated", set())) >= game_state.get("min_suspects_interrogated", 2)
                            ):
                                # Mark this suspect as the accused and call case_resolution
                                game_state["forced_accused"] = suspect["name"]
                                case_resolution()
                                return
                            else:
                                delay_print("You have a confession, but you still need more evidence to close the case.")
                                # Optional: risk—suspect's tolerance drops sharply
                                suspect["tolerance"] = max(0, suspect.get("tolerance", 1) - 2)
                        continue

                    elif choice == "12" and game_state["faith"] >= 14:
                        if suspect.get("motive") in ["Fanaticism", "Zealotry"]:
                            delay_print(f"{suspect['name']} recoils from your words. Your faith unsettles them, and they falter in their conviction.")
                            suspect["credibility"] = max(0, suspect.get("credibility", 5) - 2)
                            game_state["score"] += 5
                        else:
                            delay_print(f"You invoke a blessing. {suspect['name']} seems moved, but you sense no hidden evil.")
                        wait_for_space()
                        response_count += 1
                        continue

                    elif choice == "13":
                        if not game_state.get("persuasion_active", False):
                            delay_print(f"{CYAN}You attempt to persuade {suspect['name']}...{RESET}")
                            if game_state.get("comeliness", 0) >= 14 or game_state.get("perception", 0) >= 14:
                                delay_print(f"{CYAN}{suspect['name']} seems swayed by your words!{RESET}")
                                game_state["persuasion_active"] = True
                                game_state["journal"].append(f"Persuaded {suspect['name']} at {game_state['location']}.")
                                suspect["tolerance"] = game_state.get("suspect_tolerance", 5)
                                delay_print(f"{YELLOW}{suspect['name']}'s tolerance for questioning has been restored!{RESET}")
                            else:
                                delay_print(f"{RED}Your attempt at persuasion fails to move {suspect['name']}.{RESET}")
                            wait_for_space()
                        response_count += 1
                        continue

                    elif choice == "14":
                        if game_state.get("clues"):
                            print("Which clue would you like to present?")
                            for idx, clue in enumerate(game_state["clues"], 1):
                                print(f"[{idx}] {clue}")
                            clue_choice = input("> ").strip()
                            if clue_choice.isdigit():
                                clue_idx = int(clue_choice) - 1
                                if 0 <= clue_idx < len(game_state["clues"]):
                                    presented_clue = game_state["clues"][clue_idx]
                                if ":" in presented_clue:
                                    after_colon = presented_clue.split(":", 1)[1].strip()
                                    short_clue = after_colon.split(".", 1)[0].strip()
                                else:
                                    short_clue = presented_clue[:40]
                                delay_print(f"{YELLOW}You present the clue: {short_clue}{RESET}")# --- NEW: Suspect reacts to the clue ---
                                clue_motive = game_state.get("clue_motives", {}).get(presented_clue)
                                if clue_motive and clue_motive == suspect.get("motive"):
                                    delay_print(f"{suspect['name']} looks shaken. \"I... I don't know what to say about that.\"")
                                else:
                                    delay_print(f"{suspect['name']} glances at the clue, then shrugs. \"That doesn't prove anything about me.\"")
                                game_state["journal"].append(f"Presented clue to {suspect['name']}: {presented_clue}")
                                wait_for_space()
                                response_count += 1
                                continue
                        delay_print("You have no clues to present.")
                        wait_for_space()
                        response_count += 1
                        continue

                    elif choice == "0" or choice == "return" or choice == "":
                        describe_room()
                        return

                    else:
                        delay_print("Invalid selection.")
                        wait_for_space()
                        continue
            else:
                delay_print("Invalid selection.")
                wait_for_space()
                continue

def dream_flashback():
    global previous_menu_function
    previous_menu_function = dream_flashback
    clear()
    delay_print("You are dreaming... or remembering. A shiver creeps down your spine as your mind conjures the weight of memory.")
    delay_print("A chapel cloaked in shadow, the child's voice echoing like a song half-remembered. A locked door pulses in the back of your mind like a heartbeat.")
    delay_print("Whispers echo backward through time and thought. You wake gasping, the image of a burning sigil fading from your vision.")
    wait_for_space()
    intro_scene()

def intro_scene():
    global previous_menu_function
    previous_menu_function = intro_scene
    clear()
    delay_print("A fog rolls in over the cobblestones, thick and clinging, curling like smoke through the iron gates of the city’s forgotten quarters. The gaslamps flicker under its damp touch, casting pale halos that only make the darkness beyond feel deeper—hungrier...")
    while True:
        print("\nWhat will you do?")
        print("[1] Enter through the front gate")
        print("[2] Examine the grounds")
        print("[3] Pray silently")
        print("[4] Go to character creation")
        print("[5] Return to title screen")

        user_input = input("> ").strip().lower()
        if user_input == "1":
            enter_manor()
            break
        elif user_input == "2":
            if "Bent Key" not in game_state["inventory"]:
                game_state["inventory"].append("Bent Key")
                delay_print("You search the grounds and find a bent key half-buried in the mud. It might open something inside.")
            else:
                delay_print("You have already found the bent key.")
            wait_for_space()
        elif user_input == "3":
            game_state["faith"] += 1
            delay_print("You pause and offer a silent prayer. You feel your faith strengthen (+1 Faith).")
            wait_for_space()
        elif user_input == "4":
            character_creation()
            break
        elif user_input == "5":
            title_screen()
            break
        else:
            delay_print("Invalid choice. Please select 1 or 2.")

def enter_manor():
    global previous_menu_function
    previous_menu_function = enter_manor
    clear()
    delay_print(
    "You step into the manor, the scent of mildew thick in your nostrils. "
    "The heavy door groans shut behind you, muffling the distant toll of church bells and sealing you in a hush broken only by the slow drip of unseen water. "
    "Shadows cling to the corners, and the faded grandeur of the entrance hall seems to watch your every move, as if the house itself is holding its breath, waiting for you to trespass further."
    )
    delay_print("You feel a chill run down your spine as you realize the manor is not empty. The air is thick with secrets, and you sense that something is very wrong here.")
    delay_print("You take a deep breath, steeling yourself for what lies ahead. The manor is a labyrinth of rooms and corridors, each holding its own mysteries and dangers. You must tread carefully, for the shadows may hold more than just dust and cobwebs.")
    delay_print("You can feel the weight of the manor's history pressing down on you, urging you to uncover its hidden truths.")
    wait_for_space()
    character_creation()

def random_name():
    first_names = male_first_names + female_first_names
    return f"{random.choice(first_names)} {random.choice(last_names)}"

def random_name_and_gender():
    if random.random() < 0.5:
        first = random.choice(male_first_names)
        gender = "Male"
    else:
        first = random.choice(female_first_names)
        gender = "Female"
    last = random.choice(last_names)
    return f"{first} {last}", gender

def get_player_name():
    while True:
        print("Would you like to enter a name or have one assigned at random?")
        print("[1] Enter my own name")
        print("[2] Randomize name")

        choice = input("> ").strip()
        if choice == "2":
            name, gender = random_name_and_gender()
            print(f"Your randomized name is: {name} ({'M' if gender == 'Male' else 'F'})")
            confirm = input("Accept this name? (Y/N): ").strip().lower()
            if confirm == "y":
                game_state["name"] = name
                game_state["gender"] = gender
                return name

        elif choice == "1":
            name = input("Enter your name: ").strip()
            if name:
                return name
        else:
            print("Please select 1 or 2.")

def generate_structured_map():
    """
    Generate a manor map with key rooms (Foyer, Main Hall, Kitchen) at fixed positions and all other rooms randomly assigned.
    Ensures Foyer, Main Hall, and Kitchen are adjacent and connected.
    """
    # Use the full grid size
    positions = [(x, y) for x in range(MAP_MIN, MAP_MAX + 1) for y in range(MAP_MIN, MAP_MAX + 1)]

    # --- Place key rooms at fixed positions ---
    foyer_pos = (0, MAP_MAX)
    main_hall_pos = (0, MAP_MAX-1)  # Directly north of Foyer
    kitchen_pos = (1, MAP_MAX-1)    # Directly east of Main Hall

    visited_locations = {
        foyer_pos: "Foyer",
        main_hall_pos: "Main Hall",
        kitchen_pos: "Kitchen"
    }

    # Remove these positions from the pool so they aren't overwritten
    positions = [pos for pos in positions if pos not in visited_locations]

    # Assign all other described rooms randomly to remaining positions
    all_described_rooms = [r for r in room_templates.keys() if r not in visited_locations.values()]
    random.shuffle(positions)
    empty_room_chance = 0.10  # Some empty rooms for variety
    for pos in positions:
        if all_described_rooms and random.random() > empty_room_chance:
            room = all_described_rooms.pop()
            visited_locations[pos] = room
        else:
            visited_locations[pos] = "Empty Room"

    # --- Ensure passages between key rooms ---
    passages = {}
    for pos in visited_locations:
        passages[pos] = set()
    # Foyer <-> Main Hall
    passages[foyer_pos].add("n")
    passages[main_hall_pos].add("s")
    # Main Hall <-> Kitchen
    passages[main_hall_pos].add("e")
    passages[kitchen_pos].add("w")

    # Build passages for other rooms (connect to 2–3 adjacent rooms if possible)
    for pos in visited_locations:
        if pos in [foyer_pos, main_hall_pos, kitchen_pos]:
            continue  # Already handled above
        possible_dirs = []
        for dir_name, (dx, dy) in moves.items():
            neighbor = (pos[0] + dx, pos[1] + dy)
            if neighbor in visited_locations:
                possible_dirs.append(dir_name)
        num_exits = min(len(possible_dirs), random.randint(2, 3))
        exits = random.sample(possible_dirs, num_exits) if num_exits > 0 else []
        passages[pos].update(exits)

    # Make passages consistent (if A->B, then B->A)
    for pos, dirs in passages.items():
        for dir_name in list(dirs):
            dx, dy = moves[dir_name]
            neighbor = (pos[0] + dx, pos[1] + dy)
            rev_dir = None
            for d, (ddx, ddy) in moves.items():
                if (ddx, ddy) == (-dx, -dy):
                    rev_dir = d
                    break
            if rev_dir and neighbor in passages:
                passages[neighbor].add(rev_dir)

    # Save to game_state
    game_state["visited_locations"] = visited_locations
    game_state["passages"] = passages
    game_state["location"] = "Foyer"
    game_state["position"] = foyer_pos  # Start at
    
def associate_culprit_and_pools():
    
    # 1. Pick which pool will be the "solution" pool for this game
    solution_idx = random.randint(0, 3)
    motive_pool = motive_pools[solution_idx]
    alibi_pool = alibi_pools[solution_idx]
    clue_pool = clue_pools[solution_idx]
    clue_motives = clue_motives_pools[solution_idx]

    # 2. Pick a motive, alibi, and clue that match
    solution_motive = random.choice(motive_pool)
    solution_alibi = random.choice(alibi_pool)
    game_state["bishop_last_location"] = solution_alibi["location"]
    game_state["bishop_last_time"] = solution_alibi["time"]
    # Find a clue that matches both the motive and the alibi's location/time
    solution_clue = None
    for clue in clue_pool:
        motive = clue_motives.get(clue)
        if motive == solution_motive["short"]:
            # Optionally, you can check for location/time match if you store that in clues
            solution_clue = clue
            break
    if not solution_clue:
        solution_clue = random.choice(clue_pool)
        game_state["solution_clue"] = solution_clue
        clue_locations[game_state["bishop_last_location"]] = game_state["solution_clue"]
    # Helper to assign alibi weight
    def alibi_weight(trait, motive, alibi_text):
        weight = 2  # Start at 2 (neutral)
        # Traits that make alibis less credible
        if trait in ["Nervous", "Fanatical", "Secretive"]:
            weight -= 1
        if trait in ["Charming", "Stoic"]:
            weight += 1
        # Motives that make alibis less credible
        if motive in ["Revenge", "Fanaticism", "Desperation", "Obsession"]:
            weight -= 1
        if motive in ["Loyalty", "Ambition", "Zealotry"]:
            weight += 1
        # Alibi text cues
        if "alone" in alibi_text or "praying" in alibi_text or "midnight" in alibi_text:
            weight -= 1
        if "guests" in alibi_text or "repairing" in alibi_text or "reading" in alibi_text:
            weight += 1
        # Clamp between 1 and 4
        return max(1, min(4, weight))

    # 3. Assign the culprit
    culprit_template = random.choice(suspect_templates)
    culprit = {
        "name": culprit_template["name"],
        "motive": solution_motive["short"],
        "motive_long": solution_motive["long"],
        "alibi": solution_alibi,
        "trait": culprit_template["trait"],
        "gender": culprit_template["gender"],
        "opportunity": True,
        "is_murderer": True
    }

    # 4. Assign other suspects with mismatched elements
    other_suspects = []
    used_names = {culprit["name"]}
    for i in range(3):
        name = random.choice([s["name"] for s in suspect_templates if s["name"] not in used_names])
        used_names.add(name)
        # Pick a motive and alibi from other pools or mismatched
        other_idx = (solution_idx + i + 1) % 4
        other_motive = random.choice(motive_pools[other_idx])["short"]
        other_alibi = random.choice(alibi_pools[other_idx])
        other_suspects.append({
            "name": name,
            "motive": other_motive,
            "alibi": other_alibi,
            "opportunity": False,
            "is_murderer": False
        })

    # 5. Save to game_state
    game_state["suspects"] = [culprit] + other_suspects
    game_state["clue_pool"] = clue_pool
    game_state["clue_motives"] = clue_motives
    game_state["solution_motive"] = solution_motive["short"]
    game_state["solution_alibi"] = solution_alibi
    game_state["murderer"] = culprit["name"]

    # Ensure every suspect has a relationship field
    for suspect in game_state.get("suspects", []):
        if "relationship" not in suspect:
            suspect["relationship"] = random.choice(relationship_responses)

def character_creation():
    global previous_menu_function
    previous_menu_function = character_creation
    clear()
    delay_print("Before the hunt begins... who are you? The fog of the past clings to you, refusing to part until you define yourself.")
    game_state["name"] = get_player_name()

    print("\nChoose your background:")
    print("[1] Theologian – +2 Faith")
    print("[2] Occultist – +2 Sanity")
    print("[3] Detective – +2 Perception")
    print("[4] Priest – +1 Faith, +1 Sanity")
    print("[5] Random character (auto-assign all stats)")
    print("[6] Manual stat entry (debug)")

    bg = input("> ")
    auto_assign = False
    manual_entry = False

    if bg == "1" or bg.lower() == "theologian":
        game_state["background"] = "Theologian"
        game_state["faith"] += 2
    elif bg == "2" or bg.lower() == "occultist":
        game_state["background"] = "Occultist"
        game_state["sanity"] += 2
    elif bg == "3" or bg.lower() == "detective":
        game_state["background"] = "Detective"
        game_state["perception"] += 2
    elif bg == "4" or bg.lower() == "priest":
        game_state["background"] = "Priest"
        game_state["faith"] += 1
        game_state["sanity"] += 1
    elif bg == "5" or bg.lower() == "random":
        auto_assign = True
        game_state["background"] = random.choice(["Theologian", "Occultist", "Detective", "Priest"])
        if game_state["background"] == "Theologian":
            game_state["faith"] += 2
        elif game_state["background"] == "Occultist":
            game_state["sanity"] += 2
        elif game_state["background"] == "Detective":
            game_state["perception"] += 2
        elif game_state["background"] == "Priest":
            game_state["faith"] += 1
            game_state["sanity"] += 1
        delay_print(f"Random background assigned: {game_state['background']}")
        game_state["gender"] = random.choice(["Male", "Female", "Nonbinary"])
        delay_print(f"Random gender assigned: {game_state['gender']}")
    elif bg == "6" or bg.lower() == "manual":
        manual_entry = True
        game_state["background"] = "Debug"
    else:
        character_creation()
        return

    background_descriptions = {
    "Theologian": f"{YELLOW}A scholar of faith and doctrine, versed in the mysteries of the divine and the hidden heresies of the world. Your insight into religious matters is unmatched, and your presence brings comfort—or unease—to those around you.{RESET}",
    "Occultist": f"{YELLOW}A seeker of forbidden knowledge, drawn to the shadows where others fear to tread. You have glimpsed truths that strain the mind, and your sanity is both your shield and your burden.{RESET}",
    "Detective": f"{YELLOW}A master of observation and deduction, trained to see what others overlook. Your keen perception cuts through deception, and your logical mind is your greatest weapon.{RESET}",
    "Priest": f"{YELLOW}A shepherd of souls, balancing compassion with conviction. Your faith is a bulwark against darkness, and your words can inspire hope or dread in equal measure.{RESET}"
}
    desc = background_descriptions.get(game_state["background"])
    if desc:
        delay_print(f"\n{desc}\n")
        
    # Only ask for gender if not auto-assign
    if not auto_assign:
        print("\nChoose your gender:")
        print("[1] Male")
        print("[2] Female")
        print("[3] Nonbinary")
        while True:
            gender_choice = input("> ").strip()
            if gender_choice == "1":
                game_state["gender"] = "Male"
                break
            elif gender_choice == "2":
                game_state["gender"] = "Female"
                break
            elif gender_choice == "3":
                game_state["gender"] = "Nonbinary"
                break
            else:
                print("Please select 1, 2, or 3.")

    stats_list = ["faith", "sanity", "perception", "strength", "stamina", "agility", "comeliness"]

    if manual_entry:
        print("\nEnter each stat value (between 3 and 18):")
        for stat in stats_list:
            while True:
                try:
                    val = int(input(f"{stat.capitalize()}: "))
                    if 3 <= val <= 18:
                        game_state[stat] = val
                        break
                    else:
                        print("Value must be between 3 and 18.")
                except ValueError:
                    print("Please enter a valid number.")
        print("\nManual stat entry complete.")
        for stat in stats_list:
            print(f"{stat.capitalize()}: {game_state[stat]}")
        wait_for_space()
    elif auto_assign:
        # Randomly distribute 6 points among stats (max 18 per stat)
        stat_points = 6
        for stat in stats_list:
            base = 8 + random.randint(1, 4)
            game_state[stat] = base
        for _ in range(stat_points):
            available = [s for s in stats_list if game_state[s] < 18]
            if not available:
                break
            chosen_stat = random.choice(available)
            game_state[chosen_stat] += 1
        print("\nRandomly assigned attributes:")
        for stat in stats_list:
            print(f"{stat.capitalize()}: {game_state[stat]}")
        wait_for_space()
    else:
        # Point-buy: 6 points to distribute, min 3, max 18 per stat
        print("\nDistribute 6 points among your stats (base stats are randomly generated between 8 and 12, maximum 18 per stat).")
        stat_points = 6
        # Set base stats (after background bonus)
        for stat in stats_list:
            base = 8 + random.randint(1, 4)
            if game_state[stat] < base:
                game_state[stat] = base
        skill_map = {str(i+1): stat for i, stat in enumerate(stats_list)}
        while stat_points > 0:
            print("\nCurrent stats:")
            for i, stat in enumerate(stats_list):
                print(f"[{i+1}] {stat.capitalize()}: {game_state[stat]}")
            print(f"Points remaining: {stat_points}")
            chosen = input("Which stat do you want to increase? (name or number): ").strip().lower()
            if chosen in skill_map:
                chosen_stat = skill_map[chosen]
            elif chosen in stats_list:
                chosen_stat = chosen
            else:
                print("Invalid stat. Try again.")
                continue
            max_add = min(18 - game_state[chosen_stat], stat_points)
            if max_add == 0:
                print(f"{chosen_stat.capitalize()} is already at maximum.")
                continue
            try:
                val = int(input(f"How many points to add to {chosen_stat.capitalize()}? (1 to {max_add}): "))
                if 1 <= val <= max_add:
                    game_state[chosen_stat] += val
                    stat_points -= val
                else:
                    print(f"Value must be between 1 and {max_add}.")
            except ValueError:
                print("Please enter a valid number.")
        print("\nFinal attributes:")
        for stat in stats_list:
            print(f"{stat.capitalize()}: {game_state[stat]}")
        wait_for_space()

    game_state["inventory"].append("Envelope from the Commissioner")

    # Give player one random artifact as a clue at game start
    starting_artifact = random.choice(artifact_pool)
    game_state["inventory"].append(starting_artifact["name"])
    clue_text = f"You begin with a mysterious item: {starting_artifact['name']}. {starting_artifact['desc']}"
    game_state["clues"].append(clue_text)
    game_state["journal"].append(f"CLUE FOUND at start: {clue_text}")

    associate_culprit_and_pools()

    initialize_suspects()
    # Mark starting location visited at (0,0)
    game_state["visited_locations"] = {(0, 0): "Foyer"}
    game_state["location"] = "Foyer"
    game_state["position"] = (0, MAP_MAX)


    generate_structured_map() # Generate the structured map

    # After generate_structured_map() in character_creation()
    bishop_room = game_state.get("bishop_last_location")
    if bishop_room and bishop_room not in game_state["visited_locations"].values():
        # Find an empty room slot
        empty_positions = [pos for pos, room in game_state["visited_locations"].items() if room == "Empty Room"]
        if empty_positions:
            chosen_pos = random.choice(empty_positions)
            game_state["visited_locations"][chosen_pos] = bishop_room
        else:
            # If no empty rooms, overwrite a random non-key room
            non_key_positions = [pos for pos, room in game_state["visited_locations"].items()
                                if room not in ("Foyer", "Main Hall", "Kitchen")]
            if non_key_positions:
                chosen_pos = random.choice(non_key_positions)
                game_state["visited_locations"][chosen_pos] = bishop_room

    auto_generate_walls()
    # auto_generate_walls_and_doors() # Generate walls and locked doors
    # seal_random_region_with_locked_door()
    # create_random_locked_region()  # Create a random locked region
    # lock_all_doors()

    # print(f"Walls generated: {len(game_state['walls'])}")
    # print(f"Locked doors generated: {len(game_state['locked_doors'])}") # Debugging line

    delay_print(f"Welcome, {game_state['name']} the {game_state['background']}. The hour is late, and the shadows grow bold.")
    wait_for_space()

    assign_clues_to_rooms()
    assign_potions_to_rooms()
    assign_elder_sign_to_room()
    assign_artifacts_to_rooms()  # Assign artifacts to rooms
    place_silver_key()

    # Begin the first case
    start_first_case()

clear()
print("\nChoose your difficulty:")
print("[1] Easy")
print("[2] Hard")
while True:
    diff = input("> ").strip()
    if diff == "1":
        game_state["difficulty"] = "easy"
        game_state["required_clues"] = 2
        game_state["suspect_tolerance"] = 9
        game_state["min_suspects_interrogated"] = 3
        game_state["show_suspicion_hints"] = True  # Hints ON by default for easy mode
        print("\nEasy Mode Selected:")
        delay_print(" - Minimum clues required to solve the case: 2")
        delay_print(" - Minimum suspects interrogated: 3")
        delay_print(" - Suspects tolerate more questions before becoming hostile")
        delay_print(" - Monstrosities move at half speed (every other turn) during chase")
        delay_print(" - Suspicion hints are ON by default (can be toggled in the journal)")
        wait_for_space("Press SPACE to continue.")
        break
    elif diff == "2":
        game_state["difficulty"] = "hard"
        game_state["required_clues"] = 8
        game_state["suspect_tolerance"] = 4
        game_state["min_suspects_interrogated"] = 5
        game_state["show_suspicion_hints"] = False  # Hints OFF by default for hard mode
        print("\nHard Mode Selected:")
        delay_print(" - Minimum clues required to solve the case: 8")
        delay_print(" - Minimum suspects interrogated: 5")
        delay_print(" - Suspects are easily angered by repeated questioning")
        delay_print(" - Monstrosities move at full speed (every turn) during chase")
        delay_print(" - Suspicion hints are OFF by default (can be toggled in the journal)")
        wait_for_space("Press SPACE to continue.")
        break
    else:
        delay_print("Please select [1] or [2].")
    
def start_first_case():
    global previous_menu_function
    previous_menu_function = start_first_case
    game_state["quests"].append("Investigate the disappearance of the Bishop.")

    # Announce Bishop's last known location and time at the start of the case
    last_loc = game_state.get("bishop_last_location", "an unknown location")
    last_time = game_state.get("bishop_last_time", "an unknown time")
    # delay_print(f"The Bishop was last seen in the {last_loc} at {last_time}.")

    describe_room()
    
print("\nWould you like to:")
print("[1] Start a new game")
print("[2] Load a saved game")
while True:
    next_choice = input("> ").strip()
    if next_choice == "1":
        title_screen()
        break
    elif next_choice == "2":
        load_game()
        break
    else:
        delay_print("Please select [1] or [2].")
        
# --- Main Menu ---
title_screen()

