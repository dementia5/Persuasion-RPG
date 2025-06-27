# Persuasion: Victorian Roguelike Investigation Game
# Core Game Script

import os
import time
import random
import json

# Global player state
previous_menu_function = None

game_state = {
    "name": "",
    "gender": "",
    "background": "",
    "faith": 0,
    "sanity": 10,
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
    "reputation": 0,
}

room_templates = {
    "Library": [
        "Bookshelves loom, many tomes written in languages you don’t recognize.",
        "A shattered inkwell and a missing journal page hint at a struggle."
    ],
    "Study": [
        "The desk is overturned. Scorched fragments of parchment litter the floor.",
        "A painting swings ajar, revealing a keyhole behind it."
    ],
    "Cellar": [
        "Wine racks cover the walls, but the air smells of rot, not spirits.",
        "Chains and dried herbs hang together—ritual or restraint?"
    ],
    "Parlor": [
        "A cracked mirror leans against the fireplace, reflecting nothing.",
        "A half-burnt letter lies beside an empty tea cup."
    ],
    "Foyer": [
        "The grand entry is dimly lit. Dust motes float through the silence.",
        "You hear footsteps upstairs, then silence again."
    ],
    "Conservatory": [
        "Shattered glass and soil litter the floor. Something moved recently.",
        "Twisted vines creep up broken walls, as if trying to escape."
    ],
    "Attic": [
        "Dust chokes the air. Wooden dolls stare with painted eyes.",
        "Trunks rusted shut rattle faintly when you're near."
    ],
    "Chapel": [
        "A row of pews face an altar. The stained glass depicts twisted saints.",
        "A hymn book lies open to a page soaked in wax and blood."
    ],
    "Kitchen": [
        "Rusty pots hang askew. Something foul lingers in the cold stove.",
        "The cutting board bears fresh knife marks. Yet the room feels long abandoned."
    ],
    "Ballroom": [
        "Moonlight reflects off cracked tiles. Music echoes where none is played.",
        "Dust motes twirl in empty rhythm under the ghostly chandelier."
    ],
    "Laboratory": [
        "Beakers bubble with unknown fluids. Charts line the walls, written in cipher.",
        "A scalpel clatters off the table as if pushed by an unseen hand."
    ],
    "Smoking Room": [
        "Cigars smolder in an untouched ashtray. The fireplace burns with no fuel.",
        "Leather chairs surround a chessboard mid-game... with no players."
    ],
    "Dining Hall": [
        "The table is set for a feast no one remembers. The food is plasticine.",
        "A chair lies splintered beside a knocked-over wine bottle."
    ],
    "Garden": [
        "Statues line the path, their faces worn blank. Roses bloom black and red.",
        "A fountain drips red water. Birds refuse to sing here."
    ],
    "Stables": [
        "Empty stalls. Hoofprints lead outside, then vanish.",
        "A saddlebag hangs open, its contents spilled in panic."
    ],
    "Bedroom": [
        "The bedsheets are rumpled, the pillow still warm.",
        "A music box plays by itself when no one watches."
    ],
    "Atrium": [
        "A glass ceiling shows the stars—but the pattern is wrong.",
        "A cold wind blows inward, though every door is shut."
    ],
    "Solarium": [
        "The sun never shines here, but the plants still grow.",
        "A cracked tea set rests on a wicker table, untouched by dust."
    ],
}

direction_vectors = {
    "n":  (0, 1),   "s":  (0, -1),  "e":  (1, 0),   "w":  (-1, 0),
    "ne": (1, 1),   "nw": (-1, 1),  "se": (1, -1),  "sw": (-1, -1)
}

clue_pool = [
    "A silver pendant etched with tentacles.",
    "Blood-stained prayer book.",
    "Footprints leading to a sealed hatch.",
    "A coded diary mentioning a 'Summoning'.",
    "An empty ritual circle drawn in chalk.",
    "A page torn from a forbidden tome.",
]

