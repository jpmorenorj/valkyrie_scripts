from math import dist
import vk_orbwalker
from valkyrie import *
from helpers.flags import Orbwalker, EvadeFlags
from helpers.targeting import *
from helpers.damages import calculate_raw_spell_dmg
from helpers.spells import Slot
from time import time
import math

## Fixed collector_dmg type crash

target_selector = None
minion_selector = None

R_Enabled, E_Enabled, W_Enabled= True, True, True
W_Range = 900 # 950 
E_Range = 1200
R_Targets = 3

def is_immobile(ctx, target):
	for buff in target.buffs:

		if 'snare' in buff.name.lower():
			return True
		elif 'stun' in buff.name.lower():
			return True
		elif 'suppress' in buff.name.lower():
			return True
		elif 'root' in buff.name.lower():
			return True
		elif 'taunt' in buff.name.lower():
			return True
		elif 'sleep' in buff.name.lower():
			return True
		elif 'knockup' in buff.name.lower():
			return True
		elif 'binding' in buff.name.lower():
			return True
		elif 'morganaq' in buff.name.lower():
			return True
		elif 'jhinw' in buff.name.lower():
			return True
	return False

def calc_q_damage(ctx, target):
    q_dmg = calculate_raw_spell_dmg(ctx.player, ctx.player.spells[Slot.Q])
    return q_dmg.calc_against(ctx, ctx.player, target)

def calc_w_damage(ctx, target):
    w_dmg = calculate_raw_spell_dmg(ctx.player, ctx.player.spells[Slot.W])
    return w_dmg.calc_against(ctx, ctx.player, target)

def calc_e_damage(ctx, target):
    e_dmg = calculate_raw_spell_dmg(ctx.player, ctx.player.spells[Slot.E])
    return e_dmg.calc_against(ctx, ctx.player, target)

def calc_r_damage(ctx, target):
    r_dmg = calculate_raw_spell_dmg(ctx.player, ctx.player.spells[Slot.R])
    return r_dmg.calc_against(ctx, ctx.player, target)

def get_enemy_targets(ctx: Context, range):
    return ctx.champs.enemy_to(ctx.player).targetable().near(ctx.player, range).get()

def get_minion_targets(ctx: Context, range):
    return ctx.minions.enemy_to(ctx.player).targetable().near(ctx.player, range).get()

def get_jg_targets(ctx: Context, range):
    return ctx.jungle.enemy_to(ctx.player).targetable().near(ctx.player, range).get()

def calc_collector_dmg(player):
	return player.health * 0.05

def combo_w(ctx, W):

	if not ctx.player.can_cast_spell(W):
		return

	if ctx.player.curr_casting is not None:
		return

	if W_Enabled:
		Current_Target = target_selector.get_target(ctx, get_enemy_targets(ctx, W_Range))

		if Current_Target is None:
			return

		predicted_pos = ctx.predict_cast_point(ctx.player, Current_Target, W)

		if predicted_pos is not None:
			ctx.cast_spell(W, predicted_pos)

def point_under_turret(ctx, pos: Vec3):
	turrets = ctx.turrets.enemy_to(ctx.player).alive().near(ctx.player.pos, 1250).get()

	for turret in turrets:
		if pos.distance(turret.pos) <= 915:
			return True

	return False

def point_has_minion(ctx, pos: Vec3):
	minions = ctx.minions.enemy_to(ctx.player).targetable().near(pos, 1250).get()

	for minion in minions:
		try:
			if pos.distance(minion.pos) < 250:
				return True
		except:
			pass

	return False

def point_has_enemy_champ(ctx, pos: Vec3):
	champs = ctx.champs.enemy_to(ctx.player).targetable().near(pos, 1250).get()

	for champ in champs:
		try:
			if pos.distance(champ.pos) < E_Range+100:
				return True
		except:
			pass

	return False

def combo_r(ctx, R):

	if not ctx.player.can_cast_spell(R):
		return

	if ctx.player.curr_casting is not None:
		return

	if R_Enabled:
		possible_targets = get_enemy_targets(ctx, 850)

		if len(possible_targets) >= R_Targets:
			ctx.cast_spell(R, None)


def valkyrie_menu(ctx: Context):
	ui = ctx.ui

	global W_Enabled, E_Enabled, R_Enabled

	ui.text('[dTwitch] Doom Twitch                                                      Version [0.2]\nDeveloped by Luck#1337')
	ui.separator()
	if ui.beginmenu("Plague Core"):
		if ui.beginmenu("[W] Venom Cask"):
			W_Enabled = ui.checkbox('Enabled [W]', W_Enabled)
			ui.endmenu()
		if ui.beginmenu("[E] Contaminate"):
			E_Enabled = ui.checkbox('Enabled Auto [E]', E_Enabled)
			ui.endmenu()
		if ui.beginmenu("[R] Spray and Pray"):
			R_Enabled = ui.checkbox('Enabled [R]', R_Enabled)
			R_Min = ui.sliderint('Use [R] Targets >=', R_Targets, 0, 5)
			ui.endmenu()

		ui.endmenu()
	ui.separator()
	

def valkyrie_on_load(ctx: Context):
	global target_selector, minion_selector

	if not Orbwalker.Present:
		target_selector = None
		minion_selector = None
	else:
		target_selector = Orbwalker.SelectorChampion
		minion_selector = Orbwalker.SelectorMonster

	cfg = ctx.cfg

	cfg.get_bool("R_Enabled", R_Enabled)
	cfg.get_bool("W_Enabled", W_Enabled)
	cfg.get_bool("E_Enabled", E_Enabled)
	cfg.get_int("R_Targets", R_Targets)

def valkyrie_on_save(ctx: Context):
	cfg = ctx.cfg
	
	cfg.get_bool("R_Enabled", R_Enabled)
	cfg.get_bool("W_Enabled", W_Enabled)
	cfg.get_bool("E_Enabled", E_Enabled)
	cfg.get_int("R_Targets", R_Targets)

def valkyrie_exec(ctx: Context):

	player = ctx.player
	W = ctx.player.spells[Slot.W]
	E = ctx.player.spells[Slot.E]
	R = ctx.player.spells[Slot.R]
	ctx.pill("Twitch", Col.Black, Col.Cyan)
	collector_dmg = 0

	if Orbwalker.Attacking:
		return

	if ctx.player.dead:
		return

	if ctx.player.curr_casting is not None:
		return

	if E_Enabled:

		has_collector = False
		for val in player.item_slots:
			if val.item and val.item.id == 6676:
				has_collector = True
				break

		for champ in ctx.champs.enemy_to(player).targetable().near(player, E_Range).get():
			if has_collector:
				collector_dmg = calc_collector_dmg(champ)

			if champ.health - calculate_raw_spell_dmg(player, E).calc_against(ctx, player, champ) - collector_dmg <= 0.0:
				ctx.cast_spell(E, None)
				break

	if Orbwalker.CurrentMode == Orbwalker.ModeKite:

		combo_w(ctx, W)
		combo_r(ctx, R)


