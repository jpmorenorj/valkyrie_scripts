from math import dist
import vk_orbwalker
from valkyrie import *
from helpers.flags import Orbwalker, EvadeFlags
from helpers.targeting import *
from helpers.damages import calculate_raw_spell_dmg
from helpers.spells import Slot
from time import time
import math

target_selector = None
minion_selector = None


R_Enabled, E_Enabled, W_Enabled, Q_Enabled = True, True, True, True
Q_Range = 600
W_Range = 2700
R_Min = 1000
R_Max = 3000
R_Under_HP = 35
R_Target_HP = 25
R_Radius = 525

last_positions = []
last_pos_id = []

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

def combo_q(ctx, Q):

	if not ctx.player.can_cast_spell(Q):
		return

	if ctx.player.curr_casting is not None:
		return

	if Q_Enabled:
		Current_Target = target_selector.get_target(ctx, get_enemy_targets(ctx, Q_Range))

		if Current_Target is None:
			return

		ctx.cast_spell(Q, None)

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
		distance = ctx.player.pos.distance(Current_Target.pos)

		if predicted_pos is not None and distance > ctx.player.atk_range:
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
			if pos.distance(champ.pos) < R_Radius:
				return True
		except:
			pass

	return False

def combo_e(ctx, E):

	if not ctx.player.can_cast_spell(E):
		return

	if ctx.player.curr_casting is not None:
		return

	if E_Enabled:

		cols = ctx.collisions_for(ctx.player)
		for col in cols:
			if EvadeFlags.CurrentEvadePriority >= 2 and ctx.player.can_cast_spell(E):
				ctx.cast_spell(E, None)

def combo_r(ctx, R):

	if not ctx.player.can_cast_spell(R):
		return

	if ctx.player.curr_casting is not None:
		return

	if R_Enabled:
		possible_targets = get_enemy_targets(ctx, R_Max)
		highestDistance = 0

		for cur_target in possible_targets:
			isTagged = False

			for buff in cur_target.buffs:
				if 'kaisapassivemarker' in buff.name:
					isTagged = True

			localHealthPercent = (ctx.player.health / ctx.player.max_health) * 100
			enemyHealthPercent = (cur_target.health / cur_target.max_health) * 100

			if (localHealthPercent < R_Under_HP or enemyHealthPercent < R_Target_HP) and isTagged:
				for point in range(0, 360, 20):
					point_temp = math.radians(point)
					pX, pY, pZ = R_Radius * math.cos(point_temp) + cur_target.pos.x, cur_target.pos.y, R_Radius * math.sin(point_temp) + cur_target.pos.z

					if Vec3(pX, pY, pZ).distance(cur_target.pos) > highestDistance:

							if not point_has_enemy_champ(ctx, Vec3(pX, pY, pZ)) and not point_has_minion(ctx, Vec3(pX, pY, pZ)) and not ctx.is_wall_at(Vec3(pX, pY, pZ)) and not point_under_turret(ctx, Vec3(pX, pY, pZ)):
								highestDistance = Vec3(pX, pY, pZ).distance(cur_target.pos)
								bestPoint = Vec3(pX, pY, pZ)

				if ctx.player.can_cast_spell(R) and bestPoint is not None:
					ctx.circle(ctx.w2s(bestPoint), 10, 20, 2, Col.Green)
					ctx.cast_spell(R, bestPoint)



def valkyrie_menu(ctx: Context):
	ui = ctx.ui

	global Q_Enabled, W_Enabled, E_Enabled, R_Enabled, R_Min, R_Max, R_Target_HP, R_Under_HP

	ui.text("[dKaisa] Doom Kai'sa                                                      Version [0.1]\nDeveloped by Luck#1337")
	ui.separator()
	if ui.beginmenu("Void Core"):
		if ui.beginmenu("[Q] Icathian Rain"):
			Q_Enabled = ui.checkbox('Enabled [Q]', Q_Enabled)
			ui.endmenu()
		if ui.beginmenu("[W] Void Seeker"):
			W_Enabled = ui.checkbox('Enabled [W]', W_Enabled)
			ui.endmenu()
		if ui.beginmenu("[E] Supercharge"):
			E_Enabled = ui.checkbox('Enabled [E]', E_Enabled)
			ui.endmenu()
		if ui.beginmenu("[R] Killer Instinct"):
			R_Enabled = ui.checkbox('Enabled [R]', R_Enabled)
			R_Target_HP = ui.sliderint('Safe [R] < HP %', R_Target_HP, 0, 100)
			R_Under_HP = ui.sliderint('Safe [R] < HP %', R_Under_HP, 0, 100)
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

	cfg.get_bool("Q", Q_Enabled)
	cfg.get_bool("W", W_Enabled)
	cfg.get_bool("E", E_Enabled)
	cfg.get_bool("R_Target_HP", R_Target_HP)
	cfg.get_bool("R", R_Enabled)
	cfg.get_int("R_Under_HP", R_Under_HP)

def valkyrie_on_save(ctx: Context):
	cfg = ctx.cfg
	
	cfg.get_bool("Q", Q_Enabled)
	cfg.get_bool("W", W_Enabled)
	cfg.get_bool("E", E_Enabled)
	cfg.get_bool("R_Target_HP", R_Target_HP)
	cfg.get_bool("R", R_Enabled)
	cfg.get_int("R_Under_HP", R_Under_HP)

def valkyrie_exec(ctx: Context):

	global last_positions, last_pos_id

	player = ctx.player
	Q = ctx.player.spells[Slot.Q]
	W = ctx.player.spells[Slot.W]
	E = ctx.player.spells[Slot.E]
	R = ctx.player.spells[Slot.R]
	ctx.pill("Kai'sa", Col.Black, Col.Cyan)

	if Orbwalker.Attacking:
		return

	if ctx.player.dead:
		return

	if ctx.player.curr_casting is not None:
		return

	if Orbwalker.CurrentMode == Orbwalker.ModeKite:

		combo_e(ctx, E)
		combo_w(ctx, W)
		combo_q(ctx, Q)
		combo_r(ctx, R)