suspect_templates = [
    {"name": "Miss Vexley", "trait": "Nervous", "alibi": "Claims she was in the chapel praying."},
    {"name": "Dr. Lorn", "trait": "Stoic", "alibi": "Was tending the fire in the lounge."},
    {"name": "Bishop Greaves", "trait": "Fanatical", "alibi": "Says he heard voices in the cellar."},
    {"name": "Colonel Catsup", "trait": "Charming", "alibi": "Claims he was entertaining guests all night."},
    {"name": "Madame Thistle", "trait": "Eccentric", "alibi": "Claims to be dreaming while awake."},
    {"name": "Mr. Derry", "trait": "Quiet", "alibi": "Was tending the garden alone."},
    {"name": "Father Herne", "trait": "Whispering", "alibi": "Heard voices in the solarium."},
    {"name": "Lady Raventon", "trait": "Regal", "alibi": "Claims she saw the victim alive at midnight."},
]
# --- Reset Game State Function ---
def reset_game_state():
    for key in game_state:
        if isinstance(game_state[key], list):
            game_state[key] = []
        elif isinstance(game_state[key], dict):
            game_state[key] = {}
        elif isinstance(game_state[key], tuple):
            game_state[key] = (0, 0)
        elif isinstance(game_state[key], int):
            game_state[key] = 0
        else:
            game_state[key] = ""
    game_state["sanity"] = 10

# --- Utilities ---
def clear():
    os.system("cls" if os.name == "nt" else "clear")

def delay_print(s, speed=0.02):
    for c in s:
        print(c, end="", flush=True)
        time.sleep(speed)
    print("\n")

# --- Save / Load Game ---
def save_game():
    try:
        save_data = game_state.copy()
        save_data["visited_locations"] = {f"{k[0]},{k[1]}": v for k, v in game_state["visited_locations"].items()}
        with open("savegame.json", "w") as f:
            json.dump(save_data, f)
        print("\nGame saved.")
    except Exception as e:
        print(f"\nError saving game: {e}")
    input("\nPress Enter to continue.")

def load_game():
    global game_state
    try:
        with open("savegame.json", "r") as f:
            save_data = json.load(f)
        save_data["visited_locations"] = {tuple(map(int, k.split(","))): v for k, v in save_data["visited_locations"].items()}
        game_state.update(save_data)
        print("\nGame loaded.")
        input("\nPress Enter to resume your investigation.")
        describe_room()
    except Exception as e:
        print(f"\nError loading game: {e}")
        input("\nPress Enter to return.")
        title_screen()

# --- Display Commands ---
def show_stats():
    clear()
    delay_print(f"Name: {game_state['name']}")
    delay_print(f"Gender: {game_state['gender']}")
    delay_print(f"Background: {game_state['background']}")
    for stat in ["faith", "sanity", "perception", "strength", "stamina", "agility", "comeliness", "reputation"]:
        delay_print(f"{stat.capitalize()}: {game_state[stat]}")
    input("\nPress Enter to return.")
    if previous_menu_function:
        previous_menu_function()
    else:
        title_screen()

def show_inventory():
    clear()
    delay_print("Inventory:")
    if game_state["inventory"]:
        delay_print(", ".join(game_state["inventory"]))
    else:
        delay_print("Your inventory is empty.")
    input("\nPress Enter to return.")
    if previous_menu_function:
        previous_menu_function()

def show_journal():
    clear()
    delay_print("Journal Entries:")
    if game_state["journal"]:
        for entry in game_state["journal"]:
            delay_print(f"- {entry}")
    else:
        delay_print("Your journal is empty.")
    input("\nPress Enter to return.")
    if previous_menu_function:
        previous_menu_function()

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

# --- Global Command Handler ---
def handle_input(user_input, return_function):
    global previous_menu_function
    user_input = user_input.strip().lower()
    if user_input in direction_vectors:
        move_to_new_room(user_input)
    elif user_input == "help":
        show_help()
    elif user_input == "save":
        save_game()
        return_function()
    elif user_input == "load":
        load_game()
    elif user_input == "quit":
        exit()
    elif user_input in ["back", "menu", "title"]:
        title_screen()
    elif user_input == "inventory":
        show_inventory()
    elif user_input == "journal":
        show_journal()
    elif user_input == "quests":
        show_quests()
    elif user_input == "stats":
        show_stats()
    elif user_input == "map":
        display_map()
    elif user_input == "look":
        describe_current_room_brief()
    else:
        delay_print("Unknown command. Type 'help' for options.")
        return_function()

