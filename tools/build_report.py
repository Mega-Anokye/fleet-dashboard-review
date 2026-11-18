"""Rebuild the Fleet Management report pages (PBIR format) from scratch."""
import json, os, shutil, hashlib, sys

REPORT = sys.argv[1]  # path to "...Report" folder
DEF = os.path.join(REPORT, "definition")
PAGES = os.path.join(DEF, "pages")

VC_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.13.0/schema.json"
PAGE_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json"

# ---------- palette ----------
NAVY = "#1F3A5F"; BLUE = "#2F6EBA"; ORANGE = "#E8833A"; RED = "#C8553D"
GREY = "#9AA5B1"; TEXT = "#1F2937"; MUTED = "#6B7280"; BG = "#F3F5F8"
BORDER = "#E3E8EF"; WHITE = "#FFFFFF"; INSIGHT_BG = "#FFF6EE"; GREEN = "#3C8D5A"

M = "_Measures_"

# ---------- tiny helpers ----------
def lit(v): return {"expr": {"Literal": {"Value": v}}}
def s(v): return lit("'" + v.replace("'", "''") + "'")
def b(v): return lit("true" if v else "false")
def d(v): return lit(f"{v}D")
def l(v): return lit(f"{v}L")
def color(h): return {"solid": {"color": lit("'" + h + "'")}}
def props(**kw): return [{"properties": kw}]

def col(entity, prop): return {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}
def meas(prop, entity=M): return {"Measure": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}

def proj(field, name=None, active=None):
    kind = "Column" if "Column" in field else "Measure"
    ent = field[kind]["Expression"]["SourceRef"]["Entity"]; prop = field[kind]["Property"]
    p = {"field": field, "queryRef": f"{ent}.{prop}", "nativeQueryRef": prop}
    if name: p["displayName"] = name
    if active: p["active"] = True
    return p

_ids = set()
def vid(page, key):
    h = hashlib.md5(f"{page}:{key}".encode()).hexdigest()[:20]
    assert h not in _ids; _ids.add(h); return h

def container(title=None, bg=WHITE, border=True, title_size=15, pad=True):
    o = {
        "background": props(show=b(True), color=color(bg), transparency=d(0)),
        "border": props(show=b(border), color=color(BORDER), radius=d(10)),
        "dropShadow": props(show=b(False)),
    }
    if title:
        o["title"] = props(show=b(True), text=s(title), fontSize=d(title_size), fontColor=color(TEXT),
                           bold=b(True), alignment=s("left"), titleWrap=b(True))
    else:
        o["title"] = props(show=b(False))
    o["subTitle"] = props(show=b(False))
    if pad:
        o["padding"] = props(top=d(10), bottom=d(8), left=d(14), right=d(14))
    return o

def vc(page, key, x, y, w, h, z, visual, filters=None):
    v = {"$schema": VC_SCHEMA, "name": vid(page, key),
         "position": {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z},
         "visual": visual}
    if filters: v["filterConfig"] = {"filters": filters}
    return v

def topn_filter(entity, column, measure, n, descending=True):
    return {
        "name": hashlib.md5(f"{entity}{column}{measure}{n}{descending}".encode()).hexdigest()[:20],
        "field": col(entity, column), "type": "TopN",
        "filter": {"Version": 2, "From": [
            {"Name": "subquery", "Expression": {"Subquery": {"Query": {"Version": 2,
                "From": [{"Name": "d", "Entity": entity, "Type": 0}, {"Name": "_", "Entity": M, "Type": 0}],
                "Select": [{"Column": {"Expression": {"SourceRef": {"Source": "d"}}, "Property": column}, "Name": "field"}],
                "OrderBy": [{"Direction": 2 if descending else 1,
                             "Expression": {"Measure": {"Expression": {"SourceRef": {"Source": "_"}}, "Property": measure}}}],
                "Top": n}}}, "Type": 2},
            {"Name": "d", "Entity": entity, "Type": 0}],
            "Where": [{"Condition": {"In": {"Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "d"}}, "Property": column}}],
                                             "Table": {"SourceRef": {"Source": "subquery"}}}}}]}}

