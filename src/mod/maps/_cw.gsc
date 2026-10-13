// clonewars: Star Wars Battlefront II weapons, land mines and the grenade switch for every zombie map.
//
// Weapons: every WWII gun is re-written as a SWBF2 gun by its loose weapon file (tools/build_weapon_files.py), so
// the walls, the mystery box and Pack-a-Punch already hand out SWBF2 guns.  This script adds what a weapon file
// cannot: travelling blaster bolts, the Battlefront reticle while aiming down sights, the SWBF2 models sliding
// out of the walls, land mines (bought at the grenade wall) and the 3 key that switches the grenade slot between
// thermal detonators and mines.

init()
{
	maps\_cw_weapons::init();

	level._effect["cw_blaster_bolt"] = LoadFx( "misc/fx_cw_blaster_bolt" );
	level._effect["cw_blaster_impact"] = LoadFx( "misc/fx_cw_blaster_impact" );
	level._effect["cw_mine_explode"] = LoadFx( "explosions/default_explosion" );
	PrecacheModel( "tag_origin" );
	PrecacheModel( "weapon_cw_mine" );
	PrecacheShader( "cw_reticle" );
	PrecacheItem( "cw_mine" );
	PrecacheString( &"CLONEWARS_BUY_MINES" );
	PrecacheString( &"CLONEWARS_NADE_THERMAL" );
	PrecacheString( &"CLONEWARS_NADE_MINE" );

	// grenade slot: thermal detonators (the stock zombie grenade, re-skinned) and land mines
	level.cw_nade_types = [];
	level.cw_nade_types[0] = "stielhandgranate";
	level.cw_nade_types[1] = "cw_mine";
	// PRICE: every wall gun, door, debris pile, mystery box, weapon cabinet, the mine wall and Pack-a-Punch cost this
	// many points (0 = the maps' own prices).  Must match PRICE in tools/build_strings.py + tools/build_prices.py.
	level.cw_price = 0;
	// no zombie eye glow on the droids (the stock spawner checks this before attaching it)
	level.zombie_eye_glow = false;
	level.cw_mine_cost = 250;
	if( level.cw_price > 0 )
	{
		level.cw_mine_cost = level.cw_price;
	}
	level.cw_mine_max = 4;
	level.cw_mines_placed_max = 12;

	level thread walls_init();
	prices_init();
	level thread pap_init();
}

// self = player, on every spawn
player_init()
{
	self thread blaster_watch();
	self thread ads_reticle();
	self thread grenade_inventory();
	self thread mine_watch();
	self thread view_tuning();

	if( GetDvar( "cw_test" ) != "" && GetDvar( "cw_test" ) != "0" )
	{
		self thread test_timeline();
	}
}

weapon_class( weapon )
{
	if( IsDefined( weapon ) && IsDefined( level.cw_class[weapon] ) )
	{
		return level.cw_class[weapon];
	}
	return "";
}

is_blaster( cls )
{
	return cls == "rifle" || cls == "pistol" || cls == "commando" || cls == "shotgun" || cls == "chaingun" || cls == "sniper";
}

// ---------------------------------------------------------------- prices

// Runs during _load, before _zombiemode sets up the doors / debris / box, so every script that reads zombie_cost (to
// charge, or to pick its "[Cost: n]" hint) sees the new price.  Wall guns get theirs from mp/zombiemode.csv (the cost
// table every map's add_zombie_weapon reads first); Pack-a-Punch is scripted below (its 5000 is hard-coded).
prices_init()
{
	if( level.cw_price <= 0 )
	{
		return;
	}
	price = level.cw_price;
	names = StrTok( "zombie_door,zombie_debris,treasure_chest_use,weapon_cabinet_use", "," );
	for( n = 0; n < names.size; n++ )
	{
		ents = GetEntArray( names[n], "targetname" );
		for( i = 0; i < ents.size; i++ )
		{
			ents[i].zombie_cost = price;
		}
	}
	level.zombie_treasure_chest_cost = price;
	// hint refs the stock scripts build from the cost; the texts are the stock ones with "[Cost: n]" rewritten
	// (tools/build_strings.py)
	maps\_zombiemode_utility::add_zombie_hint( "default_buy_door_" + price, &"ZOMBIE_BUTTON_BUY_OPEN_DOOR_1000" );
	maps\_zombiemode_utility::add_zombie_hint( "default_buy_debris_" + price, &"ZOMBIE_BUTTON_BUY_CLEAR_DEBRIS_1000" );
	maps\_zombiemode_utility::add_zombie_hint( "default_treasure_chest_" + price, &"ZOMBIE_RANDOM_WEAPON_950" );
}

// ---------------------------------------------------------------- Pack-a-Punch (Der Riese)

// The stock machine charges a hard-coded 5000 (and refuses anyone with less).  Its trigger is moved out of reach and
// this runs the same sequence (knuckle crack, gun into the machine, take it within the timeout) at level.cw_price.
pap_init()
{
	trigs = GetEntArray( "zombie_vending_upgrade", "targetname" );
	level.cw_pap_cost = 5000;		// Der Riese's price
	if( level.cw_price > 0 )
	{
		level.cw_pap_cost = level.cw_price;
	}
	if( trigs.size == 0 )
	{
		if( level.script == "nazi_zombie_prototype" )
		{
			pap_nacht_init();
		}
		return;
	}
	if( level.cw_price <= 0 )
	{
		return;
	}
	PrecacheString( &"CLONEWARS_PAP" );
	PrecacheString( &"CLONEWARS_PAP_TAKE" );
	spots = [];
	for( i = 0; i < trigs.size; i++ )
	{
		spot = SpawnStruct();
		spot.origin = trigs[i].origin;
		spot.angles = trigs[i].angles;
		spot.machine = GetEnt( trigs[i].target, "targetname" );
		spots[i] = spot;
	}
	level waittill( "Pack_A_Punch_on" );
	wait( 0.5 );		// the stock thread has set the machine's wait_flag up by now
	for( i = 0; i < trigs.size; i++ )
	{
		trigs[i].origin = trigs[i].origin - ( 0, 0, 10000 );
		level thread pap_think( spots[i] );
	}
}

// ---- Nacht der Untoten has no Pack-a-Punch: a Der Riese machine is spawned upstairs, where the Halo 3 mod has it
// (waw-halo3 round 30): the bigger room on the far side of the corner wall next to the sawed-off double-barrel wall,
// its back on that wall, facing into the room.  Nacht ships no upgraded weapons: the SWBF2 "Elite" blasters are linked
// into mod.ff (weapon,sp/<name>_upgraded - PrecacheItem needs a fastfile entry) and precached here.  The two launchers
// are left out: their files would pull more effects into mod.ff and Der Riese is at its 400-effect limit.
pap_nacht_init()
{
	PrecacheModel( "zombie_vending_packapunch_on" );
	PrecacheString( &"CLONEWARS_PAP" );
	PrecacheString( &"CLONEWARS_PAP_TAKE" );
	level.cw_pap_nacht = true;
	level.cw_pap_ok = [];
	names = StrTok( "zombie_colt,colt,colt_dirty_harry,walther,sw_357,m1carbine,m1garand,gewehr43,stg44,thompson,mp40,kar98k,springfield,ptrs41_zombie,kar98k_scoped_zombie,m1garand_gl,doublebarrel,doublebarrel_sawed_grip,shotgun,fg42_bipod,mg42_bipod,30cal_bipod,bar", "," );
	for( i = 0; i < names.size; i++ )
	{
		PrecacheItem( names[i] + "_upgraded" );
		level.cw_pap_ok[names[i]] = true;
	}
	level thread pap_nacht_spawn();
}

