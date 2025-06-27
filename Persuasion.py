import random
import time
import os

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def delay_print(s):
    for c in s:
        print(c, end='', flush=True)
        time.sleep(0.02)
    print()

def title_screen():
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
    print("[1] Begin Investigation")
    print("[2] Instructions")
    print("[3] Quit")

    choice = input("> ")
    if choice == "1":
        intro_scene()
    elif choice == "2":
        instructions()
    elif choice == "3":
        exit()
    else:
        title_screen()

def instructions():
    clear()
    delay_print("Navigate using number keys. Choices matter. Your mind may not survive. You have been warned.\n")
    input("\nPress Enter to return.")
    title_screen()

def intro_scene():
    clear()
    delay_print("London, 1865. A fog rolls in over the cobblestones, thick and clinging, curling like smoke through the iron gates of the city’s forgotten quarters. The gaslamps flicker under its damp touch, casting pale halos that only make the darkness beyond feel deeper—hungrier..\n")
    delay_print("You are summoned to a manor where a priest vanished after conducting a forbidden seance...\n")
    print("\nWhat will you do?")
    print("[1] Enter through the front gate.")
    print("[2] Examine the grounds for clues.")
    print("[3] Pray silently before stepping in.")
    
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
    clear()
    delay_print("The door creaks open... a shadow passes quickly across the hall.\n")
    combat_scenario()

def investigate_grounds():
    clear()
    delay_print("You find a broken rosary in the garden, and a set of clawed tracks.\n")
    input("\nPress Enter to enter the manor.")
    combat_scenario()

def gain_faith():
    clear()
    delay_print("You whisper a psalm... and feel a calm presence.\n(+1 Faith)")
    input("\nPress Enter to continue.")
    combat_scenario()

def combat_scenario():
    clear()
    delay_print("A hooded cultist leaps from the dark!\n")
    print("Choose your action:")
    print("[1] Strike with cane")
    print("[2] Attempt to banish")
    print("[3] Flee")
    
    choice = input("> ")
    if choice == "1":
        strike_result()
    elif choice == "2":
        banish_result()
    elif choice == "3":
        delay_print("You escape, but the mystery deepens...")
        end_game()
    else:
        combat_scenario()

def strike_result():
    clear()
    outcome = random.randint(1, 10)
    if outcome > 4:
        delay_print("You strike the cultist down! Blood stains the marble.")
    else:
        delay_print("He dodges, and slashes your arm. You retreat in pain.")
    end_game()

def banish_result():
    clear()
    outcome = random.randint(1, 10)
    if outcome > 7:
        delay_print("A flash of holy light! The cultist screams and vanishes into smoke.")
    else:
        delay_print("Your words falter. The cultist laughs and slashes toward you.")
    end_game()

def end_game():
    print("\n[1] Return to Title")
    print("[2] Quit")
    choice = input("> ")
    if choice == "1":
        title_screen()
    else:
        exit()

# Start game
title_screen()
