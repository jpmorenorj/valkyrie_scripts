import vk_orbwalker
from valkyrie import *
from helpers.flags import Orbwalker
from helpers.targeting import *
from helpers.damages import MixedDamage, calculate_raw_spell_dmg
from helpers.spells import Slot
from time import time
import math

target_selector = None
minion_selector = None

Q_Enabled = True
W_Enabled = True
R_Kill_Steal = True
R_Shield_Ally = True
Q_Auto_Harass = True
W_Anti_Melee = True
W_Anti_Gap = True
Q_Range = 600
W_Range = 1115 # 1300 Original
R_Max_Range = 5000
AA_Soul_Enabled = False

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

def get_q_passive_additional_range(ctx):
	passive_stacks = ctx.player.num_buff_stacks('SennaPassive')

	return passive_stacks * 25

def calc_q_damage(ctx, target):
    q_dmg = calculate_raw_spell_dmg(ctx.player, ctx.player.spells[Slot.Q])
    return q_dmg.calc_against(ctx, ctx.player, target)

def calc_w_damage(ctx, target):
    w_dmg = calculate_raw_spell_dmg(ctx.player, ctx.player.spells[Slot.W])
    return w_dmg.calc_against(ctx, ctx.player, target)

def calc_r_damage(ctx, target):
    r_dmg = calculate_raw_spell_dmg(ctx.player, ctx.player.spells[Slot.R])
    return r_dmg.calc_against(ctx, ctx.player, target)

def get_enemy_targets(ctx: Context, range):
    return ctx.champs.enemy_to(ctx.player).targetable().near(ctx.player, range).get()

def get_allied_targets(ctx: Context, range):
    return ctx.champs.ally_to(ctx.player).targetable().near(ctx.player, range).get()

def get_minion_targets(ctx: Context, range):
    return ctx.minions.enemy_to(ctx.player).targetable().near(ctx.player, range).get()

def get_jg_targets(ctx: Context, range):
    return ctx.jungle.enemy_to(ctx.player).targetable().near(ctx.player, range).get()

def w_anti_gap_melee(ctx, W):

	if not ctx.player.can_cast_spell(W):
		return

	if W_Anti_Melee:

		possible_targets = get_enemy_targets(ctx, ctx.player.atk_range - 350)

		if len(possible_targets) == 0:
			return

		for target in possible_targets:
			ctx.cast_spell_on_unit(W, target)

	if W_Anti_Gap:

		possible_targets = get_enemy_targets(ctx, ctx.player.atk_range)

		if len(possible_targets) == 0:
			return

		for target in possible_targets:

			if target.dashing:
				ctx.cast_spell_on_unit(W, target)

def combo_q(ctx, Q):

	if not ctx.player.can_cast_spell(Q):
		return

	if Q_Enabled:
		Current_Target = target_selector.get_target(ctx, get_enemy_targets(ctx, Q_Range))

		if Current_Target is None:
			return

		pos = ctx.predict_cast_point(ctx.player, Current_Target, Q)
		if pos is not None:
			ctx.cast_spell(Q, pos)

		ctx.cast_spell_on_unit(Q, Current_Target)

def combo_w(ctx, W):

	if not ctx.player.can_cast_spell(W):
		return

	if ctx.player.curr_casting is not None:
		return

	if W_Enabled:

		aa_range = ctx.player.atk_range

		Current_Target = target_selector.get_target(ctx, get_enemy_targets(ctx, W_Range))

		if Current_Target is None:
			return

		distance = ctx.player.pos.distance(Current_Target.pos)

		if distance > aa_range + 20:
			ctx.cast_spell_on_unit(W, Current_Target)



