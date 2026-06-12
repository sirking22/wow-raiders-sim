#!/usr/bin/env python3
from pathlib import Path
import argparse, json, math
from PIL import Image, ImageDraw, ImageFont

COL = {"bg":(5,10,12),"line":(93,79,55),"hex":(91,86,70),"blocked":(32,32,30),"hero":(80,130,165),"enemy":(195,42,34),"objective":(160,90,210),"gold":(205,170,105),"text":(220,214,195),"green":(111,180,92)}

def font(size, bold=False):
    p = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(p, size) if Path(p).exists() else ImageFont.load_default()

F_TITLE = font(28, True); F_H = font(18, True); F = font(14); F_S = font(11)

def hex_points(cx, cy, r):
    return [(cx+r*math.cos(math.radians(60*i-30)), cy+r*math.sin(math.radians(60*i-30))) for i in range(6)]

def offset_center(col, row, origin, r):
    x_step = math.sqrt(3)*r
    y_step = 1.5*r
    return origin[0] + col*x_step + (row%2)*x_step/2, origin[1] + row*y_step

def render(output, field_type="STANDARD_TACTICAL_FIELD", units=None, blocked=None, objective_cells=None, footer=None, coords=False):
    specs = {"STANDARD_TACTICAL_FIELD":(11,9,"Стандартное тактическое поле"),"BOSS_ARENA":(13,11,"Босс-арена"),"CORRIDOR_CHOKEPOINT":(12,7,"Коридор / choke-point")}
    cols, rows, title = specs[field_type]
    if units:
        cols = max(cols, max(u["pos"][0] for u in units)+1)
        rows = max(rows, max(u["pos"][1] for u in units)+1)
    W,H = 1600,900
    img = Image.new("RGB",(W,H),COL["bg"]); d = ImageDraw.Draw(img)
    d.rectangle([18,18,W-18,H-18], outline=COL["line"], width=2)
    d.text((45,40),"ПОЛЕ БОЯ · ГЕКСЫ",font=F_TITLE,fill=COL["gold"])
    d.text((45,82),title,font=F_H,fill=COL["text"])
    r = min(38, 1080/(math.sqrt(3)*(cols+0.5)), 650/(1.5*(rows-1)+2))
    origin=(260,160)
    blocked=set(tuple(x) for x in (blocked or [])); objective_cells=set(tuple(x) for x in (objective_cells or []))
    minx,miny,maxx,maxy=9999,9999,-9999,-9999
    for row in range(rows):
        for col in range(cols):
            cx,cy=offset_center(col,row,origin,r)
            minx,miny,maxx,maxy=min(minx,cx-r),min(miny,cy-r),max(maxx,cx+r),max(maxy,cy+r)
            cell=(col,row); fill=None; outline=COL["hex"]
            if cell in blocked: fill=COL["blocked"]
            if cell in objective_cells: fill=(30,18,42); outline=COL["objective"]
            d.polygon(hex_points(cx,cy,r), outline=outline, fill=fill)
            if coords: d.text((cx-10,cy-6),f"{col},{row}",font=F_S,fill=(90,90,80))
    d.rounded_rectangle([minx-12,miny-12,maxx+12,maxy+12], radius=8, outline=COL["line"], width=2)
    for u in units or []:
        col,row=u["pos"]; cx,cy=offset_center(col,row,origin,r)
        color=COL["hero"] if u.get("side")=="heroes" else COL["enemy"]
        d.ellipse([cx-r*.72,cy-r*.72,cx+r*.72,cy+r*.72],outline=color,width=3,fill=(14,16,16))
        d.text((cx,cy-5),u.get("label",u.get("id","?"))[:4],anchor="mm",font=F_S,fill=COL["text"])
        if u.get("hp"): d.text((cx,cy+r*.68),u["hp"],anchor="mm",font=F_S,fill=COL["text"])
    if footer: d.text((55,815),footer,font=F_H,fill=COL["green"])
    Path(output).parent.mkdir(parents=True, exist_ok=True); img.save(output)

def units_from_run(path):
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    enc=data["encounter_results"][1]; turn=data["turn_log"][enc["turn_log_end"]-1]
    units=[]
    for uid,u in turn["state_after"]["units"].items():
        units.append({"id":uid,"label":u["name"][:4] if u["side"]=="heroes" else uid,"side":u["side"],"pos":u["pos"],"hp":u["hp"]})
    return units, f"Цель: сломать печать · итог {enc['objective']} · исход {enc['outcome']}"

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",required=True); ap.add_argument("--type",default="STANDARD_TACTICAL_FIELD"); ap.add_argument("--run-json"); ap.add_argument("--coords",action="store_true"); args=ap.parse_args()
    blocked=None; objective=None; units=[]; footer=None
    if args.type=="BOSS_ARENA": objective=[[6,5],[6,4],[5,5],[7,5],[6,6]]; blocked=[[0,0],[12,0],[0,10],[12,10],[1,0],[11,10]]
    if args.type=="CORRIDOR_CHOKEPOINT": blocked=[[0,0],[1,0],[10,0],[11,0],[0,1],[11,1],[0,5],[11,5],[0,6],[1,6],[10,6],[11,6]]
    if args.run_json: units, footer = units_from_run(args.run_json)
    render(args.output,args.type,units,blocked,objective,footer,args.coords)
if __name__=="__main__": main()