def measure_gt_filter(measure, value):
    return {"name": hashlib.md5(f"gt{measure}{value}".encode()).hexdigest()[:20],
            "field": meas(measure), "type": "Advanced",
            "filter": {"Version": 2, "From": [{"Name": "_", "Entity": M, "Type": 0}],
                       "Where": [{"Condition": {"Comparison": {"ComparisonKind": 1,
                           "Left": {"Measure": {"Expression": {"SourceRef": {"Source": "_"}}, "Property": measure}},
                           "Right": {"Literal": {"Value": f"{value}L"}}}}}]}}

def sort_def(field, desc=True):
    return {"sort": [{"field": field, "direction": "Descending" if desc else "Ascending"}]}

AXIS = dict(fontSize=d(12), labelColor=color(MUTED), showAxisTitle=b(False))

# ---------- visual builders ----------
def header(page, title, subtitle):
    vis = {"visualType": "textbox",
           "objects": {"general": props(paragraphs=None)},
           "visualContainerObjects": container(None, bg=NAVY, border=False)}
    vis["objects"]["general"] = [{"properties": {"paragraphs": [
        {"textRuns": [{"value": title, "textStyle": {"fontWeight": "bold", "fontSize": "24pt", "color": WHITE}}]},
        {"textRuns": [{"value": subtitle, "textStyle": {"fontSize": "12pt", "color": "#C9D6E8"}}]}]}}]
    vis["visualContainerObjects"]["border"] = props(show=b(False), radius=d(0))
    vis["visualContainerObjects"]["padding"] = props(top=d(12), bottom=d(8), left=d(24), right=d(24))
    return vc(page, "header", 0, 0, 1920, 96, 0, vis)

def card(page, key, x, y, w, h, z, measure, label, units=1, precision=0, value_color=NAVY, size=30):
    vis = {"visualType": "card",
           "query": {"queryState": {"Values": {"projections": [proj(meas(measure), label)]}}},
           "objects": {
               "labels": props(color=color(value_color), fontSize=d(size), labelDisplayUnits=d(units),
                               labelPrecision=l(precision), bold=b(True)),
               "categoryLabels": props(show=b(True), color=color(MUTED), fontSize=d(13)),
               "wordWrap": props(show=b(True))},
           "visualContainerObjects": container(None),
           "drillFilterOtherVisuals": True}
    return vc(page, key, x, y, w, h, z, vis)

def insight(page, key, x, y, w, h, z, measure):
    vis = {"visualType": "card",
           "query": {"queryState": {"Values": {"projections": [proj(meas(measure), "Key insight")]}}},
           "objects": {
               "labels": props(color=color(TEXT), fontSize=d(14), bold=b(False)),
               "categoryLabels": props(show=b(False)),
               "wordWrap": props(show=b(True))},
           "visualContainerObjects": container(None, bg=INSIGHT_BG),
           "drillFilterOtherVisuals": True}
    vis["visualContainerObjects"]["border"] = props(show=b(True), color=color(ORANGE), radius=d(10))
    return vc(page, key, x, y, w, h, z, vis)

def date_slicer(page, x, y, w, h, z):
    vis = {"visualType": "slicer",
           "query": {"queryState": {"Values": {"projections": [proj(col("DimDate", "Date"), "Date range", True)]}}},
           "objects": {
               "data": props(mode=s("Between")),
               "header": props(show=b(True), text=s("Date range"), textSize=d(11), fontColor=color(MUTED)),
               "date": props(textSize=d(11), fontColor=color(TEXT)),
               "slider": props(show=b(True), color=color(BLUE))},
           "visualContainerObjects": container(None, pad=False),
           "syncGroup": {"groupName": "DateRange", "fieldChanges": True, "filterChanges": True},
           "drillFilterOtherVisuals": True}
    vis["visualContainerObjects"]["padding"] = props(top=d(4), bottom=d(4), left=d(10), right=d(10))
    return vc(page, "dateslicer", x, y, w, h, z, vis)

