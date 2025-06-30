# Persuasion: Victorian Roguelike Investigation RPG Game
# Core Game Script

import os
import time
import random
import json
import sys
import threading
import msvcrt  # For Windows key detection

# --- Global State ---

MAP_MIN = -8
MAP_MAX = 7
MAP_SIZE = MAP_MAX - MAP_MIN + 1  # 16
MAP_CENTER = (MAP_SIZE // 2) - 1  # Center of the map grid

DIRECTIONS = {
    "n": (0, -1),
    "s": (0, 1),
    "e": (1, 0),
    "w": (-1, 0)
}
previous_menu_function = None

valid_directions = {"n", "s", "e", "w"}

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
    "clues": [],
    "journal": [],
    "turns": 0,
    "visited_locations": {},
    "position": (0, 0),
    "score": 0,
    "score_log": [],
#    "walls": set(),  # Each wall is ((x1, y1), (x2, y2))
}

game_state["persuasion_active"] = False
game_state["persuasion_rounds"] = 0
game_state["persuasion_uses"] = 0
game_state["persuasion_targets"] = set()

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



room_templates = room_templates = {
    "Foyer": [
        "The grand entry is dimly lit. Dust motes float through the silence. You hear footsteps upstairs, then silence again."
    ],
    "Main Hall": [
        "A vast corridor stretches in both directions, portraits watching from above. The chandeliers sway slightly despite the still air. Something unseen seems to pace behind the walls."
    ],
    "Library": [
        "Bookshelves loom, many tomes written in languages you don’t recognize. A shattered inkwell and a missing journal page hint at a struggle. A cold draft whispers through the gaps in the shelves."
    ],
    "Study": [
        "The desk is overturned. Scorched fragments of parchment litter the floor. A painting swings ajar, revealing a keyhole behind it."
    ],
    "Cellar": [
        "Wine racks cover the walls, but the air smells of rot, not spirits. Chains and dried herbs hang together—ritual or restraint? The earth floor squelches underfoot."
    ],
    "Parlor": [
        "A cracked mirror leans against the fireplace, reflecting nothing. A half-burnt letter lies beside an empty tea cup. The fire is warm, but no logs burn."
    ],
    "Chapel": [
        "Faded icons peer down from peeling walls. A candle flickers beneath a statue whose face has been scratched out. Something shuffles in the pews when you aren’t looking."
    ],
    "Conservatory": [
        "Glass walls reveal the fog beyond, pressing inward. Overgrown vines have cracked through the tiles, and something glistens in the soil. A harp in the corner is missing a string."
    ],
    "Attic": [
        "Dust coats everything in thick fur. Broken dolls and empty birdcages fill the room. You hear a child’s whisper, but the room is empty."
    ],
    "Laboratory": [
        "Vials and beakers line scorched tables. Something green bubbles inside a jar marked 'DO NOT OPEN'. Scratches on the wall form incomplete equations."
    ],
    "Torture Chamber": [
        "Instruments of pain are meticulously arranged, gleaming despite the filth. The walls are soundproofed with old cloth. A metal mask smiles eternally from the center table."
    ],
    "Kitchen": [
        "The air is thick with the scent of spoiled meat. Pots boil on their own, unattended. A bloodied apron hangs from a hook like a ghost’s robe."
    ],
    "Smoking Room": [
        "The scent of old tobacco lingers. Chairs face an empty hearth, their indentations fresh. A decanter trembles when you enter."
    ],
    "Ballroom": [
        "Cobwebs dance where dancers once did. A phonograph crackles but spins no disc. In the moonlight, footprints appear on the dust-polished floor."
    ],
    "East Bedchamber": [
        "The bed is made with surgical precision. A single rose lies across the pillow, already wilting. The window is nailed shut."
    ],
    "West Bedchamber": [
        "Curtains flutter though no window is open. The mirror is draped in black cloth. Something breathes beneath the floorboards."
    ],
    "Servant's Quarters": [
        "Bunks are made but still warm. A diary lies open on the floor, pages torn. You hear humming from the hallway, though no one approaches."
    ],
    "Dining Hall": [
        "An enormous table is set for a feast no one attends. Mold creeps along the fine china. A chair at the head is pulled back—waiting."
    ],
    "Gallery": [
        "Portraits line the walls, but their faces have been scraped off. A crimson smear crosses the floor and disappears behind a velvet curtain. You sense the paintings still watch."
    ],
    "Atrium": [
        "Twilight filters through the stained-glass ceiling. Ivy curls around marble statues with hollow eyes. Water drips from somewhere unseen."
    ],
    "Solarium": [
        "Rays of moonlight pour through broken panes. Potted plants have wilted into twisted shapes. A teacup rests beside a still-warm chair."
    ],
    "Observatory": [
        "A great telescope points at nothing. Charts and star maps are strewn in disarray. Something scratched 'They are already here' into the oak railing."
    ],
    "Garden": [
        "Overgrown paths wind through headless statuary. Roses bloom black in the moonlight. A rusted gate creaks open on its own."
    ],
    "Horse Stable": [
        "The stables smell of hay and rust. One stall door swings slowly, creaking on unseen hinges. Hoof prints lead out but never return."
    ],
    "Well House": [
        "The well is sealed with iron chains. Scratches climb the stone from inside. A chill creeps up your spine, though no wind blows."
    ]
}

suspect_templates = [
    {"name": "Miss Vexley", "trait": "Nervous", "alibi": "Claims she was in the chapel praying.", "motive": "Jealousy"},
    {"name": "Dr. Lorn", "trait": "Stoic", "alibi": "Was tending the fire in the lounge.", "motive": "Revenge"},
    {"name": "Ulric", "trait": "Fanatical", "alibi": "Says he heard voices in the cellar.", "motive": "Fanaticism"},
    {"name": "Colonel Catsup", "trait": "Charming", "alibi": "Claims he was entertaining guests all night.", "motive": "Desperation"},
    {"name": "Lady Ashcroft", "trait": "Secretive", "alibi": "Insists she was alone in the solarium, reading.", "motive": "Forbidden Love"},
    {"name": "Mr. Blackwood", "trait": "Cynical", "alibi": "Claims he was repairing a broken window in the attic.", "motive": "Ambition"}
]

# def generate_walls():
#     wall_chance = 0.18  # 18% chance for a wall between any two adjacent rooms
#     for x in range(MAP_MIN, MAP_MAX + 1):
#         for y in range(MAP_MIN, MAP_MAX + 1):
#             for dx, dy in [(0, 1), (1, 0)]:  # Only need to check E and S to avoid duplicates
#                 nx, ny = x + dx, y + dy
#                 if MAP_MIN <= nx <= MAP_MAX and MAP_MIN <= ny <= MAP_MAX:
#                     if random.random() < wall_chance:
#                         # Store both directions for easy lookup
#                         game_state["walls"].add(((x, y), (nx, ny)))
#                         game_state["walls"].add(((nx, ny), (x, y)))