pap_nacht_spawn()
{
	while( !IsDefined( level.cw_walls_ready ) )
	{
		wait( 0.1 );
	}
	wall_model = undefined;
	trigs = GetEntArray( "weapon_upgrade", "targetname" );
	for( i = 0; i < trigs.size; i++ )
	{
		if( IsDefined( trigs[i].zombie_weapon_upgrade ) && trigs[i].zombie_weapon_upgrade == "doublebarrel_sawed_grip" )
		{
			wall_model = GetEnt( trigs[i].target, "targetname" );
		}
	}
	if( !IsDefined( wall_model ) )
	{
		return;
	}
	// waw-halo3 pap_spawn (measured in game): chalk wall face ~ +x of the model, the corner wall towards +y; the machine
	// stands 74 in from the chalk wall, 42 in past the corner wall's far face, yaw 180 (its front is its local RIGHT)
	start = ( wall_model.origin[0] - 60, wall_model.origin[1], wall_model.origin[2] - 20 );
	wall = BulletTrace( start, start + ( 300, 0, 0 ), false, undefined );
	side = BulletTrace( start, start + ( 0, 400, 0 ), false, undefined );
	far_side = BulletTrace( side["position"] + ( 0, 80, 0 ), side["position"], false, undefined );
	x = wall["position"][0] - 74;
	y = far_side["position"][1] + 42;
	ground = BulletTrace( ( x, y, start[2] ), ( x, y, start[2] - 300 ), false, undefined );

	machine = Spawn( "script_model", ( x, y, ground["position"][2] ) );
	machine.angles = ( 0, 180, 0 );
	machine SetModel( "zombie_vending_packapunch_on" );
	level.cw_pap_machine = machine;

	spot = SpawnStruct();
	spot.machine = machine;
	spot.origin = machine.origin + vector_scale( AnglesToRight( machine.angles ), 30 ) + ( 0, 0, 45 );
	spot.angles = machine.angles + ( 0, 90, 0 );
	spot.gun_origin = machine.origin + ( 0, 0, 35 );
	spot.gun_angles = machine.angles + ( 0, 90, 0 );
	level thread pap_push_loop( machine );
	level thread pap_think( spot );
	if( GetDvar( "cw_test" ) != "" && GetDvar( "cw_test" ) != "0" )
	{
		SetDvar( "cw_dbg", "pap nacht at " + machine.origin );
		SetDvar( "cw_dbg", "pap nacht at " + machine.origin );
	}
}

// a spawned model is not solid (waw-halo3 round 10): keep players out of its footprint
pap_push_loop( machine )
{
	for( ;; )
	{
		wait( 0.05 );
		players = GetPlayers();
		for( i = 0; i < players.size; i++ )
		{
			p = players[i];
			f = AnglesToForward( machine.angles );
			r = AnglesToRight( machine.angles );
			d = p.origin - machine.origin;
			if( abs( d[2] ) > 80 )
			{
				continue;
			}
			along = VectorDot( d, f );
			front = VectorDot( d, r );
			if( along <= -47 || along >= 40 || front >= 41 || front <= -40 )
			{
				continue;
			}
			if( 41 - front <= along + 47 )
			{
				front = 41;
			}
			else
			{
				along = -47;
			}
			p SetOrigin( ( machine.origin[0], machine.origin[1], p.origin[2] ) + vector_scale( f, along ) + vector_scale( r, front ) );
		}
	}
}

pap_near( p, spot )
{
	if( !p maps\_zombiemode_utility::is_player_valid( p ) )
	{
		return false;
	}
	eye = p GetEye();
	d = Distance( eye, spot.origin );
	if( d > 100 )
	{
		return false;
	}
	dir = VectorNormalize( spot.origin - eye );
	return VectorDot( dir, AnglesToForward( p GetPlayerAngles() ) ) > 0.6 || d < 45;
}

pap_pressed( p )
{
	pressed = p UseButtonPressed() && !( IsDefined( p.cw_pap_use ) && p.cw_pap_use );
	p.cw_pap_use = p UseButtonPressed();
	return pressed;
}

pap_think( spot )
{
	rollers = Spawn( "script_origin", spot.origin );
	timer = Spawn( "script_origin", spot.origin );
	if( !IsDefined( level.cw_pap_nacht ) )
	{
		rollers PlayLoopSound( "packa_rollers_loop" );
	}
	origin = spot.origin;
	angles = spot.angles;
	if( IsDefined( spot.machine ) )
	{
		origin = spot.machine.origin + ( 0, 0, 35 );
		angles = spot.machine.angles + ( 0, 90, 0 );
	}

	for( ;; )
	{
		wait( 0.05 );
		players = GetPlayers();
		buyer = undefined;
		for( i = 0; i < players.size; i++ )
		{
			p = players[i];
			near = pap_near( p, spot );
			p hint( near, &"CLONEWARS_PAP" );
			if( !near )
			{
				p.cw_pap_use = p UseButtonPressed();
				continue;
			}
			if( !pap_pressed( p ) )
			{
				continue;
			}
			w = p GetCurrentWeapon();
			if( p maps\_laststand::player_is_in_laststand() || p IsThrowingGrenade() || p IsSwitchingWeapons() || IsDefined( p.is_drinking ) )
			{
				continue;
			}
			if( IsDefined( level.cw_pap_nacht ) )
			{
				if( !IsDefined( level.cw_pap_ok[w] ) )
				{
					continue;
				}
			}
			else if( !IsDefined( level.zombie_include_weapons[w] ) || !IsDefined( level.zombie_include_weapons[w + "_upgraded"] ) )
			{
				continue;
			}
			if( p.score < level.cw_pap_cost )
			{
				p PlaySound( "no_purchase" );
				continue;
			}
			buyer = p;
			break;
		}
		if( !IsDefined( buyer ) )
		{
			continue;
		}

		for( i = 0; i < players.size; i++ )
		{
			players[i] hint( false, &"CLONEWARS_PAP" );
		}
		w = buyer GetCurrentWeapon();
		buyer maps\_zombiemode_score::minus_to_player_score( level.cw_pap_cost );
		if( IsDefined( level.cw_pap_nacht ) )
		{
			// Nacht has no knuckle-crack weapon or machine sounds: the gun is handed in, the other one comes up
			PlaySoundAtPosition( "purchase", spot.origin );
			buyer TakeWeapon( w );
			prim = buyer GetWeaponsListPrimaries();
			if( prim.size > 0 )
			{
				buyer SwitchToWeapon( prim[0] );
			}
			if( IsDefined( spot.gun_origin ) )
			{
				origin = spot.gun_origin;
				angles = spot.gun_angles;
			}
		}
		else
		{
			PlaySoundAtPosition( "bottle_dispense3d", spot.origin );
			buyer thread pap_knuckle_crack();
		}
		gun = buyer pap_gun_in_machine( w, origin, angles, rollers, spot.machine );

		// take it: the buyer presses Use at the machine before the timeout
		taken = false;
		limit = GetTime() + 15000;
		if( IsDefined( level.packapunch_timeout ) )
		{
			limit = GetTime() + level.packapunch_timeout * 1000;
		}
		if( !IsDefined( level.cw_pap_nacht ) )
		{
			timer PlayLoopSound( "ticktock_loop" );
		}
		buyer.cw_pap_use = true;
		while( GetTime() < limit && IsDefined( buyer ) )
		{
			wait( 0.05 );
			near = pap_near( buyer, spot );
			buyer hint( near, &"CLONEWARS_PAP_TAKE" );
			if( near && pap_pressed( buyer ) && !buyer maps\_laststand::player_is_in_laststand() )
			{
				taken = true;
				break;
			}
			if( !near )
			{
				buyer.cw_pap_use = buyer UseButtonPressed();
			}
		}
		timer StopLoopSound( 0.05 );
		if( IsDefined( buyer ) )
		{
			buyer hint( false, &"CLONEWARS_PAP_TAKE" );
		}
		if( taken )
		{
			primaries = buyer GetWeaponsListPrimaries();
			if( IsDefined( primaries ) && primaries.size >= 2 )
			{
				buyer maps\_zombiemode_weapons::weapon_give( w + "_upgraded" );
			}
			else
			{
				buyer GiveWeapon( w + "_upgraded" );
				buyer GiveMaxAmmo( w + "_upgraded" );
			}
			buyer SwitchToWeapon( w + "_upgraded" );
		}
		else
		{
			if( !IsDefined( level.cw_pap_nacht ) )
			{
				timer PlaySound( "packa_deny" );
			}
		}
		if( IsDefined( gun ) )
		{
			gun Delete();
		}
		wait( 0.5 );
	}
}

