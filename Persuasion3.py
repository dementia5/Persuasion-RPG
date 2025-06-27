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
    "inventory": [],
    "quests": [],
    "location": "",
}

# ---------- Utility Functions ----------
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
        character_creation(skip_intro=True)
    else:
        delay_print("No save file found.")

# ---------- Game Start ----------
def title_screen():
    clear()
    print(r"""
  ____                      _                         
 |  _ \ ___  ___ ___  _ __ | |_ ___ _ __ ___  ___ ___ 
 | |_) / _ \/ __/ _ \| '_ \| __/ _ \ '__/ __|/ _ / __|
 |  __/  __| (_| (_) | | | | ||  __/ |  \__ \  __\__ \
 |_|   \___|\___\___/|_| |_|\__\___|_|  |___/\___|___/
                                                     
         A Victorian Roguelike Mystery
    """)
    print("[1] Begin New Investigation")
    print("[2] Load Game")
    print("[3] Instructions")
    print("[4] Quit")

    choice = input("> ")
    if choice == "1":
        dream_flashback()
    elif choice == "2":
        load_game()
    elif choice == "3":
        instructions()
    elif choice == "4":
        exit()
    else:
        title_screen()

def instructions():
    clear()
    delay_print("Navigate using number keys. Choices shape sanity, stats, and storyline.")
    delay_print("You play an investigator in a dark Victorian world of cults and mysteries.")
    input("Press Enter to return.")
    title_screen()

# ---------- Dream Sequence ----------
def dream_flashback():
    clear()
    delay_print("You are dreaming... or remembering.")
    delay_print("A chapel. A child's voice. A locked door in your own mind.")
    delay_print("Whispers echo backward. You wake, gasping.")
    input("Press Enter to continue.")
    intro_scene()

# ---------- Intro Scene ----------
def intro_scene():
    clear()
    delay_print("London, 1865. A fog rolls in over the cobblestones., thick and clinging, curling like smoke through the iron gates of the city’s forgotten quarters. The gaslamps flicker under its damp touch, casting pale halos that only make the darkness beyond feel deeper—hungrier..")
    delay_print("Gaslamps flicker. A red-twined letter reads: 'They've opened the wrong door. Come at once.'")
    print("\nWhat will you do?")
    print("[1] Enter through the front gate")
    print("[2] Examine the grounds")
    print("[3] Pray silently")

    choice = input("> ")
    if choice == "1":
        enter_manor()
    elif choice == "2":
        investigate_grounds()
    elif choice == "3":
        gain_faith()
    else:
        intro_scene()

def enter_manor():
    delay_print("You step into the manor. A shadow slips past the stairs.")
    character_creation()

def investigate_grounds():
    delay_print("A strange sigil drawn in ash. You pocket a bent key.")
    game_state["inventory"].append("Bent Key")
    character_creation()

def gain_faith():
    delay_print("You whisper a psalm. Something listens. (+1 Faith)")
    game_state["faith"] += 1
    character_creation()

# ---------- Character Creation ----------
def character_creation(skip_intro=False):
    if not skip_intro:
        clear()
        delay_print("Before the hunt begins... who are you?")

    game_state["name"] = input("Name: ")
    game_state["gender"] = input("Gender: ")

    print("\nChoose your background:")
    print("[1] Theologian – +Faith")
    print("[2] Occultist – +Sanity")
    print("[3] Detective – +Observation")
    print("[4] Ex-Priest – Balanced skills")

    bg = input("> ")
    if bg == "1":
        game_state["background"] = "Theologian"
        game_state["faith"] += 2
    elif bg == "2":
        game_state["background"] = "Occultist"
        game_state["sanity"] += 2
    elif bg == "3":
        game_state["background"] = "Detective"
    elif bg == "4":
        game_state["background"] = "Ex-Priest"
        game_state["faith"] += 1
        game_state["sanity"] += 1
    else:
        return character_creation()

    delay_print(f"Welcome, {game_state['name']} the {game_state['background']}.")
    input("Press Enter to begin.")
    start_first_case()

# ---------- Quest and Rooms ----------
def start_first_case():
    game_state["quests"].append("Investigate Manor Seance")
    game_state["location"] = "Foyer"
    describe_room()

def describe_room():
    clear()
    room = game_state["location"]
    descriptions = {
        "Foyer": [
            "A grand hallway with rotting portraits and a broken chandelier.",
            "The air is heavy with incense and mold.",
            "Scratched symbols circle the threshold."
        ]
    }
    delay_print(random.choice(descriptions[room]))
    input("\nPress Enter to continue.")
    encounter()

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

# ---------- Start Game ----------
title_screen()