def dropdown(page, key, x, y, w, h, z, entity, column, label, sync):
    vis = {"visualType": "slicer",
           "query": {"queryState": {"Values": {"projections": [proj(col(entity, column), label, True)]}}},
           "objects": {
               "data": props(mode=s("Dropdown")),
               "header": props(show=b(True), text=s(label), textSize=d(11), fontColor=color(MUTED)),
               "items": props(textSize=d(12), fontColor=color(TEXT)),
               "selection": props(selectAllCheckboxEnabled=b(True))},
           "visualContainerObjects": container(None, pad=False),
           "syncGroup": {"groupName": sync, "fieldChanges": True, "filterChanges": True},
           "drillFilterOtherVisuals": True}
    vis["visualContainerObjects"]["padding"] = props(top=d(4), bottom=d(4), left=d(10), right=d(10))
    return vc(page, key, x, y, w, h, z, vis)

def bar(page, key, x, y, w, h, z, title, cat, measure, fill=BLUE, n=10, desc=True, precision=None, units=None, cat_name=None, measure_name=None):
    cat_entity = cat[0]; cat_col = cat[1]
    vis = {"visualType": "clusteredBarChart",
           "query": {"queryState": {
               "Category": {"projections": [proj(col(cat_entity, cat_col), cat_name, True)]},
               "Y": {"projections": [proj(meas(measure), measure_name)]}},
               "sortDefinition": sort_def(meas(measure), desc)},
           "objects": {
               "dataPoint": props(fill=color(fill)),
               "labels": props(show=b(True), fontSize=d(12), color=color(TEXT),
                               **({"labelPrecision": l(precision)} if precision is not None else {}),
                               **({"labelDisplayUnits": d(units)} if units is not None else {})),
               "categoryAxis": props(**AXIS),
               "valueAxis": props(show=b(False), gridlineShow=b(False))},
           "visualContainerObjects": container(title),
           "drillFilterOtherVisuals": True}
    filters = [topn_filter(cat_entity, cat_col, measure, n, desc)] if n else None
    return vc(page, key, x, y, w, h, z, vis, filters)

def stacked(page, key, x, y, w, h, z, title, visual_type, cat, measures, colors, topn=None, series=None, series_colors=None, sort_measure=None, units=None):
    qs = {"Category": {"projections": [proj(col(*cat), None, True)]},
          "Y": {"projections": [proj(meas(m), nm) for m, nm in measures]}}
    if series:
        qs["Series"] = {"projections": [proj(col(*series))]}
    if sort_measure:
        qs["Tooltips"] = {"projections": [proj(meas(sort_measure), "Total")]}
    dp = []
    for (m, _), c in zip(measures, colors):
        if not series:
            dp.append({"properties": {"fill": color(c)}, "selector": {"metadata": f"{M}.{m}"}})
    if series:
        for val, c in series_colors:
            dp.append({"properties": {"fill": color(c)}, "selector": {"data": [{"scopeId": {"Comparison": {
                "ComparisonKind": 0, "Left": col(*series), "Right": {"Literal": {"Value": f"'{val}'"}}}}}]}})
    query = {"queryState": qs}
    if sort_measure:
        query["sortDefinition"] = sort_def(meas(sort_measure), True)
    else:
        query["sortDefinition"] = {"sort": [{"field": col(*cat), "direction": "Ascending"}]}
    objs = {"dataPoint": dp,
            "legend": props(show=b(True), position=s("Top"), fontSize=d(12), labelColor=color(MUTED)),
            "categoryAxis": props(**AXIS),
            "valueAxis": props(show=b(True), fontSize=d(12), labelColor=color(MUTED), showAxisTitle=b(False),
                               gridlineColor=color("#EEF1F5"), **({"labelDisplayUnits": d(units)} if units else {})),
            "labels": props(show=b(False))}
    if visual_type == "barChart":
        objs["labels"] = props(show=b(False))
        objs["totals"] = props(show=b(True), fontSize=d(12), color=color(TEXT))
        objs["valueAxis"] = props(show=b(False), gridlineShow=b(False))
    vis = {"visualType": visual_type, "query": query, "objects": objs,
           "visualContainerObjects": container(title), "drillFilterOtherVisuals": True}
    filters = [topn_filter(cat[0], cat[1], topn[0], topn[1], True)] if topn else None
    return vc(page, key, x, y, w, h, z, vis, filters)