// The stock machine's sequence (Der Riese _zombiemode_perks.gsc do_knuckle_crack / third_person_weapon_upgrade),
// copied here: functions in another script are resolved when this file compiles, and Nacht has no perks script.
pap_knuckle_crack()
{
	gun = self GetCurrentWeapon();
	if( gun == "none" || gun == "mine_bouncing_betty" )
	{
		return;
	}
	self DisableOffhandWeapons();
	self DisableWeaponCycling();
	self AllowLean( false );
	self AllowAds( false );
	self AllowSprint( false );
	self AllowProne( false );
	self AllowMelee( false );
	if( self GetStance() == "prone" )
	{
		self SetStance( "crouch" );
	}
	primaries = self GetWeaponsListPrimaries();
	self TakeWeapon( gun );
	if( primaries.size <= 1 )
	{
		self GiveWeapon( "zombie_colt" );
	}
	self GiveWeapon( "zombie_knuckle_crack" );
	self SwitchToWeapon( "zombie_knuckle_crack" );

	self.is_drinking = 1;
	self waittill_any_pap( "fake_death", "death", "player_downed", "weapon_change_complete" );

	self EnableOffhandWeapons();
	self EnableWeaponCycling();
	self AllowLean( true );
	self AllowAds( true );
	self AllowSprint( true );
	self AllowProne( true );
	self AllowMelee( true );
	self TakeWeapon( "zombie_knuckle_crack" );
	if( !self maps\_laststand::player_is_in_laststand() )
	{
		primaries = self GetWeaponsListPrimaries();
		if( IsDefined( primaries ) && primaries.size > 0 )
		{
			self SwitchToWeapon( primaries[0] );
		}
		else
		{
			self SwitchToWeapon( "zombie_colt" );
		}
	}
	self.is_drinking = undefined;
}

waittill_any_pap( a, b, c, d )
{
	self endon( a );
	self endon( b );
	self endon( c );
	self waittill( d );
}

pap_gun_in_machine( current_weapon, origin, angles, rollers, machine )
{
	forward = AnglesToForward( angles );
	interact_pos = origin + vector_scale( forward, -25 );
	gun = Spawn( "script_model", interact_pos );
	gun.angles = self.angles;
	gun SetModel( GetWeaponModel( current_weapon ) );
	if( IsDefined( level._effect["packapunch_fx"] ) )
	{
		PlayFx( level._effect["packapunch_fx"], origin + ( 0, 1, -34 ), forward );
	}
	gun RotateTo( angles + ( 0, 90, 0 ), 0.35, 0, 0 );
	wait( 0.5 );
	gun MoveTo( origin, 0.5, 0, 0 );
	if( !IsDefined( level.cw_pap_nacht ) )
	{
		rollers PlaySound( "packa_weap_upgrade" );
	}
	if( IsDefined( machine ) && IsDefined( machine.wait_flag ) )
	{
		machine.wait_flag RotateTo( machine.wait_flag.angles + ( 179, 0, 0 ), 0.25, 0, 0 );
	}
	wait( 0.35 );
	gun Delete();
	wait( 3 );
	if( !IsDefined( level.cw_pap_nacht ) )
	{
		rollers PlaySound( "packa_weap_ready" );
	}
	else
	{
		rollers PlaySound( "purchase" );
	}
	gun = Spawn( "script_model", origin );
	gun.angles = angles + ( 0, 90, 0 );
	gun SetModel( GetWeaponModel( current_weapon + "_upgraded" ) );
	gun MoveTo( interact_pos, 0.5, 0, 0 );
	if( IsDefined( machine ) && IsDefined( machine.wait_flag ) )
	{
		machine.wait_flag RotateTo( machine.wait_flag.angles - ( 179, 0, 0 ), 0.25, 0, 0 );
	}
	wait( 0.5 );
	timeout = 15;
	if( IsDefined( level.packapunch_timeout ) )
	{
		timeout = level.packapunch_timeout;
	}
	gun MoveTo( origin, timeout, 0, 0 );
	return gun;
}

// ---------------------------------------------------------------- mystery box

// The stock box picks a weapon NAME at random, and many WWII names became the same SWBF2 gun - so it handed out
// duplicates of guns already held and the odds followed the WWII line-up.  When a box finishes its spin, its pick is
// replaced (if it is one of the SWBF2 guns) by a weighted pick of a SWBF2 gun the player does not hold yet; the floating
// model is swapped to match.  Ray Gun / Wunderwaffe / monkey picks are left as the map made them.
box_init()
{
	// entries per SWBF2 gun ("0" = as many as the map has names for it)
	level.cw_box_weight = [];
	level.cw_box_weight["rifle"] = 0;
	level.cw_box_weight["chaingun"] = 0;
	level.cw_box_weight["pistol"] = 0;
	level.cw_box_weight["shotgun"] = 3;
	level.cw_box_weight["commando"] = 3;
	level.cw_box_weight["sniper"] = 2;
	level.cw_box_weight["rocket"] = 2;
	level.cw_box_weight["emp"] = 2;

	trigs = GetEntArray( "treasure_chest_use", "targetname" );
	for( i = 0; i < trigs.size; i++ )
	{
		if( !IsDefined( trigs[i].target ) )
		{
			continue;
		}
		lid = GetEnt( trigs[i].target, "targetname" );
		if( !IsDefined( lid ) || !IsDefined( lid.target ) )
		{
			continue;
		}
		org = GetEnt( lid.target, "targetname" );
		if( IsDefined( org ) )
		{
			level thread box_watch( trigs[i], org );
		}
	}
}

box_watch( trig, org )
{
	for( ;; )
	{
		org waittill( "randomization_done" );
		waittillframeend;		// the box sets weapon_string right after (or before) the notify
		w = org.weapon_string;
		if( !IsDefined( w ) || weapon_class( w ) == "" )
		{
			continue;
		}
		player = box_user( trig );
		if( !IsDefined( player ) )
		{
			continue;
		}
		pick = box_pick( player );
		if( !IsDefined( pick ) || pick == w )
		{
			continue;
		}
		org.weapon_string = pick;
		models = GetEntArray( "script_model", "classname" );
		for( i = 0; i < models.size; i++ )
		{
			if( IsDefined( models[i].model ) && models[i].model == GetWeaponModel( w ) && Distance( models[i].origin, org.origin ) < 80 )
			{
				models[i] SetModel( GetWeaponModel( pick ) );
			}
		}
		if( GetDvar( "cw_test" ) != "" && GetDvar( "cw_test" ) != "0" )
		{
			SetDvar( "cw_dbg", "box " + w + " -> " + pick + " (" + weapon_class( pick ) + ")" );
		}
	}
}

