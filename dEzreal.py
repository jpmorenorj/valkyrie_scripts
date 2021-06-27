from math import dist
import vk_orbwalker
from valkyrie import *
from helpers.flags import EvadeFlags
from dMoveModule import CurrentTarget, MovePrediction
from helpers.targeting import *
from helpers.damages import calculate_raw_spell_dmg
from helpers.spells import Slot
from boku_no_orbwalker import target_selector, Orbwalker
from time import time
import math

target_selector = None
minion_selector = None


E_Gap_Close, E_Anti_Melee, E_Force_Evade, Q_Harass, Q_Kill_Minion, R_Enabled, E_Enabled, W_Enabled, Q_Enabled, E_Safe_KS = True, True, True, True, True, True, True, True, True, True
Q_Range = 1100 # 1200 
W_Range = 1100 # 1200 
E_Range = 475
R_Min = 1000
R_Max = 3000
#R_Can_Hit = 3

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

def lasthit_q(ctx, Q):

	if not ctx.player.can_cast_spell(Q):
		return

	if Q_Kill_Minion:

		targetted_minion = minion_selector.get_target(ctx, get_minion_targets(ctx, Q_Range))
		untargetted_minions = get_minion_targets(ctx, Q_Range)
		ctx.pill("QFarm", Col.Black, Col.Cyan)

		if targetted_minion is None:
			return

		for minion in untargetted_minions:

			if minion == targetted_minion:
				continue

			if minion.dead:
				continue

			if not minion.health < calc_q_damage(ctx, minion):
				continue

			predicted_pos = ctx.predict_cast_point(ctx.player, minion, Q)

			if predicted_pos is not None:
				ctx.cast_spell(Q, predicted_pos)

def harass_q(ctx, Q):

	if not ctx.player.can_cast_spell(Q):
		return

	if Q_Harass:

		target = target_selector.get_target(ctx, get_enemy_targets(ctx, Q_Range))
		ctx.pill("Harass", Col.Black, Col.Cyan)

		if target is None:
			return

		distance = ctx.player.pos.distance(target.pos)

		if distance < ctx.player.atk_range:
			return

		predicted_pos = ctx.predict_cast_point(ctx.player, target, Q)

		if predicted_pos is not None:
			ctx.cast_spell(Q, predicted_pos)

def combo_q(ctx, Q):

	if not ctx.player.can_cast_spell(Q):
		return

	if ctx.player.curr_casting is not None:
		return

	if Q_Enabled:
		Current_Target = target_selector.get_target(ctx, get_enemy_targets(ctx, Q_Range))

		if Current_Target is None:
			return

		predicted_pos = MovePrediction.predict_collision(ctx, Q, Current_Target, 2, False)

		if predicted_pos is not None and ctx.predict_cast_point(ctx.player, Current_Target, Q) is not None:
			ctx.cast_spell(Q, predicted_pos)

def combo_w(ctx, W, Q):

	if not ctx.player.can_cast_spell(W):
		return

	if not ctx.player.can_cast_spell(Q):
		return

	if ctx.player.curr_casting is not None:
		return

	if W_Enabled:
		Current_Target = target_selector.get_target(ctx, get_enemy_targets(ctx, W_Range))

		if Current_Target is None:
			return

		predicted_Qpos = MovePrediction.predict_collision(ctx, Q, Current_Target, 3, False)
		predicted_pos = MovePrediction.predict_collision(ctx, W, Current_Target, 3, False)

		if predicted_pos is not None and predicted_Qpos is not None:
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

def combo_e(ctx, E, Q, W):

	if not ctx.player.can_cast_spell(E):
		return

	if ctx.player.curr_casting is not None:
		return

	if E_Enabled:

		q2Targets = get_enemy_targets(ctx, Q_Range*2)
		bestPoint = None
		lowestDistance = 10000

		if len(q2Targets) == 0:
			return

		if len(q2Targets) > 2:
			return

		for Current_Target in q2Targets:

			if Current_Target is None:
				return

			if ctx.player.pos.distance(Current_Target.pos) <= Q_Range:
				return

			Target_Killable = False
			totalDamage = 0

			for buff in Current_Target.buffs:
				if 'ezrealwattach' in buff.name:
					totalDamage = calc_q_damage(ctx, Current_Target) + calc_w_damage(ctx, Current_Target)

			if ctx.player.can_cast_spell(W):
				totalDamage = calc_q_damage(ctx, Current_Target) + calc_w_damage(ctx, Current_Target)

			totalDamage = calc_q_damage(ctx, Current_Target)

			if totalDamage > Current_Target.health:
				Target_Killable = True

			for point in range(0, 360, 15):
				point_temp = math.radians(point)
				pX, pY, pZ = E_Range * math.cos(point_temp) + ctx.player.pos.x, ctx.player.pos.y, E_Range * math.sin(point_temp) + ctx.player.pos.z

				if Vec3(pX, pY, pZ).distance(Current_Target.pos) < lowestDistance:

					if not point_has_minion(ctx, Vec3(pX, pY, pZ)) and not point_has_enemy_champ(ctx, Vec3(pX, pY, pZ)) and not ctx.is_wall_at(Vec3(pX, pY, pZ)) and not point_under_turret(ctx, Vec3(pX, pY, pZ)):
						lowestDistance = Vec3(pX, pY, pZ).distance(Current_Target.pos)
						bestPoint = Vec3(pX, pY, pZ)

			if ctx.player.can_cast_spell(Q) and bestPoint is not None and Target_Killable:
				ctx.circle(ctx.w2s(bestPoint), 10, 20, 2, Col.Green)
				ctx.cast_spell(E, bestPoint)

