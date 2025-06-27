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
    "observation": 0,
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
    ]
}

suspect_templates = [
    {"name": "Miss Vexley", "trait": "Nervous", "alibi": "Claims she was in the chapel praying."},
    {"name": "Dr. Lorn", "trait": "Stoic", "alibi": "Was tending the fire in the lounge."},
    {"name": "Bishop Greaves", "trait": "Fanatical", "alibi": "Says he heard voices in the cellar."},
    {"name": "Mr. Corven", "trait": "Charming", "alibi": "Claims he was entertaining guests all night."}
]

clue_pool = [
    "A silver pendant etched with tentacles.",
    "Blood-stained prayer book.",
    "Footprints leading to a sealed hatch.",
    "A coded diary mentioning a 'Summoning'.",
    "An empty ritual circle drawn in chalk.",
    "A page torn from a forbidden tome."
]

# --- Reset Game State Function ---
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
    for stat in ["faith", "sanity", "observation", "strength", "stamina", "agility", "comeliness"]:
        game_state[stat] = 0
    game_state["name"] = ""
    game_state["gender"] = ""
    game_state["background"] = ""

# Helper functions

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def delay_print(s, speed=0.02):
    for c in s:
        print(c, end='', flush=True)
        time.sleep(speed)
    print()

def save_game():
    with open("savegame.json", "w") as f:
        json.dump(game_state, f)
    delay_print("Game saved.")
    input("Press Enter to continue.")

def load_game():
    global game_state
    if os.path.exists("savegame.json"):
        with open("savegame.json", "r") as f:
            game_state = json.load(f)
        delay_print("Game loaded.")
        input("Press Enter to continue.")
        describe_room()
    else:
        delay_print("No save file found.")
        input("Press Enter to return.")
        title_screen()

def initialize_suspects():
    game_state["suspects"] = random.sample(suspect_templates, 3)

def show_stats():
    clear()
    delay_print(f"Name: {game_state['name']}")
    delay_print(f"Gender: {game_state['gender']}")
    delay_print(f"Background: {game_state['background']}")
    for stat in ["faith", "sanity", "observation", "strength", "stamina", "agility", "comeliness"]:
        delay_print(f"{stat.capitalize()}: {game_state[stat]}")
    input("Press Enter to return.")
    if previous_menu_function:
        previous_menu_function()
    else:
        title_screen()

def show_journal():
    clear()
    delay_print("Journal Entries:")
    if game_state["journal"]:
        for entry in game_state["journal"]:
            delay_print(f"- {entry}")
    else:
        delay_print("Your journal is empty.")
    input("Press Enter to return.")
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
    input("Press Enter to return.")
    if previous_menu_function:
        previous_menu_function()
    else:
        title_screen()

def show_map():
    clear()
    location = game_state["location"]
    pos = game_state["position"]
    delay_print(f"Current Location: {location} at {pos}")
    # ASCII map rendering
    delay_print("\nMap:")
    render_map()
    input("Press Enter to return.")
    if previous_menu_function:
        previous_menu_function()
    else:
        title_screen()

def render_map():
    # Show a simple 7x7 grid centered around player position (0,0)
    grid_size = 7
    half = grid_size // 2
    px, py = game_state["position"]

    for y in range(py - half, py + half + 1):
        row = ""
        for x in range(px - half, px + half + 1):
            if (x,y) == (px, py):
                # Player position
                row += " @ "
            elif (x,y) in game_state["visited_locations"]:
                loc = game_state["visited_locations"][(x,y)]
                row += f" {loc[0]} "  # First letter of location
            else:
                row += " . "
        print(row)

def show_inventory():
    clear()
    delay_print("Inventory:")
    if game_state["inventory"]:
        delay_print(", ".join(game_state["inventory"]))
    else:
        delay_print("Your inventory is empty.")
    input("Press Enter to return.")
    if previous_menu_function:
        previous_menu_function()
    else:
        title_screen()

def handle_input(user_input, return_function):
    global previous_menu_function
    if user_input == "help":
        show_help()
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
    elif user_input == "inventory":
        show_inventory()
    elif user_input == "journal":
        show_journal()
    elif user_input == "quests":
        show_quests()
    elif user_input == "map":
        show_map()
    elif user_input == "stats":
        show_stats()
    else:
        delay_print("Unknown command. Type 'help' for available options.")
        return_function()

