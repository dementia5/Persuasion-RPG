# Persuasion: Victorian Roguelike Investigation RPG Game
# Core Game Script

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
#    "walls": set(),  # Each wall is ((x1, y1), (x2, y2))
}

game_state["show_suspicion_hints"] = False
game_state["persuasion_active"] = False
game_state["persuasion_rounds"] = 0
game_state["persuasion_uses"] = 0
game_state["persuasion_targets"] = set()
game_state["chapel_pray_cooldown"] = 0

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
    "Fanaticism": "Their eyes burn with a wild, unyielding light, as if they alone can see some hidden truth in the darkness. Their hands tremble with fervor, clutching at a pendant or prayer beads as if for protection—or power. You sense a mind teetering on the edge of devotion and madness.",
    "Revenge": "A simmering anger lurks beneath their calm exterior, every word edged with old wounds and bitter memory. Their gaze flickers with resentment, and you sense they have not forgotten past slights. The air around them feels charged, as if violence is never far from their thoughts.",
    "Jealousy": "Their smile is brittle, their eyes darting to others with a mixture of longing and spite. Every gesture seems calculated, as if measuring themselves against invisible rivals. You sense a heart gnawed by envy, desperate for recognition.",
    "Forbidden Love": "A haunted tenderness lingers in their expression, shadowed by guilt and longing. They speak in half-truths, guarding secrets that ache to be confessed. You sense a soul torn between passion and peril.",
    "Desperation": "Their movements are restless, their words tinged with anxiety and a hint of pleading. You see the weight of debts and failures pressing down on them, driving them to the edge. Every glance is a search for escape—or salvation.",
    "Ambition": "They carry themselves with calculated poise, eyes always searching for advantage. Their words are smooth, but you sense a hunger for power lurking beneath the surface. Nothing, it seems, would stand in the way of their ascent.",
    "Obsession": "Their gaze is distant, fixed on patterns only they can see. They mutter to themselves, piecing together mysteries that may not exist. You sense a mind consumed by a single, all-devouring purpose.",
    "Fear": "They flinch at every sound, eyes wide and haunted. Their voice quivers, and sweat beads on their brow. You sense they are driven by terror—of secrets, of discovery, of something unseen.",
    "Blackmail": "They are guarded, every word weighed and measured. Their eyes flicker with calculation, as if always considering what you know—and what you might reveal. You sense they hold secrets, and are held by them in turn.",
    "Guilt": "Their shoulders sag beneath an invisible burden, and their eyes avoid yours. Words come slowly, as if each is a confession. You sense a soul haunted by past misdeeds.",
    "Loyalty": "They speak with conviction, their loyalty to another evident in every word. Yet there is a tension, as if torn between duty and conscience. You sense they would do anything to protect those they care for.",
    "Resentment": "Their tone is clipped, their answers curt. Old grievances simmer just beneath the surface, coloring every interaction. You sense a grudge that has festered for years.",
    "Zealotry": "Their faith is absolute, their certainty unshakeable. They speak as if on a mission ordained by higher powers. You sense a dangerous righteousness, blind to doubt or mercy.",
    "Shame": "They shrink from your gaze, cheeks flushed with embarrassment. Their words are evasive, and they seem desperate to hide some personal failing. You sense a secret that corrodes from within.",
    "Manipulation": "A sly smile plays at their lips, and their eyes never quite meet yours. Every answer feels rehearsed, every gesture calculated. You sense a master of deception, always playing a deeper game."
}