def line(page, key, x, y, w, h, z, title, measure, stroke=BLUE, units=None):
    vis = {"visualType": "lineChart",
           "query": {"queryState": {
               "Category": {"projections": [proj(col("DimDate", "Month Year"), None, True)]},
               "Y": {"projections": [proj(meas(measure))]}},
               "sortDefinition": {"sort": [{"field": col("DimDate", "Month Year"), "direction": "Ascending"}]}},
           "objects": {
               "dataPoint": props(fill=color(stroke)),
               "lineStyles": props(strokeWidth=d(3), showMarker=b(True), markerSize=d(5)),
               "legend": props(show=b(False)),
               "categoryAxis": props(**AXIS),
               "valueAxis": props(show=b(True), fontSize=d(12), labelColor=color(MUTED), showAxisTitle=b(False),
                                  gridlineColor=color("#EEF1F5"), start=d(0), **({"labelDisplayUnits": d(units)} if units else {})),
               "labels": props(show=b(False))},
           "visualContainerObjects": container(title), "drillFilterOtherVisuals": True}
    return vc(page, key, x, y, w, h, z, vis)

def column_priority(page, key, x, y, w, h, z, title):
    pcol = ("Maintenance", "Priority Clean")
    dp = [{"properties": {"fill": color(GREY)}}]
    for val, c in [("High", ORANGE), ("Critical", RED)]:
        dp.append({"properties": {"fill": color(c)}, "selector": {"data": [{"scopeId": {"Comparison": {
            "ComparisonKind": 0, "Left": col(*pcol), "Right": {"Literal": {"Value": f"'{val}'"}}}}}]}})
    vis = {"visualType": "clusteredColumnChart",
           "query": {"queryState": {
               "Category": {"projections": [proj(col(*pcol), "Priority", True)]},
               "Y": {"projections": [proj(meas("Total Maintenance Jobs"), "Jobs")]}},
               "sortDefinition": {"sort": [{"field": col(*pcol), "direction": "Ascending"}]}},
           "objects": {"dataPoint": dp,
                       "labels": props(show=b(True), fontSize=d(13), color=color(TEXT)),
                       "categoryAxis": props(**AXIS),
                       "valueAxis": props(show=b(False), gridlineShow=b(False))},
           "visualContainerObjects": container(title), "drillFilterOtherVisuals": True}
    return vc(page, key, x, y, w, h, z, vis)

def scatter(page, key, x, y, w, h, z, title, xm, ym, xname, yname, fill=BLUE):
    vis = {"visualType": "scatterChart",
           "query": {"queryState": {
               "Category": {"projections": [proj(col("DimTruck", "Truck ID"), "Truck", True)]},
               "X": {"projections": [proj(meas(xm), xname)]},
               "Y": {"projections": [proj(meas(ym), yname)]}}},
           "objects": {
               "dataPoint": props(fill=color(fill)),
               "markers": props(markerSize=d(6)) if False else props(),
               "categoryLabels": props(show=b(False)),
               "categoryAxis": props(fontSize=d(12), labelColor=color(MUTED), showAxisTitle=b(True), titleFontSize=d(12), titleColor=color(MUTED)),
               "valueAxis": props(fontSize=d(12), labelColor=color(MUTED), showAxisTitle=b(True), titleFontSize=d(12), titleColor=color(MUTED), gridlineColor=color("#EEF1F5"))},
           "visualContainerObjects": container(title), "drillFilterOtherVisuals": True}
    del vis["objects"]["markers"]
    return vc(page, key, x, y, w, h, z, vis)

