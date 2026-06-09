
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import hashlib, random, heapq, json
from pathlib import Path

COLS = "ABCDEFGH"

def rng(seed: str) -> random.Random:
    h = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return random.Random(int(h[:16], 16))

def d(seed: str, sides: int) -> int:
    return rng(seed).randint(1, sides)

def roll_expr(seed: str, expr: str):
    expr = expr.replace(" ", "")
    bonus = 0
    dice = expr
    if "+" in expr:
        dice, b = expr.split("+", 1)
        bonus = int(b)
    elif "-" in expr[1:]:
        dice, b = expr.split("-", 1)
        bonus = -int(b)
    n, s = dice.lower().split("d")
    rolls = [d(f"{seed}:{i}", int(s)) for i in range(int(n))]
    return sum(rolls) + bonus, rolls, bonus

def cell_to_xy(c: str):
    return COLS.index(c[0]) + 1, int(c[1:])

def xy_to_cell(x: int, y: int):
    return f"{COLS[x-1]}{y}"

def cheb(a: str, b: str):
    ax, ay = cell_to_xy(a); bx, by = cell_to_xy(b)
    return max(abs(ax-bx), abs(ay-by))

def adjacent(a: str, b: str):
    return cheb(a,b) == 1

@dataclass
class Cell:
    id: str
    walkable: bool = True
    cover: str = "none"
    terrain: str = "stone"
    hazard: Optional[str] = None
    height: int = 0

@dataclass
class Actor:
    id: str
    name: str
    team: str
    cls: str
    hp: int
    max_hp: int
    ac: int
    pos: str
    stats: Dict[str, int]
    prof: int = 2
    statuses: List[str] = field(default_factory=list)
    resources: Dict[str, Any] = field(default_factory=dict)
    policy: str = ""

    def mod(self, stat: str):
        return (self.stats[stat] - 10) // 2

    @property
    def alive(self):
        return self.hp > 0 and "dead" not in self.statuses and "downed" not in self.statuses

    @property
    def targetable(self):
        return "dead" not in self.statuses

