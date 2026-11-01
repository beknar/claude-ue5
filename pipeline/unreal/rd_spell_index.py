"""A helper of the dungeon levels' stages (not a stage): weapons point at their spells by place (FRDWeaponDef::SpellIndex),
and stages that each take their own spells out of the generator's table and add them again at its end (872's chi
attacks, 876's summons) move the others'. After writing the table, repoint_spell_weapons(gen) points every spell weapon
named as a spell of the table (on every hero, locked or not, and among the generator's weapons) at that spell's place
again. The table's own spells (the Mage's "Fire" for Fire Bolt) are named otherwise and never moved. Returns how many moved."""


def repoint_spell_weapons(gen):
    by = {str(s.name): i for i, s in enumerate(gen.get_editor_property("spells"))}
    moved = [0]

    def fix(ws):
        out = []
        for w in ws:
            i = by.get(str(w.name))
            if w.spell and i is not None and w.spell_index != i:
                w.spell_index = i; moved[0] += 1
            out.append(w)
        return out
    hs = list(gen.get_editor_property("heroes"))
    for h in hs:
        h.weapons = fix(h.weapons); h.locked_weapons = fix(h.locked_weapons)
    gen.set_editor_property("heroes", hs)
    gen.set_editor_property("weapons", fix(gen.get_editor_property("weapons")))
    return moved[0]
