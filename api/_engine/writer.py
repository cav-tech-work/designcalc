"""Low-level .dbpr writer — the `api` object passed to core/extension builders.
Handles ID allocation, row inserts, AP slots, venue, SPL calibration. Never touches
ProjectInformation (keeps the integrity hash valid -> file opens with no password)."""
from __future__ import annotations
import sqlite3, shutil, os, time

class Writer:
    def __init__(self, skeleton_path, out_path):
        shutil.copy(skeleton_path, out_path); os.chmod(out_path, 0o644)
        self.db = sqlite3.connect(out_path); self.c = self.db.cursor()
        self.now = int(time.time()*1000)
        self._sg  = (self.c.execute("SELECT MAX(SourceGroupId) FROM SourceGroups").fetchone()[0] or 0)+1
        self._cab = (self.c.execute("SELECT MAX(CabinetId) FROM Cabinets").fetchone()[0] or 0)+1
        self._ff  = (self.c.execute("SELECT MAX(FlyingFrameId) FROM FlyingFrames").fetchone()[0] or 0)+1
        self._aps = (self.c.execute("SELECT MAX(ArrayProcessingSlotId) FROM ArrayProcessingSlots").fetchone()[0] or 0)+1
        self._order = 0

    def reserve_order(self):
        o=self._order; self._order+=1; return o

    def _cols(self, t): return [r[1] for r in self.c.execute(f"PRAGMA table_info({t})")]
    def _ins(self, t, d):
        ks=[k for k in d if k in self._cols(t)]
        self.c.execute(f"INSERT INTO {t} ({','.join(ks)}) VALUES ({','.join('?'*len(ks))})",[d[k] for k in ks])

    def add_group(self, name, typ, system, origin, order=None, mounting=0, next_id=0,
                  has_prev=0, symmetric=0, extra=None, linkmode=0, haim=0.0):
        if order is None: order=self._order; self._order+=1
        gid=self._sg; self._sg+=1
        self._ins("SourceGroups", dict(SourceGroupId=gid,Type=typ,Name=name,OrderIndex=order,
            RemarkableChangeDate=self.now,NextSourceGroupId=next_id,ArrayProcessingEnable=0,
            ArraySightId=0,LinkMode=linkmode,Symmetric=symmetric,Mounting=mounting,RelativeDelay=None))
        sgad=dict(SourceGroupId=gid,System=system,HorizontalAiming=haim,StackedFrameAngle=0.0,
            HasPrevious=has_prev,DefaultRemoteIdSubnet=0,DefaultRemoteIdDevice=1,ShowRigging=1,
            BoxType=None,NominalDispersionAngle=0.0,OriginX=origin[0],OriginY=origin[1],
            OriginZ=origin[2],DefaultAmplifierType='D80')
        if extra: sgad.update(extra)
        self._ins("SourceGroupsAdditionalData", sgad); return gid

    def set_next(self, master, mirror):
        self.c.execute("UPDATE SourceGroups SET NextSourceGroupId=? WHERE SourceGroupId=?",(mirror,master))

    def add_cab(self, gid,pos,spk,name,splay,va,origin,order=1,hangle=0.0,rot=0.0,setup=1,comp=0,
                delay=0.0062,level=0.0,sw=(0,0,0,-0.5,-1.5),prev='',nxt='',cpp=1,align=2,linked=0):
        cid=self._cab; self._cab+=1
        self._ins("Cabinets", dict(CabinetId=cid,DeviceId=0,AmplifierChannel=0,SpeakerId=spk,
            SourceGroupId=gid,PositionIndex=pos,OrderIndex=order,HorizontalAngle=hangle,
            VerticalAngle=va,RotationAngle=rot,PivotAngle=0.0,Linked=linked,
            OriginX=origin[0],OriginY=origin[1],OriginZ=origin[2],HornRotationAngle=-1))
        self._ins("CabinetsAdditionalData", dict(CabinetId=cid,Name=name,ControllerSetup=setup,
            SplayAngle=splay,AlignmentToSubArrayTestPoint=align,CabinetsPerPosition=cpp,
            CompressionState=comp,Delay=delay,Mute=0,Level=level,Switch1=sw[0],Switch2=sw[1],
            Switch3=sw[2],Switch4=sw[3],Switch5=sw[4],PreviousObjectString=prev,NextObjectString=nxt))
        return cid

    def link(self, cab, to_cab):
        self.c.execute("UPDATE Cabinets SET Linked=? WHERE CabinetId=?",(to_cab,cab))

    def add_frame(self, gid,name,disp,angle,origin,w,fh,rh):
        fid=self._ff; self._ff+=1
        self._ins("FlyingFrames", dict(FlyingFrameId=fid,Type=2,Name=name,DisplayName=disp,
            SourceGroupId=gid,PositionIndex=1,FrameAngle=angle,FrontPickPointHole=fh,
            RearPickPointHole=rh,SinglePickPointHole=18.0,TotalWeight=w[0],FrontPickPointWeight=w[1],
            RearPickPointWeight=w[2],FrontPickPointWeightZeroDegrees=-1.0,RearPickPointWeightZeroDegrees=-1.0,
            FrontPickX=origin[0]+0.006,FrontPickY=origin[1],RearPickX=origin[0]-0.997,RearPickY=origin[1],
            SinglePickX=origin[0]-0.714,SinglePickY=origin[1],FrontPickPointPosition=0.01,
            RearPickPointPosition=1.0,SinglePickPointPosition=0.72,OriginX=origin[0],OriginY=origin[1],
            OriginZ=origin[2],LoadBeamPosition='standard'))

    def add_ap(self, gid):
        for slot in range(1,11):
            a=self._aps; self._aps+=1
            nm,cm=('Bypass','This slot is reserved for bypassing ArrayProcessing.') if slot==1 else ('','')
            self._ins("ArrayProcessingSlots", dict(ArrayProcessingSlotId=a,SourceGroupId=gid,Slot=slot,
                Name=nm,Comment=cm,SessionId=b"\x00"*16,CreatedOn='1970-01-01T05:30:00.000',Flags=1))
            self._ins("ArrayProcessingSlotsAdditionalData", dict(ArrayProcessingSlotId=a,Slope1=0.0,
                Slope2=-3.0,Slope3=-3.0,Point1X=0.0,Point2X=0.0,Temperature=293.16,Humidity=60.0,
                VenueObjectIdSelected=0,PowerGlory=0.5,SourceGroupTargetProfile=b"\x00\x00\x00\x00"))


    # boxes per amp channel by system (D80 = 4 ch/device)
    _BPC = {"KSL":2, "V-Series":2, "SL-SUB":1, "A-Series":2}

    def patch_amplifiers(self):
        """Create D80 amp devices and patch every cabinet, per Joyjeet's subnet convention:
        Mains L=1, Mains R=2, Subs=3, Front Fills=4, then L/R pairs from stage outward
        (Out Fills L=5,R=6, Delay 1 L=7,R=8, ...). Names 'subnet.dd' e.g. '1.01'."""
        c=self.c
        grp=[]  # (sgid, name, system, originX, originY, ncab)
        rows=c.execute("""SELECT sg.SourceGroupId,sg.Name,sgad.System,sgad.OriginX,sgad.OriginY
                FROM SourceGroups sg JOIN SourceGroupsAdditionalData sgad ON sgad.SourceGroupId=sg.SourceGroupId
                WHERE sg.Name!='Unused channels'""").fetchall()   # materialize first (avoid cursor reuse)
        counts={sgid:c.execute("SELECT COUNT(*) FROM Cabinets WHERE SourceGroupId=?",(sgid,)).fetchone()[0]
                for sgid,*_ in rows}
        for sgid,name,sysm,ox,oy in rows:
            if counts[sgid]: grp.append([sgid,name,sysm,ox,oy,counts[sgid]])
        def side(oy): return "L" if oy>0 else "R"
        assign={}  # sgid -> subnet
        # fixed 1-4
        for g in grp:
            if g[1]=="Mains": assign[g[0]] = 1 if g[4]>0 else 2
        for g in grp:
            if g[1]=="Sub Array": assign[g[0]]=3
            if g[1]=="Front Fills": assign[g[0]]=4
        # remaining paired systems, stage outward (by |x|), L=odd R=even from 5
        rest=sorted([g for g in grp if g[0] not in assign], key=lambda g:(abs(g[3]), g[1]))
        subnet=5; seen={}
        # group by system-name so a L/R pair shares consecutive subnets
        from collections import OrderedDict
        bysys=OrderedDict()
        for g in rest: bysys.setdefault(g[1],[]).append(g)
        for sysname,gs in sorted(bysys.items(), key=lambda kv: min(abs(x[3]) for x in kv[1])):
            L=[g for g in gs if g[4]>0]; R=[g for g in gs if g[4]<=0]
            for g in L: assign[g[0]]=subnet
            for g in R: assign[g[0]]=subnet+1
            subnet+=2
        # build devices + patch
        did=1; gfx_y=49
        for g in sorted(grp, key=lambda g: assign[g[0]]):
            sgid,name,sysm,ox,oy,n=g; sub=assign[sgid]; bpc=self._BPC.get(sysm,2)
            crows=c.execute("SELECT CabinetId,Linked FROM Cabinets WHERE SourceGroupId=? ORDER BY PositionIndex,OrderIndex",(sgid,)).fetchall()
            cabs=[r[0] for r in crows]; linkmap={cid:lk for cid,lk in crows}
            # circuits: a cabinet + whatever it is linked to/from goes on ONE channel
            # (line arrays link consecutive pairs; front fills link mirror pairs)
            circuits=[]; used=set()
            for cid in cabs:
                if cid in used: continue
                grpc=[cid]; used.add(cid)
                p=linkmap.get(cid,0)
                if p and p not in used and p in linkmap: grpc.append(p); used.add(p)
                for other,lk in linkmap.items():
                    if lk==cid and other not in used: grpc.append(other); used.add(other)
                circuits.append(grpc[:max(bpc,2)])
            dev_idx=0; ch=5; dev_id=None
            for chunk in circuits:
                if ch>4:                                    # new device
                    dev_idx+=1; ch=1; dev_id=did; did+=1
                    nm=f"{name} {sub}.{dev_idx:02d}"
                    self._ins("Devices", dict(DeviceId=dev_id,Model="D80",RemoteIdSubnet=sub,RemoteIdDevice=dev_idx,Name=nm))
                    self._ins("DevicesAmplifier", dict(DeviceId=dev_id,InputMode=0,OutputMode=0))  # matches clean corpus cabinet-driving amps
                    self._ins("PatchableGraphicsObjects", dict(PatchableObjectCategory="POC_Amplifier",
                        PatchableObjectId=dev_id,X=791.0,Y=float(gfx_y),CollapsedState=0,DisplayHorizontally=0)); gfx_y+=60
                chname=f"{name} {ch}"
                self._ins("AmplifierChannels", dict(DeviceId=dev_id,AmplifierChannel=ch,Name=chname))
                self._ins("PatchIOChannels", dict(DeviceId=dev_id,Type=1,PortNumber=ch,Name=chname,Protocol=5))  # amp speaker-output port
                for cid in chunk:
                    c.execute("UPDATE Cabinets SET DeviceId=?, AmplifierChannel=? WHERE CabinetId=?",(dev_id,ch,cid))
                ch+=1
        return {sgid:assign[sgid] for sgid in assign}

    def write_floor(self, depth_m, width_m, front_off_m=15*0.3048):
        self.c.execute("INSERT INTO VenueObjects (VenueObjectId,Name,Shape,PlaneType,Enabled,Transparent,"
            "Locked,ListenerHeight,Color,PrintColor,OriginX,OriginY,OriginZ,RotationX,RotationY,RotationZ,"
            "ScaleX,ScaleY,ScaleZ,OrderIndex,ParentVenueObjectId) VALUES "
            "(1,'Floor',1,1,1,1,0,1.7,4294945280,4294945280,0,0,0,0,0,0,1,1,1,1,0)")
        x0=front_off_m; x1=front_off_m+depth_m
        for i,(x,y) in enumerate([(x0,width_m/2),(x1,width_m/2),(x1,-width_m/2),(x0,-width_m/2)]):
            self.c.execute("INSERT INTO VenueObjectPoints (VenueObjectId,PointIndex,X,Y,Z) VALUES (1,?,?,?,0)",(i,x,y))

    def calibrate_spl(self, top_color_spl=105.0):
        self.c.execute("UPDATE SimulationProperties SET DbPerDiv=3, AutoCalculate=1, TopColorSpl=? "
                       "WHERE ViewPropertiesId=1",(top_color_spl,))

    def finalize(self):
        self.db.commit()
        for tab in ("Cabinets","SourceGroups","FlyingFrames"):
            try: self.c.execute("UPDATE sqlite_sequence SET seq=(SELECT MAX(rowid) FROM %s) WHERE name=?"%tab,(tab,))
            except Exception: pass
        self.db.commit()
        ok=self.c.execute("PRAGMA integrity_check").fetchone()[0]
        self.db.close(); return ok