def table(page, key, x, y, w, h, z, title, fields, sort_field, desc=False, filters=None, widths=None):
    vis = {"visualType": "tableEx",
           "query": {"queryState": {"Values": {"projections": [proj(f, nm) for f, nm in fields]}},
                     "sortDefinition": sort_def(sort_field, desc)},
           "objects": {
               "columnHeaders": props(fontSize=d(12), fontColor=color(WHITE), backColor=color(NAVY), bold=b(True), wordWrap=b(True)),
               "values": props(fontSize=d(12), fontColorPrimary=color(TEXT), backColorPrimary=color(WHITE),
                               fontColorSecondary=color(TEXT), backColorSecondary=color("#F5F7FA")),
               "total": props(totals=b(False)),
               "grid": props(gridHorizontal=b(True), gridHorizontalColor=color(BORDER), rowPadding=d(4))},
           "visualContainerObjects": container(title), "drillFilterOtherVisuals": True}
    if widths:
        cw = []
        for (f, _), wd in zip(fields, widths):
            p_ = proj(f)
            cw.append({"properties": {"value": d(wd)}, "selector": {"metadata": p_["queryRef"]}})
        vis["objects"]["columnWidth"] = cw
    return vc(page, key, x, y, w, h, z, vis, filters)

def note(page, key, x, y, w, h, z, paragraphs):
    pars = []
    for p in paragraphs:
        if isinstance(p, tuple):
            txt, style = p
        else:
            txt, style = p, {}
        st = {"fontSize": "16pt", "color": TEXT}; st.update(style)
        pars.append({"textRuns": [{"value": txt, "textStyle": st}]})
    vis = {"visualType": "textbox", "objects": {"general": [{"properties": {"paragraphs": pars}}]},
           "visualContainerObjects": container(None)}
    vis["visualContainerObjects"]["padding"] = props(top=d(14), bottom=d(14), left=d(20), right=d(20))
    return vc(page, key, x, y, w, h, z, vis)

# ---------- layout constants ----------
KPI_Y, KPI_H = 112, 112
INS_Y, INS_H = 238, 62
A_Y, A_H = 316, 360
B_Y, B_H = 692, 364
def kpi_x(i, n=6):
    w = (1872 - (n - 1) * 16) / n
    return 24 + i * (w + 16), w

def kpis(page, items):
    out = []
    for i, it in enumerate(items):
        x, w = kpi_x(i, len(items))
        measure, label, units, prec = it[:4]
        clr = it[4] if len(it) > 4 else NAVY
        out.append(card(page, f"kpi{i}", x, KPI_Y, w, KPI_H, 1000 + i, measure, label, units, prec, clr))
    return out

def filters_bar(page, truck=True, driver=False):
    out = []
    if truck:
        out.append(date_slicer(page, 1150, 12, 470, 72, 100))
        out.append(dropdown(page, "truckslicer", 1636, 12, 260, 72, 101, "DimTruck", "Truck ID", "Truck", "Truck"))
    if driver:
        out.append(dropdown(page, "driverslicer", 1576, 12, 320, 72, 101, "DimDriver", "Driver Name", "Driver", "Driver"))
    return out

PERIOD = "Jul 2024 – Jun 2026  ·  50 trucks  ·  all costs in USD"

# ---------- pages ----------
pages = []

# 1. Overview
p = "p1overview"
v = [header(p, "Fleet Overview", "Where the money goes and which trucks drive it  ·  " + PERIOD)]
v += filters_bar(p)
v += kpis(p, [
    ("Total Operating Cost", "Operating cost", 1000000, 2),
    ("Total Fuel Cost", "Fuel cost", 1000000, 2, BLUE),
    ("Total Maintenance Cost", "Maintenance cost", 1000, 0, ORANGE),
    ("Fuel Share of Operating Cost", "Fuel share of cost", 1, 1),
    ("Operating Cost per KM", "Operating cost per km", 1, 3),
    ("Total Distance", "Distance driven (km)", 1000000, 2),
])
v.append(insight(p, "insight", 24, INS_Y, 1872, INS_H, 1100, "Insight - Overview"))
v.append(stacked(p, "monthly", 24, A_Y, 1100, A_H, 2000, "Monthly operating cost: fuel vs maintenance",
                 "columnChart", ("DimDate", "Month Year"),
                 [("Total Fuel Cost", "Fuel"), ("Total Maintenance Cost", "Maintenance")], [BLUE, ORANGE], units=1000))