class BattleV04:
    def __init__(self, seed="enc_005_v04_reactions"):
        self.seed = seed
        self.round = 1
        self.activation = 0
        self.log = []
        self.intent_log = []
        self.gm_log = []
        self.cells = {xy_to_cell(x,y): Cell(xy_to_cell(x,y)) for x in range(1,9) for y in range(1,9)}
        self.cells["D4"] = Cell("D4", False, "full", "fallen_obelisk", None, 1)
        self.cells["B5"] = Cell("B5", True, "half", "broken_wall", None, 0)
        self.cells["E4"] = Cell("E4", True, "half", "low_wall", None, 0)
        self.cells["C5"] = Cell("C5", True, "none", "rune_circle", "unstable_rune", 0)
        self.cells["F3"] = Cell("F3", True, "none", "cracked_floor", "collapse_risk", 0)
        self.cells["G4"] = Cell("G4", True, "none", "oil_slick", "oil", 0)
        self.cells["F6"] = Cell("F6", True, "half", "high_step", None, 1)
        self.cells["G6"] = Cell("G6", True, "half", "high_step", None, 1)
        self.actors = {}
        self.setup()
        self.initiative = self.roll_initiative()

    def setup(self):
        self.actors["EZ"] = Actor("EZ","EZ","heroes","Warlock",32,32,15,"B2",{"str":10,"dex":14,"con":14,"int":10,"wis":10,"cha":18},resources={"spell1":2,"concentration":None},policy="control_survive")
        self.actors["EL"] = Actor("EL","ElMasnif","heroes","Paladin",45,45,18,"C2",{"str":18,"dex":10,"con":16,"int":8,"wis":10,"cha":14},resources={"spell1":3,"lay":20,"protection_reaction":1},policy="protect_intercept")
        self.actors["HE"] = Actor("HE","Hesh","heroes","Rogue",31,31,16,"B1",{"str":8,"dex":18,"con":14,"int":12,"wis":14,"cha":10},statuses=["hidden"],resources={"cunning_action":1},policy="assassin_backline")
        self.actors["WG"] = Actor("WG","Warglaive Hunter","enemies","Hunter",34,34,16,"F5",{"str":12,"dex":18,"con":14,"int":10,"wis":12,"cha":10},policy="dive_backline")
        self.actors["SG"] = Actor("SG","Stoneguard","enemies","Guard",44,44,17,"E6",{"str":18,"dex":10,"con":16,"int":8,"wis":10,"cha":8},policy="hold_front")
        self.actors["RS"] = Actor("RS","Rune Speaker","enemies","Caster",28,28,13,"E7",{"str":8,"dex":12,"con":12,"int":14,"wis":16,"cha":10},resources={"spell1":3},policy="heal_control")
        self.actors["XB"] = Actor("XB","Crossbow Stalker","enemies","Archer",28,28,15,"G6",{"str":10,"dex":18,"con":12,"int":10,"wis":12,"cha":8},policy="focus_caster")

    def roll_initiative(self):
        rolls=[]
        for aid,a in self.actors.items():
            r=d(f"{self.seed}:initiative:{aid}",20)
            rolls.append({"actor":aid,"d20":r,"dex_mod":a.mod("dex"),"total":r+a.mod("dex")})
        rolls.sort(key=lambda x:(x["total"],x["d20"],x["actor"]), reverse=True)
        self.initiative_rolls=rolls
        return [r["actor"] for r in rolls]

    def living(self,team):
        return [a for a in self.actors.values() if a.team==team and a.alive]

    def targetable(self,team):
        return [a for a in self.actors.values() if a.team==team and a.targetable]

    def enemies_of(self,a):
        return [x for x in self.actors.values() if x.team!=a.team and x.alive]

    def allies_of(self,a):
        return [x for x in self.actors.values() if x.team==a.team and x.id!=a.id and x.alive]

    def occ(self):
        return {a.pos:a.id for a in self.actors.values() if a.alive}

    def is_walkable(self,cell,actor_id=None):
        if cell not in self.cells or not self.cells[cell].walkable:
            return False
        o=self.occ()
        return cell not in o or o[cell]==actor_id

    def cheb(self, a, b):
        return cheb(a, b)

    def adjacent(self, a, b):
        return adjacent(a, b)

    def neighbors(self,cell):
        x,y=cell_to_xy(cell)
        out=[]
        for dx in [-1,0,1]:
            for dy in [-1,0,1]:
                if dx==0 and dy==0: continue
                nx,ny=x+dx,y+dy
                if 1<=nx<=8 and 1<=ny<=8:
                    out.append(xy_to_cell(nx,ny))
        return out

    def path_to(self,start,goal,actor_id,max_cost=6):
        if start==goal: return [start]
        pq=[(0,start,[start])]
        seen=set()
        while pq:
            cost,cell,path=heapq.heappop(pq)
            if (cell,cost) in seen: continue
            seen.add((cell,cost))
            if cost>=max_cost: continue
            for nb in self.neighbors(cell):
                if not self.cells[nb].walkable: continue
                if not self.is_walkable(nb,actor_id) and nb!=goal: continue
                np=path+[nb]
                if nb==goal: return np
                heapq.heappush(pq,(cost+1,nb,np))
        return None

    def best_adjacent(self,a,t):
        cells=[c for c in self.neighbors(t.pos) if self.is_walkable(c,a.id)]
        cells.sort(key=lambda c:(self.cheb(a.pos,c),c))
        for c in cells:
            if self.path_to(a.pos,c,a.id):
                return c
        return None

    def safest_retreat_cell(self,a,from_enemy=None):
        candidates=[c for c in self.neighbors(a.pos) if self.is_walkable(c,a.id)]
        enemies=self.enemies_of(a)
        def score(c):
            dist=sum(self.cheb(c,e.pos) for e in enemies)
            cover=1 if self.cells[c].cover=="half" else 0
            hazard=-5 if self.cells[c].hazard else 0
            return dist+cover*2+hazard
        candidates.sort(key=score, reverse=True)
        for c in candidates:
            if self.path_to(a.pos,c,a.id,3):
                return c
        return None

    def line_cells(self,a,b):
        x1,y1=cell_to_xy(a); x2,y2=cell_to_xy(b)
        steps=max(abs(x2-x1),abs(y2-y1))
        if steps==0: return [a]
        out=[]
        for i in range(steps+1):
            x=round(x1+(x2-x1)*i/steps)
            y=round(y1+(y2-y1)*i/steps)
            c=xy_to_cell(x,y)
            if not out or out[-1]!=c:
                out.append(c)
        return out

    def los(self,a,b):
        blockers=[]
        for c in self.line_cells(a,b)[1:-1]:
            if not self.cells[c].walkable or self.cells[c].cover=="full":
                blockers.append(c)
        return len(blockers)==0,blockers

    def can_target(self,a,t,range_cells):
        ok,_=self.los(a.pos,t.pos)
        return ok and self.cheb(a.pos,t.pos)<=range_cells

    def cover_bonus(self,t,melee):
        if melee: return 0
        return {"none":0,"half":2,"full":999}.get(self.cells[t.pos].cover,0)

    def add_status(self,a,s):
        if s not in a.statuses:
            a.statuses.append(s)

    def remove_status(self,a,s):
        if s in a.statuses:
            a.statuses.remove(s)

    def clear_hexes(self):
        for a in self.actors.values():
            a.statuses=[s for s in a.statuses if not s.startswith("hex:")]

    def reset_turn(self,a):
        a.resources["action"]=1
        a.resources["bonus_action"]=1
        a.resources["reaction"]=1
        a.resources["movement"]=6
        if a.id=="EL":
            a.resources["protection_reaction"]=1
        if a.id=="HE":
            a.resources["cunning_action"]=1

    def spend(self,a,cost):
        for k,v in cost.items():
            if a.resources.get(k,0)<v:
                return False
        for k,v in cost.items():
            a.resources[k]-=v
        return True

    def move(self,a,dest,max_override=None):
        start=a.pos
        max_cost=max_override if max_override is not None else a.resources.get("movement",6)
        path=self.path_to(start,dest,a.id,max_cost)
        if not path:
            return {"valid":False,"start":start,"end":start,"path":[start],"cost":0}
        cost=len(path)-1
        a.pos=dest
        if max_override is None:
            a.resources["movement"]-=cost
        ev={"valid":True,"start":start,"end":dest,"path":path,"cost":cost}
        hazards=[]
        for cell in path[1:]:
            hz=self.cells[cell].hazard
            if hz in ["unstable_rune","collapse_risk"]:
                dc=13 if hz=="unstable_rune" else 12
                r=d(f"{self.seed}:haz:{self.activation}:{a.id}:{cell}",20)
                total=r+a.mod("dex")
                if total<dc:
                    expr="1d6" if hz=="unstable_rune" else "1d4"
                    amount,rolls,fixed=roll_expr(f"{self.seed}:hazdmg:{self.activation}:{a.id}:{cell}",expr)
                    before=a.hp
                    a.hp=max(0,a.hp-amount)
                    hazards.append({"event":"hazard","cell":cell,"hazard":hz,"save":{"d20":r,"total":total,"dc":dc,"result":"fail"},"damage":{"amount":amount,"rolls":rolls,"hp_before":before,"hp_after":a.hp}})
                    self.check_down(a)
                else:
                    hazards.append({"event":"hazard","cell":cell,"hazard":hz,"save":{"d20":r,"total":total,"dc":dc,"result":"success"}})
        if hazards: ev["hazards"]=hazards
        return ev

    def check_down(self,a):
        if a.hp<=0 and "dead" not in a.statuses:
            a.hp=0
            if a.team=="heroes":
                self.add_status(a,"downed")
            else:
                self.add_status(a,"dead")

    def protection_reaction(self,target,attacker,ev):
        pal=self.actors["EL"]
        if not pal.alive or target.team!="heroes" or target.id=="EL":
            return 0
        if pal.resources.get("protection_reaction",0)<=0:
            return 0
        if self.cheb(pal.pos,target.pos)>2:
            return 0
        # Paladin reaction: reduce incoming damage by 1d8+CHA and optionally step adjacent to ally if possible.
        pal.resources["protection_reaction"]-=1
        red,rolls,fixed=roll_expr(f"{self.seed}:protect:{self.activation}:{target.id}","1d8+2")
        ev["events"].append({"event":"protection_reaction","actor":"EL","target":target.id,"attacker":attacker.id,"reduction":red,"rolls":rolls})
        return red

    def attack(self,a,target,ability,stat,dmg_exprs,melee=False,adv=False,extra=None):
        if not self.spend(a,{"action":1}):
            return {"ability":ability,"target":target.id,"error":"no_action"}
        seed=f"{self.seed}:R{self.round}:A{self.activation}:{a.id}:{ability}:{target.id}"
        if adv:
            r1=d(seed+":a",20); r2=d(seed+":b",20); r=max(r1,r2)
            roll={"advantage":[r1,r2],"selected":r}
        else:
            r=d(seed+":d20",20)
            roll={"d20":r}
        bonus=a.mod(stat)+a.prof
        ac=target.ac+self.cover_bonus(target,melee)
        total=r+bonus
        hit=r==20 or (r!=1 and total>=ac)
        hp_before=target.hp
        parts=[]; total_dmg=0
        if hit:
            for expr,dtype in dmg_exprs+(extra or []):
                amount,rolls,fixed=roll_expr(seed+":"+dtype+":"+expr,expr)
                parts.append({"expr":expr,"rolls":rolls,"fixed":fixed,"type":dtype,"amount":amount})
                total_dmg+=amount
            # reaction reduces after roll, before hp.
            dummy_ev={"events":[]}
            reduction=self.protection_reaction(target,a,dummy_ev)
            if reduction:
                parts.append({"type":"protection_reduction","amount":-min(total_dmg,reduction)})
                total_dmg=max(0,total_dmg-reduction)
            target.hp=max(0,target.hp-total_dmg)
            if hp_before>target.max_hp/2 and target.hp<=target.max_hp/2 and target.hp>0:
                self.add_status(target,"bloodied")
            self.check_down(target)
            action={"ability":ability,"target":target.id,"roll":{**roll,"bonus":bonus,"total":total,"vs_ac":ac,"result":"hit"},"damage":{"parts":parts,"total":total_dmg,"hp_before":hp_before,"hp_after":target.hp}}
            if reduction:
                action["reaction_events"]=dummy_ev["events"]
            return action
        return {"ability":ability,"target":target.id,"roll":{**roll,"bonus":bonus,"total":total,"vs_ac":ac,"result":"miss"},"damage":{"parts":parts,"total":0,"hp_before":hp_before,"hp_after":target.hp}}

    def heal_action(self,a,target,amount,source,pool=None):
        if not self.spend(a,{"action":1}):
            return {"ability":source,"target":target.id,"error":"no_action"}
        if pool:
            a.resources[pool]=max(0,a.resources.get(pool,0)-amount)
        before=target.hp
        target.hp=min(target.max_hp,target.hp+amount)
        if "downed" in target.statuses and target.hp>0:
            self.remove_status(target,"downed")
            revived=True
        else:
            revived=False
        if target.hp>target.max_hp/2:
            self.remove_status(target,"bloodied")
        return {"ability":source,"target":target.id,"healing":{"amount":amount,"hp_before":before,"hp_after":target.hp,"revived":revived}}

    def nearest(self,a):
        return min(self.enemies_of(a), key=lambda e:(self.cheb(a.pos,e.pos),e.hp))

    def choose_ranged_target(self,a,preferred,range_cells):
        for tid in preferred:
            if tid in self.actors:
                t=self.actors[tid]
                if t.alive and self.can_target(a,t,range_cells):
                    return t
        cand=[e for e in self.enemies_of(a) if self.can_target(a,e,range_cells)]
        return min(cand,key=lambda e:(e.hp,e.ac)) if cand else None

    def intent(self,aid):
        a=self.actors[aid]
        if aid=="HE":
            if a.hp<=12:
                return {"intent":"disengage_hide_survive","target":"self","reason":"Hesh low HP, keeps rogue alive."}
            for tid in ["XB","RS","WG","SG"]:
                if self.actors[tid].alive:
                    return {"intent":"assassinate_priority","target":tid,"reason":"Rogue hunts ranged/caster/wounded targets."}
        if aid=="EZ":
            melee=any(self.adjacent(a.pos,e.pos) for e in self.enemies_of(a))
            if a.hp<=14 or melee:
                return {"intent":"retreat_control","target":"WG" if self.actors["WG"].alive else "SG","reason":"Survival rule: EZ avoids previous death loop."}
            for tid in ["SG","WG","RS","XB"]:
                if self.actors[tid].alive:
                    return {"intent":"hex_blast","target":tid,"reason":"Control and focus damage."}
        if aid=="EL":
            downed=[x for x in self.actors.values() if x.team=="heroes" and "downed" in x.statuses]
            if downed and self.actors["EL"].resources.get("lay",0)>0:
                return {"intent":"revive_ally","target":downed[0].id,"reason":"Paladin revives a downed ally."}
            if a.hp<=15 and a.resources.get("lay",0)>0:
                return {"intent":"self_heal","target":"EL","reason":"Below 35% HP."}
            # protect EZ by intercepting nearest threat
            ez=self.actors["EZ"]
            if ez.targetable:
                threats=sorted(self.enemies_of(a), key=lambda e:self.cheb(e.pos,ez.pos))
                if threats:
                    return {"intent":"intercept_EZ_threat","target":threats[0].id,"reason":"Paladin protects caster."}
            return {"intent":"frontline_attack","target":self.nearest(a).id,"reason":"Hold frontline."}
        if aid=="WG":
            if self.actors["EZ"].alive:
                return {"intent":"dive_EZ","target":"EZ","reason":"Hunter dives controller."}
            if self.actors["HE"].alive:
                return {"intent":"duel_Hesh","target":"HE","reason":"Pressure rogue."}
            return {"intent":"attack_lowest","target":min(self.living("heroes"),key=lambda x:x.hp).id,"reason":"Finish low HP."}
        if aid=="SG":
            if self.actors["EL"].alive:
                return {"intent":"lock_paladin","target":"EL","reason":"Guard pins frontline."}
            return {"intent":"attack_nearest","target":self.nearest(a).id,"reason":"Nearest living target."}
        if aid=="RS":
            wounded=[e for e in self.living("enemies") if e.hp<e.max_hp*0.55]
            if wounded and a.resources.get("spell1",0)>0:
                return {"intent":"heal_wounded_enemy","target":min(wounded,key=lambda x:x.hp/x.max_hp).id,"reason":"Preserve formation."}
            return {"intent":"ruin_bolt_paladin","target":"EL" if self.actors["EL"].alive else min(self.living("heroes"),key=lambda x:x.hp).id,"reason":"Pressure heroes."}
        if aid=="XB":
            for tid in ["EZ","HE","EL"]:
                if self.actors[tid].alive:
                    return {"intent":"focus_priority","target":tid,"reason":"Archer focuses fragile high-value target."}
            return {"intent":"none","target":"none","reason":"No target."}

    def resolve(self,aid):
        a=self.actors[aid]
        self.activation+=1
        if not a.alive:
            if "downed" in a.statuses:
                ev={"activation":self.activation,"round":self.round,"actor":aid,"start":a.pos,"intent":{"intent":"death_save","target":"self","reason":"Actor is downed."},"events":[]}
                r=d(f"{self.seed}:deathsave:{self.activation}:{aid}",20)
                if r>=10:
                    self.add_status(a,"death_save_success")
                    ev["action"]={"ability":"death_save","roll":r,"result":"success"}
                else:
                    self.add_status(a,"death_save_fail")
                    ev["action"]={"ability":"death_save","roll":r,"result":"fail"}
                if a.statuses.count("death_save_fail")>=3:
                    self.add_status(a,"dead")
                    self.remove_status(a,"downed")
                    ev["events"].append({"event":"unit_dead_after_death_saves","actor":aid,"cell":a.pos})
                self.log.append(ev)
            return

        self.reset_turn(a)
        intent=self.intent(aid)
        self.intent_log.append({"activation":self.activation,"round":self.round,"actor":aid,**intent})
        ev={"activation":self.activation,"round":self.round,"actor":aid,"start":a.pos,"intent":intent,"events":[]}

        if aid=="HE":
            if a.pos=="B1":
                ev["move"]=self.move(a,"E3")
            elif intent["intent"]=="disengage_hide_survive":
                dest=self.safest_retreat_cell(a)
                if dest:
                    ev["move"]=self.move(a,dest,max_override=3)
                self.add_status(a,"hidden")
                ev["bonus_action"]={"ability":"cunning_action_hide","result":"hidden"}
            target=self.choose_ranged_target(a,[intent.get("target"),"XB","RS","WG","SG"],10)
            if target and a.resources.get("action",1)>0:
                sneak="hidden" in a.statuses or "bloodied" in target.statuses or any(self.adjacent(al.pos,target.pos) for al in self.allies_of(a))
                adv="hidden" in a.statuses
                ev["action"]=self.attack(a,target,"shortbow+sneak" if sneak else "shortbow","dex",[("1d6+4","piercing")],adv=adv,extra=[("2d6","sneak")] if sneak else [])
                self.remove_status(a,"hidden")
            elif "action" not in ev:
                ev["action"]={"ability":"hide","reason":"no target"}

        elif aid=="EZ":
            if intent["intent"]=="retreat_control":
                dest=self.safest_retreat_cell(a)
                if dest:
                    ev["move"]=self.move(a,dest,max_override=3)
                    ev["bonus_action"]={"ability":"cautious_step","result":"retreated"}
            elif a.pos=="B2":
                ev["move"]=self.move(a,"C3")
            target=self.choose_ranged_target(a,[intent["target"],"WG","SG","RS","XB"],12)
            if target:
                if a.resources.get("bonus_action",0)>0 and "hex:EZ" not in target.statuses:
                    self.clear_hexes()
                    self.add_status(target,"hex:EZ")
                    a.resources["bonus_action"]-=1
                    a.resources["concentration"]="hex:"+target.id
                    ev["bonus_action"]={"ability":"hex","target":target.id}
                extra=[("1d6","necrotic_hex")] if "hex:EZ" in target.statuses else []
                ev["action"]=self.attack(a,target,"eldritch_blast","cha",[("1d10+4","force")],extra=extra)
            else:
                ev["action"]={"ability":"dodge","reason":"no LoS target"}

        elif aid=="EL":
            target=self.actors.get(intent["target"])
            if intent["intent"]=="revive_ally" and target:
                if not self.adjacent(a.pos,target.pos):
                    dest=self.best_adjacent(a,target)
                    if dest:
                        ev["move"]=self.move(a,dest)
                amount=min(10,a.resources.get("lay",0),target.max_hp-target.hp)
                ev["action"]=self.heal_action(a,target,amount,"lay_on_hands_revive",pool="lay")
            elif intent["intent"]=="self_heal":
                amount=min(15,a.resources.get("lay",0),a.max_hp-a.hp)
                ev["action"]=self.heal_action(a,a,amount,"lay_on_hands",pool="lay")
            else:
                if target and target.alive and not self.adjacent(a.pos,target.pos):
                    dest=self.best_adjacent(a,target)
                    if dest:
                        ev["move"]=self.move(a,dest)
                adj=[e for e in self.enemies_of(a) if self.adjacent(a.pos,e.pos)]
                if adj:
                    chosen=target if target in adj else min(adj,key=lambda e:e.hp)
                    smite=a.resources.get("spell1",0)>0 and (chosen.hp>=14 or chosen.id in ["SG","WG"])
                    extra=[]; ability="greatsword"
                    if smite:
                        a.resources["spell1"]-=1
                        extra=[("2d8","radiant_smite")]
                        ability+="+smite"
                    ev["action"]=self.attack(a,chosen,ability,"str",[("2d6+4","slashing")],melee=True,extra=extra)
                else:
                    ev["action"]={"ability":"protective_guard","reason":"no adjacent target"}

        elif aid in ["WG","SG"]:
            target=self.actors.get(intent["target"])
            if target and target.alive and not self.adjacent(a.pos,target.pos):
                dest=self.best_adjacent(a,target)
                if dest:
                    ev["move"]=self.move(a,dest)
            adj=[e for e in self.enemies_of(a) if self.adjacent(a.pos,e.pos)]
            if adj:
                chosen=target if target in adj else min(adj,key=lambda e:e.hp)
                if aid=="WG":
                    ev["action"]=self.attack(a,chosen,"warglaive","dex",[("1d10+4","slashing")],melee=True)
                else:
                    ev["action"]=self.attack(a,chosen,"maul","str",[("2d6+4","bludgeoning")],melee=True)
            else:
                ev["action"]={"ability":"pressure_position","reason":"no adjacent target"}

        elif aid=="RS":
            target=self.actors.get(intent["target"])
            if intent["intent"]=="heal_wounded_enemy" and target and target.alive and a.resources.get("spell1",0)>0 and self.cheb(a.pos,target.pos)<=6:
                if self.spend(a,{"action":1}):
                    a.resources["spell1"]-=1
                    amount,rolls,fixed=roll_expr(f"{self.seed}:heal:{self.activation}:{target.id}","1d8+3")
                    before=target.hp
                    target.hp=min(target.max_hp,target.hp+amount)
                    ev["action"]={"ability":"dark_mend","target":target.id,"healing":{"expr":"1d8+3","rolls":rolls,"fixed":fixed,"amount":amount,"hp_before":before,"hp_after":target.hp}}
                    ev["events"].append({"event":"field_reaction","cell":"C5","effect":"rune circle glows after dark mend"})
            else:
                target=self.choose_ranged_target(a,[intent["target"],"EL","HE","EZ"],8)
                if target:
                    ev["action"]=self.attack(a,target,"ruin_bolt","wis",[("1d8+3","necrotic")])
                else:
                    ev["action"]={"ability":"chant","reason":"no target"}

        elif aid=="XB":
            if a.pos=="G6":
                ev["move"]=self.move(a,"H6")
            target=self.choose_ranged_target(a,[intent["target"],"EZ","HE","EL"],10)
            if target:
                ev["action"]=self.attack(a,target,"crossbow","dex",[("1d8+4","piercing")])
            else:
                ev["action"]={"ability":"aim","reason":"no LoS target"}

        act=ev.get("action")
        if isinstance(act,dict):
            if "reaction_events" in act:
                ev["events"].extend(act["reaction_events"])
            tid=act.get("target")
            if tid in self.actors and "damage" in act:
                tgt=self.actors[tid]
                hp0=act["damage"]["hp_before"]; hp1=act["damage"]["hp_after"]
                if hp1==0 and "downed" in tgt.statuses:
                    ev["events"].append({"event":"unit_downed","actor":tid,"cell":tgt.pos})
                elif hp1==0 and "dead" in tgt.statuses:
                    ev["events"].append({"event":"unit_down","actor":tid,"cell":tgt.pos})
                elif hp0>tgt.max_hp/2 and hp1<=tgt.max_hp/2:
                    ev["events"].append({"event":"bloodied","actor":tid,"cell":tgt.pos})

        # GM: pressure only, no arbitrary HP edits
        if any(e.get("event") in ["unit_downed","unit_down"] for e in ev["events"]):
            gm={"event":"gm_morale_shift","effect":"nearby enemies and allies reprioritize around the fallen unit"}
            ev["events"].append(gm)
            self.gm_log.append({"activation":self.activation,**gm})

        ev["end"]=a.pos
        ev["resources_after"]=dict(a.resources)
        self.log.append(ev)

    def run_until_end(self,max_activations=120):
        i=0
        while self.living("heroes") and self.living("enemies") and i<max_activations:
            aid=self.initiative[i % len(self.initiative)]
            if i>0 and i%len(self.initiative)==0:
                self.round+=1
            self.resolve(aid)
            i+=1
        return self.snapshot()

    def board(self):
        occ={a.pos:a.id for a in self.actors.values() if a.alive}
        down={a.pos:a.id.lower() for a in self.actors.values() if "downed" in a.statuses and "dead" not in a.statuses}
        out=[]
        for y in range(8,0,-1):
            row=[]
            for x in range(1,9):
                c=xy_to_cell(x,y)
                if c in occ: row.append(occ[c])
                elif c in down: row.append(down[c])
                elif not self.cells[c].walkable: row.append("##")
                elif self.cells[c].hazard=="unstable_rune": row.append("Ru")
                elif self.cells[c].hazard=="collapse_risk": row.append("Cr")
                elif self.cells[c].hazard=="oil": row.append("Oi")
                elif self.cells[c].cover=="half": row.append("cv")
                else: row.append("..")
            out.append(f"{y} | "+" ".join(f"{v:>2}" for v in row))
        out.append("    "+" ".join(f"{c:>2}" for c in COLS))
        return out

    def snapshot(self):
        winner="heroes" if self.living("heroes") and not self.living("enemies") else ("enemies" if self.living("enemies") and not self.living("heroes") else "unfinished")
        return {
            "snapshot_id":"snap_enc_005_v04_final",
            "seed":self.seed,
            "winner":winner,
            "round":self.round,
            "activation_count":self.activation,
            "initiative_order":self.initiative,
            "initiative_rolls":self.initiative_rolls,
            "board":self.board(),
            "actors":{aid:{"name":a.name,"team":a.team,"class":a.cls,"position":a.pos,"hp":a.hp,"max_hp":a.max_hp,"ac":a.ac,"statuses":a.statuses,"resources":a.resources} for aid,a in self.actors.items()},
            "intent_log":self.intent_log,
            "gm_log":self.gm_log,
            "log":self.log,
            "render_prompt_seed":"Render final board exactly from coordinates. Use uppercase labels for alive units and lowercase labels for downed heroes. No invented units."
        }

def main():
    out=Path(__file__).resolve().parents[1]
    sim=BattleV04()
    snap=sim.run_until_end()
    (out/"game-data/encounters").mkdir(parents=True,exist_ok=True)
    (out/"game-data/snapshots").mkdir(parents=True,exist_ok=True)
    (out/"game-data/agent-intents").mkdir(parents=True,exist_ok=True)
    (out/"game-data/encounters/enc-005-v04-full-log.json").write_text(json.dumps(snap["log"],ensure_ascii=False,indent=2),encoding="utf-8")
    (out/"game-data/agent-intents/enc-005-v04-intents.json").write_text(json.dumps(snap["intent_log"],ensure_ascii=False,indent=2),encoding="utf-8")
    (out/"game-data/encounters/enc-005-v04-final-state.json").write_text(json.dumps(snap,ensure_ascii=False,indent=2),encoding="utf-8")
    (out/"game-data/snapshots/snap-enc-005-v04-final.json").write_text(json.dumps({k:v for k,v in snap.items() if k!="log"},ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:snap[k] for k in ["winner","round","activation_count","initiative_order","board"]},ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