box_user( trig )
{
	players = GetPlayers();
	best = undefined;
	bd = 100000;
	for( i = 0; i < players.size; i++ )
	{
		d = Distance( players[i].origin, trig.origin );
		if( d < bd )
		{
			bd = d;
			best = players[i];
		}
	}
	return best;
}

box_pick( player )
{
	// SWBF2 guns the player holds (any name, upgraded too)
	held = [];
	prim = player GetWeaponsListPrimaries();
	for( i = 0; i < prim.size; i++ )
	{
		c = weapon_class( prim[i] );
		if( c != "" )
		{
			held[c] = true;
		}
	}
	// the EMP launcher (the flamethrower's slot) is limited to one in the game
	players = GetPlayers();
	for( p = 0; p < players.size; p++ )
	{
		prim = players[p] GetWeaponsListPrimaries();
		for( i = 0; i < prim.size; i++ )
		{
			if( weapon_class( prim[i] ) == "emp" )
			{
				held["emp"] = true;
			}
		}
	}

	// the names the box can give, by SWBF2 gun
	names = [];
	keys = GetArrayKeys( level.zombie_weapons );
	for( i = 0; i < keys.size; i++ )
	{
		c = weapon_class( keys[i] );
		if( c == "" || IsSubStr( keys[i], "_upgraded" ) || IsDefined( held[c] ) )
		{
			continue;
		}
		if( !IsDefined( names[c] ) )
		{
			names[c] = [];
		}
		names[c][names[c].size] = keys[i];
	}

	classes = GetArrayKeys( names );
	total = 0;
	weights = [];
	for( i = 0; i < classes.size; i++ )
	{
		w = names[classes[i]].size;
		if( IsDefined( level.cw_box_weight[classes[i]] ) && level.cw_box_weight[classes[i]] > 0 )
		{
			w = level.cw_box_weight[classes[i]];
		}
		weights[i] = w;
		total += w;
	}
	if( total <= 0 )
	{
		return undefined;
	}
	r = RandomInt( total );
	for( i = 0; i < classes.size; i++ )
	{
		if( r < weights[i] )
		{
			list = names[classes[i]];
			return list[RandomInt( list.size )];
		}
		r -= weights[i];
	}
	return undefined;
}

// ---------------------------------------------------------------- walls

walls_init()
{
	// wait for _zombiemode_weapons to set the wall triggers up (it hides their models)
	while( !IsDefined( level.zombie_weapons ) )
	{
		wait( 0.1 );
	}
	wait( 1 );

	trigs = GetEntArray( "weapon_upgrade", "targetname" );
	for( i = 0; i < trigs.size; i++ )
	{
		weapon = trigs[i].zombie_weapon_upgrade;
		if( !IsDefined( weapon ) || !IsDefined( trigs[i].target ) )
		{
			continue;
		}
		model = GetEnt( trigs[i].target, "targetname" );
		if( weapon == "stielhandgranate" || weapon == "fraggrenade" )
		{
			// the grenade wall sells land mines instead (thermal detonators still come every round)
			if( IsDefined( model ) )
			{
				model SetModel( "weapon_cw_mine" );
			}
			spot = SpawnStruct();
			spot.origin = trigs[i].origin;
			spot.model = model;
			spot.shown = false;
			trigs[i].origin = trigs[i].origin - ( 0, 0, 10000 );
			level thread mine_wall_think( spot );
			continue;
		}
		if( IsDefined( model ) && weapon_class( weapon ) != "" )
		{
			model SetModel( GetWeaponModel( weapon ) );
		}
	}

	// The mystery box picks from every registered weapon: keep the grenades (thermal detonators, molotovs) out of it.
	// Their wall buys have read their prices already, and the round award hands thermals out directly.
	nades = StrTok( "stielhandgranate,fraggrenade,molotov,cw_mine", "," );
	for( i = 0; i < nades.size; i++ )
	{
		if( IsDefined( level.zombie_weapons[nades[i]] ) )
		{
			level.zombie_weapons[nades[i]] = undefined;
		}
	}
	level.cw_walls_ready = true;
	box_init();
}

mine_wall_think( spot )
{
	for( ;; )
	{
		wait( 0.05 );
		players = get_players();
		for( i = 0; i < players.size; i++ )
		{
			p = players[i];
			near = false;
			if( p maps\_zombiemode_utility::is_player_valid( p ) )
			{
				eye = p GetEye();
				d = Distance( eye, spot.origin );
				if( d < 96 )
				{
					dir = VectorNormalize( spot.origin - eye );
					near = VectorDot( dir, AnglesToForward( p GetPlayerAngles() ) ) > 0.7 || d < 40;
				}
			}
			p hint( near, &"CLONEWARS_BUY_MINES" );
			if( !near )
			{
				p.cw_use_down = p UseButtonPressed();
				continue;
			}
			pressed = p UseButtonPressed() && !( IsDefined( p.cw_use_down ) && p.cw_use_down );
			p.cw_use_down = p UseButtonPressed();
			if( !pressed )
			{
				continue;
			}
			if( p grenade_count( "cw_mine" ) >= level.cw_mine_max || p.score < level.cw_mine_cost )
			{
				p PlaySound( "no_purchase" );
				continue;
			}
			p maps\_zombiemode_score::minus_to_player_score( level.cw_mine_cost );
			p PlaySound( "purchase" );
			p.cw_nade_owned["cw_mine"] = true;
			p grenade_set( "cw_mine", level.cw_mine_max );
			if( p.cw_nade_cur != "cw_mine" )
			{
				p grenade_select( "cw_mine" );
			}
			if( !spot.shown && IsDefined( spot.model ) )
			{
				spot.shown = true;
				spot.model thread maps\_zombiemode_weapons::weapon_show( p );
			}
		}
	}
}

// one HUD line under the crosshair for the scripted buy spots and the grenade switch
hint( show, text )
{
	if( !IsDefined( self.cw_hint ) )
	{
		h = NewClientHudElem( self );
		h.alignX = "center";
		h.alignY = "middle";
		h.horzAlign = "center";
		h.vertAlign = "middle";
		h.x = 0;
		h.y = 110;
		h.fontScale = 1.4;
		h.foreground = true;
		h.hidewheninmenu = true;
		h.alpha = 0;
		self.cw_hint = h;
	}
	if( !show )
	{
		if( IsDefined( self.cw_hint_text ) && self.cw_hint_text == text )
		{
			self.cw_hint.alpha = 0;
			self.cw_hint_text = undefined;
		}
		return;
	}
	if( !IsDefined( self.cw_hint_text ) || self.cw_hint_text != text )
	{
		self.cw_hint SetText( text );
		self.cw_hint_text = text;
	}
	self.cw_hint.alpha = 1;
}

// ---------------------------------------------------------------- per-gun view offset