def roll_fudge(num_dice=4): # FUDGE combat dice system
    return sum(random.choice([-1, 0, 1]) for _ in range(num_dice))

def generate_passages():
    """Generate a procedural map where each room has at most 4 exits, and all passages are consistent."""
    passages = {}
    for x in range(MAP_MIN, MAP_MAX + 1):
        for y in range(MAP_MIN, MAP_MAX + 1):
            pos = (x, y)
            possible_dirs = []
            for dir_name, (dx, dy) in DIRECTIONS.items():
                nx, ny = x + dx, y + dy
                if MAP_MIN <= nx <= MAP_MAX and MAP_MIN <= ny <= MAP_MAX:
                    possible_dirs.append(dir_name)
            # Limit to 4 random directions per room
            num_exits = min(len(possible_dirs), random.randint(2, 3))
            if num_exits > 0:
                exits = random.sample(possible_dirs, num_exits)
            else:
                exits = []
            passages[pos] = set(exits)

    # Make passages consistent (if A->B, then B->A), but do not exceed 4 exits per room
    for (x, y), dirs in passages.items():
        for dir_name in list(dirs):
            dx, dy = DIRECTIONS[dir_name]
            nx, ny = x + dx, y + dy
            rev_dir = None
            for d, (ddx, ddy) in DIRECTIONS.items():
                if (ddx, ddy) == (-dx, -dy):
                    rev_dir = d
                    break
            # Only add reverse direction if it doesn't exceed 4 exits
            if rev_dir:
                neighbor_exits = passages.setdefault((nx, ny), set())
                if len(neighbor_exits) < 4:
                    neighbor_exits.add(rev_dir)
                else:
                    # If neighbor already has 4 exits, remove this exit from the original room to maintain consistency
                    passages[(x, y)].discard(dir_name)
    game_state["passages"] = passages

def auto_generate_walls_and_doors():
    # Clear any existing walls/doors
    game_state["walls"] = set()
    game_state["locked_doors"] = set()
    for (x, y), exits in game_state["passages"].items():
        for dir_name, (dx, dy) in DIRECTIONS.items():
            nx, ny = x + dx, y + dy
            neighbor = (nx, ny)
            # Only check cardinal directions for walls/doors
            if dir_name in {"n", "s", "e", "w"} and MAP_MIN <= nx <= MAP_MAX and MAP_MIN <= ny <= MAP_MAX:
                # If there is NO passage in this direction, add a wall
                if dir_name not in exits:
                    # Example: you could randomly make some of these locked doors
                    if random.random() < 0.15:
                        game_state["locked_doors"].add(((x, y), neighbor))
                        game_state["locked_doors"].add((neighbor, (x, y)))
                    else:
                        game_state["walls"].add(((x, y), neighbor))
                        game_state["walls"].add((neighbor, (x, y)))

def initialize_suspects():
    game_state["suspects"] = random.sample(suspect_templates, 4)
    player_pos = (0, 0)
    MAP_MIN = -8
    MAP_MAX = 7
    # Generate possible positions within 2-4 tiles of player and inside bounds
    possible_positions = []
    for dx in range(-4, 5):
        for dy in range(-4, 5):
            dist = abs(dx) + abs(dy)
            pos = (player_pos[0] + dx, player_pos[1] + dy)
            if 2 <= dist <= 4 and MAP_MIN <= pos[0] <= MAP_MAX and MAP_MIN <= pos[1] <= MAP_MAX and pos != player_pos:
                possible_positions.append(pos)
    chosen_positions = random.sample(possible_positions, 4)
    for suspect, pos in zip(game_state["suspects"], chosen_positions):
        suspect["position"] = pos
        suspect["wait_turns"] = 0
        # Assign random stats for combat
        suspect["strength"] = random.randint(7, 13)
        suspect["stamina"] = random.randint(7, 13)
        suspect["agility"] = random.randint(7, 13)

    # --- Assign murderer at random ---
    murderer = random.choice(game_state["suspects"])
    for suspect in game_state["suspects"]:
        suspect["is_murderer"] = (suspect is murderer)
    game_state["murderer"] = murderer["name"]

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

clue_pool = [
    "A silver pendant etched with tentacles.",
    "Blood-stained prayer book.",
    "Footprints leading to a sealed hatch.",
    "A coded diary mentioning a 'Summoning'.",
    "An empty ritual circle drawn in chalk.",
    "A page torn from a forbidden tome.",
    "A torn letter from the Bishop addressed to Lady Ashcroft.",
    "A pawn ticket for a golden chalice, issued the day before the Bishop vanished.",
    "A threatening note warning the Bishop to abandon his 'awakening.'"
]

clue_motives = {
    "A silver pendant etched with tentacles.": "Fanaticism",
    "Blood-stained prayer book.": "Fanaticism",
    "Footprints leading to a sealed hatch.": "Ambition",
    "A coded diary mentioning a 'Summoning'.": "Revenge",
    "An empty ritual circle drawn in chalk.": "Fanaticism",
    "A page torn from a forbidden tome.": "Blackmail",
    "A torn letter from the Bishop addressed to Lady Ashcroft.": "Forbidden Love",
    "A pawn ticket for a golden chalice, issued the day before the Bishop vanished.": "Desperation",
    "A threatening note warning the Bishop to abandon his 'awakening.'": "Fear"
}

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
        "name": "Silver Crucifix",
        "desc": "An ornate cross, tarnished with age. It seems to pulse with a faint warmth.",
        "effect": "faith",
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
    }
]

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