def show_help():
    delay_print("Available commands:")
    delay_print("- save: Save your game")
    delay_print("- load: Load a previous save")
    delay_print("- quit: Quit the game")
    delay_print("- back/menu: Return to the previous menu")
    delay_print("- title: Return to the title screen")
    delay_print("- inventory: Show your inventory")
    delay_print("- journal: Show your journal entries")
    delay_print("- quests: Show active quests")
    delay_print("- map: Show current location")
    delay_print("- stats: Show character stats")
    input("Press Enter to return.")
    if previous_menu_function:
        previous_menu_function()
    else:
        title_screen()

def title_screen():
    global previous_menu_function
    previous_menu_function = title_screen
    clear()
    print("""
  _____                              _             
 |  __ \                            (_)            
 | |__) |__ _ __ ___ _   _  __ _ ___ _  ___  _ __  
 |  ___/ _ \ '__/ __| | | |/ _` / __| |/ _ \| '_ \\
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
    input("Press Enter to return.")
    title_screen()

def move_to_new_room(direction=None):
    # Movement logic using coordinate system and visited_locations
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
    new_pos = (x + dx, y + dy)
    game_state["position"] = new_pos

    # Assign a new or existing location name for new_pos
    if new_pos not in game_state["visited_locations"]:
        new_location = random.choice(list(room_templates.keys()))
        game_state["visited_locations"][new_pos] = new_location
    game_state["location"] = game_state["visited_locations"][new_pos]

    input("Press Enter to enter the new room.")
    describe_room()

# Add clue with pause
def add_random_clue():
    clue = random.choice(clue_pool)
    if clue not in game_state["clues"]:
        game_state["clues"].append(clue)
        delay_print(f"Clue discovered: {clue}")
        game_state["journal"].append(f"Clue found: {clue}")
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
    delay_print(random.choice(descriptions))
    print("\nWhat would you like to do?")
    print("[1] Search the room")
    print("[2] Move to another room")
    print("[3] Check journal")
    print("[4] Check inventory")
    print("[5] Interrogate suspect")
    print("[6] Attempt case resolution")
    print("[7] Save game")
    print("[8] Quit to title")

    user_input = input("> ").strip().lower()
    if user_input == "1":
        add_random_clue()
        describe_room()
    elif user_input == "2":
        # Ask for direction input
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
        show_journal()
    elif user_input == "4":
        show_inventory()
    elif user_input == "5":
        interrogate_suspect()
    elif user_input == "6":
        case_resolution()
    elif user_input == "7" or user_input == "save":
        save_game()
        describe_room()
    elif user_input == "8" or user_input == "quit":
        title_screen()
    else:
        handle_input(user_input, describe_room)
def interrogate_suspect():
    global previous_menu_function
    previous_menu_function = interrogate_suspect
    suspects = game_state["suspects"]
    clear()
    print("\nChoose someone to interrogate:")
    for i, s in enumerate(suspects):
        print(f"[{i+1}] {s['name']} – {s['trait']}")
    print(f"[{len(suspects)+1}] Return")

    user_input = input("> ").strip().lower()
    if user_input.isdigit():
        idx = int(user_input) - 1
        if 0 <= idx < len(suspects):
            suspect = suspects[idx]
            clear()
            delay_print(f"You confront {suspect['name']}.")
            delay_print(suspect["alibi"])
            input("Press Enter to continue.")
            describe_room()
        elif idx == len(suspects):
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
    delay_print("London, 1865. A fog rolls in over the cobblestones, thick and clinging, curling like smoke through the iron gates of the city’s forgotten quarters. The gaslamps flicker under its damp touch, casting pale halos that only make the darkness beyond feel deeper—hungrier...")
    print("\nWhat will you do?")
    print("[1] Enter through the front gate")
    print("[2] Examine the grounds")
    print("[3] Pray silently")

    user_input = input("> ").strip().lower()
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

def enter_manor():
    global previous_menu_function
    previous_menu_function = enter_manor
    clear()
    delay_print("You step into the manor, the scent of mildew thick in your nostrils. A shadow slips past the stairs, just at the edge of sight.")
    character_creation()

def character_creation():
    global previous_menu_function
    previous_menu_function = character_creation
    clear()
    delay_print("Before the hunt begins... who are you? The fog of the past clings to you, refusing to part until you define yourself.")
    game_state["name"] = input("Name: ")
    game_state["gender"] = input("Gender: ")

    print("\nChoose your background:")
    print("[1] Theologian – +2 Faith")
    print("[2] Occultist – +2 Sanity")
    print("[3] Detective – +2 Observation")
    print("[4] Ex-Priest – +1 Faith, +1 Sanity")

    bg = input("> ")
    if bg == "1":
        game_state["background"] = "Theologian"
        game_state["faith"] += 2
    elif bg == "2":
        game_state["background"] = "Occultist"
        game_state["sanity"] += 2
    elif bg == "3":
        game_state["background"] = "Detective"
        game_state["observation"] += 2
    elif bg == "4":
        game_state["background"] = "Ex-Priest"
        game_state["faith"] += 1
        game_state["sanity"] += 1
    else:
        character_creation()
        return

    # Assign base values and random bonus to all stats
    for stat in ["faith", "sanity", "observation", "strength", "stamina", "agility", "comeliness"]:
        base = 8 + random.randint(1, 4)
        game_state[stat] = base

    # Allow player to distribute 6 additional points
    stat_points = 6
    print("\nDistribute 6 additional points among your attributes (for a max of 18):")
    while stat_points > 0:
        print(f"\nPoints remaining: {stat_points}")
        for stat in ["faith", "sanity", "observation", "strength", "stamina", "agility", "comeliness"]:
            print(f"{stat.capitalize()}: [{game_state[stat]}]")

        chosen_stat = input("\nEnter the attribute to increase: ").lower()
        if chosen_stat not in game_state or chosen_stat not in ["faith", "sanity", "observation", "strength", "stamina", "agility", "comeliness"]:
            print("Invalid stat name. Try again.")
            continue

        try:
            add = int(input(f"How many points would you like to add to {chosen_stat.capitalize()}? (You have {stat_points} left): "))
            if 0 <= add <= stat_points:
                game_state[chosen_stat] += add
                stat_points -= add
            else:
                print("Invalid amount. Please enter a number within the remaining point range.")
        except ValueError:
            print("Please enter a valid number.")

    # Final confirmation
    print("\nFinal attributes:")
    for stat in ["faith", "sanity", "observation", "strength", "stamina", "agility", "comeliness"]:
        print(f"{stat.capitalize()}: {game_state[stat]}")

    confirm = input("Accept these stats? (Y/N): ").strip().lower()
    if confirm != 'y':
        character_creation()
        return

    initialize_suspects()
    # Mark starting location visited at (0,0)
    game_state["visited_locations"] = {(0, 0): "Foyer"}
    game_state["location"] = "Foyer"
    game_state["position"] = (0, 0)
    delay_print(f"Welcome, {game_state['name']} the {game_state['background']}. The hour is late, and the shadows grow bold.")
    input("Press Enter to begin.")
    start_first_case()

def start_first_case():
    global previous_menu_function
    previous_menu_function = start_first_case
    game_state["quests"].append("Investigate Manor Seance")
    describe_room()

# --- Skill-check combat system ---

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
        game_state["journal"].append(f"Defeated by {enemy_name}. Survived, but barely.")

    input("Press Enter to continue.")

# Start the game by showing title screen
title_screen()
# Movement system with coordinates and ASCII map visualization

# Direction vectors for coordinate changes
direction_vectors = {
    "n":  (0, 1),
    "s":  (0, -1),
    "e":  (1, 0),
    "w":  (-1, 0),
    "ne": (1, 1),
    "nw": (-1, 1),
    "se": (1, -1),
    "sw": (-1, -1)
}

def display_map():
    clear()
    # Get all visited coordinates
    coords = list(game_state.get("visited_locations", {}).keys())
    if not coords:
        delay_print("Map is empty. No locations visited yet.")
        input("Press Enter to return.")
        previous_menu_function()
        return
    
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    # Build a grid
    grid = []
    for y in range(max_y, min_y - 1, -1):
        row = []
        for x in range(min_x, max_x + 1):
            if (x, y) == game_state.get("position"):
                row.append("P")  # Player's current position
            elif (x, y) in game_state["visited_locations"]:
                row.append("O")  # Visited location
            else:
                row.append(".")  # Unknown / unvisited
        grid.append(row)

    # Print the map
    print("Map Key: P=You, O=Visited Location, .=Unknown\n")
    for row in grid:
        print(" ".join(row))

    print("\nVisited Locations:")
    for coord, name in game_state["visited_locations"].items():
        print(f"{name} at {coord}")

    input("\nPress Enter to return.")
    previous_menu_function()

def move_player():
    global previous_menu_function
    previous_menu_function = move_player
    clear()
    delay_print(f"Current location: {game_state['location']} at {game_state['position']}")
    delay_print("Choose direction to move: N, S, E, W, NE, NW, SE, SW or 'back' to return.")
    user_input = input("> ").strip().lower()

    if user_input in ["back", "menu"]:
        previous_menu_function = describe_room
        describe_room()
        return
    elif user_input in direction_vectors:
        dx, dy = direction_vectors[user_input]
        new_x = game_state["position"][0] + dx
        new_y = game_state["position"][1] + dy
        new_pos = (new_x, new_y)

        # Check if location exists or create new room
        if new_pos in game_state.get("visited_locations", {}):
            new_location = game_state["visited_locations"][new_pos]
        else:
            new_location = random.choice(list(room_templates.keys()))
            game_state["visited_locations"][new_pos] = new_location

        game_state["position"] = new_pos
        game_state["location"] = new_location
        delay_print(f"You move {user_input.upper()} to {new_location}.")
        input("Press Enter to continue.")
        describe_room()
    else:
        delay_print("Invalid direction.")
        input("Press Enter to continue.")
        move_player()

# Modify describe_room menu to include move_player option

def describe_room():
    global previous_menu_function
    previous_menu_function = describe_room
    clear()
    room = game_state["location"]
    descriptions = room_templates.get(room, ["It's a bare and quiet room."])
    delay_print(random.choice(descriptions))
    print("\nWhat would you like to do?")
    print("[1] Search the room")
    print("[2] Move to another room (directional)")
    print("[3] Check journal")
    print("[4] Check inventory")
    print("[5] Interrogate suspect")
    print("[6] Attempt case resolution")
    print("[7] View map")
    print("[8] Save game")
    print("[9] Quit to title")

    user_input = input("> ").strip().lower()
    if user_input == "1":
        add_random_clue()
        describe_room()
    elif user_input == "2":
        move_player()
    elif user_input == "3":
        show_journal()
    elif user_input == "4":
        show_inventory()
    elif user_input == "5":
        interrogate_suspect()
    elif user_input == "6":
        case_resolution()
    elif user_input == "7":
        display_map()
    elif user_input == "8" or user_input == "save":
        save_game()
        describe_room()
    elif user_input == "9" or user_input == "quit":
        title_screen()
    else:
        handle_input(user_input, describe_room)
def save_game():
    # Save full game state including visited locations and position
    with open("savegame.json", "w") as f:
        json.dump(game_state, f)
    delay_print("Game saved.")
    input("Press Enter to continue.")

def load_game():
    global game_state, previous_menu_function
    if os.path.exists("savegame.json"):
        with open("savegame.json", "r") as f:
            game_state = json.load(f)
        delay_print("Game loaded.")
        input("Press Enter to continue.")
        if "position" not in game_state or "visited_locations" not in game_state:
            # Initialize if missing
            game_state["position"] = (0, 0)
            game_state["visited_locations"] = {(0, 0): game_state.get("location", "Foyer")}
        previous_menu_function = describe_room
        describe_room()
    else:
        delay_print("No save file found.")
        input("Press Enter to return.")
        title_screen()

def new_investigation_setup():
    global game_state
    # Clear all game state except name, gender, background for new game
    keep_keys = ["name", "gender", "background"]
    saved_data = {k: game_state.get(k, "") for k in keep_keys}
    game_state.clear()
    game_state.update({
        "faith": 0,
        "sanity": 10,
        "observation": 0,
        "strength": 0,
        "stamina": 0,
        "agility": 0,
        "comeliness": 0,
        "inventory": [],
        "quests": [],
        "location": "Foyer",
        "suspects": [],
        "clues": [],
        "journal": [],
        "turns": 0,
        "visited_locations": {(0, 0): "Foyer"},
        "position": (0, 0)
    })
    game_state.update(saved_data)
    initialize_suspects()
    delay_print(f"Starting new investigation, {game_state['name']}...")
    input("Press Enter to continue.")
    describe_room()

def title_screen():
    global previous_menu_function
    previous_menu_function = title_screen
    clear()
    print("""
  _____                              _             
 |  __ \\                            (_)            
 | |__) |__ _ __ ___ _   _  __ _ ___ _  ___  _ __  
 |  ___/ _ \\ '__/ __| | | |/ _` / __| |/ _ \\| '_ \\
 | |  |  __/ |  \\__ \\ |_| | (_| \\__ \\ | (_) | | | |
 |_|   \\___|_|  |___/\\__,_|\\__,_|___/_|\\___/|_| |_|
                                                  
         A Victorian Roguelike Mystery
    """)
    print("[1] Begin New Investigation")
    print("[2] Load Game")
    print("[3] Instructions")
    print("[4] Quit")

    user_input = input("\n> ").strip().lower()

    if user_input == "1":
        character_creation()
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
    input("Press Enter to return.")
    title_screen()

def character_creation():
    global previous_menu_function
    previous_menu_function = character_creation
    clear()
    delay_print("Before the hunt begins... who are you? The fog of the past clings to you, refusing to part until you define yourself.")
    game_state["name"] = input("Name: ")
    game_state["gender"] = input("Gender: ")

    print("\nChoose your background:")
    print("[1] Theologian – +2 Faith")
    print("[2] Occultist – +2 Sanity")
    print("[3] Detective – +2 Observation")
    print("[4] Ex-Priest – +1 Faith, +1 Sanity")

    bg = input("> ")
    if bg == "1":
        game_state["background"] = "Theologian"
        game_state["faith"] += 2
    elif bg == "2":
        game_state["background"] = "Occultist"
        game_state["sanity"] += 2
    elif bg == "3":
        game_state["background"] = "Detective"
        game_state["observation"] += 2
    elif bg == "4":
        game_state["background"] = "Ex-Priest"
        game_state["faith"] += 1
        game_state["sanity"] += 1
    else:
        character_creation()

    # Assign base values and random bonus to all stats
    for stat in ["faith", "sanity", "observation", "strength", "stamina", "agility", "comeliness"]:
        base = 8 + random.randint(1, 4)
        game_state[stat] = base

    # Allow player to distribute 6 additional points
    stat_points = 6
    print("\nDistribute 6 additional points among your attributes (for a max of 18):")
    while stat_points > 0:
        print(f"\nPoints remaining: {stat_points}")
        for stat in ["faith", "sanity", "observation", "strength", "stamina", "agility", "comeliness"]:
            print(f"{stat.capitalize()}: [{game_state[stat]}]")

        chosen_stat = input("\nEnter the attribute to increase: ").lower()
        if chosen_stat not in game_state or chosen_stat not in ["faith", "sanity", "observation", "strength", "stamina", "agility", "comeliness"]:
            print("Invalid stat name. Try again.")
            continue

        try:
            add = int(input(f"How many points would you like to add to {chosen_stat.capitalize()}? (You have {stat_points} left): "))
            if 0 <= add <= stat_points:
                game_state[chosen_stat] += add
                stat_points -= add
            else:
                print("Invalid amount. Please enter a number within the remaining point range.")
        except ValueError:
            print("Please enter a valid number.")

    # Final confirmation
    print("\nFinal attributes:")
    for stat in ["faith", "sanity", "observation", "strength", "stamina", "agility", "comeliness"]:
        print(f"{stat.capitalize()}: {game_state[stat]}")

    confirm = input("Accept these stats? (Y/N): ").strip().lower()
    if confirm != 'y':
        return character_creation()

    new_investigation_setup()
def new_investigation_setup():
    # Clear previous game data when starting a new investigation
    game_state["inventory"] = []
    game_state["journal"] = []
    game_state["quests"] = []
    game_state["clues"] = []
    game_state["suspects"] = []
    game_state["turns"] = 0
    initialize_suspects()
    delay_print(f"Welcome, {game_state['name']} the {game_state['background']}. The hour is late, and the shadows grow bold.")
    input("Press Enter to begin.")
    start_first_case()

def start_first_case():
    global previous_menu_function
    previous_menu_function = start_first_case
    game_state["quests"].append("Investigate Manor Seance")
    game_state["location"] = "Foyer"
    describe_room()

def describe_room():
    global previous_menu_function
    previous_menu_function = describe_room
    clear()
    room = game_state["location"]
    descriptions = room_templates.get(room, ["It's a bare and quiet room."])
    delay_print(random.choice(descriptions))
    print("\nWhat would you like to do?")
    print("[1] Search the room")
    print("[2] Move to another room")
    print("[3] Check journal")
    print("[4] Check inventory")
    print("[5] Interrogate suspect")
    print("[6] Attempt case resolution")
    print("[7] Save game")
    print("[8] Quit to title")

    user_input = input("> ").strip().lower()
    if user_input == "1":
        add_random_clue()
        describe_room()
    elif user_input == "2":
        move_to_new_room()
    elif user_input == "3":
        show_journal()
    elif user_input == "4":
        show_inventory()
    elif user_input == "5":
        interrogate_suspect()
    elif user_input == "6":
        case_resolution()
    elif user_input == "7" or user_input == "save":
        save_game()
        describe_room()
    elif user_input == "8" or user_input == "quit":
        title_screen()
    else:
        handle_input(user_input, describe_room)
def interrogate_suspect():
    global previous_menu_function
    previous_menu_function = interrogate_suspect
    suspects = game_state["suspects"]
    print("\nChoose someone to interrogate:")
    for i, s in enumerate(suspects):
        print(f"[{i+1}] {s['name']} – {s['trait']}")
    print(f"[{len(suspects)+1}] Return")

    user_input = input("> ").strip().lower()
    if user_input.isdigit():
        idx = int(user_input) - 1
        if 0 <= idx < len(suspects):
            suspect = suspects[idx]
            delay_print(f"You confront {suspect['name']}.")
            delay_print(suspect["alibi"])
            input("Press Enter to continue.")
            describe_room()
        elif idx == len(suspects):
            describe_room()
        else:
            handle_input(user_input, interrogate_suspect)
    else:
        handle_input(user_input, interrogate_suspect)

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
    delay_print("London, 1865. A fog rolls in over the cobblestones, thick and clinging, curling like smoke through the iron gates of the city’s forgotten quarters. The gaslamps flicker under its damp touch, casting pale halos that only make the darkness beyond feel deeper—hungrier...")
    print("\nWhat will you do?")
    print("[1] Enter through the front gate")
    print("[2] Examine the grounds")
    print("[3] Pray silently")

    user_input = input("> ").strip().lower()
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

def enter_manor():
    global previous_menu_function
    previous_menu_function = enter_manor
    delay_print("You step into the manor, the scent of mildew thick in your nostrils. A shadow slips past the stairs, just at the edge of sight.")
    character_creation()

def character_creation():
    global previous_menu_function
    previous_menu_function = character_creation
    clear()
    delay_print("Before the hunt begins... who are you? The fog of the past clings to you, refusing to part until you define yourself.")
    game_state["name"] = input("Name: ")
    game_state["gender"] = input("Gender: ")

    print("\nChoose your background:")
    print("[1] Theologian – +2 Faith")
    print("[2] Occultist – +2 Sanity")
    print("[3] Detective – +2 Observation")
    print("[4] Ex-Priest – +1 Faith, +1 Sanity")

    bg = input("> ")
    if bg == "1":
        game_state["background"] = "Theologian"
        game_state["faith"] += 2
    elif bg == "2":
        game_state["background"] = "Occultist"
        game_state["sanity"] += 2
    elif bg == "3":
        game_state["background"] = "Detective"
        game_state["observation"] += 2
    elif bg == "4":
        game_state["background"] = "Ex-Priest"
        game_state["faith"] += 1
        game_state["sanity"] += 1
    else:
        character_creation()

    # Assign base values and random bonus to all stats
    for stat in ["faith", "sanity", "observation", "strength", "stamina", "agility", "comeliness"]:
        base = 8 + random.randint(1, 4)
        game_state[stat] = base

    # Allow player to distribute 6 additional points
    stat_points = 6
    print("\nDistribute 6 additional points among your attributes (for a max of 18):")
    while stat_points > 0:
        print(f"\nPoints remaining: {stat_points}")
        for stat in ["faith", "sanity", "observation", "strength", "stamina", "agility", "comeliness"]:
            print(f"{stat.capitalize()}: [{game_state[stat]}]")

        chosen_stat = input("\nEnter the attribute to increase: ").lower()
        if chosen_stat not in game_state or chosen_stat not in ["faith", "sanity", "observation", "strength", "stamina", "agility", "comeliness"]:
            print("Invalid stat name. Try again.")
            continue

        try:
            add = int(input(f"How many points would you like to add to {chosen_stat.capitalize()}? (You have {stat_points} left): "))
            if 0 <= add <= stat_points:
                game_state[chosen_stat] += add
                stat_points -= add
            else:
                print("Invalid amount. Please enter a number within the remaining point range.")
        except ValueError:
            print("Please enter a valid number.")

    # Final confirmation
    print("\nFinal attributes:")
    for stat in ["faith", "sanity", "observation", "strength", "stamina", "agility", "comeliness"]:
        print(f"{stat.capitalize()}: {game_state[stat]}")

    confirm = input("Accept these stats? (Y/N): ").strip().lower()
    if confirm != 'y':
        return character_creation()

    new_investigation_setup()

# Start the game
title_screen()