// Some guns sit closer to / farther from the body than their animations put them: the client view-model offset
// (cg_gun_x = forward, inches; hands and gun move together) is set while that gun is in hand.
view_tuning()
{
	self notify( "cw_view_tuning" );
	self endon( "cw_view_tuning" );
	self endon( "disconnect" );

	offset = [];
	offset["sniper"] = 3;
	offset["emp"] = 3;
	offset["rocket"] = -1.5;
	offset["pistol"] = 6;
	offset["commando"] = 6;
	last = -999;
	for( ;; )
	{
		x = 0;
		c = weapon_class( self GetCurrentWeapon() );
		if( IsDefined( offset[c] ) )
		{
			x = offset[c];
		}
		if( x != last && GetDvar( "cw_test" ) != "5" )
		{
			self SetClientDvar( "cg_gun_x", x );
			last = x;
		}
		wait( 0.05 );
	}
}

// ---------------------------------------------------------------- blaster bolts / reticle

// The guns are normal hitscan weapons (so damage, headshots and points behave like any zombie-mode gun);
// this only draws the travelling bolt and its impact.
blaster_watch()
{
	self notify( "cw_blaster_watch" );
	self endon( "cw_blaster_watch" );
	self endon( "disconnect" );

	for( ;; )
	{
		self waittill( "weapon_fired" );
		cls = weapon_class( self GetCurrentWeapon() );
		if( !is_blaster( cls ) )
		{
			continue;
		}
		if( cls == "shotgun" )
		{
			for( i = 0; i < 4; i++ )
			{
				self thread fire_bolt( cls, 4.5 );
			}
		}
		else
		{
			self thread fire_bolt( cls, 0 );
		}
	}
}

fire_bolt( cls, cone )
{
	angles = self GetPlayerAngles();
	if( cone > 0 )
	{
		angles = angles + ( RandomFloatRange( 0 - cone, cone ), RandomFloatRange( 0 - cone, cone ), 0 );
	}
	forward = AnglesToForward( angles );
	right = AnglesToRight( angles );
	up = AnglesToUp( angles );

	eye = self GetEye();
	trace = BulletTrace( eye, eye + vector_scale( forward, 6000 ), true, self );
	end = trace["position"];

	// leave from roughly where the muzzle sits on screen, not from between the eyes
	side = 5;
	drop = 4;
	speed = 4500;
	if( cls == "pistol" || cls == "commando" )
	{
		side = 4;
		drop = 3;
	}
	else if( cls == "sniper" )
	{
		speed = 9000;
	}
	if( self PlayerAds() > 0.5 )
	{
		side = 0;
		drop = 2;
	}
	start = eye + vector_scale( forward, 34 ) + vector_scale( right, side ) - vector_scale( up, drop );
	dist = Distance( start, end );
	if( dist < 48 )
	{
		PlayFx( level._effect["cw_blaster_impact"], end );
		return;
	}

	bolt = Spawn( "script_model", start );
	bolt SetModel( "tag_origin" );
	bolt.angles = VectorToAngles( end - start );
	PlayFxOnTag( level._effect["cw_blaster_bolt"], bolt, "tag_origin" );

	time = dist / speed;
	if( time < 0.05 )
	{
		time = 0.05;
	}
	bolt MoveTo( end, time );
	wait( time );

	PlayFx( level._effect["cw_blaster_impact"], end );
	bolt Delete();
}

// The engine hides the weapon's own crosshair while aiming down sights; SWBF2 has no iron sights (aiming zooms, the
// gun stays in the hip pose, the sniper's zoom hides it), so the Battlefront reticle stays on screen in ADS.
ads_reticle()
{
	self notify( "cw_ads_reticle" );
	self endon( "cw_ads_reticle" );
	self endon( "disconnect" );

	if( !IsDefined( self.cw_reticle_hud ) )
	{
		hud = NewClientHudElem( self );
		hud.alignX = "center";
		hud.alignY = "middle";
		hud.horzAlign = "center";
		hud.vertAlign = "middle";
		hud.x = 0;
		hud.y = 0;
		hud.hidewheninmenu = true;
		hud.alpha = 0;
		hud SetShader( "cw_reticle", 32, 32 );
		self.cw_reticle_hud = hud;
	}

	for( ;; )
	{
		alpha = 0;
		cls = weapon_class( self GetCurrentWeapon() );
		if( IsAlive( self ) && cls != "" )
		{
			// fade in over the last part of the raise, as the stock crosshair fades out
			alpha = ( self PlayerAds() - 0.5 ) * 2;
			if( alpha < 0 )
			{
				alpha = 0;
			}
		}
		self.cw_reticle_hud.alpha = alpha;
		wait( 0.05 );
	}
}

// ---------------------------------------------------------------- grenade slot: thermal detonators + land mines

// Only the ACTIVE type is held as a weapon (so the HUD shows its icon and count); the other count is kept here.
// The stock round award (thermal) and a wall buy (mines) are merged in when they turn up.  The 3 key (launcher
// bind: set cw_nade_cycle 1) switches type; emptying the active type switches to the other if it has any left.
grenade_inventory()
{
	self notify( "cw_grenade_inventory" );
	self endon( "cw_grenade_inventory" );
	self endon( "disconnect" );

	types = level.cw_nade_types;
	self.cw_nades = [];
	self.cw_nade_owned = [];
	for( i = 0; i < types.size; i++ )
	{
		self.cw_nades[types[i]] = 0;
		self.cw_nade_owned[types[i]] = ( types[i] != "cw_mine" );
	}
	self.cw_nade_cur = "stielhandgranate";
	self.cw_nade_cycle = false;
	self thread grenade_cycle_listen();

	last = 0;
	for( ;; )
	{
		wait( 0.05 );
		if( self IsThrowingGrenade() )
		{
			continue;
		}

		// the inactive type turned up as a weapon: the stock round award (thermal) - merge it in
		for( i = 0; i < types.size; i++ )
		{
			t = types[i];
			if( t == self.cw_nade_cur || !self HasWeapon( t ) )
			{
				continue;
			}
			count = self GetWeaponAmmoClip( t );
			self TakeWeapon( t );
			// the game start hands the grenade out empty before the real round award: only count real grenades
			if( count > 0 )
			{
				if( t == "stielhandgranate" )
				{
					self.cw_nades[t] = grenade_award( self.cw_nades[t] );
				}
				else if( count > self.cw_nades[t] )
				{
					self.cw_nades[t] = count;
				}
			}
			if( self HasWeapon( self.cw_nade_cur ) )
			{
				self SwitchToOffhand( self.cw_nade_cur );
			}
		}

		cur = self.cw_nade_cur;
		if( !self HasWeapon( cur ) && self.cw_nades[cur] > 0 )
		{
			self GiveWeapon( cur );
			self SetWeaponAmmoClip( cur, self.cw_nades[cur] );
			self SwitchToOffhand( cur );
		}
		now = self grenade_count( cur );
		if( self.cw_nade_cycle || ( last > 0 && now == 0 ) )
		{
			pressed = self.cw_nade_cycle;
			self.cw_nade_cycle = false;
			next = self grenade_next( cur, pressed );
			if( next != cur )
			{
				self grenade_select( next );
			}
			else if( pressed )
			{
				self thread grenade_label( cur );
			}
		}
		last = self grenade_count( self.cw_nade_cur );
	}
}

grenade_cycle_listen()
{
	self endon( "cw_grenade_inventory" );
	self endon( "disconnect" );

	SetDvar( "cw_nade_cycle", "0" );
	for( ;; )
	{
		wait( 0.05 );
		if( GetDvar( "cw_nade_cycle" ) != "0" )
		{
			SetDvar( "cw_nade_cycle", "0" );
			self.cw_nade_cycle = true;
		}
	}
}

