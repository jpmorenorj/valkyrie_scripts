from math import dist
import vk_orbwalker
from valkyrie import *
from helpers.flags import Orbwalker, EvadeFlags
from helpers.targeting import *
from boku_no_orbwalker import target_selector
from helpers.damages import calculate_raw_spell_dmg
from helpers.spells import Slot
from time import time
import math

target_selector = None
minion_selector = None

R_Enabled, E_Enabled, W_Enabled, Q_Enabled = True, True, True, True
W_Range = 900 # 950 
E_Range = 1200
W_Surrounded = 3

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

def get_e_range(ctx):
	return 525 + (ctx.player.lvl * 8) - 8

def get_e_stack_damage(ctx, Current_Target, additional_stacks):
	return ((calc_e_damage(ctx, Current_Target) / 100) * 30) * Current_Target.num_buff_stacks('tristanaecharge') + additional_stacks

def point_has_minion(ctx, pos: Vec3):
	minions = ctx.minions.enemy_to(ctx.player).targetable().near(pos, 1250).get()

	for minion in minions:
		try:
			if pos.distance(minion.pos) < ctx.player.atk_range:
				return True
		except:
			pass

	return False

def point_has_enemy_champ(ctx, pos: Vec3):
	champs = ctx.champs.enemy_to(ctx.player).targetable().near(pos, 1250).get()

	for champ in champs:
		try:
			if pos.distance(champ.pos) < ctx.player.atk_range:
				return True
		except:
			pass

	return False

def combo_q(ctx, Q):

	if not ctx.player.can_cast_spell(Q):
		return

	if ctx.player.curr_casting is not None:
		return

	if W_Enabled:
		Current_Target = target_selector.get_target(ctx, get_enemy_targets(ctx, ctx.player.atk_range+100))

		if Current_Target is None:
			return

		ctx.cast_spell(Q, None)

def killsteal_w(ctx, W):

	wTargetsKS = get_enemy_targets(ctx, W_Range + ctx.player.atk_range)
	highestDistance = 0

	if len(wTargetsKS) > 2:
		return

def combo_w(ctx, W):

	if not ctx.player.can_cast_spell(W):
		return

	if ctx.player.curr_casting is not None:
		return

	if W_Enabled:
		
		wTargets = get_enemy_targets(ctx, 350)
		bestPoint = None
		lowestDistance = 10000

		if len(wTargets) < W_Surrounded:
			return

		for Current_Target in wTargets:

			if Current_Target is None:
				return

			for point in range(0, 360, 15):
				point_temp = math.radians(point)
				pX, pY, pZ = W_Range * math.cos(point_temp) + ctx.player.pos.x, ctx.player.pos.y, W_Range * math.sin(point_temp) + ctx.player.pos.z

				if Vec3(pX, pY, pZ).distance(Current_Target.pos) < lowestDistance:

					if not point_has_minion(ctx, Vec3(pX, pY, pZ)) and not point_has_enemy_champ(ctx, Vec3(pX, pY, pZ)) and not ctx.is_wall_at(Vec3(pX, pY, pZ)) and not point_under_turret(ctx, Vec3(pX, pY, pZ)):
						lowestDistance = Vec3(pX, pY, pZ).distance(Current_Target.pos)
						bestPoint = Vec3(pX, pY, pZ)

			if ctx.player.can_cast_spell(W) and bestPoint:
				ctx.circle(ctx.w2s(bestPoint), 10, 20, 2, Col.Green)
				ctx.cast_spell(W, bestPoint)

def combo_e(ctx, E):

	if not ctx.player.can_cast_spell(E):
		return

	if ctx.player.curr_casting is not None:
		return

	if E_Enabled:
		Current_Target = target_selector.get_target(ctx, get_enemy_targets(ctx, get_e_range(ctx)))

		if Current_Target is None:
			return

		ctx.cast_spell_on_unit(E, Current_Target)

def point_under_turret(ctx, pos: Vec3):
	turrets = ctx.turrets.enemy_to(ctx.player).alive().near(ctx.player.pos, 1250).get()

	for turret in turrets:
		if pos.distance(turret.pos) <= 915:
			return True

	return False

def combo_r(ctx, R):

	if not ctx.player.can_cast_spell(R):
		return

	if ctx.player.curr_casting is not None:
		return

	if R_Enabled:

		Current_Target = target_selector.get_target(ctx, get_enemy_targets(ctx, ctx.player.atk_range + ctx.player.static.gameplay_radius))

		if Current_Target is None:
			return
		
		current_E_damage = get_e_stack_damage(ctx, Current_Target, 2)

		has_collector = False
		collector_dmg = 0
		for val in ctx.player.item_slots:
			if val.item and val.item.id == 6676:
				has_collector = True
				break

		if has_collector:
			collector_dmg = calc_collector_dmg(Current_Target)

		if current_E_damage + collector_dmg > Current_Target.health or calc_r_damage(ctx, Current_Target) + collector_dmg > Current_Target.health:
			ctx.cast_spell_on_unit(R, Current_Target)

def valkyrie_menu(ctx: Context):
	ui = ctx.ui

	global W_Enabled, E_Enabled, R_Enabled, Q_Enabled, W_Surrounded

	ui.text('[dTristana] Doom Tristana                                                      Version [0.2]\nDeveloped by Luck#1337')
	ui.separator()
	if ui.beginmenu("Gunner Core"):
		if ui.beginmenu("[Q] Rapid Fire"):
			W_Enabled = ui.checkbox('Enabled [Q]', W_Enabled)
			ui.endmenu()
		if ui.beginmenu("[W] Rocket Jump"):
			W_Enabled = ui.checkbox('Enabled [W]', W_Enabled)
			W_Surrounded = ui.sliderint('Use [W] Safe Pos if Champ Count >=', W_Surrounded, 0, 5)
			ui.endmenu()
		if ui.beginmenu("[E] Explosive Charge"):
			E_Enabled = ui.checkbox('Enabled [E]', E_Enabled)
			ui.endmenu()
		if ui.beginmenu("[R] Spray and Pray"):
			R_Enabled = ui.checkbox('Enabled Smart [R]', R_Enabled)
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

	cfg.get_bool("Q_Enabled", Q_Enabled)
	cfg.get_bool("R_Enabled", R_Enabled)
	cfg.get_bool("W_Enabled", W_Enabled)
	cfg.get_int("W_Surrounded", W_Surrounded)
	cfg.get_bool("E_Enabled", E_Enabled)

def valkyrie_on_save(ctx: Context):
	cfg = ctx.cfg
	
	cfg.get_bool("Q_Enabled", Q_Enabled)
	cfg.get_bool("R_Enabled", R_Enabled)
	cfg.get_bool("W_Enabled", W_Enabled)
	cfg.get_int("W_Surrounded", W_Surrounded)
	cfg.get_bool("E_Enabled", E_Enabled)

def valkyrie_exec(ctx: Context):

	player = ctx.player
	Q = ctx.player.spells[Slot.Q]
	W = ctx.player.spells[Slot.W]
	E = ctx.player.spells[Slot.E]
	R = ctx.player.spells[Slot.R]
	ctx.pill("Tristana", Col.Black, Col.Cyan)

	if Orbwalker.Attacking:
		return

	if ctx.player.dead:
		return

	if ctx.player.curr_casting is not None:
		return

	if Orbwalker.CurrentMode == Orbwalker.ModeKite:

		combo_e(ctx, E)
		combo_q(ctx, Q)
		combo_w(ctx, W)
		combo_r(ctx, R)


