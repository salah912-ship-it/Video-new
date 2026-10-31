/*  PUNTOCOM – THE WAY TO US
    After Effects project builder (ExtendScript, AE CC 2020+).

    File > Scripts > Run Script File…  and pick this file.  It asks for the
    repository root folder (the one containing 00_assets/), then builds and saves
    05_aftereffects/PUNTOCOM_TheWayToUs.aep with:

      01_METRO_OPENING      00:00-00:05  Cimiano photos, 2.5D push/pull, title
      02_STREET_SEQUENCES   00:05-00:17  exit card + slots for AI clips / 3D plate
      03_GPS_MAP            00:17-00:22  3D-camera map plane, markers
      04_ROUTE_ANIMATION    (nested in 03) orange route, Trim Paths
      05_STOREFRONT         00:22-00:29  ORIGINAL storefront, parallax push-in, GPS line
      06_LOGO_REVEAL        00:29-00:35  ORIGINAL logo layers, gold sweep
      00_MAIN_1080x1920     final timeline + audio

    Only stable, documented scripting APIs are used. Nothing here edits the
    original logo or storefront pixels: they are imported as footage and only
    transformed (position/scale/opacity) or masked for reveals.
*/
(function buildPuntocom() {
    var W = 1080, H = 1920, FPS = 30, DUR = 35;
    var ORANGE = [245 / 255, 130 / 255, 32 / 255], BLACK = [17 / 255, 17 / 255, 17 / 255];
    var NAVY = [12 / 255, 22 / 255, 32 / 255], GOLD = [201 / 255, 151 / 255, 74 / 255], WHITE = [1, 1, 1];

    var root = Folder.selectDialog("Select the Video-new repository root (contains 00_assets)");
    if (!root) return;
    function f(rel) { var x = new File(root.fsName + "/" + rel); if (!x.exists) throw new Error("Missing asset: " + rel); return x; }

    app.beginUndoGroup("Build PUNTOCOM project");
    app.newProject(); var proj = app.project;

    // ------------------------------------------------------------ folders
    var fAssets = proj.items.addFolder("_ASSETS"), fPre = proj.items.addFolder("_PRECOMPS"), fAudio = proj.items.addFolder("_AUDIO");
    var fRef = proj.items.addFolder("_REFERENCE_ONLY (do not render)");
    function imp(rel, folder) {
        var io = new ImportOptions(f(rel)); var it = proj.importFile(io); it.parentFolder = folder; return it;
    }
    var A = {
        platform: imp("00_assets/cimiano/IMG_2111_cimiano_platform.jpg", fAssets),
        entrance: imp("00_assets/cimiano/IMG_4079_cimiano_entrance.jpg", fAssets),
        entrance2: imp("00_assets/cimiano/IMG_4081_cimiano_entrance_wide.jpg", fAssets),
        store: imp("00_assets/storefront/puntocom_storefront_original.jpg", fAssets),
        logoSym: imp("06_motion_graphics/puntocom_logo_symbol.png", fAssets),
        logoWord: imp("06_motion_graphics/puntocom_logo_wordmark.png", fAssets),
        logoSub: imp("06_motion_graphics/puntocom_logo_subline.png", fAssets),
        logoMaster: imp("00_assets/logo/puntocom_logo_master.jpg", fRef),
        mix: imp("07_audio/puntocom_mix.wav", fAudio)
    };
    var plate = null; // optional: rendered programmatic master used as a reference/plate
    try { plate = imp("08_render/PUNTOCOM_TheWayToUs_1080x1920_30fps.mp4", fRef); } catch (e) {}

    // ------------------------------------------------------------ helpers
    function comp(name, dur, folder) { var c = proj.items.addComp(name, W, H, 1, dur, FPS); c.parentFolder = folder || fPre; c.motionBlur = true; return c; }
    function ease(prop) {
        // Spatial and 1D properties take one KeyframeEase; non-spatial multi-D (e.g. Scale) take one per dimension.
        var n = 1;
        if (!prop.isSpatial && prop.propertyValueType !== PropertyValueType.OneD && prop.value instanceof Array) n = prop.value.length;
        var e = []; for (var i = 0; i < n; i++) e.push(new KeyframeEase(0, 66));
        for (var k = 1; k <= prop.numKeys; k++) prop.setTemporalEaseAtKey(k, e, e);
    }
    function keys(prop, tv) { for (var i = 0; i < tv.length; i++) prop.setValueAtTime(tv[i][0], tv[i][1]); try { ease(prop); } catch (e) {} }
    function tr(layer) { return layer.property("ADBE Transform Group"); }
    function textLayer(c, s, size, color, font, pos, tracking) {
        var l = c.layers.addText(s); var td = l.property("ADBE Text Properties").property("ADBE Text Document");
        var d = td.value; d.resetCharStyle(); d.fontSize = size; d.fillColor = color; d.applyFill = true; d.applyStroke = false;
        try { d.font = font; } catch (e) {} d.justification = ParagraphJustification.CENTER_JUSTIFY; d.tracking = tracking || 0;
        td.setValue(d); tr(l).property("ADBE Position").setValue(pos); return l;
    }
    function shapePath(c, name, verts, strokeColor, width, closed) {
        var l = c.layers.addShape(); l.name = name;
        var grp = l.property("ADBE Root Vectors Group").addProperty("ADBE Vector Group");
        var vecs = grp.property("ADBE Vectors Group");
        var pth = vecs.addProperty("ADBE Vector Shape - Group");
        var sh = new Shape(); sh.vertices = verts; sh.closed = !!closed; pth.property("ADBE Vector Shape").setValue(sh);
        var st = vecs.addProperty("ADBE Vector Graphic - Stroke");
        st.property("ADBE Vector Stroke Color").setValue(strokeColor); st.property("ADBE Vector Stroke Width").setValue(width);
        st.property("ADBE Vector Stroke Line Cap").setValue(2); st.property("ADBE Vector Stroke Line Join").setValue(2);
        var trim = l.property("ADBE Root Vectors Group").addProperty("ADBE Vector Filter - Trim");
        return { layer: l, trim: trim };
    }
    function glow(l, radius) { try { var g = l.property("ADBE Effect Parade").addProperty("ADBE Glo2"); g.property("ADBE Glo2-0003").setValue(radius || 30); } catch (e) {} }
    function solid(c, name, col) { return c.layers.addSolid(col, name, W, H, 1); }
    function fitScaleH(item) { return 100 * H / item.height; }

    // ============================================================ 01 METRO OPENING (0-5s)
    var c1 = comp("01_METRO_OPENING", 5.2);
    var lp = c1.layers.add(A.platform); lp.outPoint = 2.1;
    keys(tr(lp).property("ADBE Scale"), [[0, [180, 180]], [2.05, [205, 205]]]);
    keys(tr(lp).property("ADBE Anchor Point"), [[0, [400, 330]], [2.05, [420, 300]]]);
    tr(lp).property("ADBE Position").setValue([W / 2, H / 2]);
    keys(tr(lp).property("ADBE Opacity"), [[0, 0], [0.5, 100]]);
    var le = c1.layers.add(A.entrance); le.startTime = 0; le.inPoint = 1.9;
    keys(tr(le).property("ADBE Scale"), [[1.9, [275, 275]], [5.2, [190, 190]]]);
    keys(tr(le).property("ADBE Anchor Point"), [[1.9, [517, 560]], [5.2, [560, 640]]]);
    tr(le).property("ADBE Position").setValue([W / 2, H / 2]);
    keys(tr(le).property("ADBE Opacity"), [[1.9, 0], [2.15, 100]]);
    var t1 = textLayer(c1, "CIMIANO", 150, WHITE, "InterDisplay-Black", [W / 2 - 70, 470], 0);
    keys(tr(t1).property("ADBE Opacity"), [[2.5, 0], [3.1, 100], [4.9, 100], [5.2, 0]]);
    keys(tr(t1).property("ADBE Position"), [[2.5, [W / 2 - 70, 510]], [3.3, [W / 2 - 70, 470]]]);
    var t1b = textLayer(c1, "PARTENZA", 30, ORANGE, "Inter-Bold", [W / 2, 360], 450);
    t1b.parent = t1;
    var badge = c1.layers.addShape(); badge.name = "M2 badge";
    var bg = badge.property("ADBE Root Vectors Group").addProperty("ADBE Vector Group").property("ADBE Vectors Group");
    var rr = bg.addProperty("ADBE Vector Shape - Rect"); rr.property("ADBE Vector Rect Size").setValue([130, 124]); rr.property("ADBE Vector Rect Roundness").setValue(22);
    bg.addProperty("ADBE Vector Graphic - Fill").property("ADBE Vector Fill Color").setValue([0, 150 / 255, 64 / 255]);
    tr(badge).property("ADBE Position").setValue([890, 470]); badge.parent = t1;
    var t1c = textLayer(c1, "M2", 76, WHITE, "InterDisplay-Black", [890, 497], 0); t1c.parent = t1;
    var ul = shapePath(c1, "underline", [[230, 565], [850, 565]], ORANGE, 6);
    keys(ul.trim.property("ADBE Vector Trim End"), [[2.9, 0], [3.7, 100]]); ul.layer.parent = t1;

    // ============================================================ 02 STREET SEQUENCES (5-17s)
    var c2 = comp("02_STREET_SEQUENCES", 12);
    var s2bg = c2.layers.add(A.entrance2); tr(s2bg).property("ADBE Scale").setValue([460, 460]); tr(s2bg).property("ADBE Position").setValue([W / 2, H / 2]);
    try { s2bg.property("ADBE Effect Parade").addProperty("ADBE Gaussian Blur 2").property("ADBE Gaussian Blur 2-0001").setValue(60); } catch (e) {}
    s2bg.outPoint = 2.4;
    var card = c2.layers.add(A.entrance2); card.outPoint = 2.4; card.threeDLayer = true;
    keys(tr(card).property("ADBE Scale"), [[0, [205, 205, 205]], [1.7, [225, 225, 225]], [2.4, [1200, 1200, 1200]]]);
    keys(tr(card).property("ADBE Anchor Point"), [[1.7, [228, 225, 0]], [2.4, [228, 300, 0]]]);
    tr(card).property("ADBE Position").setValue([W / 2, H / 2 - 40, 0]);
    keys(tr(card).property("ADBE Y Rotation"), [[0, -6], [2.4, 4]]);
    var ex = textLayer(c2, "ESCI IN SUPERFICIE", 52, WHITE, "Inter-Black", [W / 2, 1360], 160);
    keys(tr(ex).property("ADBE Opacity"), [[0.3, 0], [0.7, 100], [1.9, 100], [2.2, 0]]);
    // --- AI clip slots: drop generated clips (see 03_ai_prompts) onto these placeholders, Alt-drag to replace.
    var slots = [["AI_S02_exit_stairs (replace)", 2.2, 2.8], ["AI_S03a_residential_zona30 (replace)", 5.0, 3.2], ["AI_S03b_park_fence (replace)", 8.2, 1.8], ["AI_S03c_trafficlight_ViaPadova (replace)", 10.0, 2.0]];
    for (var i = 0; i < slots.length; i++) {
        var sl = solid(c2, slots[i][0], [0.07, 0.07, 0.08]); sl.startTime = 0; sl.inPoint = slots[i][1]; sl.outPoint = slots[i][1] + slots[i][2];
        sl.guideLayer = false; sl.label = 11;
    }
    if (plate) { // programmatic 3D street plate from the master render as a stand-in
        var pl = c2.layers.add(plate); pl.startTime = -5; pl.inPoint = 2.2; pl.outPoint = 12; pl.moveToEnd(); pl.name = "PLATE_programmatic_street (stand-in)";
    }
    var cards = [["1  Esci dalla metro", "Cimiano · Linea M2", 2.6, 5.3], ["2  Strade residenziali", "Zona 30 · lungo il parco", 5.5, 8.4], ["3  Al semaforo: Via Padova", "Prosegui fino al numero 167", 8.6, 11.6]];
    for (var k = 0; k < cards.length; k++) {
        var ct = textLayer(c2, cards[k][0] + "\r" + cards[k][1], 46, WHITE, "Inter-Bold", [W / 2, 290], 0);
        ct.inPoint = cards[k][2]; ct.outPoint = cards[k][3];
        keys(tr(ct).property("ADBE Position"), [[cards[k][2], [W / 2 - 80, 290]], [cards[k][2] + 0.6, [W / 2, 290]]]);
        keys(tr(ct).property("ADBE Opacity"), [[cards[k][2], 0], [cards[k][2] + 0.45, 100], [cards[k][3] - 0.35, 100], [cards[k][3], 0]]);
    }

    // ============================================================ 04 ROUTE ANIMATION (nested in map)
    var MS = 2400;
    var c4 = proj.items.addComp("04_ROUTE_ANIMATION", MS, MS, 1, 5.5, FPS); c4.parentFolder = fPre;
    // Schematic geometry (NOT to scale). Replace vertices with projected real coordinates when a
    // verified route export (GPX/GeoJSON) is available – see 01_analysis/route_analysis.md.
    var vp = shapePath(c4, "VIA PADOVA (schematic axis)", [[250, 1990], [900, 1500], [1640, 860], [2250, 330]], [0.47, 0.48, 0.52], 44);
    var m2 = shapePath(c4, "M2 (schematic)", [[150, 2250], [560, 1560], [820, 1050], [1000, 300]], [0, 0.59, 0.25], 16);
    var rt = shapePath(c4, "ROUTE Cimiano -> Via Padova 167", [[560, 1560], [820, 1560], [1150, 1330], [1420, 1060], [1640, 860]], ORANGE, 30);
    keys(rt.trim.property("ADBE Vector Trim End"), [[0.6, 0], [3.6, 100]]);
    glow(rt.layer, 40);
    var dash = shapePath(c4, "ROUTE arrows (dashes)", [[560, 1560], [820, 1560], [1150, 1330], [1420, 1060], [1640, 860]], [1, 0.92, 0.82], 8);
    try {
        var stG = dash.layer.property("ADBE Root Vectors Group").property(1).property("ADBE Vectors Group").property(2);
        var ds = stG.property("ADBE Vector Stroke Dashes"); ds.addProperty("ADBE Vector Stroke Dash 1").setValue(20); ds.addProperty("ADBE Vector Stroke Gap 1").setValue(60);
        ds.addProperty("ADBE Vector Stroke Offset").expression = "-time*240";
    } catch (e) {}
    dash.trim.property("ADBE Vector Trim End").expression = 'thisComp.layer("ROUTE Cimiano -> Via Padova 167").content("ADBE Vector Filter - Trim").end';

    // ============================================================ 03 GPS MAP (17-22s)
    var c3 = comp("03_GPS_MAP", 5.5);
    var mbg = solid(c3, "map ground", [13 / 255, 14 / 255, 17 / 255]);
    var mapL = c3.layers.add(c4); mapL.threeDLayer = true; mapL.name = "MAP PLANE (3D)";
    tr(mapL).property("ADBE Position").setValue([W / 2, H / 2, 0]);
    keys(tr(mapL).property("ADBE Orientation"), [[0, [0, 0, 352]], [5.5, [0, 0, 374]]]);
    keys(tr(mapL).property("ADBE X Rotation"), [[0, 0], [1.5, -52], [3.7, -52], [5.3, -24]]);
    keys(tr(mapL).property("ADBE Anchor Point"), [[0, [560, 1560, 0]], [3.9, [1420, 1060, 0]], [5.3, [1640, 860, 0]]]);
    keys(tr(mapL).property("ADBE Scale"), [[0, [70, 70, 70]], [3.7, [90, 90, 90]], [5.3, [180, 180, 180]]]);
    var cam = c3.layers.addCamera("MAP CAMERA", [W / 2, H / 2]);
    cam.property("ADBE Camera Options Group").property("ADBE Camera Zoom").setValue(1600);
    var ctrl = c3.layers.addNull(); ctrl.name = "CTRL camera drift"; ctrl.threeDLayer = true; cam.parent = ctrl;
    keys(tr(ctrl).property("ADBE Position"), [[0, [W / 2, H / 2, 0]], [5.5, [W / 2, H / 2 - 60, 120]]]);
    var lc = textLayer(c3, "CIMIANO\rM2", 40, WHITE, "Inter-Black", [700, 1040], 0);
    var ld = textLayer(c3, "PUNTOCOM\rVIA PADOVA 167", 40, WHITE, "Inter-Black", [720, 640], 0);
    keys(tr(ld).property("ADBE Opacity"), [[3.4, 0], [4.0, 100]]);
    var pin = c3.layers.addShape(); pin.name = "DESTINATION PIN";
    var pg = pin.property("ADBE Root Vectors Group").addProperty("ADBE Vector Group").property("ADBE Vectors Group");
    var pe = pg.addProperty("ADBE Vector Shape - Ellipse"); pe.property("ADBE Vector Ellipse Size").setValue([70, 70]);
    pg.addProperty("ADBE Vector Graphic - Fill").property("ADBE Vector Fill Color").setValue(ORANGE);
    tr(pin).property("ADBE Position").setValue([W / 2, 760]);
    keys(tr(pin).property("ADBE Scale"), [[3.4, [0, 0]], [3.9, [115, 115]], [4.1, [100, 100]]]);
    var disc = textLayer(c3, "Schema indicativo · non in scala", 24, [0.6, 0.6, 0.6], "Inter-Medium", [W / 2, 1820], 0);

    // ============================================================ 05 STOREFRONT (22-29s)
    var c5 = comp("05_STOREFRONT", 7);
    var sbg = c5.layers.add(A.store); sbg.name = "PARALLAX PLATE (blurred copy)";
    try { sbg.property("ADBE Effect Parade").addProperty("ADBE Gaussian Blur 2").property("ADBE Gaussian Blur 2-0001").setValue(80); } catch (e) {}
    keys(tr(sbg).property("ADBE Scale"), [[0, [235, 235]], [7, [300, 300]]]);
    keys(tr(sbg).property("ADBE Opacity"), [[0, 55]]);
    var sf = c5.layers.add(A.store); sf.name = "STOREFRONT – ORIGINAL (do not modify)";
    // push-in: from full facade to the CAF-PATRONATO entrance
    keys(tr(sf).property("ADBE Scale"), [[0, [47, 47]], [7, [80, 80]]]);
    keys(tr(sf).property("ADBE Anchor Point"), [[0, [1178, 800]], [7, [1660, 830]]]);
    keys(tr(sbg).property("ADBE Anchor Point"), [[0, [1178, 800]], [7, [1660, 830]]]);
    tr(sf).property("ADBE Position").setValue([W / 2, H / 2]); tr(sbg).property("ADBE Position").setValue([W / 2, H / 2]);
    // GPS line parented to the photo so it tracks the push-in exactly (image-pixel coordinates).
    var gps = shapePath(c5, "GPS LINE -> entrance", [[980, 1660], [1240, 1610], [1480, 1560], [1726, 1505]], ORANGE, 20);
    gps.layer.parent = sf; tr(gps.layer).property("ADBE Position").setValue([0, 0]); tr(gps.layer).property("ADBE Anchor Point").setValue([0, 0]);
    keys(gps.trim.property("ADBE Vector Trim End"), [[0.9, 0], [3.0, 100]]); glow(gps.layer, 30);
    var arr = textLayer(c5, "SEI ARRIVATO\rPUNTOCOM · VIA PADOVA 167", 40, WHITE, "Inter-Black", [W / 2, 215], 0);
    keys(tr(arr).property("ADBE Opacity"), [[2.6, 0], [3.2, 100], [6.4, 100], [6.9, 0]]);
    var chips = textLayer(c5, "CAF   ·   PATRONATO   ·   IMMIGRAZIONE   ·   CONTABILITÀ", 27, WHITE, "Inter-Bold", [W / 2, 1835], 0);
    keys(tr(chips).property("ADBE Opacity"), [[3.9, 0], [4.6, 100], [6.4, 100], [6.9, 0]]);
    var sweep = solid(c5, "light sweep (Add)", [0.27, 0.18, 0.08]); sweep.blendingMode = BlendingMode.ADD;
    var sm = sweep.property("ADBE Mask Parade").addProperty("ADBE Mask Atom");
    var ms = new Shape(); ms.vertices = [[-90, 0], [90, 0], [-190, H], [-370, H]]; ms.closed = true; sm.property("ADBE Mask Shape").setValue(ms);
    sm.property("ADBE Mask Feather").setValue([140, 140]);
    keys(tr(sweep).property("ADBE Position"), [[1.2, [-500 + W / 2, H / 2]], [3.6, [W + 500 + W / 2, H / 2]]]);

    // ============================================================ 06 LOGO REVEAL (29-35s)
    var c6 = comp("06_LOGO_REVEAL", 6.1);
    var nv = solid(c6, "NAVY background", NAVY);
    try { var rg = nv.property("ADBE Effect Parade").addProperty("ADBE Ramp"); rg.property("ADBE Ramp-0005").setValue(2);
          rg.property("ADBE Ramp-0002").setValue([22 / 255, 36 / 255, 54 / 255, 1]); rg.property("ADBE Ramp-0004").setValue([5 / 255, 12 / 255, 18 / 255, 1]);
          rg.property("ADBE Ramp-0001").setValue([W / 2, 800]); rg.property("ADBE Ramp-0003").setValue([W, H]); } catch (e) {}
    var gsw = solid(c6, "GOLD light sweep (Add)", GOLD); gsw.blendingMode = BlendingMode.ADD;
    var gm = gsw.property("ADBE Mask Parade").addProperty("ADBE Mask Atom");
    var gs = new Shape(); gs.vertices = [[-60, 0], [60, 0], [-260, H], [-380, H]]; gs.closed = true; gm.property("ADBE Mask Shape").setValue(gs);
    gm.property("ADBE Mask Feather").setValue([160, 160]);
    keys(tr(gsw).property("ADBE Position"), [[-0.2, [-600 + W / 2, H / 2]], [1.2, [W + 600 + W / 2, H / 2]]]);
    keys(tr(gsw).property("ADBE Opacity"), [[0, 60]]);
    var LS = 145, LY = 800;
    var sym = c6.layers.add(A.logoSym); sym.name = "LOGO symbol (original)";
    tr(sym).property("ADBE Position").setValue([W / 2, LY]);
    keys(tr(sym).property("ADBE Scale"), [[0.6, [LS * 0.9, LS * 0.9]], [1.8, [LS, LS]]]);
    keys(tr(sym).property("ADBE Opacity"), [[0.6, 0], [1.6, 100]]);
    try { var gb = sym.property("ADBE Effect Parade").addProperty("ADBE Gaussian Blur 2"); keys(gb.property("ADBE Gaussian Blur 2-0001"), [[0.6, 20], [1.8, 0]]); } catch (e) {}
    var wm = c6.layers.add(A.logoWord); wm.name = "LOGO wordmark (original)";
    tr(wm).property("ADBE Position").setValue([W / 2, LY]); tr(wm).property("ADBE Scale").setValue([LS, LS]);
    var wmk = wm.property("ADBE Mask Parade").addProperty("ADBE Mask Atom"); wmk.property("ADBE Mask Feather").setValue([60, 0]);
    var w0 = new Shape(); w0.vertices = [[0, 0], [0, 0], [0, 620], [0, 620]]; w0.closed = true;
    var w1 = new Shape(); w1.vertices = [[0, 0], [1004, 0], [1004, 620], [0, 620]]; w1.closed = true;
    wmk.property("ADBE Mask Shape").setValueAtTime(1.6, w0); wmk.property("ADBE Mask Shape").setValueAtTime(2.6, w1);
    var sb = c6.layers.add(A.logoSub); sb.name = "LOGO CAF PATRONATO (original)";
    tr(sb).property("ADBE Position").setValue([W / 2, LY]); tr(sb).property("ADBE Scale").setValue([LS, LS]);
    keys(tr(sb).property("ADBE Opacity"), [[2.4, 0], [3.3, 100]]);
    var ad = textLayer(c6, "Via Padova 167 – Milano", 46, WHITE, "Inter-Medium", [W / 2, 1316], 30);
    keys(tr(ad).property("ADBE Opacity"), [[3.3, 0], [4.1, 100]]);
    var cl = textLayer(c6, "Siamo qui per aiutarti!", 62, GOLD, "InterDisplay-SemiBold", [W / 2, 1426], 0);
    keys(tr(cl).property("ADBE Opacity"), [[3.9, 0], [4.8, 100]]);

    // ============================================================ 07 FINAL / MAIN
    var fFinal = proj.items.addFolder("_FINAL");
    var main = comp("00_MAIN_1080x1920", DUR, fFinal);
    function put(c, start, name) { var l = main.layers.add(c); l.startTime = start; if (name) l.name = name; return l; }
    var L6 = put(c6, 28.9, "S06 BRAND REVEAL");
    var L5 = put(c5, 21.9, "S05 ARRIVAL"); L5.outPoint = 29.0;
    var L3 = put(c3, 16.9, "S04 GPS MAP"); L3.outPoint = 22.4;
    var L2 = put(c2, 4.9, "S02-S03 STREET"); L2.outPoint = 17.1;
    var L1 = put(c1, 0, "S01 CIMIANO M2"); L1.outPoint = 5.0;
    // transitions: short cross-dissolves on overlaps (refine with the agency's own transitions)
    var ov = [[L2, 4.9, 5.1], [L3, 16.9, 17.3], [L5, 21.9, 22.5], [L6, 28.9, 29.3]];
    for (var q = 0; q < ov.length; q++) keys(tr(ov[q][0]).property("ADBE Opacity"), [[ov[q][1], 0], [ov[q][2], 100]]);
    var adj = main.layers.addSolid([1, 1, 1], "GRADE (adjustment)", W, H, 1); adj.adjustmentLayer = true;
    try { adj.property("ADBE Effect Parade").addProperty("ADBE CurvesCustom"); adj.property("ADBE Effect Parade").addProperty("ADBE Lumetri"); } catch (e) {}
    var rail = shapePath(main, "PROGRESS RAIL", [[60, 94], [W - 60, 94]], ORANGE, 4);
    keys(rail.trim.property("ADBE Vector Trim End"), [[0.4, 0], [28.6, 100]]); rail.layer.outPoint = 29.2;
    var subs = [["Sei alla fermata Cimiano della linea M2?", 0.6, 4.95], ["Raggiungerci è semplicissimo!", 5.25, 9.8],
                ["Segui il percorso verso Via Padova…", 10.2, 16.6], ["…e troverai Puntocom al numero 167.", 17.3, 21.9],
                ["CAF, Patronato e tanti servizi per te.", 23.0, 28.6]];
    for (var s = 0; s < subs.length; s++) {
        var st = textLayer(main, subs[s][0], 44, WHITE, "Inter-SemiBold", [W / 2, s === 4 ? 1715 : 1640], 0);
        st.inPoint = subs[s][1]; st.outPoint = subs[s][2]; st.name = "SUB " + (s + 1);
    }
    var au = main.layers.add(A.mix); au.name = "MIX (music+sfx[+VO])";
    if (plate) { var ref = main.layers.add(plate); ref.name = "REFERENCE master render (guide)"; ref.guideLayer = true; ref.enabled = false; ref.moveToEnd(); }

    // ------------------------------------------------------------ render queue + save
    var rq = proj.renderQueue.items.add(main);
    try { rq.outputModule(1).applyTemplate("H.264 - Match Render Settings - 15 Mbps"); } catch (e) {}
    try { rq.outputModule(1).file = new File(root.fsName + "/08_render/PUNTOCOM_TheWayToUs_AE.mp4"); } catch (e) {}
    main.openInViewer();
    app.endUndoGroup();
    var out = new File(root.fsName + "/05_aftereffects/PUNTOCOM_TheWayToUs.aep");
    proj.save(out);
    alert("PUNTOCOM project built and saved:\n" + out.fsName + "\n\nReplace the AI_* placeholder solids with generated clips (03_ai_prompts).");
})();
