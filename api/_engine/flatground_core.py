"""
Flat-ground design core — single source of truth for Joyjeet's house style.

ONE shared line-array builder (`build_line`) applies every house principle:
  - trim DERIVED from a target frame angle (~-6 deg, never steeper than ~-7)
  - box COUNT scales with throw (anchored: KSL @ 68 m -> 16)
  - deep-J splay, gain-shaded bottom, Line/Arc by splay
  - lowest edge capped at 20 ft; mains/array width kept inside the venue
  - confirmed L/R pairing recipe (pair link + Linked pairs + AP slots)
Mains, out fills and delays ALL go through it — same concepts everywhere.
The confirmed 16-box Test_v1 mains are reproduced exactly (regression anchor).
"""
from __future__ import annotations
import math

FT = 0.3048
THROW_WINDOW  = 68.0
FRONT_OFFSET  = 15.0 * FT     # audience plane starts ~15 ft off the datum
TARGET_FRAME  = 5.0            # aim frame ~-5 deg (Joyjeet reviewed)
OVERSHOOT     = 3.0            # ~3 deg overshoot above far point (reviewed)
MAINS_LOWEST_EDGE = 6.096     # 20 ft cap
MAINS_Y_MAX   = 10.67
MAINS_X       = 1.5
LCR_WIDTH_M   = 250 * FT      # add a centre only past 250 ft width
VARIANCE_FRAC = 0.80          # delays' <=3-4 dB even-coverage end ~= 0.8 x design throw
OVERLAP_M     = 17.5 * FT      # next system hands off 15-20 ft before coverage end
def delay1_from_mains_ft(n):  # mains <=3-4 dB reach scales with box count
    return 185.0 + (n-16)*8.75 # 16 -> 185 ft, 14 -> 167.5 ft (Joyjeet anchors)

MAINS_SPLAY = [0,0,1,0,0,1,0,1,0,1,1,2,3,4,6,9]   # USER-CONFIRMED (16 box)

# per-system specs
SPECS = {
    "KSL": dict(box_h=0.3323, first=0.175, bph=0.325,
                frame=("KSLFlyingFrame","KSL Flying frame",(970.0,487.0,483.0),9,23),
                sw=lambda i,n:(0, 1 if i<2 else 0, 0, -0.5, -1.5)),   # CUT off, HFC top2, CPL
    "V-Series": dict(box_h=0.3106, first=0.16, bph=0.31,
                frame=("VFlyingFrame","V Flying frame",(160.8,63.7,97.1),0,12),
                sw=lambda i,n:(0,0,0,-5.5,0.5)),
}

def _clamp(v,lo,hi): return max(lo,min(hi,v))
def mains_count(throw): return _clamp(round(16*throw/THROW_WINDOW/2)*2, 6, 24)
def mains_y(width_m):   return round(min(MAINS_Y_MAX, width_m/4.0), 2)
def sub_stacks(width_m):return _clamp(round(8*width_m/46.0), 3, 14)
def ff_count(width_m):  return _clamp(round(6*width_m/46.0/2)*2, 4, 12)
def ff_span_ft(my_m):   return round((my_m/FT)*0.714, 1)

def deep_j_splay(n):
    if n==16: return list(MAINS_SPLAY)
    ns=max(2,round(n*0.4)); top=[0 if i%3<2 else 1 for i in range(ns)]
    nb=n-ns; bot=[max(1,round(1+(9-1)*k/max(1,nb-1))) for k in range(nb)]
    return top+bot

def mains_levels(n):
    k=max(2,round(n/4)); lev=[0.0]*(n-k)
    for j in range(k): lev.append(-0.5 if j<k/2 else -1.0)
    return lev

def _chain(fx,fa,splays,h,first):
    x,y,z=fx; va=fa; r=math.radians(va); x+=first*math.sin(r); z-=first*math.cos(r); out=[(va,(x,y,z))]
    for s in splays[1:]:
        r=math.radians(va); x+=h*math.sin(r); z-=h*math.cos(r); va=va-s-0.1; out.append((va,(x,y,z)))
    return out