// stock round award: fewer than 1 -> 2, fewer than 2 -> 3, otherwise 4
grenade_award( n )
{
	if( n < 1 )
	{
		return 2;
	}
	if( n < 2 )
	{
		return 3;
	}
	return 4;
}

grenade_count( t )
{
	if( t == self.cw_nade_cur && self HasWeapon( t ) )
	{
		return self GetWeaponAmmoClip( t );
	}
	return self.cw_nades[t];
}

grenade_set( t, n )
{
	if( t == self.cw_nade_cur && self HasWeapon( t ) )
	{
		self SetWeaponAmmoClip( t, n );
	}
	self.cw_nades[t] = n;
}

// the other owned type; on a key press it may be empty (shows its 0 on the HUD), automatic switches need ammo
grenade_next( cur, pressed )
{
	types = level.cw_nade_types;
	for( i = 0; i < types.size; i++ )
	{
		t = types[i];
		if( t == cur || !self.cw_nade_owned[t] )
		{
			continue;
		}
		if( pressed || self.cw_nades[t] > 0 )
		{
			return t;
		}
	}
	return cur;
}

grenade_select( t )
{
	cur = self.cw_nade_cur;
	if( self HasWeapon( cur ) )
	{
		self.cw_nades[cur] = self GetWeaponAmmoClip( cur );
		self TakeWeapon( cur );
	}
	self GiveWeapon( t );
	self SetWeaponAmmoClip( t, self.cw_nades[t] );
	self SwitchToOffhand( t );
	self.cw_nade_cur = t;
	self thread grenade_label( t );
}

grenade_label( t )
{
	self notify( "cw_grenade_label" );
	self endon( "cw_grenade_label" );
	self endon( "disconnect" );

	text = &"CLONEWARS_NADE_THERMAL";
	if( t == "cw_mine" )
	{
		text = &"CLONEWARS_NADE_MINE";
	}
	self hint( true, text );
	wait( 1.5 );
	self hint( false, text );
}

// ---------------------------------------------------------------- land mines

// A thrown mine is a short lob with a long fuse; once it comes to rest it is swapped for a planted mine that
// blows up when a droid walks over it.  (Threads started on a grenade entity do not run: track it from here.)
mine_watch()
{
	self notify( "cw_mine_watch" );
	self endon( "cw_mine_watch" );
	self endon( "disconnect" );

	if( !IsDefined( self.cw_mines ) )
	{
		self.cw_mines = [];
	}
	for( ;; )
	{
		self waittill( "grenade_fire", grenade, weapname );
		if( IsDefined( grenade ) && IsDefined( weapname ) && ToLower( weapname ) == "cw_mine" )
		{
			self thread mine_track( grenade );
		}
	}
}

mine_track( grenade )
{
	self endon( "disconnect" );

	prev = grenade.origin;
	still = 0;
	for( t = 0; t < 80; t++ )
	{
		wait( 0.05 );
		if( !IsDefined( grenade ) )
		{
			return;
		}
		if( DistanceSquared( grenade.origin, prev ) < 0.25 )
		{
			still++;
			if( still >= 3 )
			{
				break;
			}
		}
		else
		{
			still = 0;
		}
		prev = grenade.origin;
	}
	if( !IsDefined( grenade ) )
	{
		return;
	}

	pos = grenade.origin;
	trace = BulletTrace( pos + ( 0, 0, 8 ), pos - ( 0, 0, 48 ), false, grenade );
	if( trace["fraction"] < 1 )
	{
		pos = trace["position"];
	}
	grenade Delete();
	self mine_plant( pos );
}

// self = owner
mine_plant( pos )
{
	mine = Spawn( "script_model", pos );
	mine SetModel( "weapon_cw_mine" );
	mine.angles = ( 0, RandomInt( 360 ), 0 );
	mine.owner = self;

	// oldest planted mine goes when the player is over the limit
	live = [];
	for( i = 0; i < self.cw_mines.size; i++ )
	{
		if( IsDefined( self.cw_mines[i] ) )
		{
			live[live.size] = self.cw_mines[i];
		}
	}
	if( live.size >= level.cw_mines_placed_max )
	{
		live[0] notify( "cw_mine_remove" );
		live[0] Delete();
		rest = [];
		for( i = 1; i < live.size; i++ )
		{
			rest[rest.size] = live[i];
		}
		live = rest;
	}
	live[live.size] = mine;
	self.cw_mines = live;

	level thread mine_arm( mine );
}

mine_arm( mine )
{
	// (no endon "death": deleting the mine below would end this thread before the blast)
	mine endon( "cw_mine_remove" );

	wait( 1 );
	PlaySoundAtPosition( "weap_raise", mine.origin );
	// proximity: any droid (or hellhound) within 64 units across and 60 up / down
	for( ;; )
	{
		wait( 0.1 );
		near = false;
		ai = GetAiArray( "axis" );
		for( i = 0; i < ai.size; i++ )
		{
			dz = ai[i].origin[2] - mine.origin[2];
			if( dz < 60 && dz > -60 && Distance2D( ai[i].origin, mine.origin ) < 64 )
			{
				near = true;
				break;
			}
		}
		if( near )
		{
			break;
		}
	}

	origin = mine.origin + ( 0, 0, 6 );
	owner = mine.owner;
	mine Delete();

	PlayFx( level._effect["cw_mine_explode"], origin );
	PlaySoundAtPosition( "rpg_impact_boom", origin );
	Earthquake( 0.5, 0.5, origin, 400 );

	// droids only (Battlefront mines do not hurt their owner's side); credit the kills to the owner
	hit = 0;
	ai = GetAiArray( "axis" );
	for( i = 0; i < ai.size; i++ )
	{
		if( !IsDefined( ai[i] ) || !IsAlive( ai[i] ) )
		{
			continue;
		}
		dz = ai[i].origin[2] - origin[2];
		d = Distance( ai[i].origin, origin );
		if( d > 200 || dz > 80 || dz < -80 )
		{
			continue;
		}
		dmg = int( 2000 - d * 8 );
		hit++;
		if( IsDefined( owner ) )
		{
			ai[i] DoDamage( dmg, origin, owner );
		}
		else
		{
			ai[i] DoDamage( dmg, origin );
		}
	}
	if( GetDvar( "cw_test" ) != "" && GetDvar( "cw_test" ) != "0" )
	{
		SetDvar( "cw_dbg", "boom at " + origin + " hit " + hit );
	}
}

// ---------------------------------------------------------------- helpers

get_players()
{
	return GetPlayers();
}

vector_scale( vec, scale )
{
	return ( vec[0] * scale, vec[1] * scale, vec[2] * scale );
}

// ---------------------------------------------------------------- developer test modes (+set cw_test <n>)