def combo_r(ctx, R):

	if not ctx.player.can_cast_spell(R):
		return

	if ctx.player.curr_casting is not None:
		return

	if R_Enabled:
		possible_targets = get_enemy_targets(ctx, R_Max)

		for cur_target in possible_targets:
			distance = ctx.player.pos.distance(cur_target.pos)
			W_Attached = False
			Target_Killable = False

			for buff in cur_target.buffs:
				if 'ezrealwattach' in buff.name:
					W_Attached = True

			if W_Attached:
				if calc_r_damage(ctx, cur_target) + calc_w_damage(ctx, cur_target) > cur_target.health:
					Target_Killable = True

			if calc_r_damage(ctx, cur_target) > cur_target.health:
				Target_Killable = True

			if cur_target is not None and not (distance < R_Min) and not (distance > R_Max) and Target_Killable:
				predicted_pos = MovePrediction.predict_collision(ctx, R, cur_target, 10, True)

				if predicted_pos is not None:
					ctx.cast_spell(R, predicted_pos)



def valkyrie_menu(ctx: Context):
	ui = ctx.ui

	global Q_Enabled, W_Enabled, E_Enabled, R_Enabled, Q_Kill_Minion, R_Min, R_Max, Q_Harass, E_Gap_Close, E_Anti_Melee, E_Force_Evade, E_Safe_KS#, R_Can_Hit

	ui.text('[dEzreal] Doom Ezreal                                                      Version [0.3]\nDeveloped by Luck#1337')
	ui.separator()
	if ui.beginmenu("Explorer Core"):
		if ui.beginmenu("[Q] Mystic Shot"):
			Q_Enabled = ui.checkbox('Enabled [Q]', Q_Enabled)
			ui.endmenu()
		if ui.beginmenu("[W] Essence Flux"):
			W_Enabled = ui.checkbox('Enabled [W]', W_Enabled)
			ui.endmenu()
		if ui.beginmenu("[E] Arcane Shift"):
			E_Enabled = ui.checkbox('Enabled [E]', E_Enabled)
			E_Gap_Close = ui.checkbox('[E] Anti-Gap', E_Gap_Close)
			E_Anti_Melee = ui.checkbox('[E] Anti-Melee', E_Anti_Melee)
			E_Force_Evade = ui.checkbox('[E] Force Evade', E_Force_Evade)
			E_Safe_KS = ui.checkbox('[E] Safe Kill Steal', E_Safe_KS)
			ui.endmenu()
		if ui.beginmenu("[R] Trueshot Barrage"):
			R_Enabled = ui.checkbox('Enabled [R]', R_Enabled)
			R_Min = ui.sliderint('Min. [R] Range', R_Min, 0, 1000)
			R_Max = ui.sliderint('Max. [R] Range', R_Max, 1000, 5000)
			ui.endmenu()

		ui.endmenu()
	ui.separator()
	if ui.beginmenu("Farming Core"):
		if ui.beginmenu("[Q] Mystic Shot"):
			Q_Kill_Minion = ui.checkbox("[Q] Killable Minion", Q_Kill_Minion)
			ui.endmenu()
		ui.endmenu()
	ui.separator()
	if ui.beginmenu("Harass Core"):
		if ui.beginmenu("[Q] Mystic Shot"):
			Q_Harass = ui.checkbox("[Q] Harass", Q_Harass)
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
	cfg.get_bool("Q_KS_MINION", Q_Kill_Minion)
	cfg.get_bool("E_Gap_Close", E_Gap_Close)
	cfg.get_bool("E_Anti_Melee", E_Anti_Melee)
	cfg.get_bool("E_Force_Evade", E_Force_Evade)
	cfg.get_bool("E_Safe_KS", E_Safe_KS)
	cfg.get_bool("R", R_Enabled)
	cfg.get_int("R_Min", R_Min)
	cfg.get_int("R_Max", R_Max)

