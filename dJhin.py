import vk_orbwalker
from valkyrie import *
from helpers.flags import Orbwalker
from helpers.targeting import *
from helpers.damages import calculate_raw_spell_dmg
from helpers.spells import Slot
from time import time

target_selector = None
minion_selector = None

Q_Enabled = True
W_Enabled = True
E_Enabled = True
E_CC_Enabled = True
R_Enabled = True
W_Jungle_Steal = True
W_Kill_Steal = True
Q_Kill_Minion = True
Q_Only_Reloading = True
Q_Range = 555
W_Range = 2420 # 2520 Original
E_Range = 755
R_Range = 3050 # 3500 Original

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

def lasthit_q(ctx, jhinQ):

	if not ctx.player.can_cast_spell(jhinQ):
		return

	if Q_Kill_Minion:
		Current_Target = minion_selector.get_target(ctx, get_minion_targets(ctx, Q_Range))

		if Current_Target is None:
			return

		if Current_Target is None:
			return

		if calc_q_damage(ctx, Current_Target) > Current_Target.health and not Q_Only_Reloading:
			ctx.cast_spell_on_unit(jhinQ, Current_Target)
		elif calc_q_damage(ctx, Current_Target) > Current_Target.health and Q_Only_Reloading and ctx.player.has_buff('JhinPassiveReload'):
			ctx.cast_spell_on_unit(jhinQ, Current_Target)

def combo_q(ctx, jhinQ):

	if not ctx.player.can_cast_spell(jhinQ):
		return

	if Q_Enabled:
		Current_Target = target_selector.get_target(ctx, get_enemy_targets(ctx, Q_Range))

		if Current_Target is None:
			return

		ctx.cast_spell_on_unit(jhinQ, Current_Target)

def combo_w(ctx, jhinW):

	if not ctx.player.can_cast_spell(jhinW):
		return

	if ctx.player.curr_casting is not None:
		return

	if W_Enabled:

		aa_range = ctx.player.atk_range

		Current_Target = target_selector.get_target(ctx, get_enemy_targets(ctx, W_Range))

		if Current_Target is None:
			return

		distance = ctx.player.pos.distance(Current_Target.pos)

		if Current_Target.has_buff("jhinespotteddebuff") and distance > aa_range + 200:
			pos = ctx.predict_cast_point(ctx.player, Current_Target, jhinW)
			if pos is not None:
				ctx.cast_spell(jhinW, pos)

def combo_e(ctx, jhinE, stacks):

	if not ctx.player.can_cast_spell(jhinE):
		return

	if ctx.player.curr_casting is not None:
		return

	if E_Enabled:

		Current_Target = target_selector.get_target(ctx, get_enemy_targets(ctx, E_Range))

		if Current_Target is None:
			return

		pos = ctx.predict_cast_point(ctx.player, Current_Target, jhinE)
		if pos is not None:
			ctx.cast_spell(jhinE, pos)



def valkyrie_menu(ctx: Context):
	ui = ctx.ui

	global Q_Enabled, W_Enabled, E_Enabled, R_Enabled, W_Jungle_Steal, W_Kill_Steal, E_CC_Enabled, Q_Kill_Minion, Q_Only_Reloading

	ui.text('[dJhin] Doom Jhin                                                      Version [0.3]\nDeveloped by Luck#1337')
	ui.separator()
	if ui.beginmenu("Virtuoso Core"):
		if ui.beginmenu("[Q] Dancing Grenade"):
			Q_Enabled = ui.checkbox('Enabled [Q]', Q_Enabled)
			ui.endmenu()
		if ui.beginmenu("[W] Deadly Flourish"):
			W_Enabled = ui.checkbox('Enabled [W]', W_Enabled)
			W_Kill_Steal = ui.checkbox('[W] Kill Steal', W_Kill_Steal)
			W_Jungle_Steal = ui.checkbox('[W] Jungle Steal', W_Jungle_Steal)
			ui.endmenu()
		if ui.beginmenu("[E] Captive Audience"):
			E_Enabled = ui.checkbox('Enabled [E]', E_Enabled)
			ui.endmenu()
		if ui.beginmenu("[R] Curtain Call"):
			R_Enabled = ui.checkbox('Enabled Auto [R]', R_Enabled)
			ui.endmenu()

		ui.endmenu()
	ui.separator()
	if ui.beginmenu("Farming Core"):
		if ui.beginmenu("[Q] Dancing Grenade"):
			Q_Kill_Minion = ui.checkbox("[Q] Killable Minion ", Q_Kill_Minion)
			Q_Only_Reloading = ui.checkbox("[Q] Only If Reloading ", Q_Only_Reloading)
			ui.endmenu()
		ui.endmenu()
	ui.separator()
	if ui.beginmenu("CC Abilities"):
		if ui.beginmenu("[E] Captive Audience"):
			E_CC_Enabled = ui.checkbox("[E] On CC'd Targets", E_CC_Enabled)
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
	cfg.get_bool("W_KS", W_Kill_Steal)
	cfg.get_bool("W_KS_JG", W_Jungle_Steal)
	cfg.get_bool("E", E_Enabled)
	cfg.get_bool("E_CC_Enabled", E_CC_Enabled)
	cfg.get_bool("Q_KS_MINION", Q_Kill_Minion)
	cfg.get_bool("Q_ONLY_RELOAD", Q_Only_Reloading)
	cfg.get_bool("R", R_Enabled)