def describe_current_room_brief():
    desc = room_templates.get(game_state["location"], ["It's a nondescript room."])[0]
    delay_print(f"Room: {game_state['location']}")
    delay_print(f"{desc}")
    input("\nPress Enter to return.")
    if previous_menu_function:
        previous_menu_function()

def show_help():
    delay_print("Available commands:")
    cmds = [
        "save - Save your game",
        "load - Load a previous save",
        "quit - Quit the game",
        "inventory - View items",
        "journal - View journal entries",
        "quests - View current quests",
        "map - View map",
        "stats - View character stats",
        "look - Inspect current room",
        "n, s, e, w, ne, nw, se, sw - Move directionally"
    ]
    for c in cmds:
        delay_print(f"- {c}")
    input("\nPress Enter to return.")
    if previous_menu_function:
        previous_menu_function()
# --- Room Description ---
def describe_room():
    global previous_menu_function
    previous_menu_function = describe_room
    clear()
    pos = game_state["position"]
    room = game_state["visited_locations"].get(pos, "Unknown")
    game_state["location"] = room
    if pos not in game_state["visited_locations"]:
        game_state["visited_locations"][pos] = room
    game_state["visited_locations"][pos] = room
    desc = random.choice(room_templates.get(room, ["A bare room."]))
    delay_print(desc)
    print("\nWhat would you like to do?")
    print("[1] Search the room")
    print("[2] Move to another room")
    print("[3] Interrogate a suspect")
    print("[4] Attempt case resolution")
    print("[5] Save game")
    print("[6] Quit to title")
    print("\n(Or type a global command like 'map', 'look', 'journal', or a direction)")

    user_input = input("> ")
    if user_input == "1":
        add_random_clue()
        describe_room()
    elif user_input == "2":
        move_prompt()
    elif user_input == "3":
        interrogate_suspect()
    elif user_input == "4":
        case_resolution()
    elif user_input == "5":
        save_game()
        describe_room()
    elif user_input == "6":
        title_screen()
    else:
        handle_input(user_input, describe_room)

# --- Movement ---
def move_prompt():
    clear()
    print("Choose a direction: N, S, E, W, NE, NW, SE, SW")
    user_input = input("\n> ").strip().lower()
    if user_input in direction_vectors:
        move_to_new_room(user_input)
    else:
        delay_print("Invalid direction.")
        input("\nPress Enter to continue.")
        describe_room()

def move_to_new_room(direction):
    x, y = game_state["position"]
    dx, dy = direction_vectors[direction]
    new_pos = (x + dx, y + dy)

    if new_pos not in game_state["visited_locations"]:
        new_room = random.choice(list(room_templates.keys()))
        game_state["visited_locations"][new_pos] = new_room
    else:
        new_room = game_state["visited_locations"][new_pos]

    game_state["position"] = new_pos
    game_state["location"] = new_room
    delay_print(f"You move {direction.upper()} to {new_room}.")
    input("\nPress Enter to enter the room.")
    describe_room()

# --- Map Display ---
def display_map():
    clear()
    coords = list(game_state["visited_locations"].keys())
    if not coords:
        delay_print("Map is empty.")
        input("\nPress Enter to return.")
        previous_menu_function()
        return

    xs = [x for x, _ in coords]
    ys = [y for _, y in coords]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    for y in range(max_y, min_y - 1, -1):
        row = ""
        for x in range(min_x, max_x + 1):
            pos = (x, y)
            if pos == game_state["position"]:
                row += "[@]"
            elif pos in game_state["visited_locations"]:
                abbrev = game_state["visited_locations"][pos][0]
                row += f"[{abbrev}]"
            else:
                row += "[ ]"
        print(row)

    print("\nLegend: [@] = You, [L] = Visited Room, [ ] = Unknown")
    input("\nPress Enter to return.")
    previous_menu_function()