v.append(bar(p, "costkm", 1140, A_Y, 756, A_H, 2001, "10 trucks with the highest operating cost per km",
             ("DimTruck", "Truck ID"), "Operating Cost per KM", fill=RED, precision=3, measure_name="Cost per km"))
v.append(stacked(p, "toptrucks", 24, B_Y, 1100, B_H, 2002, "10 trucks with the highest operating cost",
                 "barChart", ("DimTruck", "Truck ID"),
                 [("Total Fuel Cost", "Fuel"), ("Total Maintenance Cost", "Maintenance")], [BLUE, ORANGE],
                 topn=("Total Operating Cost", 10), sort_measure="Total Operating Cost", units=1000))
v.append(scatter(p, "scatter", 1140, B_Y, 756, B_H, 2003, "Fuel efficiency vs maintenance cost (each dot = a truck)",
                 "Average Fuel Efficiency", "Total Maintenance Cost", "Fuel efficiency (km/L)", "Maintenance cost"))
pages.append((p, "Fleet Overview", v))

# 2. Fuel
p = "p2fuel"
v = [header(p, "Fuel", "Consumption, efficiency and fuel-record checks  ·  " + PERIOD)]
v += filters_bar(p)
v += kpis(p, [
    ("Total Fuel Cost", "Fuel cost", 1000000, 2, BLUE),
    ("Total Fuel Litres", "Litres used", 1000000, 2),
    ("Average Fuel Efficiency", "Fuel efficiency (km/L)", 1, 2),
    ("Average Fuel Price", "Average price per litre", 1, 2),
    ("Fuel Cost per KM", "Fuel cost per km", 1, 3),
    ("Duplicate Coupon Numbers", "Coupon numbers used twice", 1, 0, RED),
])
v.append(insight(p, "insight", 24, INS_Y, 1872, INS_H, 1100, "Insight - Fuel"))
v.append(line(p, "monthly", 24, A_Y, 1100, A_H, 2000, "Monthly fuel cost", "Total Fuel Cost", BLUE, units=1000))
v.append(bar(p, "worstkml", 1140, A_Y, 756, A_H, 2001, "10 least fuel-efficient trucks (km/L)",
             ("DimTruck", "Truck ID"), "Average Fuel Efficiency", fill=RED, desc=False, precision=2, measure_name="km/L"))
v.append(bar(p, "route", 24, B_Y, 760, B_H, 2002, "Fuel cost per km by route",
             ("Fuel", "Route"), "Fuel Cost per KM", fill=BLUE, n=None, precision=3, measure_name="Fuel cost per km"))
v.append(table(p, "coupons", 800, B_Y, 1096, B_H, 2003, "Fuel records sharing a coupon number (to check)",
               [(col("Fuel", "Coupon #"), "Coupon"), (col("Fuel", "Date"), "Date"), (col("Fuel", "Truck ID"), "Truck"),
                (col("Fuel", "Driver Name"), "Driver"), (col("Fuel", "Pump Location"), "Pump"),
                (meas("Total Fuel Litres"), "Litres"), (meas("Total Fuel Cost"), "Cost")],
               col("Fuel", "Coupon #"), desc=False, filters=[measure_gt_filter("Coupon Use Count", 1)],
               widths=[140, 130, 120, 210, 210, 100, 100]))
pages.append((p, "Fuel", v))

# 3. Maintenance
p = "p3maint"
v = [header(p, "Maintenance", "Cost, downtime and the balance between planned and breakdown work  ·  " + PERIOD)]
v += filters_bar(p)
v += kpis(p, [
    ("Total Maintenance Cost", "Maintenance cost", 1000, 0, ORANGE),
    ("Total Maintenance Jobs", "Jobs", 1, 0),
    ("Preventive Maintenance %", "Preventive share of jobs", 1, 1, GREEN),
    ("Critical Jobs", "Critical jobs", 1, 0, RED),
    ("Total Downtime", "Downtime (days)", 1, 0),
    ("Average Downtime", "Downtime per job (days)", 1, 1),
])
v.append(insight(p, "insight", 24, INS_Y, 1872, INS_H, 1100, "Insight - Maintenance"))
v.append(stacked(p, "monthly", 24, A_Y, 1100, A_H, 2000, "Monthly maintenance cost: preventive vs corrective",
                 "columnChart", ("DimDate", "Month Year"), [("Total Maintenance Cost", "Cost")], [ORANGE],
                 series=("Maintenance", "Maintenance Type Clean"),
                 series_colors=[("Preventive", GREEN), ("Corrective", ORANGE)], units=1000))