def _frame_angle(le,arrh,throw,o=OVERSHOOT): return -round(math.degrees(math.atan((le+arrh-1.7)/throw))-o,1)
def _trim(ax,fa,sp,h,first,le): return 100.0+(le+0.17-min(p[2] for _,p in _chain((ax,0,100.0),fa,sp,h,first)))
def ksl_setup(s): return 1 if s>=2 else 0

def design(system, throw):
    """Return the house geometry for a line array of `system` covering `throw` metres."""
    sp=SPECS[system]; te=min(throw, THROW_WINDOW)
    n=mains_count(te); splays=deep_j_splay(n); levels=mains_levels(n)
    arr_h=round(n*sp["bph"],2)
    target_le=te*math.tan(math.radians(TARGET_FRAME+OVERSHOOT))+1.7-arr_h
    le=min(MAINS_LOWEST_EDGE, max(0.5, target_le))
    fa=_frame_angle(le,arr_h,te)
    z=_trim(MAINS_X, fa, splays, sp["box_h"], sp["first"], le)
    return dict(n=n, splays=splays, levels=levels, le=le, fa=fa, z=z, throw=te)

def build_line(api, name, system, x, yc, throw, haim=0.0, delay=None, paired=True, k12=True, level_offset=0.0):
    """Build a line array (paired L/R by default) with ALL house principles.
    Used identically for mains, out fills and delays."""
    sp=SPECS[system]; d=design(system, throw); n=d["n"]; z=d["z"]; fa=d["fa"]
    dly = 0.0062 if system=="KSL" else 0.0003
    if delay is not None: dly=delay
    n_k12 = (2 if n>=8 else 0) if (system=="KSL" and k12) else 0
    ex=dict(HeightLowestEdge=d["le"], VerticalAimingAngle=0.0)
    if system=="KSL":
        ex.update(CompressionModeEnable=0,CompressionForce=9810.0,CompressionGrabLinkPosition=0.0,
                  MaxLoadTension=53.59,MaxLoadTensionBGV=55.1,MaxLoadCompression=0.0,MaxLoadCompressionBGV=0.0)
    else:
        ex.update(CompressionModeEnable=0,CompressionForce=-1.0,CompressionGrabLinkPosition=-1.0,
                  MaxLoadTension=15.87,MaxLoadTensionBGV=19.84)
    align = 2 if system=="KSL" else 4

    def one_side(gid, y, aim):
        geo=_chain((x,y,z),fa,d["splays"],sp["box_h"],sp["first"]); prev=sp["frame"][0]; pid=0
        for i,(va,xyz) in enumerate(geo):
            is12 = i>=n-n_k12
            box,spk=("KSL12",119) if is12 else (("KSL8",116) if system=="KSL" else ("V8",73))
            cid=api.add_cab(gid,i+2,spk,box,float(d["splays"][i]),round(va,4),xyz,hangle=aim,
                setup=ksl_setup(d["splays"][i]),comp=(0 if i==0 else 2),level=round(d["levels"][i]+level_offset,1),
                delay=dly,sw=sp["sw"](i,n),prev=prev,nxt=(box if i<n-1 else ''),align=align,
                linked=(pid if i%2==1 else 0)); pid=cid; prev=box
        fr=sp["frame"]; api.add_frame(gid,fr[0],fr[1],fa,(x,y,z),fr[2],fr[3],fr[4]); api.add_ap(gid)

    if not paired:
        gid=api.add_group(name,1,system,(x,yc,z),haim=haim,extra=dict(ex,HorizontalAiming=haim)); one_side(gid,yc,haim)
        return d
    mir_sym = 1 if abs(haim)>0.01 else 0
    order=api.reserve_order()
    master=api.add_group(name,1,system,(x,-abs(yc),z),order=order,symmetric=0,has_prev=0,
                         haim=-haim,extra=dict(ex,HorizontalAiming=-haim))
    mirror=api.add_group(name,1,system,(x, abs(yc),z),order=-1,symmetric=mir_sym,has_prev=1,
                         haim=haim,extra=dict(ex,HorizontalAiming=haim))
    api.set_next(master,mirror)
    one_side(master,-abs(yc),-haim); one_side(mirror,abs(yc),haim)
    return d