# --- Clue Discovery ---
def add_random_clue():
    if len(game_state["clues"]) >= len(clue_pool):
        delay_print("You've discovered all known clues.")
        return
    clue = random.choice([c for c in clue_pool if c not in game_state["clues"]])
    game_state["clues"].append(clue)
    delay_print(f"Clue discovered: {clue}")
    credibility_note = f"You believe it may relate to the ongoing investigation."
    game_state["journal"].append(f"Clue: {clue} – {credibility_note}")
    input("\nPress Enter to continue.")

# --- Suspect Interrogation ---
def interrogate_suspect():
    global previous_menu_function
    previous_menu_function = interrogate_suspect
    suspects = game_state["suspects"]
    clear()
    print("Choose a suspect to interrogate:")
    for i, s in enumerate(suspects):
        print(f"[{i+1}] {s['name']} – {s['trait']}")
    print(f"[{len(suspects)+1}] Return")

    choice = input("> ")
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(suspects):
            suspect = suspects[idx]
            process_interrogation(suspect)
        elif idx == len(suspects):
            describe_room()
        else:
            delay_print("Invalid choice.")
            input("\nPress Enter to continue.")
            interrogate_suspect()
    else:
        handle_input(choice, interrogate_suspect)

def process_interrogation(suspect):
    clear()
    delay_print(f"You sit across from {suspect['name']}, watching their every twitch.")
    delay_print(f"They say: \"{suspect['alibi']}\"")
    credibility = calculate_credibility(suspect)
    delay_print(f"\nCredibility rating: {credibility}/10")
    game_state["journal"].append(f"Interrogated {suspect['name']}: {suspect['alibi']} (Credibility: {credibility}/10)")
    game_state["reputation"] += 1
    input("\nPress Enter to continue.")
    describe_room()