v.append(column_priority(p, "priority", 1140, A_Y, 756, A_H, 2001, "Jobs by priority"))
v.append(scatter(p, "scatter", 24, B_Y, 1100, B_H, 2002, "Maintenance cost vs downtime (each dot = a truck)",
                 "Total Downtime", "Total Maintenance Cost", "Downtime (days)", "Maintenance cost", fill=ORANGE))
v.append(bar(p, "downtime", 1140, B_Y, 756, B_H, 2003, "10 trucks with the most downtime (days)",
             ("DimTruck", "Truck ID"), "Total Downtime", fill=RED, precision=1, measure_name="Downtime (days)"))
pages.append((p, "Maintenance", v))

# 4. Drivers
p = "p4drivers"
v = [header(p, "Drivers", "Safety and delivery performance, compared per 100 trips  ·  whole period Jul 2024 – Jun 2026 (driver data has no dates)")]
v += filters_bar(p, truck=False, driver=True)
v += kpis(p, [
    ("Drivers", "Drivers", 1, 0),
    ("Total Trips", "Trips completed", 1, 0),
    ("Average Safety Score", "Average safety score", 1, 1),
    ("Harsh Braking per 100 Trips", "Harsh braking per 100 trips", 1, 1, RED),
    ("Over-Speeding per 100 Trips", "Over-speeding per 100 trips", 1, 1, RED),
    ("Late Delivery Rate", "Late delivery rate", 1, 1, ORANGE),
])
v.append(insight(p, "insight", 24, INS_Y, 1872, INS_H, 1100, "Insight - Driver"))
v.append(bar(p, "harsh", 24, A_Y, 920, A_H, 2000, "10 highest harsh-braking rates (per 100 trips)",
             ("DimDriver", "Driver Name"), "Harsh Braking per 100 Trips", fill=RED, precision=1, measure_name="Per 100 trips"))
v.append(bar(p, "late", 960, A_Y, 936, A_H, 2001, "10 highest late-delivery rates",
             ("DimDriver", "Driver Name"), "Late Delivery Rate", fill=ORANGE, precision=1, measure_name="Late delivery rate"))
v.append(table(p, "scorecard", 24, B_Y, 1250, B_H, 2002, "Driver scorecard (lowest safety score first)",
               [(col("DriverPerformance", "Driver Name"), "Driver"), (col("DriverPerformance", "Truck ID"), "Truck"),
                (meas("Total Trips"), "Trips"), (meas("Average Safety Score"), "Safety score"),
                (meas("Harsh Braking per 100 Trips"), "Harsh braking /100 trips"),
                (meas("Over-Speeding per 100 Trips"), "Over-speeding /100 trips"),
                (meas("Late Delivery Rate"), "Late %"), (meas("Idling % of Hours Driven"), "Idling % of hours"),
                (col("DriverPerformance", "Fuel ECO Category"), "Eco rating")],
               meas("Average Safety Score"), desc=False,
               widths=[190, 120, 80, 110, 160, 170, 90, 140, 110]))
v.append(bar(p, "safety", 1290, B_Y, 606, B_H, 2003, "10 lowest safety scores",
             ("DimDriver", "Driver Name"), "Average Safety Score", fill=NAVY, desc=False, precision=0, measure_name="Safety score"))
pages.append((p, "Drivers", v))

