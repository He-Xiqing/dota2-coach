"""出装用法（非中文界面用英文简版，保证不出现中文）。"""

from __future__ import annotations

HOW_EN: dict[str, str] = {
    "item_manta": "Pop it to dispel silence/initiation and spawn illusions; illusions can push lanes and scout",
    "item_black_king_bar": "Pop before a fight or on the first stun; don't tank physical damage or Blade Mail, use the 10s window",
    "item_pipe": "Shield the team before magic burst; long cooldown, wait until their initiation is used",
    "item_crimson_guard": "Use once their physical cores come online; reduces attacks and physical spells, stay grouped",
    "item_spirit_vessel": "Tag high-regen targets (Necrophos/Oracle/Dazzle) before they heal; can also save allies",
    "item_lotus_orb": "Cast on yourself/ally against single-target control or silence; reflects targeted spells",
    "item_sheepstick": "Hex a key target to start or counter-initiate on a diving core",
    "item_orchid": "Silence their core to stop escapes or counter-initiation; back off if you can't kill in 5s",
    "item_ghost": "Pop against heavy physical burst for immunity and slow; don't use it into magic burst",
    "item_shivas_guard": "Use vs heavy lifesteal/attack speed/regen; reduces healing and attack speed",
    "item_assault": "Buff your physical cores' armor and attack speed before fights",
    "item_heavens_halberd": "Disarm a physical core for 5s; also grants evasion to yourself",
    "item_solar_crest": "Save an ally or buff your core's attack speed/armor",
    "item_glimmer_cape": "Cast on yourself/ally when chased; invisibility plus magic resistance",
    "item_force_staff": "Push yourself/ally out of danger, or shove an enemy into your team",
    "item_cyclone": "Cyclone a key target or save an ally; interrupts channeled spells",
    "item_aeon_disk": "Triggers automatically when bursted, once every 90s; not a routine defensive",
    "item_skadi": "Buy vs heavy lifesteal/healing; slows and reduces healing",
    "item_diffusal_blade": "Use vs mana shields/high-mana heroes; can purge buffs",
    "item_satanic": "Pop while focused to lifesteal back; don't pop inside a stun chain",
    "item_hurricane_pike": "Push attackers away to create distance; pairs with ranged cores",
    "item_mask_of_madness": "Use for farming or duels; full attack speed for 8s, avoid using while stunnable",
    "item_aghanims_scepter": "Buy when it upgrades your ultimate; skip if it changes nothing",
    "item_aghanims_shard": "Buy from the side shop after 20:00 for a cheap skill upgrade",
    "item_sange_and_yasha": "Move speed and status resistance for melee kiting and slow-heavy games",
    "item_mjollnir": "Buy vs illusions/summons; chain lightning clears waves",
    "item_dragon_lance": "Ranged cores buy it for range and HP; extra safe distance before fights",
    "item_blink": "Initiate or escape over terrain; instant repositioning on a short cooldown",
    "item_ultimate_scepter": "Buy when it upgrades your ultimate; skip if it changes nothing",
}


def how_en(item: str) -> str:
    return HOW_EN.get(item, "")
