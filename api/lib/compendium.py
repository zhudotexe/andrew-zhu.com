import json
import re

from lib.rendering import render


class Race:
    def __init__(self, name: str, source: str, page: int, size: str, speed, asi, entries, srd: bool = False,
                 darkvision: int = 0):
        self.name = name
        self.source = source
        self.page = page
        self.size = size
        self.speed = speed
        self.ability = asi
        self.entries = entries
        self.srd = srd
        self.darkvision = darkvision

    @classmethod
    def from_data(cls, data):
        size = {'T': "Tiny", 'S': "Small", 'M': "Medium", 'L': "Large", 'H': "Huge"}.get(data['size'], 'Unknown')
        return cls(data['name'], data['source'], data.get('page', '?'), size, data['speed'], data.get('ability', {}),
                   data['entries'], data['srd'], data.get('darkvision', 0))

    def get_speed_str(self):
        if isinstance(self.speed, int):
            return f"{self.speed} ft."
        elif isinstance(self.speed, dict):
            return ', '.join(f"{k} {v} ft." for k, v in self.speed.items())
        return str(self.speed)

    def get_speed_int(self):
        if isinstance(self.speed, int):
            return self.speed
        elif isinstance(self.speed, dict):
            return self.speed.get('walk', '30')
        return None

    def get_asi_str(self):
        ability = []
        for k, v in self.ability.items():
            if not k == 'choose':
                ability.append(f"{k} {v}")
            else:
                ability.append(f"Choose {v[0]['count']} from {', '.join(v[0]['from'])} {v[0].get('amount', 1)}")
        return ', '.join(ability)

    def get_traits(self):
        traits = []
        for entry in self.entries:
            if isinstance(entry, dict) and 'name' in entry:
                temp = {'name': entry['name'],
                        'text': render(entry['entries'])}
                traits.append(temp)
        return traits


class Spell:
    def __init__(self, name: str, level: int, school: str, casttime: str, range_: str, components: str, duration: str,
                 description: str, classes=None, subclasses=None, ritual: bool = False, higherlevels: str = None,
                 source: str = "homebrew", page: int = None, concentration: bool = False, automation=None,
                 srd: bool = False, image: str = None):
        if classes is None:
            classes = []
        if isinstance(classes, str):
            classes = [cls.strip() for cls in classes.split(',') if cls.strip()]
        if subclasses is None:
            subclasses = []
        if isinstance(subclasses, str):
            subclasses = [cls.strip() for cls in subclasses.split(',') if cls.strip()]
        self.name = name
        self.level = level
        self.school = school
        self.classes = classes
        self.subclasses = subclasses
        self.time = casttime
        self.range = range_
        self.components = components
        self.duration = duration
        self.ritual = ritual
        self.description = description
        self.higherlevels = higherlevels
        self.source = source
        self.page = page
        self.concentration = concentration
        self.automation = automation
        self.srd = srd
        self.image = image

        if self.concentration and 'Concentration' not in self.duration:
            self.duration = f"Concentration, up to {self.duration}"

    @classmethod
    def from_data(cls, data):  # local JSON
        data["range_"] = data.pop("range")  # ignore this
        data["automation"] = None
        return cls(**data)

    def get_school(self):
        return {
            "A": "Abjuration",
            "V": "Evocation",
            "E": "Enchantment",
            "I": "Illusion",
            "D": "Divination",
            "N": "Necromancy",
            "T": "Transmutation",
            "C": "Conjuration"
        }.get(self.school, self.school)

    def get_level(self):
        if self.level == 0:
            return "cantrip"
        if self.level == 1:
            return "1st level"
        if self.level == 2:
            return "2nd level"
        if self.level == 3:
            return "3rd level"
        return f"{self.level}th level"

    def get_combat_duration(self):
        match = re.match(r"(?:Concentration, up to )?(\d+) (\w+)", self.duration)
        if match:
            num = int(match.group(1))
            unit = match.group(2)
            if 'round' in unit:
                return num
            elif 'minute' in unit:
                if num == 1:  # anything over 1 minute can be indefinite, really
                    return 10
        return -1

    def to_dicecloud(self):
        mat = re.search(r'\(([^()]+)\)', self.components)
        text = self.description.replace('\n', '\n  ')
        if self.higherlevels:
            text += f"\n\n**At Higher Levels**: {self.higherlevels}"
        return {
            'name': self.name,
            'description': text,
            'castingTime': self.time,
            'range': self.range,
            'duration': self.duration,
            'components': {
                'verbal': 'V' in self.components,
                'somatic': 'S' in self.components,
                'concentration': self.concentration,
                'material': mat.group(1) if mat else None,
            },
            'ritual': self.ritual,
            'level': int(self.level),
            'school': self.get_school(),
            'prepared': 'prepared'
        }


class Background:
    def __init__(self, name, traits, proficiencies, source, page, srd):
        self.name = name
        self.traits = traits
        self.proficiencies = proficiencies
        self.source = source
        self.page = page
        self.srd = srd

    @classmethod
    def from_data(cls, raw):
        return cls(**raw)


class Compendium:
    def __init__(self):
        with open('./static/races.json', 'r') as f:
            _raw = json.load(f)
            self.rfeats = []
            self.fancyraces = [Race.from_data(r) for r in _raw]
            for race in _raw:
                for entry in race['entries']:
                    if isinstance(entry, dict) and 'name' in entry:
                        temp = {'name': "{}: {}".format(race['name'], entry['name']),
                                'text': render(entry['entries']), 'srd': race['srd']}
                        self.rfeats.append(temp)
        with open('./static/classes.json', 'r') as f:
            self.classes = json.load(f)
        with open('./static/classfeats.json') as f:
            self.cfeats = json.load(f)
        with open('./static/spells.json', 'r') as f:
            self.spells = [Spell.from_data(r) for r in json.load(f)]
        with open('./static/items.json', 'r') as f:
            _items = json.load(f)
            self.items = [i for i in _items if i.get('type') is not '$']
        with open('./static/backgrounds.json', 'r') as f:
            self.backgrounds = [Background.from_data(b) for b in json.load(f)]
        self.subclasses = self.load_subclasses()

    def load_subclasses(self):
        s = []
        for _class in self.classes:
            subclasses = _class.get('subclasses', [])
            for sc in subclasses:
                sc['name'] = f"{_class['name']}: {sc['name']}"
            s.extend(subclasses)
        return s


c = Compendium()
