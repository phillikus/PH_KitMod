import struct, os
OUT=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"spl") if "__file__" in globals() else "spl"
def rs(s,n=8): return s.encode().ljust(n,b"\0")[:n]

# ---------- SPL writer (V1, 114-byte header, 40-byte abilities, 48-byte effects) ----------
def fx(op,tgt=2,pw=0,p1=0,p2=0,tm=0,res=0,dur=0,pr=100,rsr="",dn=0,ds=0,sv=0,sb=0,sp=0):
    return struct.pack("<HBBiiBBIBB8siiIiI" if False else "<HBBiiBBIBB8siiIii",
        op,tgt,pw,p1,p2,tm,res,dur,pr,0,rsr.encode().ljust(8,b"\0"),dn,ds,sv,sb,sp)
assert len(fx(0))==48
def ability(icon,tgt,rng,minlvl,nfx,fxidx,proj,form=1,loc=4,speed=0,tgtn=1):
    return struct.pack("<BBH8sBBHHHHHHHHHHHH",form,0,loc,rs(icon),tgt,tgtn,rng,minlvl,speed,0,0,0,0,nfx and 0 or 0,nfx,fxidx,0,0,proj)[:40]
def ab(icon,tgt,rng,minlvl,effects_list,fxidx,proj,tgtn=0):
    b=bytearray(40)
    b[0]=1; b[1]=0; struct.pack_into("<H",b,2,4); b[4:12]=rs(icon)
    b[12]=tgt; b[13]=tgtn; struct.pack_into("<H",b,14,rng); struct.pack_into("<H",b,16,minlvl)
    struct.pack_into("<H",b,18,0); struct.pack_into("<H",b,30,len(effects_list)); struct.pack_into("<H",b,32,fxidx); struct.pack_into("<H",b,38,proj)
    return bytes(b)
def spl(path,abilities,flags=0x2004000,icon="",name=-1,desc=-1,level=1,sectype=0,school=0,exclusion=0,cfx=None):
    # abilities: list of dict(icon,tgt,rng,minlvl,proj,effects=[bytes...])
    hdr=bytearray(114)
    hdr[0:8]=b"SPL V1  "
    struct.pack_into("<i",hdr,8,name); struct.pack_into("<i",hdr,12,-1)
    struct.pack_into("<I",hdr,0x18,flags); struct.pack_into("<H",hdr,0x1c,4)  # innate
    struct.pack_into("<I",hdr,0x1e,exclusion)
    hdr[0x25]=school; hdr[0x27]=sectype
    struct.pack_into("<I",hdr,0x34,level); hdr[0x3a:0x42]=rs(icon)
    struct.pack_into("<i",hdr,0x50,-1); struct.pack_into("<i",hdr,0x54,desc if desc!=-1 else -1)
    abh=b""; allfx=[]
    ao=114
    for a in abilities:
        abh+=ab(a["icon"],a["tgt"],a["rng"],a["minlvl"],a["effects"],len(allfx),a["proj"],a.get("tgtn",0)); allfx+=a["effects"]
    cf_idx=len(allfx); cf=cfx or []
    allfx+=cf
    eo=ao+40*len(abilities)
    struct.pack_into("<I",hdr,0x64,ao); struct.pack_into("<H",hdr,0x68,len(abilities)); struct.pack_into("<I",hdr,0x6a,eo)
    struct.pack_into("<H",hdr,0x6e,cf_idx); struct.pack_into("<H",hdr,0x70,len(cf))
    open(path,"wb").write(bytes(hdr)+abh+b"".join(allfx))

# ---------- PRO from user's slwrath.pro template ----------
import sys
tpl=bytearray(open(sys.argv[1] if len(sys.argv)>1 else "slwrath.pro","rb").read())   # any area projectile (e.g. your slwrath.pro) is used as template
def pro(path,aoe_ft,sel,reps=1,delay=100,visible=False,vvc=""):
    d=bytearray(tpl)
    v=round(aoe_ft*17.07)
    flags=0x1000 | {"enemy":0x40,"party":0xC0,"all":0x00}[sel] | (1 if visible else 0)
    if vvc:
        flags |= 0x0400  # Use VVC / draw the area animation
        d[0x21C:0x224]=rs(vvc)
        struct.pack_into("<I",d,0x240,struct.unpack_from("<I",d,0x240)[0] | 0x4)  # Draw center VVC once
    struct.pack_into("<I",d,0x200,flags); struct.pack_into("<H",d,0x204,v); struct.pack_into("<H",d,0x206,v)
    struct.pack_into("<H",d,0x210,delay); d[0x216]=reps
    open(path,"wb").write(bytes(d))
