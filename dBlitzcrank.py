import vk_orbwalker
from valkyrie import *
from helpers.flags import Orbwalker
from helpers.targeting import *
from helpers.damages import calculate_raw_spell_dmg
from helpers.spells import Slot
import time

target_selector = None

Q_Enabled = True
W_Enabled = True
E_Enabled = True
R_Enabled = True
E_Melee_Range = True
Q_Kill_Steal = True
Q_Jungle_Steal = True
R_Kill_Steal = True
R_Targets = 2
Q_Range = 915 #Safe Distance | Real Range = 1115
W_Range = 1250
R_Range = 600

def calc_r_damage(ctx, target):
    r_dmg = calculate_raw_spell_dmg(ctx.player, ctx.player.spells[Slot.R])
    return r_dmg.calc_against(ctx, ctx.player, target)

def get_enemy_targets(ctx: Context, range):
    return ctx.champs.enemy_to(ctx.player).targetable().near(ctx.player, range).get()

def get_minion_targets(ctx: Context, range):
    return ctx.minions.enemy_to(ctx.player).targetable().near(ctx.player, range).get()

def blitz_q(ctx: Context, blitzQ):

	target = target_selector.get_target(ctx, get_enemy_targets(ctx, Q_Range))
	minions = get_minion_targets(ctx, 1115)

	if target is None:
		return

	if ctx.player.can_cast_spell(blitzQ):

		distance = ctx.player.pos.distance(target.pos)
		##pos = target.predict_position(blitzQ.static.cast_time + (distance/1800))	

		ctx.cast_spell_on_unit(blitzQ, target)

def blitz_w(ctx: Context, blitzW):

	target = target_selector.get_target(ctx, get_enemy_targets(ctx, W_Range))

	if target is None:
		return

	if ctx.player.can_cast_spell(blitzW):

		ctx.cast_spell(blitzW, None)

def blitz_e(ctx: Context, blitzE):

	local_range = ctx.player.atk_range
	target = target_selector.get_target(ctx, get_enemy_targets(ctx, local_range))

	if target is None:
		return

	if ctx.player.can_cast_spell(blitzE):

		ctx.cast_spell(blitzE, None)

def blitz_r(ctx: Context, blitzR):

	targets = get_enemy_targets(ctx, R_Range)

	if targets is None:
		return

	if ctx.player.can_cast_spell(blitzR) and len(targets) >= R_Targets:

		ctx.cast_spell(blitzR, None)
	


def valkyrie_menu(ctx: Context):
	ui = ctx.ui

	global Q_Enabled, W_Enabled, E_Enabled, R_Enabled, W_Range, E_Melee_Range, Q_Kill_Steal, R_Kill_Steal, Q_Jungle_Steal, R_Targets

	ui.text('[dBlitzcrank] Doom Blitzcrank                                 Version [0.1]\nDeveloped by Luck#1337')
	ui.separator()
	if ui.beginmenu("Blitzcrank Core"):
		if ui.beginmenu("[Q] Rocket Grab"):
			Q_Enabled = ui.checkbox('Enabled [Q]', Q_Enabled)
			Q_Kill_Steal = ui.checkbox('[Q] Kill Steal (Waiting for update currently broken)', Q_Kill_Steal)
			Q_Jungle_Steal = ui.checkbox('[Q] Jungle Steal (Waiting for update currently broken)', Q_Jungle_Steal)
			ui.endmenu()
		if ui.beginmenu("[W] Overdrive"):
			W_Enabled = ui.checkbox('Enabled [W]', W_Enabled)
			W_Range = ui.sliderfloat("If Target in Range", W_Range, 0.0, 2000.0)
			ui.endmenu()
		if ui.beginmenu("[E] Power Fist"):
			E_Enabled = ui.checkbox('Enabled [E]', E_Enabled)
			E_Melee_Range = ui.checkbox('Only [E] in AA Range', E_Melee_Range)
			ui.endmenu()
		if ui.beginmenu("[R] Static Field"):
			R_Enabled = ui.checkbox('Enabled [R]', R_Enabled)
			R_Targets = ui.sliderint("If Targets >=", R_Targets, 1, 5)
			R_Kill_Steal = ui.checkbox('[R] Kill Steal (Waiting for update currently broken)', R_Kill_Steal)
			ui.endmenu()

		ui.endmenu()

def valkyrie_on_load(ctx: Context):
	global target_selector

	if not Orbwalker.Present:
		target_selector = None
	else:
		target_selector = Orbwalker.SelectorChampion

	cfg = ctx.cfg

	cfg.get_bool("Q", Q_Enabled)
	cfg.get_bool("Q_KS", Q_Kill_Steal)
	cfg.get_bool("W", W_Enabled)
	cfg.get_float("W_RNG", W_Range)
	cfg.get_bool("E", E_Enabled)
	cfg.get_bool("E_MLE", E_Melee_Range)
	cfg.get_bool("R", R_Enabled)
	cfg.get_bool("R_KS", R_Kill_Steal)
	cfg.get_bool("R_TGTS", R_Targets)

def valkyrie_on_save(ctx: Context):
	cfg = ctx.cfg
	
	cfg.get_bool("Q", Q_Enabled)
	cfg.get_bool("Q_KS", Q_Kill_Steal)
	cfg.get_bool("W", W_Enabled)
	cfg.get_float("W_RNG", W_Range)
	cfg.get_bool("E", E_Enabled)
	cfg.get_bool("E_MLE", E_Melee_Range)
	cfg.get_bool("R", R_Enabled)
	cfg.get_bool("R_KS", R_Kill_Steal)
	cfg.get_bool("R_TGTS", R_Targets)

def valkyrie_exec(ctx: Context):

	player = ctx.player
	blitzQ = ctx.player.spells[Slot.Q]
	blitzW = ctx.player.spells[Slot.W]
	blitzE = ctx.player.spells[Slot.E]
	blitzR = ctx.player.spells[Slot.R]

	if R_Kill_Steal:
		R_KS_Targets = get_enemy_targets(ctx, R_Range)

		for champ in R_KS_Targets:

			if calc_r_damage(ctx, champ) > champ.health:
				ctx.cast_spell(blitzR, None)

	if Orbwalker.CurrentMode == Orbwalker.ModeKite:
		blitz_q(ctx, blitzQ)
		blitz_w(ctx, blitzW)
		blitz_e(ctx, blitzE)
		blitz_r(ctx, blitzR)

