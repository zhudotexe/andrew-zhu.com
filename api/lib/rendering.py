import logging
import re

ABILITY_MAP = {'str': 'Strength', 'dex': 'Dexterity', 'con': 'Constitution',
               'int': 'Intelligence', 'wis': 'Wisdom', 'cha': 'Charisma'}

log = logging.getLogger(__name__)


def render(text, md_breaks=False):
    """Parses a list or string from... data.
    :returns str - The final text."""
    if not isinstance(text, list):
        return parse_data_formatting(str(text))

    out = []
    join_str = '\n' if not md_breaks else '  \n'

    for entry in text:
        if not isinstance(entry, dict):
            out.append(str(entry))
        elif isinstance(entry, dict):
            if not 'type' in entry and 'title' in entry:
                out.append(f"**{entry['title']}**: {render(entry['text'])}")
            elif not 'type' in entry and 'istable' in entry:  # only for races
                temp = f"**{entry['caption']}**\n" if 'caption' in entry else ''
                temp += ' - '.join(f"**{cl}**" for cl in entry['thead']) + '\n'
                for row in entry['tbody']:
                    temp += ' - '.join(f"{col}" for col in row) + '\n'
                out.append(temp.strip())
            elif not 'type' in entry:
                out.append((f"**{entry['name']}**: " if 'name' in entry else '') +
                           render(entry['entries']))
            elif entry['type'] == 'entries':
                out.append((f"**{entry['name']}**: " if 'name' in entry else '') + render(
                    entry['entries']))  # oh gods here we goooooooo
            elif entry['type'] == 'item':
                out.append((f"**{entry['name']}**: " if 'name' in entry else '') + render(
                    entry['entry']))  # oh gods here we goooooooo
            elif entry['type'] == 'options':
                pass  # parsed separately in classfeat
            elif entry['type'] == 'list':
                out.append('\n'.join(f"- {render([t])}" for t in entry['items']))
            elif entry['type'] == 'table':
                temp = f"**{entry['caption']}**\n" if 'caption' in entry else ''
                temp += ' - '.join(f"**{cl}**" for cl in entry['colLabels']) + '\n'
                for row in entry['rows']:
                    temp += ' - '.join(f"{col}" for col in row) + '\n'
                out.append(temp.strip())
            elif entry['type'] == 'invocation':
                pass  # this is only found in options
            elif entry['type'] == 'abilityAttackMod':
                out.append(f"`{entry['name']} Attack Bonus = "
                           f"{' or '.join(ABILITY_MAP.get(a) for a in entry['attributes'])}"
                           f" modifier + Proficiency Bonus`")
            elif entry['type'] == 'abilityDc':
                out.append(f"`{entry['name']} Save DC = 8 + "
                           f"{' or '.join(ABILITY_MAP.get(a) for a in entry['attributes'])}"
                           f" modifier + Proficiency Bonus`")
            elif entry['type'] == 'bonus':
                out.append("{:+}".format(entry['value']))
            elif entry['type'] == 'dice':
                if 'toRoll' in entry:
                    out.append(' + '.join(f"{d['number']}d{d['faces']}" for d in entry['toRoll']))
                else:
                    out.append(f"{entry['number']}d{entry['faces']}")
            elif entry['type'] == 'bonusSpeed':
                out.append(f"{entry['value']} feet")
            else:
                log.warning(f"Missing entry type parse: {entry}")
        else:
            log.warning(f"Unknown entry: {entry}")

    return parse_data_formatting(join_str.join(out))


FORMATTING = {'bold': '**', 'italic': '*', 'b': '**', 'i': '*'}
PARSING = {
    'creature': lambda e: e.split('|')[-1],
    'item': lambda e: e.split('|')[0],
    'filter': lambda e: e.split('|')[0],
    'condition': lambda e: e,
    'spell': lambda e: e.split('|')[0]
}


def parse_data_formatting(text):
    """Parses a {@format } string."""
    exp = re.compile(r'{@(\w+) (.+?)}')

    def sub(match):
        if match.group(1) in PARSING:
            f = PARSING.get(match.group(1), lambda e: e)
            return f(match.group(2))
        else:
            f = FORMATTING.get(match.group(1), '')
            if not match.group(1) in FORMATTING:
                log.warning(f"Unknown tag: {match.group(1)}")
            return f"{f}{match.group(2)}{f}"

    while exp.search(text):
        text = exp.sub(sub, text)
    return text