def valkyrie_menu(ctx: Context):
	ui = ctx.ui

	global Q_Enabled, W_Enabled, R_Kill_Steal, R_Shield_Ally, Q_Auto_Harass, R_Max_Range, AA_Soul_Enabled, W_Anti_Melee, W_Anti_Gap

	ui.text('[dSenna] Doom Senna                                                      Version [0.1]\nDeveloped by Luck#1337')
	ui.separator()
	if ui.beginmenu("Senna Core"):
		if ui.beginmenu("[Q] Piercing Darkness"):
			Q_Enabled = ui.checkbox('Enabled [Q]', Q_Enabled)
			ui.endmenu()
		if ui.beginmenu("[W] Last Embrace"):
			W_Enabled = ui.checkbox('Enabled [W]', W_Enabled)
			ui.endmenu()
		ui.endmenu()
	ui.separator()
	if ui.beginmenu("Auto Harass Core"):
		if ui.beginmenu("[Q] Piercing Darkness"):
			Q_Auto_Harass = ui.checkbox("[Q] Auto Harass", Q_Auto_Harass)
			ui.separator()
			ui.text("Auto harass will trigger only when LastHit mode is being used.")
			ui.endmenu()
		ui.endmenu()
	ui.separator()
	if ui.beginmenu("Utility Core"):
		AA_Soul_Enabled = ui.checkbox("[AA] Auto Farm Souls [BROKEN]", AA_Soul_Enabled)
		if ui.beginmenu("[W] Last Embrace"):
			W_Anti_Melee = ui.checkbox("[W] Anti Melee", W_Anti_Melee)
			W_Anti_Gap = ui.checkbox("[W] Anti Gap Close", W_Anti_Gap)
			ui.endmenu()
		if ui.beginmenu("[R] Dawning Shadow"):
			R_Kill_Steal = ui.checkbox("[R] Kill Steal", R_Kill_Steal)
			R_Max_Range = ui.sliderint("[R] Kill Steal Max. Range", R_Max_Range, 2000, 10000)
			R_Shield_Ally = ui.checkbox("[R] Help Ally", R_Shield_Ally)
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
	cfg.get_bool("R_KS", R_Kill_Steal)
	cfg.get_bool("R_SA", R_Shield_Ally)
	cfg.get_bool("Q_HRS", Q_Auto_Harass)
	cfg.get_bool("R_MAX", R_Max_Range)
	cfg.get_bool("SOUL", AA_Soul_Enabled)
	cfg.get_bool("W_MLE", W_Anti_Melee)
	cfg.get_bool("W_GAP", W_Anti_Gap)

def valkyrie_on_save(ctx: Context):
	cfg = ctx.cfg
	
	cfg.get_bool("Q", Q_Enabled)
	cfg.get_bool("W", W_Enabled)
	cfg.get_bool("R_KS", R_Kill_Steal)
	cfg.get_bool("R_SA", R_Shield_Ally)
	cfg.get_bool("Q_HRS", Q_Auto_Harass)
	cfg.get_bool("R_MAX", R_Max_Range)
	cfg.get_bool("SOUL", AA_Soul_Enabled)
	cfg.get_bool("W_MLE", W_Anti_Melee)
	cfg.get_bool("W_GAP", W_Anti_Gap)

def valkyrie_exec(ctx: Context):

	global last_positions, last_pos_id, Q_Range

	if ctx.player.dead:
		return

	player = ctx.player
	Q_Range += get_q_passive_additional_range(ctx)
	Q = ctx.player.spells[Slot.Q]
	W = ctx.player.spells[Slot.W]
	E = ctx.player.spells[Slot.E]
	R = ctx.player.spells[Slot.R]

	if Orbwalker.Attacking:
		return

	if R_Kill_Steal:
		if ctx.player.curr_casting is None:

			R_KS_Targets = get_enemy_targets(ctx, R_Max_Range)

			for champ in R_KS_Targets:

				distance = ctx.player.pos.distance(champ.pos)

				if distance > 900 and calc_r_damage(ctx, champ) > champ.health:
					pos = ctx.predict_cast_point(ctx.player, champ, R)
					if pos is not None:
						ctx.cast_spell(R, pos)

	if R_Shield_Ally:
		if ctx.player.curr_casting is None:

			R_Shield_Targets = get_allied_targets(ctx, 10000)

			for champ in R_Shield_Targets:

				distance = ctx.player.pos.distance(champ.pos)
				percentageHealth = (champ.health / champ.max_health) * 100

				if percentageHealth < 18:
					pos = ctx.predict_cast_point(ctx.player, champ, R)
					if pos is not None:
						ctx.cast_spell(R, pos)

	if Orbwalker.CurrentMode == Orbwalker.ModeKite:

		combo_q(ctx, Q)
		combo_w(ctx, W)

	if Orbwalker.CurrentMode == Orbwalker.ModeLastHit or Orbwalker.CurrentMode == Orbwalker.ModeLanePush:

		if AA_Soul_Enabled:

			atk_range = ctx.player.atk_range - 5

			targets = ctx.others.enemy_to(ctx.player).targetable().near(ctx.player, atk_range).get()

			for target in targets:
				if target.name == 'sennasoul':

					now = time()
					pause = 0.1

					Orbwalker.PauseUntil = now + pause
					ctx.attack(target)