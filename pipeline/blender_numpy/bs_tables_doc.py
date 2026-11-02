"""Brokenspire's tables in docs/levels/brokenspire.md, from SourceArt/brokenspire/town.json (what 882 puts in the game):
its people (between <!-- bs:people --> and <!-- /bs:people -->) and its quests (<!-- bs:quests --> ... <!-- /bs:quests -->).
Run after changing town.json (and 882 for the game).

    python bs_tables_doc.py"""
import json, os, re
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
D = json.load(open(os.path.join(ROOT, "claude_ue5", "SourceArt", "brokenspire", "town.json"), encoding="utf-8"))
DOC = os.path.join(ROOT, "docs", "levels", "brokenspire.md")
FUNCTIONAL = {"Elder": "quests: why the town needs her", "Scholar": "quests: what the evil is", "Captain": "quests: the castle and the wilderness",
              "Smith": "opens the smithy's work", "Trader": "opens the store", "Healer": "opens the healer's", "Priest": "opens the temple's blessing",
              "Keeper": "opens her storage"}
WHERE = {"Elder": "the square, by the quest board", "Scholar": "the tavern", "Captain": "before the castle", "Smith": "the smithy", "Trader": "the store",
         "Healer": "the healer's house", "Priest": "the temple", "Keeper": "the storehouse", "Innkeeper": "the tavern", "Drunk": "the tavern, by the hearth",
         "Witch": "her hut, the town's far corner", "Child": "about the square", "Refugee": "by the gate, their tents", "Idiot": "the streets",
         "Preacher": "the square", "Mourner": "the graveyard", "Guard": "the gate, the castle's door", "Militia": "the lane inside the wall",
         "Soldier": "the barracks", "Townsfolk": "before their homes"}
def pack(t):
    m = t["mesh"].split("/")[-1]
    return f"{t['pack']} `{m}`" + (" (the drunk's own clips)" if "Drunk" in t.get("idle", "") else "")
rows = ["| Who | Role | Where | What she gets from them | Model |", "|---|---|---|---|---|"]
for t in D["townsfolk"]:
    rows.append(f"| {t['title']}, {t.get('calling', '')} | {t['role']} | {WHERE.get(t['role'], '')} | {FUNCTIONAL.get(t['role'], 'a line of theirs (' + str(len(t.get('lines', []))) + ')')}"
                f"{' and ' + str(len(t.get('topics', []))) + ' questions' if t.get('topics') else ''} | {pack(t)} |")
people = "\n".join(rows)
GOAL = {"talk": "speak with", "guards": "the Mistward Hall's guards killed", "enter": "Mistward Castle entered", "kills": "monsters killed in the castle",
        "kind": "of that kind killed in the castle", "tier": "the castle's tier opened", "boss": "tier bosses slain", "prisoners": "prisoners freed", "wild": "the wilderness (later)"}
rows = ["| Quest | Given by | After | Asks | Reward |", "|---|---|---|---|---|"]
titles = {q["id"]: q["title"] for q in D["quests"]}
for q in D["quests"]:
    g = q["goal"]; k = g.split(":")[0]
    asks = q.get("hint", "")
    rew = ", ".join(x for x in (f"{q.get('gold', 0)} gold" if q.get("gold") else "", q.get("reward", "")) if x)
    rows.append(f"| {q['title']} | {q['giver']} | {titles.get(q.get('after', ''), '')} | {asks} (`{g}` x {q.get('count', 1)}) | {rew}{' (when the gate opens)' if k == 'wild' else ''} |")
quests = "\n".join(rows)
t = open(DOC, encoding="utf-8").read()
for tag, body in (("people", people), ("quests", quests)):
    t, n = re.subn(rf"(<!-- bs:{tag} -->\n)(?:.*?\n)?(<!-- /bs:{tag} -->)", lambda m: m.group(1) + body + "\n" + m.group(2), t, flags=re.S)
    assert n == 1, f"no <!-- bs:{tag} --> markers in {DOC}"
open(DOC, "w", encoding="utf-8", newline="\n").write(t)
print("bs tables:", len(D["townsfolk"]), "people,", len(D["quests"]), "quests ->", DOC)
