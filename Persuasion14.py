# Persuasion: Victorian Roguelike Investigation RPG Game
# Core Game Script

import os
import time
import random
import json
import sys
import threading

# --- Global State ---

MAP_MIN = -8
MAP_MAX = 7
MAP_SIZE = MAP_MAX - MAP_MIN + 1  # 16
MAP_CENTER = (MAP_SIZE // 2) - 1  # Center of the map grid

DIRECTIONS = {
    "n": (0, -1),
    "s": (0, 1),
    "e": (1, 0),
    "w": (-1, 0),
    "ne": (1, -1),
    "nw": (-1, -1),
    "se": (1, 1),
    "sw": (-1, 1)
}
previous_menu_function = None

valid_directions = {"n", "s", "e", "w", "ne", "nw", "se", "sw"}

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
    "walls": set(),  # Each wall is ((x1, y1), (x2, y2))
}

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
            exits = random.sample(possible_dirs, min(4, len(possible_dirs)))
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
    # If not enough possible positions, just use whatever is available
    chosen_positions = random.sample(possible_positions, 4)
    for suspect, pos in zip(game_state["suspects"], chosen_positions):
        suspect["position"] = pos
        suspect["wait_turns"] = 0

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

def delay_print(s, speed=0.03):
    """Prints text slowly, but finishes instantly if the user presses space."""
    import msvcrt  # Windows only; for cross-platform, use 'getch' from 'getch' package

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

def save_game():
    try:
        # Convert tuple keys in visited_locations to strings for JSON
        game_state_copy = game_state.copy()
        visited_serializable = {str(k): v for k, v in game_state["visited_locations"].items()}
        game_state_copy["visited_locations"] = visited_serializable

        # Convert sets to lists for JSON serialization
        if "walls" in game_state_copy:
            game_state_copy["walls"] = list(game_state_copy["walls"])
        if "passages" in game_state_copy:
            # Convert passages dict of sets to dict of lists
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

            # Convert string keys back into tuples
            visited = {}
            for key, value in loaded_state.get("visited_locations", {}).items():
                if key.startswith("(") and "," in key:
                    x, y = map(int, key.strip("()").split(","))
                    visited[(x, y)] = value

            loaded_state["visited_locations"] = visited

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

def move_to_new_room(direction=None):
    x, y = game_state["position"]
    if direction not in DIRECTIONS:
        direction = random.choice(list(DIRECTIONS.keys()))
    dx, dy = DIRECTIONS[direction]
    new_x, new_y = x + dx, y + dy

    # Grid bounds check
    if not (MAP_MIN <= new_x <= MAP_MAX and MAP_MIN <= new_y <= MAP_MAX):
        delay_print("You sense an unnatural barrier. The manor does not extend further in that direction.")
        input("Press Enter to continue.")
        describe_room()
        return

    # Passage check
    allowed_dirs = game_state["passages"].get((x, y), set())
    if direction not in allowed_dirs:
        delay_print("A wall or locked door blocks your way. You cannot go that direction.")
        input("Press Enter to continue.")
        describe_room()
        return

    # ...rest of your movement code...

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

        # Get all adjacent positions that are visited
        x, y = suspect["position"]
        adjacent = [
            (x + dx, y + dy)
            for dx, dy in [
                (0, 1), (0, -1), (1, 0), (-1, 0),  # N, S, E, W
                (1, 1), (-1, 1), (1, -1), (-1, -1) # NE, NW, SE, SW
            ]
            if (x + dx, y + dy) in game_state["visited_locations"]
        ]

        # Move to a random adjacent visited room if possible
        if adjacent:
            suspect["position"] = random.choice(adjacent)
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
    if game_state["journal"]:
        for entry in game_state["journal"]:
            delay_print(distort_text(entry, game_state["sanity"]))
    else:
        delay_print(distort_text("Your journal is empty.", game_state["sanity"]))
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
        describe_room()
    elif user_input == "2":
        clear()
        print("Where would you like to go? (N, S, E, W, NE, NW, SE, SW)")
        dir_input = input("> ").strip().lower()
        if dir_input in ["n","s","e","w","ne","nw","se","sw"]:
            move_to_new_room(dir_input)
        else:
            delay_print("Unknown direction. Please enter a valid compass direction.")
            input("Press Enter to continue.")
            describe_room()
    elif user_input == "3":
        show_map()
        describe_room()
    elif user_input == "4":
        show_journal()
    elif user_input == "5":
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
    delay_print(f"Current Location: {location} at {pos}")
    delay_print("\nMap:")
    # Prompt for NPC toggle
    show_npcs = False
    choice = input("Show suspects on map? (Y/N): ").strip().lower()
    if choice == "y":
        show_npcs = True
    render_map(show_npcs)
    input("\nPress Enter to return.")

    # FIX: Return to previous menu or describe_room
    if previous_menu_function:
        previous_menu_function()
    else:
        describe_room()

