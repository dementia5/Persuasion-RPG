# Persuasion: Victorian Roguelike Investigation Game
# Core Game Script

import os
import time
import random
import json

# Global player state
previous_menu_function = None

valid_directions = {"n", "s", "e", "w", "ne", "nw", "se", "sw"}

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
}

room_templates = {
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
    {"name": "Miss Vexley", "trait": "Nervous", "alibi": "Claims she was in the chapel praying."},
    {"name": "Dr. Lorn", "trait": "Stoic", "alibi": "Was tending the fire in the lounge."},
    {"name": "Bishop Greaves", "trait": "Fanatical", "alibi": "Says he heard voices in the cellar."},
    {"name": "Colonel Catsup", "trait": "Charming", "alibi": "Claims he was entertaining guests all night."}
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
    game_state["position"] = (5, 1)
    for stat in ["faith", "sanity", "perception", "strength", "stamina", "agility", "comeliness"]:
        game_state[stat] = 0
    game_state["name"] = ""
    game_state["gender"] = ""
    game_state["background"] = ""

# Helper functions

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def delay_print(s, speed=0.03):
    for c in s:
        print(c, end='', flush=True)
        time.sleep(speed)
    print()

import json
import os

def save_game():
    try:
        # Convert tuple keys in visited_locations to strings for JSON
        game_state_copy = game_state.copy()
        visited_serializable = {str(k): v for k, v in game_state["visited_locations"].items()}
        game_state_copy["visited_locations"] = visited_serializable

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


def initialize_suspects():
    game_state["suspects"] = random.sample(suspect_templates, 3)

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
            delay_print(f"- {entry}")
    else:
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

def show_map():
    clear()
    location = game_state["location"]
    pos = game_state["position"]
    delay_print(f"Current Location: {location} at {pos}")
    # ASCII map rendering
    delay_print("\nMap:")
    render_map()
    input("\nPress Enter to return.")

    if previous_menu_function:
        previous_menu_function()
    else:
        title_screen()

def render_map():
    # Show a simple 11x11 grid centered around player position (0,0)
    grid_size = 11
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
    input("\nPress Enter to return.")

    if previous_menu_function:
        previous_menu_function()
    else:
        title_screen()

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
    input("\nPress Enter to return.")

    title_screen()

# --- Have narrative text distort as insanity increases ---

import random

def distort_text(text, sanity):
    if sanity >= 7:
        return text  # Clear
    elif sanity >= 4:
        # Mild distortion: scramble a few words
        words = text.split()
        for i in range(len(words)):
            if random.random() < 0.3:
                words[i] = ''.join(random.sample(words[i], len(words[i])))
        return ' '.join(words)
    elif sanity >= 1:
        # Severe distortion: reverse words and sentences
        words = text.split()
        distorted = ' '.join(words[::-1])
        return distorted
    else:
        # Broken sanity: Lovecraftian nonsense
        gibberish = ["~Ia! Shub-Niggurath~", "*the eyes... they're watching*", "ph'nglui mglw'nafh..."]
        return random.choice(gibberish)

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
    desc = random.choice(descriptions)
    distorted = distort_text(desc, game_state["sanity"])
    delay_print(distorted)

    print("\nWhat would you like to do?")
    print("[1] Search the room")
    print("[2] Move to another location")
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
    delay_print("London, 1915. A fog rolls in over the cobblestones, thick and clinging, curling like smoke through the iron gates of the city’s forgotten quarters. The gaslamps flicker under its damp touch, casting pale halos that only make the darkness beyond feel deeper—hungrier...")
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
    print("[3] Detective – +2 Perception")
    print("[4] Ex-Priest – +1 Faith, +1 Sanity")

    bg = input("> ")
    if bg == "1" or bg == "Theologian":
        game_state["background"] = "Theologian"
        game_state["faith"] += 2
    elif bg == "2" or bg == "Occultist":
        game_state["background"] = "Occultist"
        game_state["sanity"] += 2
    elif bg == "3" or bg == "Detective":
        game_state["background"] = "Detective"
        game_state["perception"] += 2
    elif bg == "4" or bg == "Ex-Priest":
        game_state["background"] = "Ex-Priest"
        game_state["faith"] += 1
        game_state["sanity"] += 1
    else:
        character_creation()
        return

    # Assign base values and random bonus to all stats
    for stat in ["faith", "sanity", "perception", "strength", "stamina", "agility", "comeliness"]:
        base = 8 + random.randint(1, 4)
        game_state[stat] = base

    # Allow player to distribute 6 additional points
    stat_points = 6
    print("\nDistribute 6 additional points among your attributes (for a max of 18):")
    while stat_points > 0:
        print(f"\nPoints remaining: {stat_points}")
        for stat in ["faith", "sanity", "perception", "strength", "stamina", "agility", "comeliness"]:
            print(f"{stat.capitalize()}: [{game_state[stat]}]")

        chosen_stat = input("\nEnter the attribute to increase: ").lower()
        if chosen_stat not in game_state or chosen_stat not in ["faith", "sanity", "perception", "strength", "stamina", "agility", "comeliness"]:
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
    for stat in ["faith", "sanity", "perception", "strength", "stamina", "agility", "comeliness"]:
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
        input("\nPress Enter to return.")

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

# ---------- Encounter Example ----------
def encounter():
    delay_print("A hooded cultist blocks your way.")
    print("[1] Strike with cane")
    print("[2] Attempt banishment")
    print("[3] Flee")

    choice = input("> ")
    if choice == "1":
        skill_check("combat")
    elif choice == "2":
        skill_check("faith")
    elif choice == "3":
        delay_print("You escape into the fog. But the case remains.")
        input("Press Enter to return to title.")
        title_screen()
    else:
        encounter()

# ---------- Skill Check ----------
def skill_check(skill):
    roll = random.randint(1, 10)
    bonus = 0
    if skill == "faith":
        bonus = game_state["faith"]
    elif skill == "combat":
        bonus = 2 if game_state["background"] in ["Detective", "Ex-Priest"] else 0

    total = roll + bonus
    delay_print(f"Skill check: {roll} + {bonus} = {total}")

    if total >= 8:
        delay_print("Success! The cultist is defeated.")
        game_state["quests"].remove("Investigate Manor Seance")
        input("Press Enter to save progress.")
        save_game()
        title_screen()
    else:
        game_state["sanity"] -= 1
        delay_print("You fail. Your mind frays. (-1 Sanity)")
        input("Press Enter to try again.")
        describe_room()

# Start the game
title_screen()
