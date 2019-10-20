from lib.dicecloud.client import DicecloudClient
from lib.dicecloud.models import Class, Effect, Feature, Parent, Proficiency
from lib.rendering import ABILITY_MAP, render

SKILL_MAP = {'acrobatics': 'acrobatics', 'animal handling': 'animalHandling', 'arcana': 'arcana',
             'athletics': 'athletics', 'deception': 'deception', 'history': 'history', 'initiative': 'initiative',
             'insight': 'insight', 'intimidation': 'intimidation', 'investigation': 'investigation',
             'medicine': 'medicine', 'nature': 'nature', 'perception': 'perception', 'performance': 'performance',
             'persuasion': 'persuasion', 'religion': 'religion', 'sleight of hand': 'sleightOfHand',
             'stealth': 'stealth', 'survival': 'survival'}

CLASS_RESOURCE_NAMES = {"Ki Points": "ki", "Rage Damage": "rageDamage", "Rages": "rages",
                        "Sorcery Points": "sorceryPoints", "Superiority Dice": "superiorityDice",
                        "1st": "level1SpellSlots", "2nd": "level2SpellSlots", "3rd": "level3SpellSlots",
                        "4th": "level4SpellSlots", "5th": "level5SpellSlots", "6th": "level6SpellSlots",
                        "7th": "level7SpellSlots", "8th": "level8SpellSlots", "9th": "level9SpellSlots"}