def render_map(show_npcs=False):
    grid_size = 11
    half = grid_size // 2
    px, py = game_state["position"]

    # Build a lookup for suspect positions if showing NPCs
    suspect_positions = {}
    if show_npcs:
        for idx, s in enumerate(game_state["suspects"], 1):
            pos = s.get("position")
            if pos:
                suspect_positions.setdefault(pos, []).append(str(idx))

    GREEN = "\033[32m"
    RESET = "\033[0m"
    sanity = game_state["sanity"]

    for y in range(py - half, py + half + 1):
        row = ""
        for x in range(px - half, px + half + 1):
            char = " . "
            if (x, y) == (px, py):
                char = " @ "
                if sanity < 4 and random.random() < 0.5:
                    char = " # "  # Glitch player marker
            elif show_npcs and (x, y) in suspect_positions:
                char = " " + "".join(suspect_positions[(x, y)]) + " "
                if sanity < 4 and random.random() < 0.4:
                    char = " ? "  # Hallucinated NPC
            elif (x, y) in game_state["visited_locations"]:
                loc = game_state["visited_locations"][(x, y)]
                char = f" {loc[0]} "
                if sanity < 4 and random.random() < 0.2:
                    char = random.choice([" ~ ", " * ", " % ", " $ "])
            elif sanity < 4 and random.random() < 0.1:
                char = random.choice([" ! ", " ? ", " # "])  # False rooms
            row += char
        print(f"{GREEN}{row}{RESET}")
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

def show_inventory():
    clear()
    delay_print("Inventory:")
    if game_state["inventory"]:
        for idx, item in enumerate(game_state["inventory"], 1):
            print(f"[{idx}] {distort_text(item, game_state['sanity'])}")
        print(f"[{len(game_state['inventory'])+1}] Return")
        choice = input("\nSelect an item to inspect or return: ")

        # Handle case where user just presses Enter
        if choice.strip() == "":
            show_inventory()
            return

        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(game_state["inventory"]):
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
    # Only show usable potions
    usable = [p for p in potion_pool if p["name"] in game_state["inventory"]]
    if not usable:
        delay_print("You have no usable potions.")
        input("\nPress Enter to return.")
        show_inventory()
        return
    print("\nWhich potion would you like to use?")
    for idx, p in enumerate(usable, 1):
        print(f"[{idx}] {p['name']} – {p['desc']}")
    print(f"[{len(usable)+1}] Return")
    choice = input("> ").strip()
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(usable):
            potion = usable[idx]
            game_state[potion["effect"]] = min(18, game_state[potion["effect"]] + potion["amount"])
            delay_print(f"You drink the {potion['name']}. {potion['desc']} (+{potion['amount']} {potion['effect'].capitalize()})")
            game_state["inventory"].remove(potion["name"])
            input("\nPress Enter to return.")
            show_inventory()
        else:
            show_inventory()
    else:
        show_inventory()
        
def handle_input(user_input, return_function):
    global previous_menu_function

    if user_input in valid_directions:
        move_to_new_room(user_input)
        return  # Prevent falling through to other cases

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
    elif user_input == "quit":
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
    delay_print("Available commands:")
    delay_print("- help: Show this help message")
    delay_print("- look [l]: Look around the current location")
    delay_print("- save: Save your game")
    delay_print("- load: Load a previous save")
    delay_print("- quit: Quit the game")
    delay_print("- back/menu: Return to the previous menu")
    delay_print("- title: Return to the title screen")
    delay_print("- inventory [i]: Show your inventory")
    delay_print("- journal [j]: Show your journal entries")
    delay_print("- quests/mystery: Show active quests")
    delay_print("- stats: Show character stats")
    delay_print("- n/s/e/w/ne/nw/se/sw: Move in that direction from any screen")
    input("\nPress Enter to return.")

    if previous_menu_function:
        previous_menu_function()
    else:
        title_screen()

def look_around():
    room = game_state["location"]
    descriptions = room_templates.get(room, ["You see nothing remarkable."])
    first_sentence = descriptions[0].split(".")[0] + "."
    delay_print(first_sentence)
    input("\nPress Enter to return.")

