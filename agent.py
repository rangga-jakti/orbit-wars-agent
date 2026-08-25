import math
from kaggle_environments.envs.orbit_wars.orbit_wars import Planet, Fleet
SUN_X,SUN_Y,SUN_R=50.0,50.0,10.0
MAX_SPEED=6.0
def fleet_speed(n):
    if n<=1: return 1.0
    return 1.0+(MAX_SPEED-1.0)*((math.log(max(1,n))/math.log(1000))**1.5)
def ttime(fx,fy,tx,ty,n):
    return max(1,int(math.ceil(math.hypot(tx-fx,ty-fy)/fleet_speed(n))))
def is_orb(p):
    return (math.hypot(p.x-SUN_X,p.y-SUN_Y)+p.radius)<50.0
def get_xy(p,step,ip,av):
    if not is_orb(p): return p.x,p.y
    init=next((Planet(*x) for x in ip if x[0]==p.id),None)
    if init is None: return p.x,p.y
    r=math.hypot(init.x-SUN_X,init.y-SUN_Y)
    a=math.atan2(init.y-SUN_Y,init.x-SUN_X)+av*step
    return SUN_X+r*math.cos(a),SUN_Y+r*math.sin(a)
def predict_intercept(sx,sy,target,step,ip,av,n_ships):
    tx,ty=get_xy(target,step,ip,av)
    t_est=ttime(sx,sy,tx,ty,n_ships)
    for _ in range(15):
        fx,fy=get_xy(target,step+t_est,ip,av)
        new_t=ttime(sx,sy,fx,fy,n_ships)
        if abs(new_t-t_est)<=1: t_est=new_t; break
        t_est=new_t
    return get_xy(target,step+t_est,ip,av)+(t_est,)
def hits_sun(fx,fy,tx,ty):
    dx,dy=tx-fx,ty-fy
    lsq=dx*dx+dy*dy
    if lsq<1e-9: return False
    t=((SUN_X-fx)*dx+(SUN_Y-fy)*dy)/lsq
    if not(0<=t<=1): return False
    return math.hypot(fx+t*dx-SUN_X,fy+t*dy-SUN_Y)<SUN_R
def safe_angle(fx,fy,tx,ty):
    d=math.atan2(ty-fy,tx-fx)
    if not hits_sun(fx,fy,tx,ty): return d
    for o in [0.3,-0.3,0.5,-0.5,0.8,-0.8,1.2,-1.2]:
        a=d+o
        if not hits_sun(fx,fy,fx+math.cos(a)*200,fy+math.sin(a)*200): return a
    return None
def agent(obs,config=None):
    try:
        isdict=isinstance(obs,dict)
        player=obs.get('player',0) if isdict else obs.player
        raw_p=obs.get('planets',[]) if isdict else obs.planets
        raw_f=obs.get('fleets',[]) if isdict else obs.fleets
        av=obs.get('angular_velocity',0.03) if isdict else getattr(obs,'angular_velocity',0.03)
        ip=list(obs.get('initial_planets',raw_p) if isdict else getattr(obs,'initial_planets',raw_p))
        step=obs.get('step',0) if isdict else getattr(obs,'step',0)
        planets=[Planet(*p) for p in raw_p]
        fleets=[Fleet(*f) for f in raw_f]
        mine=[p for p in planets if p.owner==player]
        others=[p for p in planets if p.owner!=player]
        if not mine or not others: return []
        budget={p.id:p.ships for p in mine}
        actions=[]
        mine_map={p.id:p for p in mine}
        my_fleet_targets=set()
        for f in fleets:
            if f.owner==player:
                ca,sa=math.cos(f.angle),math.sin(f.angle)
                for t in others:
                    tx2,ty2=get_xy(t,step,ip,av)
                    dx,dy=tx2-f.x,ty2-f.y
                    dist=math.hypot(dx,dy)
                    if dist<1: continue
                    if (ca*dx+sa*dy)/dist>0.85:
                        my_fleet_targets.add(t.id); break
        for ef in [f for f in fleets if f.owner!=player]:
            ca,sa=math.cos(ef.angle),math.sin(ef.angle)
            best_id,bs=None,999
            for p in mine:
                dx,dy=p.x-ef.x,p.y-ef.y
                if dx*ca+dy*sa<=0: continue
                perp=abs(dx*sa-dy*ca)
                if perp<p.radius*5 and perp<bs: bs,best_id=perp,p.id
            if best_id is None: continue
            tp=mine_map[best_id]
            deficit=int(ef.ships*1.2)-tp.ships+3
            if deficit<=0: continue
            tx2,ty2=get_xy(tp,step,ip,av)
            for h in sorted([p for p in mine if p.id!=best_id and budget.get(p.id,0)-2>=deficit],
                            key=lambda p:math.hypot(p.x-tp.x,p.y-tp.y))[:1]:
                send=min(deficit+3,budget[h.id]-2)
                if send<1: continue
                hx,hy=get_xy(h,step,ip,av)
                ang=safe_angle(hx,hy,tx2,ty2)
                if ang is None: continue
                actions.append([int(h.id),float(ang),int(send)])
                budget[h.id]-=send
        targeted=set()
        for src in sorted(mine,key=lambda p:p.ships,reverse=True):
            if len(actions)>=10: break
            avail=budget.get(src.id,0)
            if avail<2: continue
            sx,sy=get_xy(src,step,ip,av)
            best,best_score=None,-9999
            for t in others:
                if t.id in targeted or t.id in my_fleet_targets: continue
                fx,fy,travel=predict_intercept(sx,sy,t,step,ip,av,max(avail,5))
                if not(0<=fx<=100 and 0<=fy<=100): continue
                ships_there=t.ships if t.owner==-1 else t.ships+t.production*travel
                needed=int(ships_there)+1
                if avail<needed: continue
                ang=safe_angle(sx,sy,fx,fy)
                if ang is None: continue
                remaining=max(1,500-step-travel)
                score=(t.production*remaining)/(ships_there+math.hypot(fx-sx,fy-sy)*0.2+1)
                if score>best_score: best_score=score; best=(t,fx,fy,needed,ang)
            if best is None: continue
            t,fx,fy,needed,ang=best
            actions.append([int(src.id),float(ang),int(needed)])
            budget[src.id]-=needed
            targeted.add(t.id)
        return [[int(a[0]),float(a[1]),int(a[2])] for a in actions if a[2]>0]
    except Exception as e:
        import traceback;traceback.print_exc()
        return []