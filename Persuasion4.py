# Persuasion: Victorian Roguelike Investigation Game
# Core Game Script

import os
import time
import random
import json

# Global player state
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
    "turns": 0
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

def title_screen():
    clear()
    print("""
  _____                              _             
 |  __ \\                            (_)            
 | |__) |__ _ __ ___ _   _  __ _ ___ _  ___  _ __  
 |  ___/ _ \\ '__/ __| | | |/ _` / __| |/ _ \\| '_ \
 | |  |  __/ |  \\__ \\ |_| | (_| \\__ \\ | (_) | | | |
 |_|   \\___|_|  |___/\\__,_|\\__,_|___/_|\\___/|_| |_|
                                                  
         A Victorian Roguelike Mystery
    """)
    print("[1] Begin New Investigation")
    print("[2] Load Game")
    print("[3] Instructions")
    print("[4] Save Game")
    print("[5] Quit")

    choice = input("> ")
    if choice == "1":
        dream_flashback()
    elif choice == "2":
        load_game()
    elif choice == "3":
        instructions()
    elif choice == "4":
        save_game()
        title_screen()
    elif choice == "5":
        exit()
    else:
        title_screen()

def instructions():
    clear()
    delay_print("Navigate using number keys. Choices shape sanity, stats, and storyline.")
    delay_print("You play an investigator in a dark Victorian world of cults and mysteries.")
    input("Press Enter to return.")
    title_screen()

def move_to_new_room():
    game_state["location"] = random.choice(list(room_templates.keys()))
    describe_room()

def add_random_clue():
    clue = random.choice(clue_pool)
    if clue not in game_state["clues"]:
        game_state["clues"].append(clue)
        delay_print(f"Clue discovered: {clue}")

def case_resolution():
    delay_print("You gather your thoughts and review the case...")
    if len(game_state["clues"]) >= 3:
        delay_print("The truth crystallizes. You know what happened here.")
        delay_print("You record the findings in your journal.")
        game_state["journal"].append("Case solved at " + game_state["location"])
        save_game()
    else:
        delay_print("There are still missing pieces. The mystery eludes you.")
    input("Press Enter to continue.")
    title_screen()

def describe_room():
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

    choice = input("> ")
    if choice == "1":
        add_random_clue()
        describe_room()
    elif choice == "2":
        move_to_new_room()
    elif choice == "3":
        for entry in game_state["journal"]:
            delay_print(entry)
        input("Press Enter to continue.")
        describe_room()
    elif choice == "4":
        delay_print(f"Inventory: {', '.join(game_state['inventory'])}")
        input("Press Enter to continue.")
        describe_room()
    elif choice == "5":
        interrogate_suspect()
    elif choice == "6":
        case_resolution()
    elif choice == "7":
        save_game()
        describe_room()
    elif choice == "8":
        title_screen()
    else:
        describe_room()

def interrogate_suspect():
    suspects = game_state["suspects"]
    print("\nChoose someone to interrogate:")
    for i, s in enumerate(suspects):
        print(f"[{i+1}] {s['name']} – {s['trait']}")
    print(f"[{len(suspects)+1}] Return")

    choice = input("> ")
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(suspects):
            suspect = suspects[idx]
            delay_print(f"You confront {suspect['name']}.")
            delay_print(suspect["alibi"])
            input("Press Enter to continue.")
        else:
            describe_room()
    describe_room()

def dream_flashback():
    clear()
    delay_print("You are dreaming... or remembering.")
    delay_print("A chapel. A child's voice. A locked door in your own mind.")
    delay_print("Whispers echo backward. You wake, gasping.")
    input("Press Enter to continue.")
    intro_scene()

def intro_scene():
    clear()
    delay_print("London, 1865. A fog rolls in over the cobblestones...")
    print("\nWhat will you do?")
    print("[1] Enter through the front gate")
    print("[2] Examine the grounds")
    print("[3] Pray silently")

    choice = input("> ")
    if choice == "1":
        enter_manor()
    elif choice == "2":
        game_state["inventory"].append("Bent Key")
        character_creation()
    elif choice == "3":
        game_state["faith"] += 1
        character_creation()
    else:
        intro_scene()

def enter_manor():
    delay_print("You step into the manor. A shadow slips past the stairs.")
    character_creation()

def character_creation():
    clear()
    delay_print("Before the hunt begins... who are you?")
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

    stat_points = 15
    print("\nDistribute 15 points among the following attributes:")
    for stat in ["strength", "stamina", "agility", "comeliness"]:
        while True:
            val = input(f"{stat.capitalize()} (remaining {stat_points}): ")
            if val.isdigit() and 0 <= int(val) <= stat_points:
                game_state[stat] = int(val)
                stat_points -= int(val)
                break
            else:
                print("Invalid input.")

    initialize_suspects()
    delay_print(f"Welcome, {game_state['name']} the {game_state['background']}.")
    input("Press Enter to begin.")
    start_first_case()

def start_first_case():
    game_state["quests"].append("Investigate Manor Seance")
    game_state["location"] = "Foyer"
    describe_room()

title_screen()