def valkyrie_on_save(ctx: Context):
	cfg = ctx.cfg
	
	cfg.get_bool("Q", Q_Enabled)
	cfg.get_bool("W", W_Enabled)
	cfg.get_bool("W_KS", W_Kill_Steal)
	cfg.get_bool("W_KS_JG", W_Jungle_Steal)
	cfg.get_bool("E", E_Enabled)
	cfg.get_bool("E_CC_Enabled", E_CC_Enabled)
	cfg.get_bool("Q_KS_MINION", Q_Kill_Minion)
	cfg.get_bool("Q_ONLY_RELOAD", Q_Only_Reloading)
	cfg.get_bool("R", R_Enabled)

def valkyrie_exec(ctx: Context):

	global last_positions, last_pos_id

	player = ctx.player
	jhinQ = ctx.player.spells[Slot.Q]
	jhinW = ctx.player.spells[Slot.W]
	jhinE = ctx.player.spells[Slot.E]
	jhinR = ctx.player.spells[Slot.R]

	if Orbwalker.Attacking:
		return

	if ctx.player.dead:
		return

	if R_Enabled and jhinR.name == "jhinrshot":
		cur_target = target_selector.get_target(ctx, get_enemy_targets(ctx, R_Range))
		enemiesInR = get_enemy_targets(ctx, R_Range)

		if len(enemiesInR) == 0:
			last_positions = []
			last_pos_id = []

		for champ in enemiesInR:
			if champ.net_id in last_pos_id:
				continue

			last_positions.append(champ.pos)
			last_pos_id.append(champ.net_id)

		if cur_target is not None:
			ctx.cast_spell_on_unit(jhinR, cur_target)

		if not len(last_positions) == 0:
			ctx.cast_spell(jhinR, last_positions[0])

		return

	if W_Kill_Steal:
		if ctx.player.curr_casting is None:

			W_KS_Targets = get_enemy_targets(ctx, W_Range)

			for champ in W_KS_Targets:
				if calc_w_damage(ctx, champ) > champ.health:
					pos = ctx.predict_cast_point(ctx.player, champ, jhinW)
					if pos is not None:
						ctx.cast_spell(jhinW, pos)

	if W_Jungle_Steal:
		if ctx.player.curr_casting is None:

			W_JG_Targets = get_jg_targets(ctx, W_Range)

			for creep in W_JG_Targets:
				if calc_w_damage(ctx, creep) > creep.health:
					pos = ctx.predict_cast_point(ctx.player, creep, jhinE)
					if pos is not None:
						ctx.cast_spell(jhinW, pos)

	if E_CC_Enabled:

		if ctx.player.curr_casting is None:
			cur_target = target_selector.get_target(ctx, get_enemy_targets(ctx, E_Range))

			if cur_target is not None:

				if is_immobile(ctx, cur_target) and not cur_target.moving:
					pos = ctx.predict_cast_point(ctx.player, cur_target, jhinE)
					if pos is not None:
						ctx.cast_spell(jhinE, pos)

	if Orbwalker.CurrentMode == Orbwalker.ModeKite:

		e_stacks = player.num_buff_stacks('JhinEPassive')

		if player.has_buff('JhinPassiveReload'):

			combo_e(ctx, jhinE, e_stacks)

		combo_q(ctx, jhinQ)
		combo_w(ctx, jhinW)

	if Orbwalker.CurrentMode == Orbwalker.ModeLastHit or Orbwalker.CurrentMode == Orbwalker.ModeLanePush:

		lasthit_q(ctx, jhinQ)