# 5. Data checks
p = "p5checks"
v = [header(p, "Data Checks", "How far the numbers can be trusted  ·  green 0 = check passes  ·  whole dataset, no filters")]
checks = [
    ("Check - Fuel Rows", "Fuel records loaded", NAVY),
    ("Check - Fuel Duplicate SN", "Duplicate fuel record IDs", GREEN),
    ("Check - Maintenance Rows", "Maintenance records loaded", NAVY),
    ("Check - Maintenance Duplicate SN", "Duplicate maintenance record IDs", GREEN),
    ("Check - Invalid ODO Rows", "Odometer mismatches (km ≠ end − start)", GREEN),
    ("Check - Jobs Reconcile", "Jobs − preventive − corrective", GREEN),
    ("Check - Driver Trips vs Fuel Records", "Driver trips − fuel records", GREEN),
    ("Check - Fuel Cost vs Litres x Rate", "Fuel cost: litres × rate − recorded", ORANGE),
    ("Duplicate Coupon Numbers", "Coupon numbers used on 2 fills", RED),
    ("Trucks Missing Driver Data", "Trucks with no driver record", RED),
]
cw = (1872 - 4 * 16) / 5
for i, (m, lbl, c) in enumerate(checks):
    r, k = divmod(i, 5)
    v.append(card(p, f"chk{i}", 24 + k * (cw + 16), 112 + r * 136, cw, 120, 1000 + i, m, lbl, 1, 0, c, size=28))
v.append(note(p, "notes", 24, 392, 1872, 664, 3000, [
    ("What was checked and what it means", {"fontSize": "22pt", "fontWeight": "bold"}),
    "",
    "Passed: every fuel and maintenance record has a unique ID; every fuel record's distance equals end odometer minus start odometer; preventive + corrective jobs add up to the total; driver trips (10,318) match the number of fuel records.",
    "",
    "Small difference: recalculating fuel cost as litres × pump rate gives a total $393 lower than the recorded cost (about 0.02%). This looks like rounding in the pump rate and does not change any conclusion.",
    "",
    "To follow up: 56 coupon numbers each appear on two fills, on different trucks and different dates (listed on the Fuel page). In a real fleet this is worth checking with the fuel desk, as reused coupons can mean data-entry errors or misuse.",
    "",
    "Coverage gaps: 4 of the 50 trucks have no driver record, so they appear in fuel and maintenance figures but not on the Drivers page. The driver table is one row per driver for the whole period with no dates, so the date filter cannot apply to it.",
    "",
    "Method notes: driver rankings use rates per 100 trips because four drivers completed about twice as many trips as the rest, so raw counts would overstate their risk. Ratios return blank (not zero) when there is no data, so a truck with no fuel records is never ranked as 'least efficient'.",
]))
pages.append((p, "Data Checks", v))

# ---------- write ----------
keep_pages = {p[0] for p in pages}
for name in os.listdir(PAGES):
    full = os.path.join(PAGES, name)
    if os.path.isdir(full) and name not in keep_pages:
        shutil.rmtree(full, ignore_errors=True)

for pname, display, visuals in pages:
    pdir = os.path.join(PAGES, pname)
    os.makedirs(os.path.join(pdir, "visuals"), exist_ok=True)
    keep = {v_["name"] for v_ in visuals}
    for old in os.listdir(os.path.join(pdir, "visuals")):
        if old not in keep:
            shutil.rmtree(os.path.join(pdir, "visuals", old), ignore_errors=True)
    page = {"$schema": PAGE_SCHEMA, "name": pname, "displayName": display, "displayOption": "FitToPage",
            "height": 1080, "width": 1920,
            "objects": {"background": props(color=color(BG), transparency=d(0)),
                        "outspace": props(color=color(BG), transparency=d(0))}}
    json.dump(page, open(os.path.join(pdir, "page.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    for vis in visuals:
        vdir = os.path.join(pdir, "visuals", vis["name"]); os.makedirs(vdir, exist_ok=True)
        json.dump(vis, open(os.path.join(vdir, "visual.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)

json.dump({"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
           "pageOrder": [p[0] for p in pages], "activePageName": pages[0][0]},
          open(os.path.join(PAGES, "pages.json"), "w", encoding="utf-8"), indent=2)
print("pages:", [(p[1], len(p[2])) for p in pages])