pro(f"{OUT}/avguid.pro",20,"party")           # Celestial Guidance aura: 20ft radius, party only
pro(f"{OUT}/avwell.pro",15,"enemy",reps=5,delay=90,visible=True,vvc="avwellg")  # Gravity Well: persistent ground VVC
pro(f"{OUT}/avintv.pro",5,"party",reps=1)     # Celestial Intervention: small party-only burst on the target
print("pro ok")

# ======================= SPELLS =======================
FL_ACT=0x2000200      # activated ability (same as Thunderclap)
FL_HLA=0x2000600      # HLA (same as Wrath of the Storm)
FL_SUB=0x2004000      # sub-spells (same as Thunderous Smite helpers)
def A(icon,tgt,rng,minlvl,effects,proj=1): return dict(icon=icon,tgt=tgt,rng=rng,minlvl=minlvl,effects=effects,proj=proj)

# --- Astral Mark: target enemy, AC penalty (= THAC0 bonus for everyone attacking it) ---
ab_=[]
for lvl,ac,dur in [(1,2,18),(9,3,24),(17,4,30)]:
    ab_.append(A("AVMARKB",1,60,lvl,[
        fx(321,tgt=2,rsr="avmark"),
        fx(0,tgt=2,p1=ac,p2=0,tm=0,dur=dur),
        fx(142,tgt=2,p2=0,tm=0,dur=dur)]))
spl(f"{OUT}/avmark.spl",ab_,flags=FL_ACT,icon="AVMARKB",level=9)

# --- Celestial Guidance (passive): AP_ spell installs a permanent every-round trigger ---
spl(f"{OUT}/avguid.spl",[A("AVGUIDB",1,1,1,[fx(232,tgt=1,p1=0,p2=10,tm=9,rsr="avguidp")])],flags=0,icon="AVGUIDB",level=0)
ab_=[]
for lvl,b in [(1,1),(10,2),(18,3)]:
    ab_.append(A("",5,1,lvl,[
        fx(321,tgt=2,rsr="avguidp"),
        fx(325,tgt=2,p1=b,p2=0,tm=0,dur=12)]))
spl(f"{OUT}/avguidp.spl",ab_,flags=FL_SUB,level=9)

# --- Gravity Well: point target, enemies-only area pulsing 5x every 90 ticks ---
ab_=[]
for lvl,pct in [(6,50),(14,40)]:
    ab_.append(A("AVWELLB",4,60,lvl,[
        fx(321,tgt=2,rsr="avwell"),
        fx(126,tgt=2,p1=pct,p2=2,tm=0,dur=8),
        fx(142,tgt=2,p2=0,tm=0,dur=8)]))
spl(f"{OUT}/avwell.spl",ab_,flags=FL_ACT,icon="AVWELLB",level=9)

# --- Celestial Intervention: swap places with the ally + physical resistance on both ---
# Both op124 effects share the coordinates fixed at cast time: caster -> target point (ally), ally -> source point (caster).
# SWAP_ALLY_P2 is the one unverified value: if the ally does not move in game, change it (see README notes).
SWAP_CASTER_P2 = 0
SWAP_ALLY_P2   = 1
ab_=[]
for lvl,pct in [(9,25),(21,40)]:
    e=[fx(321,tgt=2,rsr="avintv"),fx(321,tgt=1,rsr="avintv"),
       fx(124,tgt=1,p1=0,p2=SWAP_CASTER_P2,tm=0),
       fx(124,tgt=2,p1=0,p2=SWAP_ALLY_P2,tm=0)]
    for t in (2,1):
        for op in (86,87,88,89): e.append(fx(op,tgt=t,p1=pct,p2=0,tm=0,dur=12))
        e.append(fx(142,tgt=t,p2=0,tm=0,dur=12))
    ab_.append(A("AVINTVB",1,90,lvl,e))
spl(f"{OUT}/avintv.spl",ab_,flags=FL_ACT,icon="AVINTVB",level=9)

print("spl ok")