room_templates = {
    "Foyer": [
        "The grand entry is dimly lit, dust motes floating through the silence. You hear footsteps upstairs, then silence again, as if the house is holding its breath. The heavy doors behind you seem to close of their own accord, sealing you inside."
    ],
    "Main Hall": [
        "A vast corridor stretches in both directions, portraits watching from above with eyes that seem to follow your every move. The chandeliers sway slightly despite the still air, casting shifting shadows on the marble floor. Something unseen seems to pace behind the walls, its presence felt but never seen."
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

import sys
import time
import msvcrt

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
    # Fallback: use motive_descriptions if not found
    if not found:
        suspect["motive_long"] = motive_descriptions.get(suspect["motive"], "No details.")

def timing_bullseye_chase(rounds=3, escape_distance=3):
    print("A chase begins! Press SPACE when the red circle (●) is in the bullseye (◎)!")
    positions = list(range(1, 22))  # 1 to 21
    center = 11
    distance = 2

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
                if i == pos:
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
                    if abs(pos - center) <= 1:
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
            print("You have escaped! The monster gives up the chase and slinks away into the shadows.")
            wait_for_space("Press SPACE to continue.")
            return True
        elif distance <= 0:
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
    import msvcrt
    print(prompt)
    while True:
        key = msvcrt.getch()
        if key == b' ':
            break

def get_direction_from_arrow():
    """Wait for an arrow key and return 'n', 's', 'e', or 'w', or None if not an arrow."""
    import msvcrt
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

def place_special_rooms():
    # Example: Place the chapel randomly
    possible_positions = [(x, y) for x in range(MAP_MIN, MAP_MAX+1) for y in range(MAP_MIN, MAP_MAX+1)]
    possible_positions.remove(game_state["entrance"])  # Don't place chapel at entrance
    chapel_pos = random.choice(possible_positions)
    game_state["chapel"] = chapel_pos
    game_state["rooms"][chapel_pos] = {"type": "Chapel", "visited": False}

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

# Call this function at the start of a new game/case, before initializing suspects and clues:

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
        suspect["strength"] = random.randint(10,16)
        suspect["stamina"] = random.randint(10,16)
        suspect["agility"] = random.randint(9,15)

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

clue_pools = [
    [
        "A blood-stained prayer book.",
        "A silver pendant etched with tentacles.",
        "An empty ritual circle drawn in chalk.",
        "A coded diary mentioning a 'Summoning'."
    ],
    [
        "A torn dance card.",
        "A wilted rose with a hidden note.",
        "A pawn ticket for a golden chalice, issued the day before the Bishop vanished.",
        "A threatening note warning the Bishop to abandon his 'awakening.'"
    ],
    [
        "A broken window latch.",
        "A missing library ledger.",
        "A muddy boot print.",
        "A page torn from a forbidden tome."
    ],
    [
        "A star chart with strange markings.",
        "A bloodstained handkerchief.",
        "A monogrammed glove found in the garden.",
        "A shattered monocle near the cellar stairs."
    ]
]

clue_motives_pools = [
    {
        "A blood-stained prayer book.": "Fanaticism",
        "A silver pendant etched with tentacles.": "Fanaticism",
        "An empty ritual circle drawn in chalk.": "Fanaticism",
        "A coded diary mentioning a 'Summoning'.": "Revenge"
    },
    {
        "A torn dance card.": "Jealousy",
        "A wilted rose with a hidden note.": "Forbidden Love",
        "A pawn ticket for a golden chalice, issued the day before the Bishop vanished.": "Desperation",
        "A threatening note warning the Bishop to abandon his 'awakening.'": "Fear"
    },
    {
        "A broken window latch.": "Ambition",
        "A missing library ledger.": "Blackmail",
        "A muddy boot print.": "Desperation",
        "A page torn from a forbidden tome.": "Blackmail"
    },
    {
        "A star chart with strange markings.": "Obsession",
        "A bloodstained handkerchief.": "Revenge",
        "A monogrammed glove found in the garden.": "Jealousy",
        "A shattered monocle near the cellar stairs.": "Ambition"
    }
]

alibi_pools = [
    [
        {"text": "Praying in the Chapel at midnight.", "location": "Chapel", "time": "Midnight"},
        {"text": "Reading in the Library at 10pm.", "location": "Library", "time": "10pm"},
        {"text": "Tending the fire in the Parlor at 11pm.", "location": "Parlor", "time": "11pm"},
        {"text": "Searching for a book in the Study at midnight.", "location": "Study", "time": "Midnight"}
    ],
    [
        {"text": "Practicing dance steps in the Ballroom at 11pm.", "location": "Ballroom", "time": "11pm"},
        {"text": "Alone in the Solarium, reading at 10pm.", "location": "Solarium", "time": "10pm"},
        {"text": "Repairing a window in the Attic at midnight.", "location": "Attic", "time": "Midnight"},
        {"text": "Inspecting the Cellar at midnight.", "location": "Cellar", "time": "Midnight"}
    ],
    [
        {"text": "Walking in the Garden at 11pm.", "location": "Garden", "time": "11pm"},
        {"text": "Observing the stars in the Observatory at 10pm.", "location": "Observatory", "time": "10pm"},
        {"text": "Dining alone in the Dining Hall at 11pm.", "location": "Dining Hall", "time": "11pm"},
        {"text": "Smoking in the Smoking Room at midnight.", "location": "Smoking Room", "time": "Midnight"}
    ],
    [
        {"text": "Feeding the horses in the Stable at 10pm.", "location": "Horse Stable", "time": "10pm"},
        {"text": "Fetching water from the Well House at 11pm.", "location": "Well House", "time": "11pm"},
        {"text": "Admiring paintings in the Gallery at 10pm.", "location": "Gallery", "time": "10pm"},
        {"text": "Resting in the East Bedchamber at midnight.", "location": "East Bedchamber", "time": "Midnight"}
    ]
]


motive_pools = [
    [
        {
            "short": "Fanaticism",
            "long": "Driven by an obsessive devotion to forbidden rites and ancient faiths, often acting without regard for consequence."
        },
        {
            "short": "Revenge",
            "long": "Always considers revenge as a first option due to a quick temper and a deep disgust with the church's hypocrisy."
        },
        {
            "short": "Jealousy",
            "long": "Harbors envy for the Bishop's influence and resents being overlooked, fueling bitter rivalry."
        },
        {
            "short": "Forbidden Love",
            "long": "Secretly in love with someone close to the Bishop, willing to do anything to protect or possess them."
        }
    ],
    [
        {
            "short": "Desperation",
            "long": "Haunted by debts and personal failures, willing to risk everything for a chance at redemption or escape."
        },
        {
            "short": "Ambition",
            "long": "Sees the Bishop's disappearance as a stepping stone to greater power within the church or society."
        },
        {
            "short": "Fear",
            "long": "Terrified of secrets being revealed, acts out of self-preservation and paranoia."
        },
        {
            "short": "Blackmail",
            "long": "Holds or is held by dangerous secrets, manipulating others to maintain control."
        }
    ],
    [
        {
            "short": "Obsession",
            "long": "Fixated on unraveling cosmic mysteries, even at the cost of others' lives or sanity."
        },
        {
            "short": "Greed",
            "long": "Motivated by material gain, coveting the Bishop's wealth or relics."
        },
        {
            "short": "Guilt",
            "long": "Haunted by past misdeeds, desperate to cover up involvement in earlier crimes."
        },
        {
            "short": "Loyalty",
            "long": "Acts to protect a loved one or mentor, even if it means committing a terrible act."
        }
    ],
    [
        {
            "short": "Resentment",
            "long": "Nurtures a long-standing grudge against the Bishop for personal slights or injustices."
        },
        {
            "short": "Zealotry",
            "long": "Believes the Bishop's removal is a holy duty, convinced of their own righteousness."
        },
        {
            "short": "Shame",
            "long": "Driven by the need to hide a scandal or personal failing at any cost."
        },
        {
            "short": "Manipulation",
            "long": "Sees others as pawns, orchestrating events to serve a hidden agenda."
        }
    ]
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
    for clue, room in zip(game_state["clue_pool"], possible_rooms):
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
    """Prints text slowly, but finishes instantly if the user presses space or if speed=0."""
    import msvcrt  # Windows only; for cross-platform, use 'getch' from 'getch' package
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
            for key in ["breadcrumbs", "persuasion_targets", "walls", "locked_doors", "suspects_interrogated"]:
                if key in loaded_state:
                    if isinstance(loaded_state[key], list):
                        loaded_state[key] = set(to_tuple(item) for item in loaded_state[key])
                    elif isinstance(loaded_state[key], set):
                        loaded_state[key] = set(to_tuple(item) for item in loaded_state[key])
                    else:
                        loaded_state[key] = set()
                else:
                    loaded_state[key] = set()
                    # After loading game_state from JSON and other set conversions
                    if "searched_rooms" in loaded_state:
                        loaded_state["searched_rooms"] = set(tuple(item) for item in loaded_state["searched_rooms"])
                    else:
                        loaded_state["searched_rooms"] = set()

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

    # Limit movement to within 16x16 grid
    if not (MAP_MIN <= new_x <= MAP_MAX and MAP_MIN <= new_y <= MAP_MAX):
        delay_print("You sense an unnatural barrier. The manor does not extend further in that direction.")
        wait_for_space()
        show_map()
        return

    allowed_dirs = game_state["passages"].get((x, y), set())
    if direction not in allowed_dirs:
        delay_print("A wall or obstacle blocks your way. You cannot go that direction.")
        wait_for_space()
        show_map()
        return

    # --- Block movement through walls and locked doors, and allow unlocking with a key ---
    walls = game_state.get("walls", set())
    locked_doors = game_state.get("locked_doors", set())
    pos = (x, y)
    new_pos = (new_x, new_y)
    if ((pos, new_pos) in walls):
        # Reveal both cells for wall rendering in fog of war
        if "breadcrumbs" not in game_state or not isinstance(game_state["breadcrumbs"], set):
            game_state["breadcrumbs"] = set()
        game_state["breadcrumbs"].add(pos)
        game_state["breadcrumbs"].add(new_pos)
        delay_print("A wall blocks your way.")
        wait_for_space()
        show_map()
        return
    elif ((pos, new_pos) in locked_doors):
        # Reveal both cells for door rendering in fog of war
        if "breadcrumbs" not in game_state or not isinstance(game_state["breadcrumbs"], set):
            game_state["breadcrumbs"] = set()
        game_state["breadcrumbs"].add(pos)
        game_state["breadcrumbs"].add(new_pos)
        # Check for key in inventory
        has_key = any(key in game_state["inventory"] for key in ["Strange Key", "Bent Key"])
        if has_key:
            print(f"{ORANGE}A locked door blocks your way. You have a key that might fit!{RESET}")
            use = input("Use a key to unlock the door? (Y/N): ").strip().lower()
            if use == "y":
                # Remove one key from inventory (prioritize Strange Key)
                for key in ["Strange Key", "Bent Key"]:
                    if key in game_state["inventory"]:
                        game_state["inventory"].remove(key)
                        delay_print(f"You use the {key} to unlock the door.")
                        break
                # Unlock the door (remove from locked_doors both directions)
                locked_doors.discard((pos, new_pos))
                locked_doors.discard((new_pos, pos))
                game_state["locked_doors"] = locked_doors
                delay_print("The door unlocks with a satisfying click.")
                wait_for_space()
                # Now allow movement to proceed
            else:
                delay_print("You decide not to use a key right now.")
                wait_for_space()
                show_map()
                return
        else:
            delay_print("A locked door blocks your way. You need a key to proceed.")
            wait_for_space()
            show_map()
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

    # # Check for suspects in the same room
    # suspects_here = [
    #     s for s in game_state["suspects"]
    #     if s.get("position") == game_state["position"]
    # ]
    # if suspects_here:
    #     names = ', '.join(s["name"] for s in suspects_here)
    #     delay_print(f"You see someone here: {names}")

    if show_room:
        # wait_for_space()
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
        walls = game_state.get("walls", set())
        locked_doors = game_state.get("locked_doors", set())
        adjacent = []
        for dx, dy in [
            (0, 1), (0, -1), (1, 0), (-1, 0),  # N, S, E, W
            # (1, 1), (-1, 1), (1, -1), (-1, -1) # NE, NW, SE, SW
        ]:
            nx, ny = x + dx, y + dy
            if MAP_MIN <= nx <= MAP_MAX and MAP_MIN <= ny <= MAP_MAX:
                # Only add if not blocked by wall or locked door
                if ((x, y), (nx, ny)) not in walls and ((x, y), (nx, ny)) not in locked_doors:
                    adjacent.append((nx, ny))

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
    wait_for_space()

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
            delay_print(entry)
    if artifacts:
        print("\n--- Artifacts Discovered ---")
        for entry in artifacts:
            delay_print(entry)
    if responses:
        print("\n--- Suspect Responses ---")
        for entry in responses:
            # If hints are OFF, strip asterisk and suspicion note
            if not show_hints and entry.startswith("* "):
                lines = entry.split("\n")
                # Remove asterisk and suspicion note if present
                if lines[0].startswith("* "):
                    lines[0] = lines[0][2:]
                if len(lines) > 1 and "(This suspect is a strong candidate" in lines[1]:
                    lines.pop(1)
                entry = "\n".join(lines)
            delay_print(entry)
    if not clues and not artifacts and not responses:
        delay_print("Your journal is empty.")

    # Place the toggle at the end, just before wait_for_space
    print(f"\nHints are currently {'ON' if show_hints else 'OFF'}.")
    print("[T] Toggle suspicion hints   [Enter] Continue\n")
    choice = input("> ").strip().lower()
    if choice == "t":
        game_state["show_suspicion_hints"] = not show_hints
        show_journal()
        return

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
    print(f"Current Location: {location} at {pos}")
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

    print("\nUse arrow keys or N/S/E/W to move, or press Enter to return to the action menu.")

    import msvcrt
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
            else:
                # Reset alert if no suspects here
                if not suspects_here:
                    last_alerted_position = None
            show_map()
            return

def render_map(show_npcs=False, fog_of_war=False):
    grid_size = 8  # Adjust as needed for your grid
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

    sanity = game_state["sanity"]
    breadcrumbs = set(game_state.get("breadcrumbs", []))
    breadcrumbs.add((px, py))

    # --- COMPRESSED LEGEND (2 columns) ---
    legend = {}
    for room in set(game_state["visited_locations"].values()):
        letter = room[0].upper()
        if letter not in legend:
            legend[letter] = room
    legend_items = [f"{letter} = {room}" for letter, room in sorted(legend.items())]
    col_count = 2
    col_len = (len(legend_items) + col_count - 1) // col_count
    legend_lines = []
    for i in range(col_len):
        left = legend_items[i]
        right = legend_items[i + col_len] if i + col_len < len(legend_items) else ""
        legend_lines.append(f"{left:<25} {right}")

    walls = game_state.get("walls", set())
    locked_doors = game_state.get("locked_doors", set())
    visited = set(game_state["visited_locations"].keys())

    for row_idx, y in enumerate(range(py - half, py + half + 1)):
        row = ""
        for x in range(px - half, px + half + 1):
            pos = (x, y)
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
                elif loc == "Cellar":
                    char = " E "
                    color = GREY if searched else YELLOW
                elif loc in ("East Bedchamber", "West Bedchamber"):
                    char = " R "
                    color = GREY if searched else YELLOW
                else:
                    char = f" {loc[0]} "
                    color = GREY if searched else YELLOW
                if sanity < 4 and random.random() < 0.2:
                    char = random.choice([" ~ ", " * ", " % ", " $ "])
            elif fog_of_war and pos in breadcrumbs:
                char = f"{GREY} ◉ {RESET}"
                color = ""
            else:
                char = "   "
                color = ""
            row += f"{color}{char}{RESET}"

            # Only add vertical wall/space if not the last cell in the row
            if x < px + half:
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
        # Print the map row with the corresponding legend line (if any)
        if row_idx < len(legend_lines):
            print(f"{row}   {legend_lines[row_idx]}")
        else:
            print(row)

        # Draw horizontal walls/doors below this row (unless last row)
        if row_idx < grid_size - 1:
            wall_row = ""
            for x in range(px - half, px + half + 1):
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
                if x < px + half:
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
            print(f"{wall_row}")

    print("\nSuspects:")
    for idx, s in enumerate(game_state["suspects"], 1):
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

def use_item(return_func=None):
    # List of items to highlight in orange during combat
    combat_highlight = {"Phial of Holy Water", "Silver Dagger"}
    # Detect if called from combat by checking the return_func (lambda: None is used in combat)
    from_combat = return_func is not None and getattr(return_func, "__name__", "") == "<lambda>"

    usable = [item for item in game_state["inventory"] if item in [a["name"] for a in artifact_pool + potion_pool]]
    if not usable:
        delay_print("You have no usable items.")
        wait_for_space()
        if return_func:
            return_func()
        else:
            show_inventory()
        return

    print("\nWhich item would you like to use?")
    for idx, name in enumerate(usable, 1):
        if from_combat and name in combat_highlight:
            print(f"{ORANGE}[{idx}] {name}{RESET}")
        else:
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
                # Special effects
                if artifact["effect"] == "clue":
                    # Reveal a random clue not yet found
                    missing = [c for c in game_state["clue_pool"] if c not in game_state["clues"]]
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
                        missing = [c for c in game_state["clue_pool"] if c not in game_state["clues"]]
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
                wait_for_space()
                if return_func:
                    return_func()
                else:
                    show_inventory()
                return

            elif potion:
                game_state[potion["effect"]] = min(18, game_state[potion["effect"]] + potion["amount"])
                delay_print(f"You drink the {potion['name']}. {potion['desc']} (+{potion['amount']} {potion['effect'].capitalize()})")
                game_state["inventory"].remove(potion["name"])
                wait_for_space()
                if return_func:
                    return_func()
                else:
                    show_inventory()
                return
        elif idx == len(usable):  # Return option
            if return_func:
                return_func()
            else:
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
    print("- quests/mystery: Show active quests")
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
            # Remove this potion from all other rooms so it can't be found again
            for r in list(potion_locations.keys()):
                if potion_locations[r]["name"] == potion["name"] and r != room:
                    del potion_locations[r]
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
        # Remove this artifact from all other rooms so it can't be found again
        for r in list(game_state["artifact_locations"].keys()):
            if game_state["artifact_locations"][r]["name"] == artifact["name"] and r != room:
                del game_state["artifact_locations"][r]
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
    wait_for_space("Press SPACE to continue.")

def case_resolution():
    delay_print("You gather your thoughts and review the case... Pages of notes flicker in your mind like a shuffled deck of ghosts.")
    if len(game_state["clues"]) >= 3:
        if game_state["faith"] >= 15:
            delay_print(f"{YELLOW}Your unwavering faith has illuminated the truth. Evil recoils before your conviction, and the manor's curse is lifted!{RESET}")
            delay_print("You have achieved the True Faith ending.")
            game_state["score"] += 50  # Bonus for faith ending
        else:
            delay_print("The truth crystallizes. It is as chilling as it is inevitable, threading through every clue you've seen.")
        delay_print("You record the findings in your journal. The ink trembles as if the truth resists being committed to paper.")
        game_state["journal"].append("Case solved at " + game_state["location"])
        game_state["score"] += 100  # Add to score for solving the case
        delay_print("You have solved the case! Your score is now: " + str(game_state["score"]))
        delay_print("You feel a sense of closure, but also a lingering unease. The shadows of the manor still seem to whisper secrets you may never fully understand.")
        save_game()
    else:
        delay_print("There are still missing pieces. They flit just beyond comprehension like shadows behind stained glass.")
    wait_for_space()
    title_screen()

def describe_room():
    global previous_menu_function
    previous_menu_function = describe_room
    clear()
    room = game_state["location"]
    # --- Suspect alert: always show if someone is here ---
    suspects_here = [
        s for s in game_state["suspects"]
        if s.get("position") == game_state["position"]
    ]
    if suspects_here:
        names = ', '.join(s["name"] for s in suspects_here)
        delay_print(f"You see someone here: {names}")
        
    if len(game_state["clues"]) >= 5 and sum(
        1 for s in game_state["suspects"]
        if any(f"You confront {s['name']}" in entry or f"Survived combat against {s['name']}" in entry for entry in game_state["journal"])
    ) >= 2:
        print(f"{ORANGE}You feel you have gathered enough evidence to make an accusation. The truth is within your grasp...{RESET}")
    # --- Show room name at the top in GREEN ---
    print(f"\n{GREEN}=== {room} ==={RESET}\n")
    descriptions = room_templates.get(room, ["It's a bare and quiet room."])
    desc = random.choice(descriptions)
    distorted = distort_text(desc, game_state["sanity"])

    # --- Supernatural Event/Cut Scene ---
    # Pick 5 random supernatural rooms at game start and store in game_state
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
        # Non-supernatural room, just print the description
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

    # Chapel prayer option
    if room == "Chapel":
        print(f"{ORANGE}[P] Pray for guidance{RESET}")
    if suspects_here:
        suspect_names = ", ".join(s["name"] for s in suspects_here)
        print(f"{ORANGE}[6] Interrogate suspect ({suspect_names}){RESET}")
    # Only show case resolution if at least 5 clues and 2 suspects interrogated
    if len(game_state["clues"]) >= 5 and interrogated_count >= 2:
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

    print("\n(You can use arrow keys to move when prompted for a direction, but only on the 'Map' option.)")
    user_input = input("> ").strip().lower()
    if user_input == "1":
        add_random_clue()
        game_state["turns"] += 1
        if game_state["turns"] % 15 == 0:
            game_state["score"] -= 1
            game_state["score_log"].append("15 turns taken [-1]")
        wait_for_space()
        describe_room()
        return
    elif user_input == "2":
        clear()
        print("Where would you like to go? (N, S, E, W)")
        print("You can also use arrow keys.")
        import msvcrt
        dir_input = input("> ").strip().lower()
        if dir_input in ["n", "s", "e", "w"]:
            move_to_new_room(dir_input)
            game_state["turns"] += 1
            if game_state["turns"] % 15 == 0:
                game_state["score"] -= 1
                game_state["score_log"].append("15 turns taken [-1]")
        else:
            print("Press an arrow key to move, or Enter to return.")
            if msvcrt.kbhit():
                direction = get_direction_from_arrow()
                if direction:
                    move_to_new_room(direction)
                    game_state["turns"] += 1
                    if game_state["turns"] % 15 == 0:
                        game_state["score"] -= 1
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
            game_state["journal"].append("Prayed for guidance in the chapel.")
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
    suspects_here = [
        s for s in game_state["suspects"]
        if s.get("position") == game_state["position"]
    ]
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
                game_state["suspects_interrogated"].add(suspect["name"])
                clear()
                # --- Use long motive description if available ---
                desc = suspect.get("motive_long") or motive_descriptions.get(suspect.get("motive"), "")
                if desc:
                    delay_print(desc)
                delay_print(f"You confront {suspect['name']}.")

                asked_question = False  # Track if any of [A], [M], [T], [S] has been asked
                info_shown = False      # Track if info block has been shown

                while True:
                    print("\nOptions:")
                    options = set()

                    if asked_question:
                        print("[J] Enter this testimony in your journal")
                        options = {"j"}
                        if suspect.get("credibility", 5) < 5:
                            print(f"{ORANGE}[P] PERSUADE them to reveal more{RESET}")
                            options.add("p")
                        if game_state["clues"]:
                            print(f"{ORANGE}[C] Confront with a clue{RESET}")
                            options.add("c")
                    print("[O] Observe body language")
                    options.add("o")
                    # print("[L] Leave interrogation")
                    # options.add("l")
                    print("[A] Ask about their relationship to the Bishop")
                    options.add("a")
                    # print("[M] Ask about their motive")
                    # options.add("m")
                    print("[T] Ask where they were at the time of the crime")
                    options.add("t")
                    print("[S] Ask who they suspect")
                    options.add("s")
                    if game_state["faith"] >= 14:
                        print(f"{ORANGE}[B] Bless or rebuke the suspect (Faith){RESET}")
                        options.add("b")
                    print("[R] Return to action menu")
                    options.add("r")

                    choice = input("> ").strip().lower()

                    # Show info block only after first ask
                    if not info_shown and choice in {"a", "m", "t", "s"}:
                        # Calculate effective alibi weight
                        effective_weight = suspect.get("alibi_weight", 2)
                        if game_state.get("persuasion_active", False):
                            effective_weight = max(1, effective_weight - 1)
                        if game_state.get("perception", 0) >= 14:
                            effective_weight = max(1, effective_weight - 1)

                        delay_print(f"Alibi Credibility (1=least, 4=most): {effective_weight}/4")
                        if effective_weight == 1:
                            delay_print("Their alibi seems very shaky.")
                        elif effective_weight == 2:
                            delay_print("Their alibi is questionable.")
                        elif effective_weight == 3:
                            delay_print("Their alibi seems fairly solid.")
                        else:
                            delay_print("Their alibi is very convincing.")

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

                        if comeliness_mod > 0:
                            delay_print(f"Your presence seems to sway them. (Comeliness modifier: +{comeliness_mod})")
                        delay_print(f"Credibility rating: {effective_credibility}/10")
                        delay_print(f"Perception (with boost): {effective_perception}/18")
                        # delay_print(suspect["alibi"])
                        info_shown = True
                        asked_question = True

                    if choice == "b" and "b" in options:
                        if suspect.get("motive") in ["Fanaticism", "Zealotry"]:
                            delay_print(f"{suspect['name']} recoils from your words. Your faith unsettles them, and they falter in their conviction.")
                            suspect["credibility"] = max(0, suspect.get("credibility", 5) - 2)
                            game_state["score"] += 5
                        else:
                            delay_print(f"You invoke a blessing. {suspect['name']} seems moved, but you sense no hidden evil.")
                        wait_for_space()
                        continue

                    if choice == "p" and "p" in options:
                        # Skill check: perception or sanity
                        skill = random.choice(["perception", "sanity"])
                        roll = game_state[skill] + roll_fudge()
                        delay_print(f"(Push check: {skill.capitalize()} + die roll = {roll})")
                        if roll > 12:
                            delay_print("Your pressure pays off. The suspect cracks and reveals more!")
                            # Reveal a new clue or contradiction
                            if suspect.get("is_murderer"):
                                delay_print("You catch a flicker of guilt in their eyes. They are hiding something big.")
                                key_clue = game_state.get("solution_clue")
                                if key_clue and key_clue not in game_state["clues"]:
                                    game_state["clues"].append(key_clue)
                                    delay_print(f"They let slip a vital detail: {key_clue}")
                                    game_state["journal"].append(f"CLUE FOUND during interrogation: {key_clue}")
                                    game_state["score"] += 10
                            else:
                                delay_print("They reveal a detail that points suspicion elsewhere.")
                                unused_clues = [c for c in game_state["clue_pool"] if c not in game_state["clues"]]
                                if unused_clues:
                                    clue = random.choice(unused_clues)
                                    game_state["clues"].append(clue)
                                    delay_print(f"They mention something odd: {clue}")
                                    game_state["journal"].append(f"CLUE FOUND during interrogation: {clue}")
                                    game_state["score"] += 5
                        else:
                            delay_print("The suspect grows agitated and refuses to say more.")
                            suspect["credibility"] = max(0, suspect["credibility"] - 1)
                        wait_for_space()
                        continue

                    elif choice == "j" and "j" in options:
                        entries = []
                        if asked_question:
                            entries.append(f"Testimony from {suspect['name']} at {game_state['location']}:")
                            if "relationship" in suspect:
                                entries.append(f"  Relationship: {suspect.get('relationship', 'No details.')}")
                            if "motive" in suspect:
                                entries.append(f"  Motive: {suspect.get('motive', 'Unknown')}")
                            if "alibi" in suspect:
                                entries.append(f"  Alibi: {suspect.get('alibi', 'No details.')}")
                            entries.append("-----------------------------")

                            # --- Advanced suspicion marker (unchanged) ---
                            suspicion_score = 0
                            if suspect.get("credibility", 5) <= 2:
                                suspicion_score += 1
                            if suspect.get("motive") == game_state.get("solution_motive"):
                                suspicion_score += 1
                            alibi_weight = suspect.get("alibi_weight", 2)
                            if alibi_weight <= 2:
                                suspicion_score += 1
                            if suspect.get("opportunity"):
                                suspicion_score += 1

                            if suspicion_score >= 2:
                                entries[0] = "* " + entries[0]
                                entries.insert(1, f"{ORANGE}(This suspect is a strong candidate for the culprit based on your deductions.){RESET}")

                            journal_entry = "\n".join(entries)
                            already_recorded = any(
                                f"Testimony from {suspect['name']} at {game_state['location']}:" in entry
                                for entry in game_state["journal"]
                            )
                            if already_recorded:
                                delay_print("Testimony for this suspect at this location is already in your journal.")
                            else:
                                game_state["journal"].append(journal_entry)
                                delay_print("Testimony recorded in your journal.")
                        else:
                            delay_print("Ask at least one question before recording testimony.")
                        wait_for_space()
                        continue

                    elif choice == "c" and "c" in options:
                        print("Which clue do you want to confront with?")
                        for i, clue in enumerate(game_state["clues"], 1):
                            print(f"[{i}] {clue}")
                        clue_choice = input("> ").strip()
                        if clue_choice.isdigit():
                            clue_idx = int(clue_choice) - 1
                            if 0 <= clue_idx < len(game_state["clues"]):
                                clue = game_state["clues"][clue_idx]
                                if game_state["clue_motives"].get(clue) == suspect["motive"]:
                                    delay_print("The suspect's eyes widen—they recognize the clue! You sense a breakthrough.")
                                    suspect["credibility"] = max(0, suspect["credibility"] - 2)
                                    delay_print("They stammer and contradict themselves. You sense they're hiding something.")
                                    game_state["score"] += 15
                                    # Record confrontation in journal
                                    game_state["journal"].append(
                                        f"Confronted {suspect['name']} with clue: {clue} at {game_state['location']}"
                                    )
                                else:
                                    delay_print("The suspect scoffs at your accusation.")
                                    suspect["credibility"] = max(0, suspect["credibility"] - 1)
                        wait_for_space()
                        continue

                    elif choice == "o" and "o" in options:
                        roll = game_state["perception"] + roll_fudge()
                        if roll >= 12:
                            delay_print(f"(Observation check: Perception + die roll = {roll})")
                            delay_print("You notice a nervous tic. The suspect is definitely hiding something.")
                            # Record observation in journal
                            game_state["journal"].append(
                                f"Observed {suspect['name']}'s body language at {game_state['location']}: hiding something."
                            )
                        else:
                            delay_print("You can't read their body language this time.")
                        wait_for_space()
                        continue

                    elif choice == "a" and "a" in options:
                        rel = suspect.get('relationship', 'I had my reasons for being here, but the Bishop and I were not close.')
                        delay_print(f"{suspect['name']} says: '{rel}'")
                        # Record relationship testimony
                        game_state["journal"].append(
                            f"Testimony from {suspect['name']} at {game_state['location']}: Relationship: {rel}"
                        )
                        asked_question = True
                        wait_for_space()
                        continue

                    elif choice == "m" and "m" in options:
                        mot_long = suspect.get('motive_long') or motive_descriptions.get(suspect.get('motive'), suspect.get('motive', 'I had no reason to harm the Bishop.'))
                        mot_short = suspect.get('motive', 'Unknown')
                        delay_print(f"{suspect['name']} says: '{mot_long}'")
                        # Record motive testimony using the short version
                        game_state["journal"].append(
                            f"Testimony from {suspect['name']} at {game_state['location']}: Motive: {mot_short}"
                        )
                        asked_question = True
                        wait_for_space()
                        continue

                    elif choice == "t" and "t" in options:
                        alibi = suspect.get('alibi', 'I was alone, and no one can confirm my whereabouts.')
                        delay_print(f"{suspect['name']} says: '{alibi}'")
                        # Record alibi testimony
                        game_state["journal"].append(
                            f"Testimony from {suspect['name']} at {game_state['location']}: Alibi: {alibi}"
                        )
                        asked_question = True
                        wait_for_space()
                        continue

                    elif choice == "s" and "s" in options:
                        other_name = random.choice([s['name'] for s in game_state['suspects'] if s['name'] != suspect['name']])
                        delay_print(f"{suspect['name']} says: 'If you ask me, {other_name} seemed suspicious.'")
                        # Record suspicion testimony
                        game_state["journal"].append(
                            f"Testimony from {suspect['name']} at {game_state['location']}: Suspects {other_name}"
                        )
                        asked_question = True
                        wait_for_space()
                        continue

                    elif choice == "l":
                        describe_room()
                        return

                    elif choice == "r":
                        describe_room()
                        return

                    else:
                        handle_input(choice, interrogate_suspect)
                        continue
            else:
                delay_print("Invalid selection.")
                wait_for_space()
                continue
        else:
            handle_input(user_input, interrogate_suspect)
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
    Generate a manor map with 16 fixed rooms and fill the rest with random rooms,
    ensuring no two random rooms share the same first letter with each other or with the fixed rooms.
    """
    grid_half = 3  # For a 8x8 grid centered at (0,0)
    # 16 fixed rooms for coverage
    fixed_room_names = [
        "Foyer", "Main Hall", "Manor Grounds", "Atrium", "Solarium", "Cellar",
        "Garden", "Observatory", "Well House", "Horse Stable",
        "Library", "Study", "Dining Hall", "Gallery", "Ballroom", "Chapel"
    ]
    # Assign 16 unique positions for these rooms
    fixed_positions_list = [
        (0, 0), (0, -1), (0, 1), (-grid_half, 0), (grid_half, 0), (0, grid_half),
        (-grid_half - 1, 0), (grid_half + 1, 0), (0, grid_half + 1), (0, grid_half + 2),
        (-2, -2), (2, -2), (-2, 2), (2, 2), (-2, 0), (2, 0)
    ]
    fixed_positions = dict(zip(fixed_positions_list, fixed_room_names))

    # Find all remaining rooms not in fixed positions
    all_manor_rooms = [r for r in room_templates if r not in fixed_positions.values()]
    available_positions = []
    for x in range(-grid_half, grid_half + 1):
        for y in range(-grid_half, grid_half + 1):
            pos = (x, y)
            if pos not in fixed_positions:
                available_positions.append(pos)
    random.shuffle(available_positions)

    # Helper to pick random rooms with unique first letters (not overlapping with fixed)
    def pick_unique_initial_rooms(room_list, count, fixed_rooms):
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

    # Pick random rooms for available positions, no shared first letter with fixed or each other
    random_rooms = pick_unique_initial_rooms(all_manor_rooms, len(available_positions), fixed_room_names)
    random_rooms_iter = iter(random_rooms)

    visited_locations = fixed_positions.copy()
    empty_room_chance = 0.10  # Some empty rooms for variety
    for pos in available_positions:
        try:
            if random.random() > empty_room_chance:
                room = next(random_rooms_iter)
                visited_locations[pos] = room
            else:
                visited_locations[pos] = "Empty Room"
        except StopIteration:
            visited_locations[pos] = "Empty Room"

    # Build passages for fixed rooms (simple: connect to adjacent fixed rooms if possible)
    passages = {}
    for pos in visited_locations:
        possible_dirs = []
        for dir_name, (dx, dy) in DIRECTIONS.items():
            neighbor = (pos[0] + dx, pos[1] + dy)
            if neighbor in visited_locations:
                possible_dirs.append(dir_name)
        num_exits = min(len(possible_dirs), random.randint(2, 3))
        if num_exits > 0:
            exits = random.sample(possible_dirs, num_exits)
        else:
            exits = []
        passages[pos] = set(exits)

    # Make passages consistent (if A->B, then B->A)
    for pos, dirs in passages.items():
        for dir_name in list(dirs):
            dx, dy = DIRECTIONS[dir_name]
            neighbor = (pos[0] + dx, pos[1] + dy)
            rev_dir = None
            for d, (ddx, ddy) in DIRECTIONS.items():
                if (ddx, ddy) == (-dx, -dy):
                    rev_dir = d
                    break
            if rev_dir and neighbor in passages:
                passages[neighbor].add(rev_dir)

    # Save to game_state
    game_state["visited_locations"] = visited_locations
    game_state["passages"] = passages
    game_state["location"] = "Foyer"
    game_state["position"] = (0,0)  # Start at the Foyer

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
    culprit = {
        "name": random.choice([s["name"] for s in suspect_templates]),
        "motive": solution_motive["short"],
        "motive_long": solution_motive["long"],
        "alibi": solution_alibi,
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
    game_state["position"] = (0, 0)

    generate_structured_map() # Generate the structured map
    auto_generate_walls_and_doors() # Generate walls and locked doors
    print(f"Walls generated: {len(game_state['walls'])}")
    print(f"Locked doors generated: {len(game_state['locked_doors'])}") # Debugging line

    delay_print(f"Welcome, {game_state['name']} the {game_state['background']}. The hour is late, and the shadows grow bold.")
    wait_for_space()

    assign_clues_to_rooms()
    assign_potions_to_rooms()
    assign_elder_sign_to_room()
    assign_artifacts_to_rooms()  # Assign artifacts to rooms

    # Begin the first case
    start_first_case()

def start_first_case():
    global previous_menu_function
    previous_menu_function = start_first_case
    game_state["quests"].append("Investigate the disappearance of the Bishop.")

    # Announce Bishop's last known location and time at the start of the case
    last_loc = game_state.get("bishop_last_location", "an unknown location")
    last_time = game_state.get("bishop_last_time", "an unknown time")
    # delay_print(f"The Bishop was last seen in the {last_loc} at {last_time}.")

    describe_room()

def skill_check_combat(enemy_name, enemy_difficulty=None, stat=None):
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
    else:
        enemy_stamina = enemy_difficulty if enemy_difficulty is not None else 10
        enemy_strength = 8
        enemy_agility = 8

    # --- DEFINE FLAVOR LISTS HERE ---
    enemy_flavor = [
        f"{enemy_name} lands a heavy blow to your ribs.",
        f"{enemy_name} slams a fist into your shoulder.",
        f"{enemy_name} catches you off guard with a quick punch.",
        f"{enemy_name} drives you back with a sudden shove.",
        f"{enemy_name} lands a glancing blow to your cheek.",
        f"{enemy_name} strikes you with surprising force.",
        f"{enemy_name}'s fingernails rip into your throat, leaving burning scratches.",
        f"{enemy_name} grabs your hair and slams your head against the wall."
    ]
    gory_flavor = [
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
    ]
    horror_text = [
        f"As {enemy_name} strikes you, their flesh ripples and splits, revealing writhing tentacles and lidless, unblinking eyes.",
        f"{enemy_name}'s mouth distends impossibly wide, emitting a chorus of whispers in a language not meant for human ears.",
        f"Your attacker’s skin sloughs away, replaced by a mass of chitinous plates and twitching, alien appendages.",
        f"With a sickening crack, {enemy_name}'s limbs elongate and bend backwards, their face melting into a mass of wriggling feelers.",
        f"The corpse of {enemy_name} convulses, sprouting glistening, phosphorescent tendrils that thrash blindly at the air."
    ]
    # --- END FLAVOR LISTS ---

    round_num = 1
    sanity_lost = 0  # Track total sanity loss in this combat
    transformed = False  # Track if the suspect has transformed

    while player_stamina > 0 and enemy_stamina > 0:
        clear()
        if game_state["sanity"] < 4:
            delay_print(RED + "WARNING: Your sanity is dangerously low!" + RESET)
        if player_agility < 4:
            delay_print(RED + "WARNING: Your agility is dangerously low!" + RESET)
        if player_strength < 4:
            delay_print(RED + "WARNING: Your strength is dangerously low!" + RESET)
        if player_stamina < 4:
            delay_print(RED + "WARNING: Your stamina is dangerously low!" + RESET)

        delay_print(f"--- Melee Round {round_num} ---")
        delay_print(f"Your Stamina: {player_stamina} | {enemy_name}'s Stamina: {enemy_stamina}")

        # Show sanity every round after transformation
        if transformed:
            delay_print(f"Your Sanity: {game_state['sanity']}")

        # --- Add combat options here ---
        print("\nWhat will you do?")
        print("[A] Attack")
        print("[U] Use an item")
        print("[F] Flee")
        print("[S] Show stats")

        action = input("> ").strip().lower()
        if action == "u":
            use_item(lambda: None)
            # Update player stats in case a potion/artifact was used
            player_stamina = game_state["stamina"]
            player_strength = game_state["strength"]
            player_agility = game_state["agility"]
            continue  # Skip to next round after using an item
        elif action == "s":
            show_stats()
            continue
        elif action == "f":
            if transformed:
                print(f"{ORANGE}[F] Flee for your life!{RESET} or press Enter to stand your ground.")
                flee_choice = input("> ").strip().lower()
                if flee_choice == "f":
                    escaped = timing_bullseye_chase()
                    if escaped:
                        delay_print("You manage to escape the horror and slam the door behind you!")
                        wait_for_space()
                        describe_room()
                        return
                    else:
                        delay_print("The horror catches you! You are forced to fight for your life!")
                        # Continue combat as normal
            else:
                delay_print(RED + "You attempt to flee, but your opponent lands a parting blow! (Stamina -2, Score -10)" + RESET)
                game_state["stamina"] = max(0, game_state["stamina"] - 2)
                game_state["score"] -= 10
                wait_for_space()
                describe_room()
                return

        # Player's composite score
        player_base = (player_strength + player_stamina + player_agility) // 3
        player_roll = player_base + roll_fudge() + (player_agility - enemy_agility) // 2

        # Enemy's composite score
        enemy_base = (enemy_strength + enemy_stamina + enemy_agility) // 3
        enemy_roll = enemy_base + roll_fudge() + (enemy_agility - player_agility) // 2

        delay_print(f"Your combat score: {player_base} + die roll + agility mod = {YELLOW}{player_roll}{RESET}")
        delay_print(f"Enemy combat score: {enemy_base} + die roll + agility mod = {YELLOW}{enemy_roll}{RESET}")

        if player_roll >= enemy_roll:
            # Player hits enemy
            player_damage = max(1, 1 + (player_strength - enemy_strength) // 4)
            delay_print(YELLOW + f"You strike {enemy_name} for {player_damage} damage!" + RESET)
            enemy_stamina -= player_damage
        else:
            damage = max(1, 1 + (enemy_strength - player_strength) // 4)
            # Faith reduces supernatural damage from transformed foes
            if transformed and game_state["faith"] >= 14:
                delay_print(f"{ORANGE}Your faith shields you from the worst of the supernatural assault! (Damage halved){RESET}")
                damage = max(1, damage // 2)
            elder_god_twist = False
            if suspect and random.random() < 0.15 and sanity_lost == 0:
                elder_god_twist = True
            if elder_god_twist:
                # --- Transformation occurs here ---
                if not transformed:
                    delay_print(RED + "The suspect's body contorts and transforms into a monstrous horror!" + RESET)
                    enemy_strength += 1
                    if suspect:
                        suspect["strength"] = enemy_strength
                    transformed = True
                            # --- Offer flee option here ---
                    print(f"{ORANGE}[F] Flee for your life!{RESET} or press Enter to stand your ground.")
                    flee_choice = input("> ").strip().lower()
                    if flee_choice == "f":
                        escaped = timing_bullseye_chase()
                        if escaped:
                            delay_print("You manage to escape the horror and slam the door behind you!")
                            wait_for_space()
                            describe_room()
                            return
                        else:
                            delay_print("The horror catches you! You are forced to fight for your life!")
                            # Continue combat as normal
                delay_print(f"Your Sanity: {game_state['sanity']}")
                delay_print(ORANGE + random.choice(gory_flavor) + RESET)
                delay_print(f"You lose {damage} stamina.")
                delay_print("\n" + random.choice(horror_text))
                delay_print("You reel in terror as the truth is revealed: this was no mere mortal, but a servant of some higher unspeakable evil from some other upside down plane of existence!")
                game_state["sanity"] = max(0, game_state["sanity"] - 1)
                sanity_lost = 2
            else:
                if transformed:
                    delay_print(ORANGE + random.choice(gory_flavor) + RESET)
                    delay_print(f"You lose {damage} stamina.")
                    delay_print("\n" + random.choice(horror_text))
                else:
                    delay_print(ORANGE + random.choice(enemy_flavor) + RESET)
                    delay_print(f"You lose {damage} stamina.")
                player_stamina -= damage

        delay_print(f"Your Stamina: {player_stamina} | {enemy_name}'s Stamina: {enemy_stamina}")
        round_num += 1
        wait_for_space()

    # End of combat (rest of your function unchanged)
    game_state["stamina"] = player_stamina
    if suspect:
        suspect["stamina"] = enemy_stamina

    if player_stamina > 0:
        delay_print(f"You overcome the threat posed by {enemy_name}! You live to investigate another day.")
        game_state["journal"].append(f"Survived combat against {enemy_name}.")
        if suspect:
            suspect["stamina"] = 0
            if 'transformed' in locals() and transformed:
                print("P̴̧̧͔̦̲͙͉̘̰̜͎̤̻̹̤͋̀̈́̄́̂͐͂̈́̓͐͒͜͝h̴̡̡̡̲͓̜̬͎̖̟̞̦͙̑̀͊̎̌̐̆̽̆̈́̆͌̕ͅ'̶̜̟͛̉̎̅̿̊n̴͇̟͋g̴̥̦̟̘̝̱͉̲̤͙͇͋̄̐̏͊̔͌́͛̇l̶̡͙̻̗̩̬̣̰͚̯̲̉̃̒́͛͆͋̀͛͆̃͜͝ụ̷̧̧͎̯̜͕̻̘̬̙̱͈͛͐ͅi̴̖͓̥͔͕͍̮͇̼͚̗̭̻͌̈́̈́̈́͊̿̀͆͋̀͌̍̀̍͜͠͠͝ ̵̢̩̟̫̣̪̬͍̳̞̰͕̝͚̣͗͛̈́͘̚m̷̛͔̱̎̐̊̀͐̑͆̑̈́͛͘͝g̸̡̨͛͒̈͆͝l̸̡̨͕̣͎̙͕̥͛̎͆̊͛̋̍̿͐̅̄̋̔̈́̓̕͝w̵̧̖̟̠̼̠̼̗̜̱͈̮̩͆'̴͕̟̹͙̝̼͖̟̈̃̈́̉͛̀͛̂͘͝n̸̲̜̭̪̩̅͌̀̏͛̅̎̋͑͐̏̈́̽̌͝͝a̵̡̫͙̻͓͉͈͈͉̙͑͗͗͝f̵̨̖̯̳̮̳̼̺̠̰̘̘̙̗͍͖͆͑̀͂͋̈̑̈͜͝h̸͏̡̛͈̱͇͉̯̹̘͋̄̾̽͋́͂͛̊̕͝ ̸̧̣̫̳̥̥̲̖̻̭̾̅̎́̀̓̉́̇̕͝͝ͅͅw̴̨͖̼͕͉͍̺͐́̈̈́ģ̴̛̫͎̼̥͕̦̮͈̩̺̈́̃̇a̶̛̱͔̩̦͙͇̖͚̲̙͖͚͎͈̓͑̀͒ḩ̶̨̝̺͚͎̺̙͕̞̂͐̂́̈́̍͛͝ͅ'̵͚̝̝̩̗̭̦̇̐̈́̃̊̌̔́̌͝͝͝ͅņ̴̗͕̬̞̻̼̜̥͈̣̬͇̦̻͖̏́̓͒̈́͐́͠ͅa̸̹̟̯͈̣͖͙͝g̴̨̼̤̜̥̼̰͈̞̪̙̭̅̃͛̆l̸͚̗͉̖̰̿̊͐͌̈́̃ͅ ̷̟͇͕̘̰̤͖̰̜̝̰̗̼̟̱͖̂̈̈́̔̌̊̕͜f̸̧̲̬̤͍̙̰͎̲͖̭̜̖̫̅̒́̃͜h̴̛̩̫͕̣̻͛́́̏̈́̐ẗ̵̨̛̛̻̻͉̗̲̙̠̦̜̔̾͒̑͂̈́͑̏̈͊̊͋ͅa̷̢̰͍̞̭̗̜̣̒̔͑ǧ̴̨̱̘̣͕͙̘̺͍̦̒͌́̓̎͋n̴͍͔͔͙̰͐͜!")
                game_state["score"] -= 15
                delay_print("You have taken a life in self-defense. The weight of this act will haunt you. (-15 Score)")
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
   \   / _ \| | | | | |    / _ \/ __|/ _ \
    | | (_) | |_| | | |___| (_) \__ \  __/
    |_|\___/ \__,_| |______\___/|___/\___|
    """ + RESET)        
        delay_print("Sorry!")
        show_score()
        wait_for_space()
        title_screen()
        return

    if player_stamina <= 0:
        delay_print("You have succumbed to exhaustion. The investigation ends here.")
        game_state["score"] -= 35
        show_score()
        wait_for_space()
        title_screen()
    else:
        wait_for_space()

# --- Main Menu ---
title_screen()