def valkyrie_on_save(ctx: Context):
	cfg = ctx.cfg
	
	cfg.get_bool("Q", Q_Enabled)
	cfg.get_bool("W", W_Enabled)
	cfg.get_bool("E", E_Enabled)
	cfg.get_bool("Q_KS_MINION", Q_Kill_Minion)
	cfg.get_bool("E_Gap_Close", E_Gap_Close)
	cfg.get_bool("E_Anti_Melee", E_Anti_Melee)
	cfg.get_bool("E_Force_Evade", E_Force_Evade)
	cfg.get_bool("E_Safe_KS", E_Safe_KS)
	cfg.get_bool("R", R_Enabled)
	cfg.get_int("R_Min", R_Min)
	cfg.get_int("R_Max", R_Max)

def valkyrie_exec(ctx: Context):

	global last_positions, last_pos_id

	player = ctx.player
	Q = ctx.player.spells[Slot.Q]
	W = ctx.player.spells[Slot.W]
	E = ctx.player.spells[Slot.E]
	R = ctx.player.spells[Slot.R]
	highestDistance = 0
	bestPoint = None
	ctx.pill("Ezreal", Col.Black, Col.Cyan)

	if Orbwalker.Attacking:
		return

	if ctx.player.dead:
		return

	if ctx.player.curr_casting is not None:
		return

	if E_Force_Evade:
		cols = ctx.collisions_for(ctx.player)
		for col in cols:
			if EvadeFlags.EvadeEndTime + 0.15 >= col.time_until_impact and EvadeFlags.CurrentEvadePriority >= 2 and ctx.player.can_cast_spell(E) and col.final:
				ctx.cast_spell(E, ctx.player.pos + ((EvadeFlags.EvadePoint - ctx.player.pos).normalize() * ctx.player.pos.distance(EvadeFlags.EvadePoint)*4))
				ctx.pill("Evading", Col.Black, Col.Blue)

	if E_Anti_Melee:
		targets_melee_range = get_enemy_targets(ctx, 250)
		if len(targets_melee_range) > 0 and ctx.player.can_cast_spell(E):
			for danger in targets_melee_range:
				for point in range(0, 360, 20):
					point_temp = math.radians(point)
					pX, pY, pZ = E_Range * math.cos(point_temp) + ctx.player.pos.x, ctx.player.pos.y, E_Range * math.sin(point_temp) + ctx.player.pos.z

					if Vec3(pX, pY, pZ).distance(danger.pos) > highestDistance:

							if not point_has_enemy_champ(ctx, Vec3(pX, pY, pZ)) and not point_has_minion(ctx, Vec3(pX, pY, pZ)) and not ctx.is_wall_at(Vec3(pX, pY, pZ)) and not point_under_turret(ctx, Vec3(pX, pY, pZ)):
								highestDistance = Vec3(pX, pY, pZ).distance(danger.pos)
								bestPoint = Vec3(pX, pY, pZ)

				if ctx.player.can_cast_spell(Q) and bestPoint is not None:
					ctx.circle(ctx.w2s(bestPoint), 10, 20, 2, Col.Green)
					ctx.cast_spell(E, bestPoint)

	if E_Gap_Close:
		targets_gap_range = get_enemy_targets(ctx, E_Range)
		if len(targets_gap_range) > 0 and ctx.player.can_cast_spell(E):
			for danger in targets_gap_range:
				if danger.dashing:
					for point in range(0, 360, 20):
						point_temp = math.radians(point)
						pX, pY, pZ = E_Range * math.cos(point_temp) + ctx.player.pos.x, ctx.player.pos.y, E_Range * math.sin(point_temp) + ctx.player.pos.z

						if Vec3(pX, pY, pZ).distance(danger.pos) > highestDistance:

								if not point_has_enemy_champ(ctx, Vec3(pX, pY, pZ)) and not ctx.is_wall_at(Vec3(pX, pY, pZ)) and not point_under_turret(ctx, Vec3(pX, pY, pZ)):
									highestDistance = Vec3(pX, pY, pZ).distance(danger.pos)
									bestPoint = Vec3(pX, pY, pZ)

					if ctx.player.can_cast_spell(Q) and bestPoint is not None:
						ctx.circle(ctx.w2s(bestPoint), 10, 20, 2, Col.Green)
						ctx.cast_spell(E, bestPoint)

	if Orbwalker.CurrentMode == Orbwalker.ModeKite:

		combo_e(ctx, E, Q, W)
		combo_w(ctx, W, Q)
		combo_q(ctx, Q)
		combo_r(ctx, R)

	if Orbwalker.CurrentMode == Orbwalker.ModeLanePush:

		lasthit_q(ctx, Q)

	if Orbwalker.CurrentMode == Orbwalker.ModeLastHit:

		harass_q(ctx, Q)