def calculate_credibility(suspect):
    base = game_state["perception"] + game_state["sanity"] + game_state["reputation"]
    difficulty = 10
    roll = random.randint(1, 6)
    score = min(10, max(1, base // 3 + roll))
    return score
# --- Case Resolution ---
def case_resolution():
    delay_print("You gather your thoughts and review the case...")
    clue_count = len(game_state["clues"])
    if clue_count >= 4:
        delay_print("The truth emerges like mist parting under a lantern's glow.")
        delay_print("You have enough evidence to accuse the true culprit.")
        game_state["journal"].append(f"Case resolved with {clue_count} clues.")
        game_state["quests"] = []
        input("\nPress Enter to return to the title screen.")
        title_screen()
    else:
        delay_print("Not enough evidence yet... the threads do not fully weave together.")
        input("\nPress Enter to continue.")
        describe_room()

# --- Look Command ---
def look_around():
    room = game_state["location"]
    descriptions = room_templates.get(room, ["A shadowy chamber."])
    first_sentence = descriptions[0].split('.')[0]
    delay_print(f"You look around: {first_sentence}.")
    input("\nPress Enter to continue.")
    previous_menu_function()

# --- Handle Input Extended ---
def handle_input(user_input, return_function):
    global previous_menu_function
    cmd = user_input.lower().strip()
    if cmd in direction_vectors:
        move_to_new_room(cmd)
    elif cmd == "look":
        look_around()
    elif cmd == "help":
        show_help()
    elif cmd == "save":
        save_game()
        return_function()
    elif cmd == "load":
        load_game()
    elif cmd == "quit":
        exit()
    elif cmd in ["back", "menu"]:
        if previous_menu_function:
            previous_menu_function()
        else:
            title_screen()
    elif cmd == "title":
        title_screen()
    elif cmd == "inventory":
        show_inventory()
    elif cmd == "journal":
        show_journal()
    elif cmd == "quests":
        show_quests()
    elif cmd == "map":
        display_map()
    elif cmd == "stats":
        show_stats()
    else:
        delay_print("Unknown command. Type 'help' for available options.")
        return_function()

# --- Save and Load ---
def save_game():
    save_data = {
        **game_state,
        "visited_locations": {f"{x},{y}": name for (x, y), name in game_state["visited_locations"].items()}
    }
    try:
        with open("savegame.json", "w") as f:
            json.dump(save_data, f)
        delay_print("Game saved successfully.")
    except Exception as e:
        delay_print(f"Error saving game: {e}")
    print()
    input("Press Enter to continue.")

def load_game():
    global game_state
    try:
        with open("savegame.json", "r") as f:
            loaded = json.load(f)
            visited = loaded.pop("visited_locations", {})
            game_state.update(loaded)
            game_state["visited_locations"] = {
                tuple(map(int, k.split(','))): v for k, v in visited.items()
            }
        delay_print("Game loaded. Resuming investigation...")
        print()
        input("Press Enter to continue.")
        describe_room()
    except Exception as e:
        delay_print(f"Error loading game: {e}")
        print()
        input("Press Enter to return to the title screen.")
        title_screen()

# --- Journal Display ---
def show_journal():
    clear()
    delay_print("Journal Entries:")
    if game_state["journal"]:
        for entry in game_state["journal"]:
            delay_print(f"- {entry}")
    else:
        delay_print("Your journal is empty.")
    print()
    input("Press Enter to return.")
    if previous_menu_function:
        previous_menu_function()
    else:
        title_screen()

# --- Inventory Display ---
def show_inventory():
    clear()
    delay_print("Inventory:")
    if game_state["inventory"]:
        for item in game_state["inventory"]:
            delay_print(f"- {item}")
    else:
        delay_print("You are carrying nothing.")
    print()
    input("Press Enter to return.")
    if previous_menu_function:
        previous_menu_function()
    else:
        title_screen()

# --- Display Stats ---
def show_stats():
    clear()
    delay_print(f"Name: {game_state['name']}")
    delay_print(f"Gender: {game_state['gender']}")
    delay_print(f"Background: {game_state['background']}")
    for stat in ["faith", "sanity", "perception", "strength", "stamina", "agility", "comeliness"]:
        delay_print(f"{stat.capitalize()}: {game_state[stat]}")
    delay_print(f"Reputation: {game_state.get('reputation', 0)}")
    print()
    input("Press Enter to return.")
    if previous_menu_function:
        previous_menu_function()
    else:
        title_screen()

# --- Game Initialization ---
def initialize_game():
    reset_game_state()
    game_state["reputation"] = 0
    initialize_suspects()
    game_state["visited_locations"][(0, 0)] = "Foyer"
    game_state["location"] = "Foyer"
    game_state["position"] = (0, 0)
    delay_print("A new investigation begins...")
    print()
    input("Press Enter to continue.")
    describe_room()
# --- Case Resolution ---
def case_resolution():
    delay_print("You gather your thoughts and review the case...")
    clue_count = len(game_state["clues"])
    if clue_count >= 4:
        delay_print("The truth emerges like mist parting under a lantern's glow.")
        delay_print("You have enough evidence to accuse the true culprit.")
        game_state["journal"].append(f"Case resolved with {clue_count} clues.")
        game_state["quests"] = []
        input("\nPress Enter to return to the title screen.")
        title_screen()
    else:
        delay_print("Not enough evidence yet... the threads do not fully weave together.")
        input("\nPress Enter to continue.")
        describe_room()

# --- Look Command ---
def look_around():
    room = game_state["location"]
    descriptions = room_templates.get(room, ["A shadowy chamber."])
    first_sentence = descriptions[0].split('.')[0]
    delay_print(f"You look around: {first_sentence}.")
    input("\nPress Enter to continue.")
    previous_menu_function()

# --- Handle Input Extended ---
def handle_input(user_input, return_function):
    global previous_menu_function
    cmd = user_input.lower().strip()
    if cmd in direction_vectors:
        move_to_new_room(cmd)
    elif cmd == "look":
        look_around()
    elif cmd == "help":
        show_help()
    elif cmd == "save":
        save_game()
        return_function()
    elif cmd == "load":
        load_game()
    elif cmd == "quit":
        exit()
    elif cmd in ["back", "menu"]:
        if previous_menu_function:
            previous_menu_function()
        else:
            title_screen()
    elif cmd == "title":
        title_screen()
    elif cmd == "inventory":
        show_inventory()
    elif cmd == "journal":
        show_journal()
    elif cmd == "quests":
        show_quests()
    elif cmd == "map":
        display_map()
    elif cmd == "stats":
        show_stats()
    else:
        delay_print("Unknown command. Type 'help' for available options.")
        return_function()

# --- Save and Load ---
def save_game():
    save_data = {
        **game_state,
        "visited_locations": {f"{x},{y}": name for (x, y), name in game_state["visited_locations"].items()}
    }
    try:
        with open("savegame.json", "w") as f:
            json.dump(save_data, f)
        delay_print("Game saved successfully.")
    except Exception as e:
        delay_print(f"Error saving game: {e}")
    print()
    input("Press Enter to continue.")

def load_game():
    global game_state
    try:
        with open("savegame.json", "r") as f:
            loaded = json.load(f)
            visited = loaded.pop("visited_locations", {})
            game_state.update(loaded)
            game_state["visited_locations"] = {
                tuple(map(int, k.split(','))): v for k, v in visited.items()
            }
        delay_print("Game loaded. Resuming investigation...")
        print()
        input("Press Enter to continue.")
        describe_room()
    except Exception as e:
        delay_print(f"Error loading game: {e}")
        print()
        input("Press Enter to return to the title screen.")
        title_screen()

# --- Journal Display ---
def show_journal():
    clear()
    delay_print("Journal Entries:")
    if game_state["journal"]:
        for entry in game_state["journal"]:
            delay_print(f"- {entry}")
    else:
        delay_print("Your journal is empty.")
    print()
    input("Press Enter to return.")
    if previous_menu_function:
        previous_menu_function()
    else:
        title_screen()

# --- Inventory Display ---
def show_inventory():
    clear()
    delay_print("Inventory:")
    if game_state["inventory"]:
        for item in game_state["inventory"]:
            delay_print(f"- {item}")
    else:
        delay_print("You are carrying nothing.")
    print()
    input("Press Enter to return.")
    if previous_menu_function:
        previous_menu_function()
    else:
        title_screen()

# --- Display Stats ---
def show_stats():
    clear()
    delay_print(f"Name: {game_state['name']}")
    delay_print(f"Gender: {game_state['gender']}")
    delay_print(f"Background: {game_state['background']}")
    for stat in ["faith", "sanity", "perception", "strength", "stamina", "agility", "comeliness"]:
        delay_print(f"{stat.capitalize()}: {game_state[stat]}")
    delay_print(f"Reputation: {game_state.get('reputation', 0)}")
    print()
    input("Press Enter to return.")
    if previous_menu_function:
        previous_menu_function()
    else:
        title_screen()

# --- Game Initialization ---
def initialize_game():
    reset_game_state()
    game_state["reputation"] = 0
    initialize_suspects()
    game_state["visited_locations"][(0, 0)] = "Foyer"
    game_state["location"] = "Foyer"
    game_state["position"] = (0, 0)
    delay_print("A new investigation begins...")
    print()
    input("Press Enter to continue.")
    describe_room()
# --- Title Screen ---
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

# --- Instructions ---
def instructions():
    global previous_menu_function
    previous_menu_function = instructions
    clear()
    delay_print("Navigate using number keys. Choices shape sanity, stats, and storyline.")
    delay_print("You play an investigator in a dark Victorian world of cults and secrets.")
    delay_print("Global commands: N, S, E, W, NE, NW, SE, SW, save, load, help, inventory, journal, stats, quests, map, look.")
    delay_print("Use skill checks and clues to solve the case before your sanity runs dry.")
    print()
    input("Press Enter to return to the title screen.")
    title_screen()

# --- Dream Flashback Sequence ---
def dream_flashback():
    global previous_menu_function
    previous_menu_function = dream_flashback
    clear()
    delay_print("You are dreaming... or remembering.")
    delay_print("A chapel cloaked in shadow. A child's voice echoes like a song half-remembered.")
    delay_print("You wake, heart pounding, the image of a burning sigil scorched behind your eyelids.")
    print()
    input("Press Enter to continue.")
    intro_scene()

# --- Intro Scene ---
def intro_scene():
    global previous_menu_function
    previous_menu_function = intro_scene
    clear()
    delay_print("London, 1865. A fog creeps through crooked alleys. Gaslamps flicker, dying in the mist.")
    delay_print("The manor looms ahead, its gates half-open. An unnatural silence presses against your ears.")
    print("\nWhat will you do?")
    print("[1] Enter through the front gate")
    print("[2] Examine the grounds")
    print("[3] Pray silently")

    user_input = input("\n> ").strip().lower()
    if user_input == "1":
        enter_manor()
    elif user_input == "2":
        game_state["inventory"].append("Bent Key")
        character_creation()
    elif user_input == "3":
        game_state["faith"] += 1
        character_creation()
    else:
        handle_input(user_input, intro_scene)

# --- Manor Entry ---
def enter_manor():
    global previous_menu_function
    previous_menu_function = enter_manor
    clear()
    delay_print("You step inside the manor. The scent of mildew and ash hits you. A shadow slips upstairs.")
    print()
    input("Press Enter to continue.")
    character_creation()

# --- Character Creation ---
def character_creation():
    global previous_menu_function
    previous_menu_function = character_creation
    clear()
    delay_print("Before the hunt begins... who are you?")
    game_state["name"] = input("Name: ")
    game_state["gender"] = input("Gender: ")

    print("\nChoose your background:")
    print("[1] Theologian – +2 Faith")
    print("[2] Occultist – +2 Sanity")
    print("[3] Detective – +2 Perception")
    print("[4] Ex-Priest – +1 Faith, +1 Sanity")

    bg = input("> ").strip()
    if bg == "1":
        game_state["background"] = "Theologian"
        game_state["faith"] += 2
    elif bg == "2":
        game_state["background"] = "Occultist"
        game_state["sanity"] += 2
    elif bg == "3":
        game_state["background"] = "Detective"
        game_state["perception"] += 2
    elif bg == "4":
        game_state["background"] = "Ex-Priest"
        game_state["faith"] += 1
        game_state["sanity"] += 1
    else:
        character_creation()
        return

    # Assign base stats
    for stat in ["faith", "sanity", "perception", "strength", "stamina", "agility", "comeliness"]:
        game_state[stat] += random.randint(1, 3)

    # Allow stat customization
    stat_points = 6
    print("\nDistribute 6 extra points among your attributes:")
    while stat_points > 0:
        print(f"\nPoints left: {stat_points}")
        for stat in ["faith", "sanity", "perception", "strength", "stamina", "agility", "comeliness"]:
            print(f"{stat.capitalize()}: {game_state[stat]}")
        choice = input("Choose stat: ").lower()
        if choice in game_state and choice in ["faith", "sanity", "perception", "strength", "stamina", "agility", "comeliness"]:
            try:
                add = int(input(f"Add how many to {choice}? "))
                if 0 < add <= stat_points:
                    game_state[choice] += add
                    stat_points -= add
                else:
                    print("Invalid amount.")
            except ValueError:
                print("Must enter a number.")
        else:
            print("Invalid stat.")
    
    print("\nFinal stats:")
    for stat in ["faith", "sanity", "perception", "strength", "stamina", "agility", "comeliness"]:
        print(f"{stat.capitalize()}: {game_state[stat]}")
    if input("Confirm? (Y/N): ").lower().strip() != 'y':
        return character_creation()

    initialize_game()
# --- Initialize Game State ---
def initialize_game():
    initialize_suspects()
    assign_murderer()
    generate_room_map()
    game_state["quests"].append("Investigate the manor")
    game_state["visited_locations"] = {(0, 0): "Foyer"}
    game_state["location"] = "Foyer"
    game_state["position"] = (0, 0)
    game_state["turns"] = 0
    game_state["journal"].append("Entered the manor to begin investigation.")
    delay_print(f"Welcome, {game_state['name']} the {game_state['background']}. The hour is late, and the shadows grow bold.")
    input("Press Enter to begin.")
    describe_room()

# --- Assign One Murderer Among Suspects ---
def assign_murderer():
    murderer = random.choice(game_state["suspects"])
    murderer["murderer"] = True
    for suspect in game_state["suspects"]:
        if "murderer" not in suspect:
            suspect["murderer"] = False

# --- Run Interrogation with Hybrid Combat Option ---
def interrogate_suspect():
    global previous_menu_function
    previous_menu_function = interrogate_suspect
    clear()
    delay_print("Choose a suspect to interrogate:")
    for idx, s in enumerate(game_state["suspects"]):
        print(f"[{idx+1}] {s['name']} – {s['trait']}")
    print(f"[{len(game_state['suspects'])+1}] Return")

    choice = input("> ").strip()
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(game_state["suspects"]):
            suspect = game_state["suspects"][idx]
            run_interrogation(suspect)
        else:
            describe_room()
    else:
        handle_input(choice, interrogate_suspect)

def run_interrogation(suspect):
    clear()
    delay_print(f"You confront {suspect['name']}.")
    delay_print(f'"{suspect["alibi"]}"')

    score = credibility_score(suspect)
    labels = {4: "Highly Credible", 3: "Credible", 2: "Dubious", 1: "Contradictory"}
    label = labels.get(score, "Unknown")

    game_state["journal"].append(f"Interrogated {suspect['name']} – Response was {label}.")
    input("\nPress Enter to continue.")
    print("\n[1] Continue Investigation")
    print("[2] Accuse")
    print("[3] Attack")
    print("[4] Return")
    choice = input("> ").strip()
    if choice == "1":
        describe_room()
    elif choice == "2":
        handle_accusation(suspect)
    elif choice == "3":
        skill_check_combat(suspect["name"], 5 + random.randint(1, 4), "strength")
        describe_room()
    else:
        describe_room()

# --- Accusation System ---
def handle_accusation(suspect):
    if suspect.get("murderer"):
        delay_print("You accuse the murderer. Justice is served!")
        game_state["journal"].append(f"Accused {suspect['name']} – Confirmed guilty.")
        input("Press Enter to conclude the case.")
        title_screen()
    else:
        delay_print("Your accusation was wrong. The true killer remains at large...")
        game_state["sanity"] -= 2
        game_state["journal"].append(f"Accused {suspect['name']} – Innocent.")
        input("Press Enter to continue.")
        describe_room()

# --- Credibility Score Calculator ---
def credibility_score(suspect):
    base = game_state["perception"] // 3
    bonus = game_state.get("reputation", 0)
    roll = random.randint(1, 4)
    total = base + bonus + roll
    if suspect.get("murderer"):
        total -= 2  # More likely to lie
    return max(1, min(4, total))

# --- NPC Dynamic Movement System (Turn-Based) ---
def npc_movement():
    occupied = set([game_state["position"]])
    for suspect in game_state["suspects"]:
        move = random.choice(list(direction_vectors.values()))
        current_pos = suspect.get("position", (0, 0))
        new_pos = (current_pos[0] + move[0], current_pos[1] + move[1])
        if new_pos not in occupied:
            suspect["position"] = new_pos
            occupied.add(new_pos)

# --- Look Global Command ---
def look_room():
    descs = room_templates.get(game_state["location"], ["It's hard to see anything."])
    first_sentence = descs[0].split(".")[0] + "."
    delay_print(first_sentence)
    print()
    input("Press Enter to continue.")
    previous_menu_function()

# --- Global Input Mod Extension (Including Directions) ---
def handle_input(user_input, return_function):
    global previous_menu_function
    dirs = ["n", "s", "e", "w", "ne", "nw", "se", "sw"]
    if user_input == "help":
        show_help()
    elif user_input == "save":
        save_game()
        return_function()
    elif user_input == "load":
        load_game()
    elif user_input == "quit":
        exit()
    elif user_input in ["back", "menu"]:
        if previous_menu_function:
            previous_menu_function()
        else:
            title_screen()
    elif user_input == "title":
        title_screen()
    elif user_input == "inventory":
        show_inventory()
    elif user_input == "journal":
        show_journal()
    elif user_input == "quests":
        show_quests()
    elif user_input == "map":
        display_map()
    elif user_input == "stats":
        show_stats()
    elif user_input == "look":
        look_room()
    elif user_input in dirs:
        move_to_new_room(user_input)
    else:
        delay_print("Unknown command. Type 'help' for options.")
        return_function()