def create_char(api_key, name, level, race, _class, subclass, background):
    # things to add in batches
    effects = []
    features = []
    profs_to_add = []

    caveats = []  # a to do list for the user

    # setup client
    dc = DicecloudClient(None, None, api_key, no_meteor=True)

    # Name Gen + Setup
    #    DMG name gen
    char_id = dc.create_character(name=name, race=race.name, backstory=background.name)

    # Stat Gen
    # Allow user to enter base values
    caveats.append("**Base Ability Scores**: Enter your base ability scores (without modifiers) in the feature "
                   "titled Base Ability Scores.")

    # Race Gen
    #    Racial Features
    speed = race.get_speed_int()
    if speed:
        effects.append(Effect(Parent.race(char_id), 'base', value=int(speed), stat='speed'))

    for k, v in race.ability.items():
        if not k == 'choose':
            effects.append(Effect(Parent.race(char_id), 'add', value=int(v), stat=ABILITY_MAP[k].lower()))
        else:
            effects.append(Effect(Parent.race(char_id), 'add', value=int(v[0].get('amount', 1))))
            caveats.append(
                f"**Racial Ability Bonus ({int(v[0].get('amount', 1)):+})**: In your race (Journal tab), select the"
                f" score you want a bonus to (choose {v[0]['count']} from {', '.join(v[0]['from'])}).")

    for t in race.get_traits():
        features.append(Feature(t['name'], t['text']))
    caveats.append("**Racial Features**: Check that the number of uses for each feature is correct, and apply "
                   "any effects they grant.")

    # Class Gen
    #    Class Features
    class_id = dc.insert_class(char_id, Class(level, _class['name']))
    effects.append(Effect(Parent.class_(class_id), 'add', stat=f"d{_class['hd']['faces']}HitDice",
                          calculation=f"{_class['name']}Level"))

    hp_per_level = (int(_class['hd']['faces']) / 2) + 1
    first_level_hp = int(_class['hd']['faces']) - hp_per_level
    effects.append(Effect(Parent.class_(class_id), 'add', stat='hitPoints',
                          calculation=f"{hp_per_level}*{_class['name']}Level+{first_level_hp}"))
    caveats.append("**HP**: HP is currently calculated using class average; change the value in the Journal tab "
                   "under your class if you wish to change it.")

    for saveProf in _class['proficiency']:
        prof_key = ABILITY_MAP.get(saveProf).lower() + 'Save'
        profs_to_add.append(Proficiency(Parent.class_(class_id), prof_key, type_='save'))
    for prof in _class['startingProficiencies'].get('armor', []):
        profs_to_add.append(Proficiency(Parent.class_(class_id), prof, type_='armor'))
    for prof in _class['startingProficiencies'].get('weapons', []):
        profs_to_add.append(Proficiency(Parent.class_(class_id), prof, type_='weapon'))
    for prof in _class['startingProficiencies'].get('tools', []):
        profs_to_add.append(Proficiency(Parent.class_(class_id), prof, type_='tool'))
    for _ in range(int(_class['startingProficiencies']['skills']['choose'])):
        profs_to_add.append(Proficiency(Parent.class_(class_id), type_='skill'))  # add placeholders
    caveats.append(f"**Skill Proficiencies**: You get to choose your skill proficiencies. Under your class "
                   f"in the Journal tab, you may select {_class['startingProficiencies']['skills']['choose']} "
                   f"skills from {', '.join(_class['startingProficiencies']['skills']['from'])}.")

    equip_choices = '\n'.join(f"• {i}" for i in _class['startingEquipment']['default'])
    gold_alt = f"Alternatively, you may start with {_class['startingEquipment']['goldAlternative']} gp " \
               f"to buy your own equipment." if 'goldAlternative' in _class['startingEquipment'] else ''
    starting_items = f"You start with the following items, plus anything provided by your background.  \n" \
                     f"{equip_choices}  \n" \
                     f"{gold_alt}"
    caveats.append(f"**Starting Class Equipment**: {starting_items}")

    level_resources = {}
    for table in _class.get('classTableGroups', []):
        relevant_row = table['rows'][level - 1]
        for i, col in enumerate(relevant_row):
            level_resources[table['colLabels'][i]] = render([col])

    for res_name, res_value in level_resources.items():
        stat_name = CLASS_RESOURCE_NAMES.get(res_name)
        if stat_name:
            try:
                effects.append(Effect(Parent.class_(class_id), 'base', value=int(res_value), stat=stat_name))
            except ValueError:  # edge case: level 20 barb rage
                pass

    num_subclass_features = 0
    for level in range(1, level + 1):
        level_features = _class['classFeatures'][level - 1]
        for f in level_features:
            if f.get('gainSubclassFeature'):
                num_subclass_features += 1
            text = render(f['entries'], True)
            features.append(Feature(f['name'], text))
    for num in range(num_subclass_features):
        level_features = subclass['subclassFeatures'][num]
        for feature in level_features:
            for entry in feature.get('entries', []):
                if not isinstance(entry, dict):
                    continue
                if not entry.get('type') == 'entries':
                    continue
                fe = {'name': entry['name'],
                      'text': render(entry['entries'], True)}
                features.append(Feature(fe['name'], fe['text']))
    caveats.append("**Class Features**: Check that the number of uses for each feature is correct, and apply "
                   "any effects they grant.")
    caveats.append("**Spellcasting**: If your class can cast spells, be sure to set your number of known spells, "
                   "max prepared, DC, attack bonus, and what spells you know in the Spells tab. You can add a "
                   "spell to your spellbook by using the spellbook tool.")

    # Background Gen
    #    Inventory/Trait Gen
    for trait in background.traits:
        text = trait['text']
        if any(i in trait['name'].lower() for i in ('proficiency', 'language')):
            continue
        if trait['name'].lower().startswith('feature'):
            tname = trait['name'][9:]
            features.append(Feature(tname, text))
        elif trait['name'].lower().startswith('equipment'):
            caveats.append(f"**Background Equipment**: Your background grants you {text}")

    for proftype, profs in background.proficiencies.items():
        if proftype == 'tool':
            for prof in profs:
                profs_to_add.append(Proficiency(Parent.background(char_id), prof, type_='tool'))
        elif proftype == 'skill':
            for prof in profs:
                dc_prof = SKILL_MAP.get(prof, prof)
                if dc_prof:
                    profs_to_add.append(Proficiency(Parent.background(char_id), dc_prof))
                else:
                    profs_to_add.append(Proficiency(Parent.background(char_id)))
                    caveats.append(f"**Choose Skill**: Your background gives you proficiency in either {prof}. "
                                   f"Choose this in the Background section of the Persona tab.")
        elif proftype == 'language':
            for prof in profs:
                profs_to_add.append(Proficiency(Parent.background(char_id), prof, type_='language'))
            caveats.append("**Languages**: Some backgrounds' languages may ask you to choose one or more. Fill "
                           "this out in the Background section of the Persona tab.")

    features.append(
        Feature("!!! Caveats !!!", "**__Caveats__**  \nNot everything is automagical! Here are some things you still "
                                   "have to do manually:  \n" + '\n\n'.join(caveats)))

    dc.insert_features(char_id, features)
    dc.insert_effects(char_id, effects)
    dc.insert_proficiencies(char_id, profs_to_add)

    return char_id


if __name__ == '__main__':
    from lib.compendium import c

    api_key = input("API Key: ")
    name = input("Name: ")
    level = int(input("Level: "))
    racename = input("Race: ")
    race = next(r for r in c.fancyraces if r['name'].lower() == racename.lower().strip())
    klassname = input("Class: ")
    klass = next(r for r in c.classes if r['name'].lower() == klassname.lower().strip())
    subclassname = input("Subclass: ")
    subclass = next(r for r in klass['subclasses'] if r['name'].lower() == subclassname.lower().strip())
    backgroundname = input("Background: ")
    background = next(r for r in c.backgrounds if r['name'].lower() == backgroundname.lower().strip())

    create_char(api_key, name, level, race, klass, subclass, background)