# ---------------- subs & front fills (scale with width) ----------------
SUB_SPACING=7.0*FT
SUB_TAPER=[0.004556,0.001547,0.000671,0.0003,0.0003,0.000671,0.001547,0.004556]
def _sub_taper(ns): mid=(ns-1)/2; return [round(0.0003+abs(i-mid)*0.0011,6) for i in range(ns)]
def build_sub_array(api, width_m=46.0):
    ns=sub_stacks(width_m)
    gid=api.add_group("Sub Array",3,"SL-SUB",(0,0,0),mounting=1,linkmode=1,symmetric=1,
                     extra=dict(BoxType="SL-SUB",NominalDispersionAngle=90.0))
    ys=[(i-(ns-1)/2)*-SUB_SPACING for i in range(ns)]; taper=SUB_TAPER if ns==8 else _sub_taper(ns)
    for p,(yy,dly) in enumerate(zip(ys,taper),1):
        api.add_cab(gid,p,114,"SL-SUB",0,0,(1.0,yy,0.0),order=1,setup=0,delay=dly,cpp=2,sw=(0,0,0,-5.5,0.5),nxt="SL-SUB",align=0)
        api.add_cab(gid,p,114,"SL-SUB",0,0,(0.05,yy,0.6),order=2,setup=0,delay=dly,cpp=1,sw=(0,0,0,-5.5,0.5),prev="SL-SUB",align=0)

def _ff_layout(nff, span_ft):
    half=nff//2; ys=[round(span_ft*(half-i)/half,1) for i in range(half)]; ys=ys+[-y for y in ys]; lay=[]
    for y in ys:
        lvl=-4.0 if abs(y)>=span_ft*0.75 else (-1.0 if abs(y)>=span_ft*0.4 else 0.0)
        lay.append((y,lvl,90 if y>0 else 270))
    return lay
def build_front_fills(api, width_m=46.0, mains_y_m=10.67):
    nff=ff_count(width_m); layout=_ff_layout(nff, ff_span_ft(mains_y_m))
    gid=api.add_group("Front Fills",2,"A-Series",(0,0,0),mounting=1,linkmode=1,symmetric=1); ids=[]
    for i,(yft,lvl,rot) in enumerate(layout):
        ids.append(api.add_cab(gid,i+1,127,"AL90 PS",0,22.0,(0.6,yft*FT,4.4*FT),rot=float(rot),setup=1,
            delay=0.0003,level=lvl,sw=(1,0,0,-5.5,0.5),prev="AL90 PS",nxt=("AL90 PS" if i<len(layout)-1 else ""),align=0))
    half=len(ids)//2
    for k in range(half): api.link(ids[len(ids)-1-k], ids[k])

def build_core(api, depth_m, width_m, mains_variance_limit_m=None):
    far=FRONT_OFFSET+depth_m; throw=min(far-MAINS_X, THROW_WINDOW)
    my=mains_y(width_m)
    d=build_line(api,"Mains","KSL",MAINS_X,my,throw)      # <-- mains via the shared builder
    build_sub_array(api, width_m)
    build_front_fills(api, width_m, my)
    # coverage_end = distance where mains level variance stays <= 3-4 dB. Estimated from
    # the mains BOX COUNT (delay-1 distance + hand-off overlap), capped at the design
    # throw. TRUE value comes from ArrayCalc's Direct-SPL curve; pass mains_variance_limit_m.
    est = MAINS_X + delay1_from_mains_ft(d['n'])*FT + OVERLAP_M
    est = min(est, MAINS_X + throw)
    cov_end = mains_variance_limit_m if mains_variance_limit_m else round(est,2)
    return dict(frame_angle=d["fa"], lowest_edge_ft=round(d["le"]/FT,1), mains_boxes_per_side=d["n"],
                mains_y_m=my, coverage_end_m=cov_end, mains_reach_m=round(MAINS_X+throw,2),
                coverage_end_is_estimate=(mains_variance_limit_m is None))