# Potions to be scattered
potion_pool = [
    {"name": "Potion of Strength", "effect": "strength", "amount": 2, "desc": "A crimson tonic that invigorates the muscles."},
    {"name": "Potion of Stamina", "effect": "stamina", "amount": 2, "desc": "A cloudy elixir that fortifies your endurance."}
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
    for clue, room in zip(clue_pool, possible_rooms):
        clue_locations[room] = clue

def assign_artifacts_to_rooms():
    possible_rooms = [r for r in room_templates.keys() if r != "Foyer"]
    random.shuffle(possible_rooms)
    # Randomly select 6 unique artifacts for this playthrough
    available_artifacts = random.sample(artifact_pool, 6)
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
    """Prints text slowly, but finishes instantly if the user presses space."""
    import msvcrt  # Windows only; for cross-platform, use 'getch' from 'getch' package
    import threading
    
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

    for c in s:
        if stop[0]:
            print(s[s.index(c):], end='', flush=True)
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

def save_game():
    try:
        game_state_copy = game_state.copy()

        # Convert tuple keys in visited_locations to strings for JSON
        visited_serializable = {str(k): v for k, v in game_state["visited_locations"].items()}
        game_state_copy["visited_locations"] = visited_serializable

        # Convert tuple keys in room_flavor_used to strings for JSON
        if "room_flavor_used" in game_state:
            flavor_serializable = {str(k): v for k, v in game_state["room_flavor_used"].items()}
            game_state_copy["room_flavor_used"] = flavor_serializable

        # Convert sets to lists for JSON serialization
        for key in ["breadcrumbs", "persuasion_targets", "walls", "locked_doors"]:
            if key in game_state_copy and isinstance(game_state_copy[key], set):
                # Convert tuples inside the set to lists for JSON
                game_state_copy[key] = [list(item) for item in game_state_copy[key]]

        # Convert passages dict of sets to dict of lists
        if "passages" in game_state_copy:
            game_state_copy["passages"] = {str(k): list(v) for k, v in game_state_copy["passages"].items()}

        with open("savegame.json", "w") as f:
            json.dump(game_state_copy, f)

        print("Game saved.")
    except Exception as e:
        print(f"Error saving game: {e}")
    input("Press Enter to continue.")

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

            # Ensure breadcrumbs exists and is a set of tuples
            if "breadcrumbs" not in loaded_state or not isinstance(loaded_state["breadcrumbs"], set):
                loaded_state["breadcrumbs"] = set()
            else:
                loaded_state["breadcrumbs"] = set(tuple(item) for item in loaded_state["breadcrumbs"])

            # Convert position from list to tuple
            if "position" in loaded_state and isinstance(loaded_state["position"], list):
                loaded_state["position"] = tuple(loaded_state["position"])

            game_state.update(loaded_state)

            print("Game loaded.")
            input("Press Enter to continue.")

            if game_state.get("location"):
                previous_menu_function = describe_room
                describe_room()
            else:
                title_screen()
        else:
            print("No save file found.")
            input("\nPress Enter to return.")
            title_screen()
    except Exception as e:
        print(f"Error loading game: {e}")
        input("\nPress Enter to return.")
        title_screen()
        
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

    # Limit movement to within 16x16 grid
    if not (MAP_MIN <= new_x <= MAP_MAX and MAP_MIN <= new_y <= MAP_MAX):
        delay_print("You sense an unnatural barrier. The manor does not extend further in that direction.")
        input("Press Enter to continue.")
        describe_room()
        return

    allowed_dirs = game_state["passages"].get((x, y), set())
    if direction not in allowed_dirs:
        delay_print("A wall or obstacle blocks your way. You cannot go that direction.")
        input("Press Enter to continue.")
        describe_room()
        return

    # --- NEW: Block movement through walls and locked doors ---
    walls = game_state.get("walls", set())
    locked_doors = game_state.get("locked_doors", set())
    pos = (x, y)
    new_pos = (new_x, new_y)
    if ((pos, new_pos) in walls) or ((pos, new_pos) in locked_doors):
        delay_print("A wall or locked door blocks your way.")
        input("Press Enter to continue.")
        describe_room()
        return

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

    # Check for suspects in the same room
    suspects_here = [
        s for s in game_state["suspects"]
        if s.get("position") == game_state["position"]
    ]
    if suspects_here:
        names = ', '.join(s["name"] for s in suspects_here)
        delay_print(f"You see someone here: {names}")

    if show_room:
        input("Press Enter to enter the new room.")
        game_state["score"] -= 1  # Encourage efficiency
        describe_room()

def move_suspects():
    """Move each suspect to a random adjacent visited room, or let them stand still for 1-2 turns."""
    for suspect in game_state["suspects"]:
        # Initialize suspect position if not set (start at random valid position)
        if "position" not in suspect or suspect["position"] is None:
            while True:
                pos = (random.randint(MAP_MIN, MAP_MAX), random.randint(MAP_MIN, MAP_MAX))
                if pos != game_state["position"]:
                    suspect["position"] = pos
                    suspect["wait_turns"] = 0
                    break

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
        adjacent = [
            (x + dx, y + dy)
            for dx, dy in [
                (0, 1), (0, -1), (1, 0), (-1, 0),  # N, S, E, W
                (1, 1), (-1, 1), (1, -1), (-1, -1) # NE, NW, SE, SW
            ]
            if MAP_MIN <= x + dx <= MAP_MAX and MAP_MIN <= y + dy <= MAP_MAX
        ]


        # Move to a random adjacent visited room if possible
        if adjacent:
            suspect["position"] = random.choice(adjacent)
       #    print(f"[DEBUG] {suspect['name']} moved to {suspect['position']}") # Debugging line to track suspect movement
        # else: no move (surrounded by unvisited rooms or walls)

def show_stats():
    clear()
    delay_print(f"Name: {game_state['name']}")
    delay_print(f"Gender: {game_state['gender']}")
    delay_print(f"Background: {game_state['background']}")
    for stat in ["faith", "sanity", "perception", "strength", "stamina", "agility", "comeliness"]:
        delay_print(f"{stat.capitalize()}: {game_state[stat]}")
    input("\nPress Enter to return.")

    if previous_menu_function:
        previous_menu_function()
    else:
        title_screen()

def show_journal():
    clear()
    delay_print("Journal Entries:")
    clues = [entry for entry in game_state["journal"] if entry.startswith("CLUE FOUND")]
    artifacts = [entry for entry in game_state["journal"] if entry.startswith("ARTIFACT FOUND")]
    responses = [entry for entry in game_state["journal"] if not entry.startswith("CLUE FOUND") and not entry.startswith("ARTIFACT FOUND")]

    if clues:
        delay_print("\n--- Clues Discovered ---")
        for entry in clues:
            delay_print(entry)
    if artifacts:
        delay_print("\n--- Artifacts Discovered ---")
        for entry in artifacts:
            delay_print(entry)
    if responses:
        delay_print("\n--- Suspect Responses ---")
        for entry in responses:
            delay_print(entry)
    if not clues and not artifacts and not responses:
        delay_print("Your journal is empty.")
    input("\nPress Enter to return.")
    if previous_menu_function:
        previous_menu_function()
    else:
        title_screen()

def show_quests():
    clear()
    delay_print("Active Quests:")
    if game_state["quests"]:
        for quest in game_state["quests"]:
            delay_print(f"- {quest}")
    else:
        delay_print("No active quests.")
    input("\nPress Enter to return.")

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
        print("[6] Interrogate suspect")
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
            input("Press Enter to continue.")
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
        describe_room()
    elif user_input == "9" or user_input == "quit":
        title_screen()
    else:
        handle_input(user_input, describe_room)


def show_map():
    clear()
    location = game_state["location"]
    pos = game_state["position"]
    print(f"Current Location: {location} at {pos}")
    look_around(pause=False)  # Show short description under current location

    delay_print("\nMap:")

    # Only ask for fog of war toggle once per session
    if "fog_of_war" not in game_state:
        choice = input("Show only visited rooms/walls on map (fog of war)? (Y/N): ").strip().lower()
        game_state["fog_of_war"] = (choice == "y")

    show_npcs = game_state.get("can_see_npcs", False)
    render_map(show_npcs, fog_of_war=game_state.get("fog_of_war", False))

    print("\nType a direction (N/S/E/W) and press Enter to move, or just press Enter to return to the action menu.")

    user_input = input("> ").strip().lower()
    if user_input == "":
        if previous_menu_function:
            previous_menu_function()
        else:
            describe_room()
        return
    elif user_input in valid_directions:
        move_to_new_room(user_input, show_room=False)
        show_map()  # Show updated map after move
    else:
        delay_print("Unknown command. Use N/S/E/W or Enter to return.")
        show_map()

def render_map(show_npcs=False, fog_of_war=False):
    grid_size = 11
    half = grid_size // 2
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

    GREEN = "\033[32m"
    GREY = "\033[90m"
    WHITE = "\033[97m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    RESET = "\033[0m"

    sanity = game_state["sanity"]
    breadcrumbs = set(game_state.get("breadcrumbs", []))
    breadcrumbs.add(game_state["position"])

    legend = {}
    for room in set(game_state["visited_locations"].values()):
        letter = room[0].upper()
        if letter not in legend:
            legend[letter] = room
    legend_lines = [f"{letter} = {room}" for letter, room in sorted(legend.items())]
    legend_lines += [""] * (grid_size - len(legend_lines))

    # Ensure walls and locked_doors exist
    walls = game_state.get("walls", set())
    locked_doors = game_state.get("locked_doors", set())

    visited = set(game_state["visited_locations"].keys())

    # Print map with vertical and horizontal walls/doors
    for row_idx, y in enumerate(range(py - half, py + half + 1)):
        row = ""
        for x in range(px - half, px + half + 1):
            pos = (x, y)
            # --- FOG OF WAR: Only show visited rooms ---
            if fog_of_war and pos not in visited:
                row += "   "
                row += SPACE
                continue

            char = " ◉ "
            color = GREEN
            if pos == (px, py):
                char = " @ "
                color = CYAN
                if sanity < 4 and random.random() < 0.5:
                    char = " # "
            elif show_npcs and pos in suspect_positions:
                char = " " + "".join(suspect_positions[pos]) + " "
                color = YELLOW
                if sanity < 4 and random.random() < 0.4:
                    char = " ? "
            elif pos in game_state["visited_locations"]:
                loc = game_state["visited_locations"][pos]
                char = f" {loc[0]} "
                color = YELLOW
                if sanity < 4 and random.random() < 0.2:
                    char = random.choice([" ~ ", " * ", " % ", " $ "])
            elif sanity < 4 and random.random() < 0.1:
                char = random.choice([" ! ", " ? ", " # "])
                color = GREEN
            row += f"{color}{char}{RESET}"

            # Draw vertical wall/door to the right of this cell, only if both cells are visited (for fog of war)
            right_pos = (x + 1, y)
            if fog_of_war and (pos not in visited or right_pos not in visited):
                row += SPACE
            elif ((pos, right_pos) in locked_doors):
                row += VERT_DOOR
            elif ((pos, right_pos) in walls):
                row += VERT_WALL
            else:
                row += SPACE
        print(f"{row}   {legend_lines[row_idx]}")

        # Draw horizontal walls/doors below this row (unless last row)
        if row_idx < grid_size - 1:
            wall_row = ""
            for x in range(px - half, px + half + 1):
                pos = (x, y)
                below_pos = (x, y + 1)
                # Only show horizontal walls/doors if both cells are visited (for fog of war)
                if fog_of_war and (pos not in visited or below_pos not in visited):
                    wall_row += SPACE * 3
                elif ((pos, below_pos) in locked_doors):
                    wall_row += HORZ_DOOR * 3
                elif ((pos, below_pos) in walls):
                    wall_row += HORZ_WALL * 3
                else:
                    wall_row += SPACE * 3
                # Add a space or wall/door between cells
                right_pos = (x + 1, y)
                if fog_of_war and (pos not in visited or right_pos not in visited):
                    wall_row += SPACE
                elif ((pos, right_pos) in locked_doors):
                    wall_row += VERT_DOOR
                elif ((pos, right_pos) in walls):
                    wall_row += VERT_WALL
                else:
                    wall_row += SPACE
            print(f"{wall_row}")

    # Add to breadcrumbs after rendering
    if "breadcrumbs" not in game_state:
        game_state["breadcrumbs"] = set()
    game_state["breadcrumbs"].add(game_state["position"])

    # Whisper-like message
    if sanity < 4 and random.random() < 0.5:
        whispers = [
            "You hear your name in the walls.",
            "Something moves just out of sight.",
            "The rooms are not where you left them.",
            "Did you see that shadow move?",
            "A voice whispers: 'Leave...'"
        ]
        delay_print(random.choice(whispers))

    # --- Show available exits at the bottom of the map ---
    x, y = game_state["position"]
    available_exits = [d.upper() for d in game_state["passages"].get((x, y), set())]
    if available_exits:
        print(f"\nAvailable exits: {', '.join(available_exits)}")
    else:
        print("\nThere are no available exits from this room.")
    
def show_inventory():
    clear()
    delay_print("Inventory:")
    if game_state["inventory"]:
        for idx, item in enumerate(game_state["inventory"], 1):
            print(f"[{idx}] {distort_text(item, game_state['sanity'])}")
        print(f"[{len(game_state['inventory'])+1}] Use an item")
        print(f"[{len(game_state['inventory'])+2}] Return")
        choice = input("\nSelect an item to inspect, use, or return: ")

        # Handle case where user just presses Enter
        if choice.strip() == "":
            show_inventory()
            return

        if choice.isdigit():
            idx = int(choice) - 1
            if idx == len(game_state["inventory"]):  # Use an item
                use_item()
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
                    input("\nPress Enter to return.")

                elif item == "Elder Sign":
                    delay_print(
                        "Elder Sign: A strange, star-shaped talisman carved from ancient stone. "
                        "Its lines twist in impossible angles, and the air around it feels subtly warped. "
                        "Legends say it wards off the Old Ones and brings strength to the faithful."
                    )
                    input("\nPress Enter to return.")

                elif item == "Scrying Lens":
                    delay_print(
                        "Scrying Lens: A cloudy crystal lens set in tarnished silver. When held to the eye, it reveals the hidden movements of those who dwell within the manor."
                    )
                    input("\nPress Enter to return.")

                else:
                    delay_print(f"You inspect the {item}.")
                    input("\nPress Enter to return.")
                show_inventory()
            elif idx == len(game_state["inventory"]):  # Return option
                if previous_menu_function:
                    previous_menu_function()
                else:
                    describe_room()
            else:
                show_inventory()
        else:
            show_inventory()
    else:
        delay_print(distort_text("Your inventory is empty.", game_state["sanity"]))
        input("\nPress Enter to return.")

    if previous_menu_function:
        previous_menu_function()
    else:
        title_screen()

def use_item():
    usable = [item for item in game_state["inventory"] if item in [a["name"] for a in artifact_pool + potion_pool]]
    if not usable:
        delay_print("You have no usable items.")
        input("\nPress Enter to return.")
        show_inventory()
        return
    print("\nWhich item would you like to use?")
    for idx, name in enumerate(usable, 1):
        print(f"[{idx}] {name}")
    print(f"[{len(usable)+1}] Return")
    choice = input("> ").strip()
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(usable):
            item_name = usable[idx]
            # Find artifact or potion
            artifact = next((a for a in artifact_pool if a["name"] == item_name), None)
            potion = next((p for p in potion_pool if p["name"] == item_name), None)
            if artifact:
                # Apply main effect
                if artifact.get("effect") in game_state:
                    game_state[artifact["effect"]] = min(18, game_state[artifact["effect"]] + artifact["amount"])
                    delay_print(f"You use the {artifact['name']}. {artifact['desc']} (+{artifact['amount']} {artifact['effect'].capitalize()})")
                # Apply side effect if any
                if "side_effects" in artifact:
                    for stat, amt in artifact["side_effects"]:
                        game_state[stat] = max(0, min(18, game_state[stat] + amt))
                        delay_print(f"Side effect: {stat.capitalize()} {'+' if amt > 0 else ''}{amt}")
                # Special effects
                if artifact["effect"] == "clue":
                    # Reveal a random clue not yet found
                    missing = [c for c in clue_pool if c not in game_state["clues"]]
                    if missing:
                        clue = random.choice(missing)
                        game_state["clues"].append(clue)
                        delay_print(f"The {artifact['name']} reveals a clue: {clue}")
                elif artifact["effect"] == "hint":
                    delay_print("A vision flashes before your eyes, hinting at the truth. (You gain a hint!)")
                elif artifact["effect"] == "secret":
                    delay_print("The candlelight flickers, revealing a hidden message on the wall.")
                elif artifact["effect"] == "random":
                    effect = random.choice(["clue", "sanity", "hint"])
                    if effect == "clue":
                        missing = [c for c in clue_pool if c not in game_state["clues"]]
                        if missing:
                            clue = random.choice(missing)
                            game_state["clues"].append(clue)
                            delay_print(f"The skull whispers a clue: {clue}")
                    elif effect == "sanity":
                        game_state["sanity"] = max(0, game_state["sanity"] - 2)
                        delay_print("The skull whispers forbidden secrets. You feel your sanity slipping (-2 Sanity).")
                    else:
                        delay_print("The skull whispers a cryptic hint about the case.")
                elif artifact["effect"] == "shortcut":
                    delay_print("You decipher the map and discover a shortcut. (A hidden room is revealed!)")
                elif artifact["effect"] == "quest":
                    delay_print("The letter reveals a new lead. (A side quest or clue is added!)")
                    game_state["quests"].append("Follow up on the sealed letter.")
                elif artifact["effect"] == "puzzle":
                    delay_print("You feel this ring may be important for a puzzle or ending.")
                elif artifact["effect"] == "repel":
                    delay_print("You feel protected from supernatural harm.")
                elif artifact["effect"] == "warn":
                    delay_print("The watch ticks rapidly, warning you of imminent danger.")
                elif artifact["effect"] == "ritual":
                    delay_print("You sense this will be useful in a ritual or puzzle.")
                elif artifact["effect"] == "unlock":
                    delay_print("You sense this key will open something important.")
                # Remove after use (permanent effect)
                game_state["inventory"].remove(item_name)
                input("\nPress Enter to return.")
                show_inventory()
                return
            elif potion:
                game_state[potion["effect"]] = min(18, game_state[potion["effect"]] + potion["amount"])
                delay_print(f"You drink the {potion['name']}. {potion['desc']} (+{potion['amount']} {potion['effect'].capitalize()})")
                game_state["inventory"].remove(potion["name"])
                input("\nPress Enter to return.")
                show_inventory()
                return
        else:
            show_inventory()
    else:
        show_inventory()
        
def handle_input(user_input, return_function):
    global previous_menu_function

    if user_input in valid_directions:
        move_to_new_room(user_input)
        return  # Prevent falling through to other cases
    elif user_input == "score":
        show_score()
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
    elif user_input == "quit" or user_input == "q" or user_input == "exit":
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
    else:
        delay_print("Unknown command. Type 'help' for available options.")
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
    print("- quests/mystery: Show active quests")
    print("- stats: Show character stats")
    print("- score: Show your current score and scoring breakdown")
    print("- n/s/e/w/ne/nw/se/sw: Move in that direction from any screen")
    input("\nPress Enter to return.")

    if previous_menu_function:
        previous_menu_function()
    else:
        title_screen()

def look_around(pause=True):
    room = game_state["location"]
    descriptions = room_templates.get(room, ["You see nothing remarkable."])
    first_sentence = descriptions[0].split(".")[0] + "."
    delay_print(first_sentence)
    if pause:
        input("\nPress Enter to return.")

def title_screen():
    global previous_menu_function
    previous_menu_function = title_screen
    clear()
    print(r"""
  _____                              _             
 |  __ \                            (_)            
 | |__) |__ _ __ ___ _   _  __ _ ___ _  ___  _ __  
 |  ___/ _ \ '__/ __| | | |/ _` / __| |/ _ \| '_ \ 
 | |  |  __/ |  \__ \ |_| | (_| \__ \ | (_) | | | |
 |_|   \___|_|  |___/\__,_|\__,_|___/_|\___/|_| |_|
                                                  
        
    """)
    delay_print("A Victorian Roguelike Mystery!")
    print("[1] Begin New Investigation")
    print("[2] Load Game")
    print("[3] Instructions")
    print("[4] Quit")

    user_input = input("\n> ").strip().lower()

    if user_input == "1":
        dream_flashback()
    elif user_input == "2":
        load_game()
    elif user_input == "3":
        instructions()
    elif user_input == "4" or user_input == "quit" or user_input == "q" or user_input == "exit":
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
    input("\nPress Enter to return.")
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

def add_random_clue():
    room = game_state["location"]
    found_something = False

    # Clue logic (as before)
    clue = clue_locations.get(room)
    if clue and clue not in game_state["clues"]:
        if random.random() < 0.8: 
            game_state["clues"].append(clue)
            delay_print(f"Clue discovered: {clue}")
            game_state["journal"].append(f"CLUE FOUND at {game_state['location']}: {clue}")
            game_state["score"] += 10  # Add to score for finding a clue
            game_state["score_log"].append(f"Clue: {clue} [+10]")
            print(f"[DEBUG] Score after finding clue: {game_state['score']}")
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
            found_something = True

    # Artifact logic
    artifact = game_state.get("artifact_locations", {}).get(room)
    if artifact and artifact["name"] not in game_state["inventory"]:
        game_state["inventory"].append(artifact["name"])
        delay_print(f"You found {artifact['name']}! {artifact['desc']}")
        game_state["score"] += 20  # Add to score for finding an artifact
        print(f"[DEBUG] Score after finding artifact: {game_state['score']}")
        game_state["journal"].append(f"ARTIFACT FOUND at {game_state['location']}: {artifact['name']}")
        game_state["score_log"].append(f"Artifact: {artifact['name']} [+20]") 
        found_something = True

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
    for entry in penalties:
        print(entry)

    print("\n--- Scoring Rules ---")
    print("Clues found: +10 each")
    print("Suspects interrogated: +15 each")
    print("Artifacts found: +20 each")
    print("Case solved: +100")
    print("Each 5 turns taken: -1")
    print("Stamina dropped to 0: -25")
    print("Sanity dropped to 0: -50")
    print("Killing any suspect: -30")
    input("Press Enter to continue.")

def case_resolution():
    delay_print("You gather your thoughts and review the case... Pages of notes flicker in your mind like a shuffled deck of ghosts.")
    if len(game_state["clues"]) >= 3:
        delay_print("The truth crystallizes. It is as chilling as it is inevitable, threading through every clue you've seen.")
        delay_print("You record the findings in your journal. The ink trembles as if the truth resists being committed to paper.")
        game_state["journal"].append("Case solved at " + game_state["location"])
        game_state["score"] += 100  # Add to score for solving the case
        delay_print("You have solved the case! Your score is now: " + str(game_state["score"]))
        delay_print("You feel a sense of closure, but also a lingering unease. The shadows of the manor still seem to whisper secrets you may never fully understand.")
        save_game()
    else:
        delay_print("There are still missing pieces. They flit just beyond comprehension like shadows behind stained glass.")
    input("Press Enter to continue.")
    title_screen()

def describe_room():
    global previous_menu_function
    previous_menu_function = describe_room
    clear()
    room = game_state["location"]
    # --- Show room name at the top ---
    print(f"\n=== {room} ===\n")
    descriptions = room_templates.get(room, ["It's a bare and quiet room."])
    desc = random.choice(descriptions)
    distorted = distort_text(desc, game_state["sanity"])
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
       # Show inventory tip only on first entry
        if not game_state.get("inventory_tip_shown"):
            print("\nCheck your inventory (press '5' or 'i') to see your list of belongings.")
            game_state["inventory_tip_shown"] = True
    # Otherwise, use 40% chance as normal
    elif available_indices and random.random() < 0.40:
        idx = random.choice(available_indices)
        flavor = flavor_text_pool[idx]
        delay_print(distort_text(flavor, game_state["sanity"]))
        used.setdefault(pos, []).append(idx)
        game_state["room_flavor_used"] = used
    elif not available_indices:
        # Reset so new ones can be used on future revisits
        used[pos] = []


    # Check if any suspect is present in the current room
    suspects_here = [
        s for s in game_state["suspects"]
        if s.get("position") == game_state["position"]
    ]

    # Count interrogated suspects (by journal entry)
    interrogated_count = sum(
        1 for s in game_state["suspects"]
        if any(f"You confront {s['name']}" in entry or f"Survived combat against {s['name']}" in entry for entry in game_state["journal"])
    )

    print("\nWhat would you like to do?")
    print("[1] Search the room")
    print("[2] Move to another location")
    print("[3] Show map")
    print("[4] Check journal")
    print("[5] Check inventory")
    if suspects_here:
        print("[6] Interrogate suspect")
    # Only show case resolution if at least 5 clues and 2 suspects interrogated
    if len(game_state["clues"]) >= 5 and interrogated_count >= 2:
        print("[7] Attempt case resolution")
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

    user_input = input("> ").strip().lower()
    if user_input == "1":
        add_random_clue()
        game_state["turns"] += 1
        if game_state["turns"] % 15 == 0:
            game_state["score"] -= 1
            game_state["score_log"].append("15 turns taken [-1]")
        input("Press Enter to return to the action menu.")
        describe_room()
        return
    elif user_input == "2":
        clear()
        print("Where would you like to go? (N, S, E, W, NE, NW, SE, SW)")
        dir_input = input("> ").strip().lower()
        if dir_input in ["n","s","e","w","ne","nw","se","sw"]:
            move_to_new_room(dir_input)
            game_state["turns"] += 1
            if game_state["turns"] % 15 == 0:
                game_state["score"] -= 1
                game_state["score_log"].append("15 turns taken [-1]")
        else:
            delay_print("Unknown direction. Please enter a valid compass direction.")
            input("Press Enter to continue.")
            describe_room()
    elif user_input == "3":
        show_map()
        # describe_room() # Return to room description after showing map to prevent double map display
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
        show_score() # Show score before quitting
        title_screen()
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
    suspects_here = [
        s for s in game_state["suspects"]
        if s.get("position") == game_state["position"]
    ]
    if not suspects_here:
        delay_print("There is no one here to interrogate.")
        input("Press Enter to continue.")
        describe_room()
        return

    clear()
    print("\nChoose someone to interrogate:")
    for i, s in enumerate(suspects_here):
        print(f"[{i+1}] {s['name']} – {s['trait']}")
    print(f"[{len(suspects_here)+1}] Return")

    # Persuasion option
    can_persuade = (
        game_state["stamina"] > 9 and
        game_state.get("persuasion_uses", 0) < 2 and
        not game_state.get("persuasion_active", False)
    )
    if can_persuade:
        print(f"[P] Persuade (costs 3 stamina, boosts perception for 3 rounds, up to 2 suspects per game)")

    user_input = input("> ").strip().lower()
    if can_persuade and user_input == "p":
        game_state["stamina"] -= 3
        game_state["persuasion_active"] = True
        game_state["persuasion_rounds"] = 3
        game_state["persuasion_uses"] = game_state.get("persuasion_uses", 0) + 1
        delay_print("You steel yourself and focus your will, reading every twitch and hesitation. Your perception is heightened!")
        input("Press Enter to continue.")
        interrogate_suspect()
        return

    if user_input.isdigit():
        idx = int(user_input) - 1
        if 0 <= idx < len(suspects_here):
            suspect = suspects_here[idx]
            clear()
            delay_print(f"You confront {suspect['name']}.")

            # Persuasion effect
            perception_mod = 0
            if game_state.get("persuasion_active", False):
                perception_mod = 3
                game_state["persuasion_rounds"] -= 1
                game_state.setdefault("persuasion_targets", set()).add(suspect["name"])
                if game_state["persuasion_rounds"] <= 0 or len(game_state["persuasion_targets"]) >= 2:
                    game_state["persuasion_active"] = False
                    game_state["persuasion_rounds"] = 0
                    game_state["persuasion_targets"] = set()
                delay_print("(Persuasion: Your perception is boosted!)")

            # Comeliness modifier
            comeliness_mod = 0
            if game_state["comeliness"] >= 17:
                comeliness_mod = 2
            elif game_state["comeliness"] >= 14:
                comeliness_mod = 1

            # Initialize credibility if not set
            if "credibility" not in suspect:
                suspect["credibility"] = random.randint(1, 10)

            effective_credibility = suspect["credibility"] + comeliness_mod
            effective_perception = game_state["perception"] + perception_mod

            delay_print(f"Your presence seems to sway them. (Comeliness modifier: +{comeliness_mod})")
            delay_print(f"Credibility rating: {effective_credibility}/10")
            delay_print(f"Perception (with boost): {effective_perception}/18")
            delay_print(suspect["alibi"])

            # Journal logging for suspect responses

            journal_entry = (
                f"Location: {game_state['location']}\n"
                f"Suspect: {suspect['name']}\n"
                f"Credibility: {effective_credibility}/10\n"
                f"Alibi: {suspect['alibi']}\n"
                "-----------------------------"
            )
            game_state["journal"].append(journal_entry)

           
            # Perception check: observe body language
            print("\nOptions:")
            print("[J] Enter this testimony in your journal")
            options = {"j"}
            if suspect["credibility"] < 5:
                print("[P] Push harder for the truth")
                options.add("p")
            if game_state["clues"]:
                print("[C] Confront with a clue")
                options.add("c")
            print("[O] Observe body language")
            options.add("o")
            print("[L] Leave interrogation")
            options.add("l")
            print("[R] Return to action menu")
            options.add("r")

            choice = input("> ").strip().lower()
            if choice == "p" and "p" in options:
                # Skill check: perception or sanity
                skill = random.choice(["perception", "sanity"])
                roll = game_state[skill] + roll_fudge()
                if roll > 12:
                    delay_print("Your pressure pays off. The suspect cracks and reveals more!")
                    # Reveal a new clue or contradiction
                    if suspect.get("is_murderer"):
                        delay_print("You catch a flicker of guilt in their eyes. They are hiding something big.")
                    else:
                        delay_print("They reveal a detail that points suspicion elsewhere.")
                else:
                    delay_print("The suspect grows agitated and refuses to say more.")
                    suspect["credibility"] = max(0, suspect["credibility"] - 1)
                input("Press Enter to continue.")
                interrogate_suspect()
                return
            elif choice == "j" and "j" in options:
                delay_print("Testimony already recorded in your journal.")
                input("Press Enter to continue.")
                interrogate_suspect()
                return
            elif choice == "c" and "c" in options:
                print("Which clue do you want to confront with?")
                for i, clue in enumerate(game_state["clues"], 1):
                    print(f"[{i}] {clue}")
                clue_choice = input("> ").strip()
                if clue_choice.isdigit():
                    clue_idx = int(clue_choice) - 1
                    if 0 <= clue_idx < len(game_state["clues"]):
                        clue = game_state["clues"][clue_idx]
                        # Check for alignment
                        if clue_motives.get(clue) == suspect["motive"]:
                            delay_print("The suspect's eyes widen—they recognize the clue! You sense a breakthrough.")
                            # Optionally, lower credibility or reveal more
                            suspect["credibility"] = max(0, suspect["credibility"] - 2)
                            delay_print("They stammer and contradict themselves. You sense they're hiding something.")
                            game_state["score"] += 15 # Add to score for successful clue confrontation
                        else:
                            delay_print("The suspect scoffs at your accusation.")
                            suspect["credibility"] = max(0, suspect["credibility"] - 1)
                input("Press Enter to continue.")
                interrogate_suspect()
                return
            elif choice == "o" and "o" in options:
                # Perception check
                roll = game_state["perception"] + roll_fudge()
                if roll >= 12:
                    delay_print("You notice a nervous tic. The suspect is definitely hiding something.")
                else:
                    delay_print("You can't read their body language this time.")
                input("Press Enter to continue.")
                interrogate_suspect()
                return
            
            elif choice == "l":
                describe_room()
                return
            elif choice == "r":
                describe_room()
                return
            else:
                interrogate_suspect()
                return

def dream_flashback():
    global previous_menu_function
    previous_menu_function = dream_flashback
    clear()
    delay_print("You are dreaming... or remembering. A shiver creeps down your spine as your mind conjures the weight of memory.")
    delay_print("A chapel cloaked in shadow, the child's voice echoing like a song half-remembered. A locked door pulses in the back of your mind like a heartbeat.")
    delay_print("Whispers echo backward through time and thought. You wake gasping, the image of a burning sigil fading from your vision.")
    input("Press Enter to continue.")
    intro_scene()

def intro_scene():
    global previous_menu_function
    previous_menu_function = intro_scene
    clear()
    delay_print("London, 1915. A fog rolls in over the cobblestones, thick and clinging, curling like smoke through the iron gates of the city’s forgotten quarters. The gaslamps flicker under its damp touch, casting pale halos that only make the darkness beyond feel deeper—hungrier...")
    while True:
        print("\nWhat will you do?")
        print("[1] Enter through the front gate")
        print("[2] Examine the grounds")
        print("[3] Pray silently")
        print("[4] Continue to character creation")

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
            input("Press Enter to return to the menu.")
        elif user_input == "3":
            game_state["faith"] += 1
            delay_print("You pause and offer a silent prayer. You feel your faith strengthen (+1 Faith).")
            input("Press Enter to return to the menu.")
        elif user_input == "4":
            character_creation()
            break
        else:
            delay_print("Invalid choice. Please select 1 or 2.")

def enter_manor():
    global previous_menu_function
    previous_menu_function = enter_manor
    clear()
    delay_print("You step into the manor, the scent of mildew thick in your nostrils. A shadow slips past the stairs, just at the edge of sight.")
    input("Press Enter to continue.")
    character_creation()

def random_name():
    first_names = [
        "Arthur", "Edmund", "Henry", "Charles", "Frederick", "Walter", "Reginald", "Albert", "Theodore", "Percival",
        "Eleanor", "Beatrice", "Clara", "Agnes", "Edith", "Florence", "Lillian", "Mabel", "Violet", "Winifred"
    ]
    last_names = [
        "Ashcroft", "Blackwood", "Carrow", "Davenport", "Ellery", "Fairchild", "Godwin", "Hawthorne", "Ingram", "Jasper",
        "Kingsley", "Loxley", "Montague", "Norwood", "Ormond", "Pembroke", "Quill", "Ravenswood", "Sinclair", "Thorne"
    ]
    return f"{random.choice(first_names)} {random.choice(last_names)}"

def get_player_name():
    while True:
        print("Would you like to enter a name or have one assigned at random?")
        print("[1] Enter my own name")
        print("[2] Randomize name")

        choice = input("> ").strip()
        if choice == "2":
            name = random_name()
            print(f"Your randomized name is: {name}")
            confirm = input("Accept this name? (Y/N): ").strip().lower()
            if confirm == "y":
                return name

        elif choice == "1":
            name = input("Enter your name: ").strip()
            if name:
                return name
        else:
            print("Please select 1 or 2.")

def character_creation():
    global previous_menu_function
    previous_menu_function = character_creation
    clear()
    delay_print("Before the hunt begins... who are you? The fog of the past clings to you, refusing to part until you define yourself.")
    game_state["name"] = get_player_name()
    game_state["gender"] = input("Gender: ")

    print("\nChoose your background:")
    print("[1] Theologian – +2 Faith")
    print("[2] Occultist – +2 Sanity")
    print("[3] Detective – +2 Perception")
    print("[4] Priest – +1 Faith, +1 Sanity")
    print("[5] Random character (auto-assign all stats)")
    print("[6] Manual stat entry (debug)")  # <-- Add this line

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
    elif bg == "6" or bg.lower() == "manual":
        manual_entry = True
        game_state["background"] = "Debug"
    else:
        character_creation()
        return

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
        input("Press Enter to continue.")
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
        input("Press Enter to continue.")
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
        input("Press Enter to continue.")

    game_state["inventory"].append("Envelope from the Commissioner")

    # Give player one random artifact as a clue at game start
    starting_artifact = random.choice(artifact_pool)
    game_state["inventory"].append(starting_artifact["name"])
    clue_text = f"You begin with a mysterious item: {starting_artifact['name']}. {starting_artifact['desc']}"
    game_state["clues"].append(clue_text)
    game_state["journal"].append(f"CLUE FOUND at start: {clue_text}")

    initialize_suspects()
    # Mark starting location visited at (0,0)
    game_state["visited_locations"] = {(0, 0): "Foyer"}
    game_state["location"] = "Foyer"
    game_state["position"] = (0, 0)

    generate_passages() # Generate passages between rooms
    auto_generate_walls_and_doors() # Generate walls and doors automatically
    print(f"Walls generated: {len(game_state['walls'])}")
    print(f"Locked doors generated: {len(game_state['locked_doors'])}") # Debugging line

    delay_print(f"Welcome, {game_state['name']} the {game_state['background']}. The hour is late, and the shadows grow bold.")
    input("Press Enter to begin.")

    assign_clues_to_rooms()
    assign_potions_to_rooms()
    assign_elder_sign_to_room()
    assign_artifacts_to_rooms()  # Assign artifacts to rooms

    # Begin the first case
    start_first_case()

def start_first_case():
    global previous_menu_function
    previous_menu_function = start_first_case
    game_state["quests"].append("Investigate Manor Seance")
    describe_room()

def skill_check_combat(enemy_name, enemy_difficulty=None, stat=None):
    clear()
    suspect = next((s for s in game_state["suspects"] if s["name"] == enemy_name), None)
    delay_print(f"You face off against {enemy_name}. The air crackles with tension.")
    input("Press Enter to continue.")

    player_stamina = game_state["stamina"]
    if suspect:
        enemy_stamina = suspect.get("stamina", 10)
        enemy_name = suspect["name"]
    else:
        enemy_stamina = enemy_difficulty if enemy_difficulty is not None else 10

    round_num = 1
    while player_stamina > 0 and enemy_stamina > 0:
        clear()
        delay_print(f"--- Combat Round {round_num} ---")
        delay_print(f"Your Stamina: {player_stamina} | {enemy_name}'s Stamina: {enemy_stamina}")

        # Player's composite score
        player_base = (game_state["strength"] + game_state["stamina"] + game_state["agility"]) // 3
        player_roll = player_base + roll_fudge()

        # Enemy's composite score
        if suspect:
            enemy_base = (suspect.get("strength", 8) + suspect.get("stamina", 8) + suspect.get("agility", 8)) // 3
        else:
            enemy_base = enemy_difficulty if enemy_difficulty is not None else 8
        enemy_roll = enemy_base + roll_fudge()

        delay_print(f"Your combat score: {player_base} + die roll = {player_roll}")
        delay_print(f"Enemy combat score: {enemy_base} + die roll = {enemy_roll}")

        # Determine round outcome
        if player_roll >= enemy_roll:
            delay_print(f"You land a blow! {enemy_name} loses 2 stamina.")
            enemy_stamina -= 2
            game_state["sanity"] = max(1, game_state["sanity"] - 1)
        else:
            delay_print(f"{enemy_name} strikes you! You lose 2 stamina.")
            player_stamina -= 2
            game_state["sanity"] = max(0, game_state["sanity"] - 2)
        delay_print(f"Your Stamina: {player_stamina} | {enemy_name}'s Stamina: {enemy_stamina}")
        input("Press Enter to continue.")
        round_num += 1

    # End of combat
    game_state["stamina"] = player_stamina
    if suspect:
        suspect["stamina"] = enemy_stamina

    if player_stamina > 0:
        delay_print(f"You overcome the threat posed by {enemy_name}! You live to investigate another day.")
        game_state["journal"].append(f"Survived combat against {enemy_name}.")
        if suspect:
            suspect["stamina"] = 0
            # Penalize for killing any suspect (manslaughter), not just the murderer
            game_state["score"] -= 15
            delay_print("You have taken a life in self-defense. The weight of this act will haunt you. (-15 Score)")
    else:
        delay_print(f"The encounter with {enemy_name} overwhelms you...")
        game_state["journal"].append(f"Defeated by {enemy_name}. Survived, but barely.")

    # Check if the suspect was the murderer and was just defeated
    if suspect and suspect.get("is_murderer") and player_stamina > 0:
        game_state["score"] -= 25  # Penalize for violent resolution
        delay_print(f"As {suspect['name']} falls, the truth is revealed: {suspect['name']} was the murderer all along!")
        delay_print("But justice through violence is not justice at all. The Commissioner is furious at your methods.")
        delay_print("You have failed to solve the mystery through deduction. The case is closed in disgrace.")
        print(r"""
 __     __           _                    
 \ \   / /          | |                   
  \ \_/ /__  _   _  | |     ___  ___  ___ 
   \   / _ \| | | | | |    / _ \/ __|/ _ \
    | | (_) | |_| | | |___| (_) \__ \  __/
    |_|\___/ \__,_| |______\___/|___/\___|
    """)        
        delay_print("Sorry!")
        show_score()  # <-- Show score before returning to title
        input("Press Enter to continue.")
        title_screen()
        return

    if player_stamina <= 0:
        delay_print("You have succumbed to exhaustion. The investigation ends here.")
        game_state["score"] -= 35  # Penalize for failure
        show_score()  # <-- Show score before returning to title
        input("Press Enter to continue.")
        title_screen()
    else:
        input("Press Enter to continue.")

# --- Start the Game ---   
title_screen()