def title_screen():
    global previous_menu_function
    previous_menu_function = title_screen
    clear()
    print("""
  _____                              _             
 |  __ \                            (_)            
 | |__) |__ _ __ ___ _   _  __ _ ___ _  ___  _ __  
 |  ___/ _ \ '__/ __| | | |/ _` / __| |/ _ \| '_ \ 
 | |  |  __/ |  \__ \ |_| | (_| \__ \ | (_) | | | |
 |_|   \___|_|  |___/\__,_|\__,_|___/_|\___/|_| |_|
                                                  
         A Victorian Roguelike Mystery
    """)
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
    elif user_input == "4" or user_input == "quit":
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

    if sanity >= 7:
        return text  # Clear
    elif sanity >= 4:
        # Mild distortion: jumble some words
        words = text.split()
        for i in range(len(words)):
            if random.random() < 0.3:
                words[i] = jumble_word(words[i])
        return ' '.join(words)
    elif sanity >= 3:
        # Severe distortion: reverse words and jumble
        words = text.split()
        words = [jumble_word(w) for w in words[::-1]]
        return ' '.join(words)
    else:
        # Zalgo/unicode glitch
        return zalgo(text)

def move_to_new_room(direction=None):
    x, y = game_state["position"]
    moves = {
        "n": (0, -1),
        "s": (0, 1),
        "e": (1, 0),
        "w": (-1, 0),
        "ne": (1, -1),
        "nw": (-1, -1),
        "se": (1, 1),
        "sw": (-1, 1)
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

    new_pos = (new_x, new_y)
    game_state["position"] = new_pos

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

    input("Press Enter to enter the new room.")
    
    describe_room()

def add_random_clue():
    room = game_state["location"]
    found_something = False

    # Clue logic (as before)
    clue = clue_locations.get(room)
    if clue and clue not in game_state["clues"]:
        if random.random() < 0.6:
            game_state["clues"].append(clue)
            delay_print(f"Clue discovered: {clue}")
            game_state["journal"].append(f"Clue found: {clue}")
            found_something = True

    # Potion logic
    potion = potion_locations.get(room)
    if potion and potion["name"] not in game_state["inventory"]:
        if random.random() < 0.6:
            game_state["inventory"].append(potion["name"])
            delay_print(f"You found a {potion['name']}! {potion['desc']}")
            found_something = True

    if not found_something:
        delay_print("You search carefully, but find nothing new.")
    input("Press Enter to continue.")

def case_resolution():
    delay_print("You gather your thoughts and review the case... Pages of notes flicker in your mind like a shuffled deck of ghosts.")
    if len(game_state["clues"]) >= 3:
        delay_print("The truth crystallizes. It is as chilling as it is inevitable, threading through every clue you've seen.")
        delay_print("You record the findings in your journal. The ink trembles as if the truth resists being committed to paper.")
        game_state["journal"].append("Case solved at " + game_state["location"])
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
    descriptions = room_templates.get(room, ["It's a bare and quiet room."])
    desc = random.choice(descriptions)
    distorted = distort_text(desc, game_state["sanity"])
    delay_print(distorted)

    # --- Flavor text logic (25% chance) ---
    pos = game_state["position"]
    used = game_state.setdefault("room_flavor_used", {})
    used_indices = used.get(pos, [])
    available_indices = [i for i in range(len(flavor_text_pool)) if i not in used_indices]
    if available_indices and random.random() < 0.25:
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

    user_input = input("> ").strip().lower()
    if user_input == "1":
        add_random_clue()
        describe_room()
    elif user_input == "2":
        clear()
        print("Where would you like to go? (N, S, E, W, NE, NW, SE, SW)")
        dir_input = input("> ").strip().lower()
        if dir_input in ["n","s","e","w","ne","nw","se","sw"]:
            move_to_new_room(dir_input)
        else:
            delay_print("Unknown direction. Please enter a valid compass direction.")
            input("Press Enter to continue.")
            describe_room()
    elif user_input == "3":
        show_map()
        describe_room()
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

    user_input = input("> ").strip().lower()
    if user_input.isdigit():
        idx = int(user_input) - 1
        if 0 <= idx < len(suspects_here):
            suspect = suspects_here[idx]
            clear()
            delay_print(f"You confront {suspect['name']}.")

            # --- Comeliness modifier ---
            comeliness_mod = 0
            if game_state["comeliness"] >= 17:
                comeliness_mod = 2
            elif game_state["comeliness"] >= 14:
                comeliness_mod = 1

            # Initialize credibility if not set
            if "credibility" not in suspect:
                suspect["credibility"] = random.randint(1, 10)

            # Apply comeliness modifier
            effective_credibility = suspect["credibility"] + comeliness_mod

            delay_print(f"Your presence seems to sway them. (Comeliness modifier: +{comeliness_mod})")
            delay_print(f"Credibility rating: {effective_credibility}/10")
            delay_print(suspect["alibi"])

            # Lower credibility after questioning
            suspect["credibility"] = max(0, suspect["credibility"] - 1)

            # If credibility is too low, suspect attacks!
            if suspect["credibility"] <= 2:
                delay_print(f"{suspect['name']} snaps under pressure and lashes out at you!")
                skill_check_combat(suspect['name'], random.randint(4, 8), stat="strength")
                # Optionally, after combat, credibility resets a bit
                suspect["credibility"] = min(5, suspect["credibility"] + 2)

            input("Press Enter to continue.")
            describe_room()
        elif idx == len(suspects_here):
            describe_room()
        else:
            delay_print("Invalid choice.")
            input("Press Enter to continue.")
            interrogate_suspect()
    else:
        handle_input(user_input, interrogate_suspect)

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
            delay_print("Invalid choice. Please select an option.")

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

    bg = input("> ")
    auto_assign = False
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
    else:
        character_creation()
        return

    # Assign base values and random bonus to all stats
    for stat in ["faith", "sanity", "perception", "strength", "stamina", "agility", "comeliness"]:
        base = 8 + random.randint(1, 4)
        game_state[stat] = base

    stat_points = 6
    stats_list = ["faith", "sanity", "perception", "strength", "stamina", "agility", "comeliness"]

    if auto_assign:
        # Randomly distribute 6 points among stats (max 18 per stat)
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
        print("\nDistribute 6 additional points among your attributes (for a max of 18):")
        while stat_points > 0:
            print(f"\nPoints remaining: {stat_points}")
            for idx, stat in enumerate(stats_list, 1):
                print(f"[{idx}] {stat.capitalize()}: [{game_state[stat]}]")

            chosen_stat = input("\nEnter the attribute to increase (name or number): ").strip().lower()
            if chosen_stat.isdigit():
                stat_idx = int(chosen_stat) - 1
                if 0 <= stat_idx < len(stats_list):
                    chosen_stat = stats_list[stat_idx]
                else:
                    print("Invalid stat number. Try again.")
                    continue
            elif chosen_stat not in stats_list:
                print("Invalid stat name. Try again.")
                continue

            try:
                add = int(input(f"How many points would you like to add to {chosen_stat.capitalize()}? (You have {stat_points} left): "))
                if 0 <= add <= stat_points and game_state[chosen_stat] + add <= 18:
                    game_state[chosen_stat] += add
                    stat_points -= add
                else:
                    print("Invalid amount. Please enter a number within the remaining point range and stat limit.")
            except ValueError:
                print("Please enter a valid number.")

        # Final confirmation
        print("\nFinal attributes:")
        for stat in stats_list:
            print(f"{stat.capitalize()}: {game_state[stat]}")
        confirm = input("Accept these stats? (Y/N): ").strip().lower()
        if confirm != 'y':
            character_creation()
            return
    game_state["inventory"].append("Envelope from the Commissioner")

    initialize_suspects()
    # Mark starting location visited at (0,0)
    game_state["visited_locations"] = {(0, 0): "Foyer"}
    game_state["location"] = "Foyer"
    game_state["position"] = (0, 0)
    generate_passages()  # <--- Add this line
    delay_print(f"Welcome, {game_state['name']} the {game_state['background']}. The hour is late, and the shadows grow bold.")
    input("Press Enter to begin.")

    assign_clues_to_rooms()
    assign_potions_to_rooms()

# Begin the first case

    start_first_case()

def start_first_case():
    global previous_menu_function
    previous_menu_function = start_first_case
    game_state["quests"].append("Investigate Manor Seance")
    describe_room()

def skill_check_combat(enemy_name, enemy_difficulty, stat="strength"):
    clear()
    delay_print(f"You face off against {enemy_name}. A sense of dread fills the air.")
    input("Press Enter to continue.")
    player_roll = game_state[stat] + random.randint(1, 6)
    enemy_roll = enemy_difficulty + random.randint(1, 6)
    delay_print(f"You roll a {player_roll}. The enemy rolls a {enemy_roll}.")
    input("Press Enter to continue.")

    if player_roll >= enemy_roll:
        delay_print(f"You overcome the threat posed by {enemy_name}! You live to investigate another day.")
        input("Press Enter to continue.")
        game_state["sanity"] = max(1, game_state["sanity"] - 1)
        game_state["journal"].append(f"Survived combat against {enemy_name}.")
    else:
        delay_print(f"The encounter with {enemy_name} overwhelms you...")
        input("Press Enter to continue.")
        game_state["sanity"] = max(0, game_state["sanity"] - 2)
        game_state["health"] = max(0, game_state["health"] - 3)  # Example: lose 3 health
        game_state["journal"].append(f"Defeated by {enemy_name}. Survived, but barely.")
    if game_state["health"] <= 0:
        delay_print("You have succumbed to your wounds. The investigation ends here.")
        input("Press Enter to continue.")
        title_screen()
    input("Press Enter to continue.")

# --- Start the game ---
title_screen()