test_timeline()
{
	self endon( "disconnect" );
	wait( 3 );
	self EnableInvulnerability();
	mode = GetDvar( "cw_test" );

	if( mode == "1" )
	{
		// every SWBF2 gun in hand for cw_ty seconds (default 5), in the order the harness expects
		level thread test_kill_all();
		secs = GetDvarFloat( "cw_ty" );
		if( secs <= 0 )
		{
			secs = 5;
		}
		// stock names the map loads (their weapon files are the SWBF2 overrides)
		list = StrTok( "cw_dc15,zombie_colt,sw_357,doublebarrel,bar,ptrs41_zombie,panzerschrek,m2_flamethrower_zombie", "," );
		if( GetDvar( "cw_test_only" ) != "" )
		{
			list = StrTok( GetDvar( "cw_test_only" ), "," );
		}
		for( i = 0; i < list.size; i++ )
		{
			w = self GetCurrentWeapon();
			if( w != "none" && w != list[i] )
			{
				self TakeWeapon( w );
			}
			self GiveWeapon( list[i] );
			self GiveMaxAmmo( list[i] );
			self SwitchToWeapon( list[i] );
			// level view down the longest free line (the start room's bars stopped projectiles at once)
			best = 0;
			yaw = 0;
			for( a = 0; a < 360; a += 15 )
			{
				tr = BulletTrace( self GetEye(), self GetEye() + vector_scale( AnglesToForward( ( 0, a, 0 ) ), 2000 ), false, self );
				if( tr["fraction"] > best )
				{
					best = tr["fraction"];
					yaw = a;
				}
			}
			self SetPlayerAngles( ( 0, yaw, 0 ) );
			SetDvar( "cw_dbg", "weapon " + list[i] );
			SetDvar( "cw_dbg", "weapon " + list[i] );
			wait( secs );
		}
	}
	else if( mode == "6" )
	{
		// mine trigger: a ring of mines round the player (god mode); the droids that come for him walk into them
		wait( 2 );
		for( n = 0; n < 8; n++ )
		{
			pos = self.origin + vector_scale( AnglesToForward( ( 0, n * 45, 0 ) ), 50 );
			tr = BulletTrace( pos + ( 0, 0, 30 ), pos - ( 0, 0, 60 ), false, self );
			self mine_plant( tr["position"] );
		}
		self SetPlayerAngles( ( 35, 0, 0 ) );
		SetDvar( "cw_dbg", "planted ring" );
		SetDvar( "cw_dbg", "planted ring" );
		for( ;; )
		{
			wait( 1 );
			best = 99999;
			live = 0;
			ai = GetAiArray( "axis" );
			for( m = 0; m < self.cw_mines.size; m++ )
			{
				if( !IsDefined( self.cw_mines[m] ) )
				{
					continue;
				}
				live++;
				for( i = 0; i < ai.size; i++ )
				{
					d = Distance2D( ai[i].origin, self.cw_mines[m].origin );
					if( d < best )
					{
						best = d;
					}
				}
			}
			SetDvar( "cw_dbg", "mines " + live + " ai " + ai.size + " closest " + int( best ) );
		}
	}
	else if( mode == "7" )
	{
		level thread test_kill_all();
		self maps\_zombiemode_score::add_to_player_score( 100 );
		gun = "zombie_thompson";
		if( level.script == "nazi_zombie_prototype" )
		{
			gun = "thompson";
		}
		self GiveWeapon( gun );
		self GiveMaxAmmo( gun );
		self SwitchToWeapon( gun );
		level notify( "Pack_A_Punch_on" );
		wait( 1.5 );
		trigs = GetEntArray( "zombie_vending_upgrade", "targetname" );
		if( trigs.size == 0 )
		{
			while( !IsDefined( level.cw_pap_machine ) )
			{
				wait( 0.1 );
			}
			m = level.cw_pap_machine;
			front = AnglesToRight( m.angles );
			self SetOrigin( m.origin + vector_scale( front, 70 ) );
			self SetPlayerAngles( VectorToAngles( ( m.origin + ( 0, 0, 40 ) ) - ( self.origin + ( 0, 0, 60 ) ) ) );
			for( ;; )
			{
				wait( 1 );
				SetDvar( "cw_dbg", "pap score " + self.score + " weapon " + self GetCurrentWeapon() );
			}
		}
		t = trigs[0];
		spot = t.origin + ( 0, 0, 10000 );
		best = 0;
		yaw = 0;
		for( a = 0; a < 360; a += 30 )
		{
			tr = BulletTrace( spot, spot + vector_scale( AnglesToForward( ( 0, a, 0 ) ), 200 ), false, self );
			if( tr["fraction"] > best )
			{
				best = tr["fraction"];
				yaw = a;
			}
		}
		fwd = AnglesToForward( ( 0, yaw, 0 ) );
		ground = BulletTrace( spot + vector_scale( fwd, 55 ), spot + vector_scale( fwd, 55 ) - ( 0, 0, 200 ), false, self );
		self SetOrigin( ground["position"] );
		self SetPlayerAngles( ( 10, yaw + 180, 0 ) );
		for( ;; )
		{
			wait( 1 );
			SetDvar( "cw_dbg", "pap score " + self.score + " weapon " + self GetCurrentWeapon() );
		}
	}
	else if( mode == "10" )
	{
		// static droid in front of the player with the stock eye glow on J_Eyeball_LE (as _zombiemode_spawner does)
		level thread test_kill_all();
		models = StrTok( "cw_bdroid,cw_bdroid_assault,cw_sbdroid", "," );
		fwd = AnglesToForward( ( 0, self.angles[1], 0 ) );
		for( i = 0; i < models.size; i++ )
		{
			right = AnglesToRight( ( 0, self.angles[1], 0 ) );
			pos = self.origin + vector_scale( fwd, 120 ) + vector_scale( right, ( i - 1 ) * 40 );
			d = Spawn( "script_model", pos );
			d SetModel( models[i] );
			d.angles = ( 0, self.angles[1], 0 );
			wait( 0.1 );
			e = Spawn( "script_model", d GetTagOrigin( "J_Eyeball_LE" ) );
			e.angles = d GetTagAngles( "J_Eyeball_LE" );
			e SetModel( "tag_origin" );
			e LinkTo( d, "J_Eyeball_LE" );
			wait( 0.1 );
			if( GetDvar( "cw_test_only" ) != "free" )
			{
				PlayFxOnTag( level._effect["eye_glow"], e, "tag_origin" );
			}
			f = Spawn( "script_model", d GetTagOrigin( "J_Eyeball_LE" ) );
			f SetModel( "tag_origin" );
			wait( 0.1 );
			if( GetDvar( "cw_test_only" ) == "free" )
			{
				PlayFxOnTag( level._effect["eye_glow"], f, "tag_origin" );
			}
			SetDvar( "cw_dbg", "eye " + models[i] + " tag " + ( d GetTagOrigin( "J_Eyeball_LE" ) - d.origin ) + " head " + ( d GetTagOrigin( "J_Head" ) - d.origin ) );
		}
		self SetPlayerAngles( ( -2, self.angles[1], 0 ) );
		self SetClientDvar( "cg_fov", GetDvar( "cw_fov" ) );
	}
	else if( mode == "9" )
	{
		level thread test_kill_all();
		while( !IsDefined( level.cw_walls_ready ) )
		{
			wait( 0.1 );
		}
		keys = GetArrayKeys( level.zombie_weapons );
		for( i = 0; i < keys.size; i++ )
		{
			if( weapon_class( keys[i] ) == "rifle" && !IsSubStr( keys[i], "_upgraded" ) )
			{
				self GiveWeapon( keys[i] );		// hold a Blaster Rifle: the box must not offer another
				break;
			}
		}
		wait( 0.5 );
		n = [];
		for( i = 0; i < 600; i++ )
		{
			c = weapon_class( box_pick( self ) );
			if( !IsDefined( n[c] ) )
			{
				n[c] = 0;
			}
			n[c]++;
		}
		keys = GetArrayKeys( n );
		msg = "";
		for( i = 0; i < keys.size; i++ )
		{
			msg = msg + keys[i] + "=" + n[keys[i]] + " ";
		}
		SetDvar( "cw_dbg", "boxodds " + msg );
		SetDvar( "cw_dbg", "boxodds " + msg );
		SetDvar( "cw_dbg", "done" );
		SetDvar( "cw_dbg", "done" );
	}
	else if( mode == "8" )
	{
		// mystery box pool: every weapon the box can hand out on this map, given one after another
		level thread test_kill_all();
		while( !IsDefined( level.cw_walls_ready ) )
		{
			wait( 0.1 );
		}
		keys = GetArrayKeys( level.zombie_weapons );
		list = "";
		for( i = 0; i < keys.size; i++ )
		{
			if( keys[i] == "mine_bouncing_betty" )
			{
				continue;		// the box skips it itself
			}
			list = list + keys[i] + "=" + weapon_class( keys[i] ) + " ";
		}
		SetDvar( "cw_dbg", "pool " + keys.size + " " + list );
		SetDvar( "cw_dbg", "pool " + keys.size + " " + list );
		secs = GetDvarFloat( "cw_ty" );
		if( secs <= 0 )
		{
			secs = 1.5;
		}
		for( i = 0; i < keys.size; i++ )
		{
			if( keys[i] == "mine_bouncing_betty" )
			{
				continue;
			}
			w = self GetCurrentWeapon();
			if( w != "none" && w != keys[i] && w != "zombie_colt" )
			{
				self TakeWeapon( w );
			}
			self GiveWeapon( keys[i] );
			self GiveMaxAmmo( keys[i] );
			self SwitchToWeapon( keys[i] );
			wait( secs );
			SetDvar( "cw_dbg", "gave " + keys[i] + " holding " + self GetCurrentWeapon() + " ammo " + self GetWeaponAmmoStock( keys[i] ) );
		}
		SetDvar( "cw_dbg", "done" );
		SetDvar( "cw_dbg", "done" );
	}
	else if( mode == "5" )
	{
		// placement sweep: each weapon (cw_test_only) at each cg_gun offset (cw_offs "x_y_z|x_y_z|..."), the harness
		// takes a screenshot on every "cw_dbg shot <weapon> <k>" line of console.log
		level thread test_kill_all();
		list = StrTok( GetDvar( "cw_test_only" ), "," );
		offs = StrTok( GetDvar( "cw_offs" ), "|" );
		for( i = 0; i < list.size; i++ )
		{
			w = self GetCurrentWeapon();
			if( w != "none" && w != list[i] )
			{
				self TakeWeapon( w );
			}
			self GiveWeapon( list[i] );
			self GiveMaxAmmo( list[i] );
			self SwitchToWeapon( list[i] );
			wait( 2.5 );
			for( k = 0; k < offs.size; k++ )
			{
				o = StrTok( offs[k], "_" );
				self SetClientDvar( "cg_gun_x", o[0] );
				self SetClientDvar( "cg_gun_y", o[1] );
				self SetClientDvar( "cg_gun_z", o[2] );
				wait( 0.4 );
				SetDvar( "cw_dbg", "shot " + list[i] + " " + k );
				SetDvar( "cw_dbg", "shot " + list[i] + " " + k );
				wait( 1.4 );
			}
			self SetClientDvar( "cg_gun_x", "0" );
			self SetClientDvar( "cg_gun_y", "0" );
			self SetClientDvar( "cg_gun_z", "0" );
		}
		SetDvar( "cw_dbg", "done" );
		SetDvar( "cw_dbg", "done" );
	}
	else if( mode == "2" )
	{
		// look at the nearest droid's head through a narrow field of view
		self SetClientDvar( "cg_fov", GetDvar( "cw_fov" ) );
		for( ;; )
		{
			wait( 0.05 );
			ai = GetAiArray( "axis" );
			best = undefined;
			bd = 100000;
			for( i = 0; i < ai.size; i++ )
			{
				d = Distance( ai[i].origin, self.origin );
				if( d < bd && d > 60 )
				{
					bd = d;
					best = ai[i];
				}
			}
			if( IsDefined( best ) )
			{
				self SetPlayerAngles( VectorToAngles( best GetTagOrigin( "j_head" ) - self GetEye() ) );
			}
		}
	}
	else if( mode == "3" )
	{
		// mines: owned + 4, active; the harness throws with G and switches with 3
		level thread test_kill_far();
		wait( 2 );
		self.cw_nade_owned["cw_mine"] = true;
		self grenade_set( "cw_mine", 4 );
		self grenade_select( "cw_mine" );
		for( ;; )
		{
			wait( 1 );
			msg = "cur " + self.cw_nade_cur + " thermal " + self grenade_count( "stielhandgranate" ) + " mine " + self grenade_count( "cw_mine" ) + " placed " + self.cw_mines.size;
			SetDvar( "cw_dbg", msg );
		}
	}
	else if( mode == "4" )
	{
		// mine wall: stand in front of the grenade wall with points; the harness presses F
		level thread test_kill_all();
		self maps\_zombiemode_score::add_to_player_score( 5000 );
		trigs = GetEntArray( "weapon_upgrade", "targetname" );
		if( GetDvar( "cw_test_only" ) == "box" )
		{
			trigs = GetEntArray( "treasure_chest_use", "targetname" );
			for( i = 0; i < trigs.size; i++ )
			{
				trigs[i].zombie_weapon_upgrade = "box";
			}
		}
		for( i = 0; i < trigs.size; i++ )
		{
			want = GetDvar( "cw_test_only" );
			if( ( want == "" && trigs[i].origin[2] < -5000 ) || ( want != "" && trigs[i].zombie_weapon_upgrade == want ) )
			{
				spot = trigs[i].origin;
				if( spot[2] < -5000 )
				{
					spot = spot + ( 0, 0, 10000 );
				}
				// stand on the open side of the wall (the longest free trace), facing it
				best = 0;
				yaw = 0;
				for( a = 0; a < 360; a += 45 )
				{
					tr = BulletTrace( spot, spot + vector_scale( AnglesToForward( ( 0, a, 0 ) ), 200 ), false, self );
					if( tr["fraction"] > best )
					{
						best = tr["fraction"];
						yaw = a;
					}
				}
				fwd = AnglesToForward( ( 0, yaw, 0 ) );
				ground = BulletTrace( spot + vector_scale( fwd, 45 ), spot + vector_scale( fwd, 45 ) - ( 0, 0, 200 ), false, self );
				self SetOrigin( ground["position"] );
				self SetPlayerAngles( ( 15, yaw + 180, 0 ) );
				SetDvar( "cw_dbg", "at mine wall yaw " + yaw );
			}
		}
		for( ;; )
		{
			wait( 1 );
			prim = self GetWeaponsListPrimaries();
			plist = "";
			for( q = 0; q < prim.size; q++ )
			{
				plist = plist + prim[q] + " ";
			}
			SetDvar( "cw_dbg", "score " + self.score + " cur " + self.cw_nade_cur + " mine " + self grenade_count( "cw_mine" ) + " guns " + plist );
		}
	}
}

test_kill_all()
{
	for( ;; )
	{
		ai = GetAiArray( "axis" );
		for( i = 0; i < ai.size; i++ )
		{
			ai[i] DoDamage( ai[i].health + 666, ai[i].origin );
		}
		wait( 0.25 );
	}
}

// keep droids coming but kill the ones that get close to the player (mine test: they must walk over the mines)
test_kill_far()
{
	for( ;; )
	{
		wait( 0.25 );
		players = GetPlayers();
		ai = GetAiArray( "axis" );
		for( i = 0; i < ai.size; i++ )
		{
			if( Distance( ai[i].origin, players[0].origin ) < 40 )
			{
				ai[i] DoDamage( ai[i].health + 666, ai[i].origin );
			}
		}
	}
}
