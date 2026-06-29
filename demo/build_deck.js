const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const FA = require("react-icons/fa");

// ── Light palette ───────────────────────────────────────────────────────────
const C = {
  bg:    "FAFAF7",  // slide background (warm off-white)
  bg2:   "F4F3EE",  // alt background
  card:  "FFFFFF",  // card surface
  card2: "F1EFE8",  // filled card / stat
  line:  "DAD8CF",  // border
  txt:   "23222B",  // near-black
  txt2:  "5F5E5A",  // muted
  txt3:  "9A998F",  // hint
  purple:"534AB7",  // primary accent (text-safe on light)
  purpleF:"EEEDFE", // purple fill
  purpleD:"3C3489",
  teal:  "15876A",  // teal accent (text-safe)
  tealF: "E1F5EE",
  tealD: "0F6E56",
  amber: "BA7517",
  amberF:"FAEEDA",
  amberD:"854F0B",
  blue:  "185FA5",
  coral: "993C1D",
  code:  "1F1F2B",  // code text
};
const FONT_H = "Trebuchet MS";
const FONT_B = "Calibri";

async function icon(IconComponent, color = "#000000", size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComponent, { color, size: String(size) })
  );
  const png = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + png.toString("base64");
}

(async () => {
  const need = {
    mobile: FA.FaMobileAlt, robot: FA.FaRobot, file: FA.FaFileAlt, list: FA.FaListUl,
    play: FA.FaPlay, sync: FA.FaSync, chart: FA.FaChartBar, check: FA.FaCheckCircle,
    bolt: FA.FaBolt, cloud: FA.FaCloud, apple: FA.FaApple, android: FA.FaAndroid,
    heart: FA.FaHeartbeat, cog: FA.FaCogs, bug: FA.FaBug, clock: FA.FaClock,
    users: FA.FaUsers, shield: FA.FaShieldAlt, rocket: FA.FaRocket, mail: FA.FaEnvelope,
    sitemap: FA.FaSitemap, gauge: FA.FaTachometerAlt, magic: FA.FaMagic, server: FA.FaServer,
    vial: FA.FaVial, clip: FA.FaClipboardCheck, ticket: FA.FaTicketAlt, hand: FA.FaHandPointer,
  };
  const colorMap = {
    mobile:"#534AB7", robot:"#534AB7", file:"#534AB7", list:"#534AB7", play:"#534AB7",
    sync:"#BA7517", chart:"#15876A", check:"#15876A", bolt:"#BA7517", cloud:"#185FA5",
    apple:"#444441", android:"#15876A", heart:"#993C1D", cog:"#5F5E5A", bug:"#993C1D",
    clock:"#5F5E5A", users:"#185FA5", shield:"#15876A", rocket:"#534AB7", mail:"#185FA5",
    sitemap:"#534AB7", gauge:"#15876A", magic:"#BA7517", server:"#5F5E5A", vial:"#15876A",
    clip:"#15876A", ticket:"#15876A", hand:"#BA7517",
  };
  const I = {};
  for (const k of Object.keys(need)) I[k] = await icon(need[k], colorMap[k]);
  const Iw = {}; // white variant for colored circles
  for (const k of ["play","check","sync"]) Iw[k] = await icon(need[k], "#FFFFFF");

  const p = new pptxgen();
  p.layout = "LAYOUT_WIDE";
  p.author = "Virat Saroha";
  p.title = "Agentic Mobile App Automation — Demo";
  const PW = 13.333, PH = 7.5;

  const shadow = () => ({ type:"outer", color:"6F6E66", blur:7, offset:2, angle:135, opacity:0.18 });

  function bg(s, color){ s.background = { color }; }
  function kicker(s, text, x=0.7, y=0.55){
    s.addShape(p.shapes.RECTANGLE, { x, y:y+0.02, w:0.16, h:0.28, fill:{color:C.purple} });
    s.addText(text.toUpperCase(), { x:x+0.28, y, w:9, h:0.32, fontFace:FONT_H, fontSize:13,
      bold:true, color:C.purple, charSpacing:3, align:"left", valign:"middle", margin:0 });
  }
  function title(s, text, x=0.7, y=0.95, w=12, size=34, color=C.txt){
    s.addText(text, { x, y, w, h:0.9, fontFace:FONT_H, fontSize:size, bold:true, color,
      align:"left", valign:"middle", margin:0 });
  }
  function pageNum(s, n){
    s.addText(String(n).padStart(2,"0")+"  /  12", { x:PW-2.0, y:PH-0.5, w:1.6, h:0.3,
      fontFace:FONT_B, fontSize:10, color:C.txt3, align:"right", valign:"middle" });
    s.addText("Agentic Mobile App Automation", { x:0.7, y:PH-0.5, w:4, h:0.3, fontFace:FONT_B, fontSize:10,
      color:C.txt3, align:"left", valign:"middle" });
  }
  function card(s, x, y, w, h, fill=C.card){
    s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill:{color:fill},
      line:{color:C.line, width:1}, rectRadius:0.09, shadow:shadow() });
  }

  // ════════════════════════════════════════════════════════ SLIDE 1 — Title
  let s = p.addSlide(); bg(s, C.bg);
  s.addShape(p.shapes.RECTANGLE, { x:0, y:0, w:PW, h:0.14, fill:{color:C.purple} });
  s.addShape(p.shapes.OVAL, { x:0.75, y:1.95, w:1.05, h:1.05, fill:{color:C.purpleF}, line:{color:C.purple, width:1.5} });
  s.addImage({ data:I.mobile, x:1.05, y:2.25, w:0.45, h:0.45 });
  s.addText("Agentic Mobile App", { x:0.7, y:3.15, w:12, h:0.95, fontFace:FONT_H, fontSize:54,
    bold:true, color:C.txt, align:"left", valign:"middle", margin:0 });
  s.addText("Automation", { x:0.7, y:4.05, w:12, h:0.95, fontFace:FONT_H, fontSize:54,
    bold:true, color:C.purple, align:"left", valign:"middle", margin:0 });
  s.addText("Autonomous, agent-driven test automation for the UZIO Mobile app",
    { x:0.72, y:5.05, w:11.5, h:0.5, fontFace:FONT_B, fontSize:19, color:C.txt2, align:"left", margin:0 });
  const tags = ["Appium + Python + pytest","Android & iOS","BrowserStack + local","6-strategy self-healing"];
  let tx = 0.72;
  for (const t of tags){
    const tw = 0.42 + t.length*0.108;
    s.addShape(p.shapes.ROUNDED_RECTANGLE, { x:tx, y:5.7, w:tw, h:0.45, fill:{color:C.card2},
      line:{color:C.line, width:1}, rectRadius:0.22 });
    s.addText(t, { x:tx, y:5.7, w:tw, h:0.45, fontFace:FONT_B, fontSize:12.5, color:C.txt2,
      align:"center", valign:"middle", margin:0 });
    tx += tw + 0.22;
  }
  s.addText([
    { text:"Demo  ", options:{ color:C.purple, bold:true } },
    { text:"·  Virat Saroha  ·  QA Engineering, UZIO", options:{ color:C.txt2 } },
  ], { x:0.72, y:6.55, w:11, h:0.4, fontFace:FONT_B, fontSize:15, align:"left", margin:0 });
  s.addNotes("Opening line: 'This is Agentic Mobile App Automation — a framework I built that runs our entire mobile QA cycle on its own.' Set the frame: it takes a Jira ticket or a whole suite, writes the tests, runs them on real devices or BrowserStack, fixes its own broken locators, and ships a report to the team. Built on Appium + Python + pytest, cross-platform Android and iOS. Tell them you'll finish with a live run on a real phone.");

  // ════════════════════════════════════════════════════════ SLIDE 2 — Challenge
  s = p.addSlide(); bg(s, C.bg2);
  kicker(s, "Why this exists");
  title(s, "Manual mobile QA doesn't scale");
  const pains = [
    [I.clock, "Slow & repetitive", "Every build needs the same login → navigate → clock in/out → logout checks re-run by hand."],
    [I.bug, "Brittle UI", "React Native screens change text and layout often — scripts break and need constant babysitting."],
    [I.mobile, "Device matrix", "Android and iOS, multiple OS versions and devices — impossible to cover manually each release."],
    [I.users, "No traceability", "Hard to tie test runs back to Jira tickets, or to hand QA a clean, shareable report."],
  ];
  let cy = 2.05;
  for (const [ic, h, d] of pains){
    card(s, 0.7, cy, 11.95, 1.0, C.card);
    s.addShape(p.shapes.OVAL, { x:1.0, y:cy+0.26, w:0.48, h:0.48, fill:{color:C.card2}, line:{color:C.line,width:1} });
    s.addImage({ data:ic, x:1.11, y:cy+0.37, w:0.26, h:0.26 });
    s.addText(h, { x:1.75, y:cy, w:3.4, h:1.0, fontFace:FONT_H, fontSize:17, bold:true,
      color:C.txt, align:"left", valign:"middle", margin:0 });
    s.addText(d, { x:5.2, y:cy, w:7.2, h:1.0, fontFace:FONT_B, fontSize:13.5, color:C.txt2,
      align:"left", valign:"middle", margin:0 });
    cy += 1.13;
  }
  pageNum(s, 2);
  s.addNotes("Frame the pain before the solution. Mobile QA is the most repetitive work we do — the same login-to-logout path, every single build. React Native makes it worse: there are no testIDs and the visible text changes often, so hand-written scripts break constantly. Add the Android + iOS device matrix and it's simply not coverable by hand each release. And manually, there's no clean link back to the Jira ticket or a report you can share. These four problems are exactly what the framework was built to remove.");

  // ════════════════════════════════════════════════════════ SLIDE 3 — Overview
  s = p.addSlide(); bg(s, C.bg);
  kicker(s, "The solution");
  title(s, "One pipeline: ticket in, tested report out");
  s.addText("The framework chains five specialised agents into a single autonomous flow. Point it at a Jira ticket or a whole suite — it writes the tests, runs them on real devices or the cloud, fixes its own broken locators, and ships a polished report to the team.",
    { x:0.7, y:1.9, w:7.0, h:1.6, fontFace:FONT_B, fontSize:16, color:C.txt2, align:"left", valign:"top", lineSpacingMultiple:1.15, margin:0 });
  const feats = [
    [I.robot, "5 autonomous agents", "Requirements → generation → execution → healing → reporting."],
    [I.magic, "Self-healing locators", "6-strategy cascade survives RN text & layout changes."],
    [I.cloud, "Run anywhere", "Local device, simulator, or BrowserStack cloud."],
    [I.chart, "Offline HTML reports", "Self-contained, screenshots inline, auto-shared."],
  ];
  let fy = 1.9;
  for (const [ic, h, d] of feats){
    card(s, 8.0, fy, 4.6, 1.18, C.card);
    s.addImage({ data:ic, x:8.28, y:fy+0.28, w:0.42, h:0.42 });
    s.addText(h, { x:8.85, y:fy+0.16, w:3.6, h:0.4, fontFace:FONT_H, fontSize:14.5, bold:true, color:C.txt, align:"left", margin:0 });
    s.addText(d, { x:8.85, y:fy+0.56, w:3.6, h:0.55, fontFace:FONT_B, fontSize:11.5, color:C.txt2, align:"left", margin:0 });
    fy += 1.31;
  }
  s.addShape(p.shapes.RECTANGLE, { x:0.7, y:4.05, w:0.14, h:0.26, fill:{color:C.teal} });
  s.addText("EARLY RESULTS", { x:0.94, y:4.03, w:6, h:0.3, fontFace:FONT_H, fontSize:12.5, bold:true, color:C.teal, charSpacing:2, align:"left", valign:"middle", margin:0 });
  const stats = [["14/16","nav tests green"],["6/6","sanity green on device"],["0","app-exit incidents"]];
  let sx = 0.7;
  for (const [big, lab] of stats){
    s.addShape(p.shapes.ROUNDED_RECTANGLE, { x:sx, y:4.55, w:2.27, h:1.7, fill:{color:C.card2}, line:{color:C.line,width:1}, rectRadius:0.08 });
    s.addText(big, { x:sx, y:4.78, w:2.27, h:0.85, fontFace:FONT_H, fontSize:38, bold:true, color:C.teal, align:"center", valign:"middle", margin:0 });
    s.addText(lab, { x:sx, y:5.62, w:2.27, h:0.5, fontFace:FONT_B, fontSize:13, color:C.txt2, align:"center", valign:"middle", margin:0 });
    sx += 2.42;
  }
  pageNum(s, 3);
  s.addNotes("This is the one-sentence pitch: ticket in, tested report out. Everything between is automated. The four cards on the right are the pillars — five agents, self-healing, run anywhere, offline reports — and we'll go one level deeper on each in the next few slides. The stats at the bottom are real: 6 of 6 sanity tests green on a physical Samsung, 14 of 16 navigation tests passing after self-healing, and zero incidents of the automation walking out of the app since the safety guards landed.");

  // ════════════════════════════════════════════════════════ SLIDE 4 — Pipeline
  s = p.addSlide(); bg(s, C.bg2);
  kicker(s, "How it works");
  title(s, "The 5-agent pipeline");
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x:0.7, y:2.0, w:2.7, h:0.5, fill:{color:C.tealF}, line:{color:C.teal,width:1}, rectRadius:0.25 });
  s.addImage({ data:I.ticket, x:0.92, y:2.13, w:0.24, h:0.24 });
  s.addText("Jira ticket / suite", { x:1.2, y:2.0, w:2.2, h:0.5, fontFace:FONT_B, fontSize:13, bold:true, color:C.tealD, align:"left", valign:"middle", margin:0 });
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x:PW-3.4, y:2.0, w:2.7, h:0.5, fill:{color:C.purpleF}, line:{color:C.purple,width:1}, rectRadius:0.25 });
  s.addImage({ data:I.chart, x:PW-3.18, y:2.13, w:0.24, h:0.24 });
  s.addText("HTML report + notify", { x:PW-2.9, y:2.0, w:2.3, h:0.5, fontFace:FONT_B, fontSize:13, bold:true, color:C.purpleD, align:"left", valign:"middle", margin:0 });
  const agents = [
    [I.file, "1", "Requirements", "Jira → requirements\n+ UzioMobile screens"],
    [I.list, "2", "Test generation", "Plain-English cases\npytest + Excel"],
    [I.play, "3", "Execution", "Device / simulator\nBrowserStack cloud"],
    [I.sync, "4", "Self-healing", "6-strategy\nlocator repair"],
    [I.chart, "5", "Reporting", "HTML report\nChat / email"],
  ];
  const n = agents.length, gap = 0.34, marginX = 0.7;
  const cw = (PW - marginX*2 - gap*(n-1)) / n;
  const ay = 2.95, ah = 2.0;
  for (let i=0;i<n-1;i++){
    const ax = marginX + (i+1)*cw + i*gap;
    s.addShape(p.shapes.RECTANGLE, { x:ax+0.04, y:ay+ah/2-0.02, w:gap-0.08, h:0.05, fill:{color:C.teal} });
  }
  for (let i=0;i<n;i++){
    const [ic, num, h, d] = agents[i];
    const ax = marginX + i*(cw+gap);
    const accent = i===3 ? C.amber : C.purple;
    s.addShape(p.shapes.ROUNDED_RECTANGLE, { x:ax, y:ay, w:cw, h:ah, fill:{color:C.card}, line:{color:accent, width:1.5}, rectRadius:0.1, shadow:shadow() });
    s.addText("AGENT "+num, { x:ax, y:ay+0.18, w:cw, h:0.3, fontFace:FONT_B, fontSize:10.5, bold:true, color:C.txt3, charSpacing:2, align:"center", margin:0 });
    s.addImage({ data:ic, x:ax+cw/2-0.3, y:ay+0.52, w:0.6, h:0.6 });
    s.addText(h, { x:ax, y:ay+1.18, w:cw, h:0.35, fontFace:FONT_H, fontSize:14.5, bold:true, color:C.txt, align:"center", margin:0 });
    s.addText(d, { x:ax, y:ay+1.5, w:cw, h:0.45, fontFace:FONT_B, fontSize:10.5, color:C.txt2, align:"center", valign:"top", margin:0, lineSpacingMultiple:0.95 });
  }
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x:5.1, y:5.45, w:5.6, h:0.62, fill:{color:C.amberF}, line:{color:C.amber, width:1, dashType:"dash"}, rectRadius:0.1 });
  s.addImage({ data:I.sync, x:5.35, y:5.61, w:0.3, h:0.3 });
  s.addText("Self-heal loop — patch locator, re-run execution", { x:5.75, y:5.45, w:4.8, h:0.62, fontFace:FONT_B, fontSize:13, bold:true, color:C.amberD, align:"left", valign:"middle", margin:0 });
  s.addText("Per-Jira:  /requirements-agent  →  /test-generation-agent  →  /execution-agent  →  /self-healing-agent  →  /reporting-agent",
    { x:0.7, y:6.45, w:11.95, h:0.4, fontFace:"Consolas", fontSize:11.5, color:C.txt3, align:"center", margin:0 });
  pageNum(s, 4);
  s.addNotes("This is the heart of the system — walk left to right. Agent 1 reads the Jira ticket and the actual UzioMobile screens. Agent 2 turns that into plain-English test cases plus runnable pytest and an Excel workbook. Agent 3 executes on a device, simulator, or BrowserStack. Agent 4 is the differentiator — when a locator breaks it heals it and re-runs execution, that's the amber loop. Agent 5 builds the report and notifies the team. Two orchestrators chain it all for sanity and regression; the command line at the bottom is the per-ticket flow. TRANSITION: 'Let me show you this running live' — switch to the animated diagram or the dashboard here.");

  // ════════════════════════════════════════════════════════ SLIDE 5 — Architecture
  s = p.addSlide(); bg(s, C.bg);
  kicker(s, "Under the hood");
  title(s, "Framework architecture");
  const arch = [
    [I.cog, "core/", "Engine", "config_loader · driver_factory · element_healer · base_page · locators · reporter"],
    [I.sitemap, "pages/", "Page objects", "login · dashboard · time_tracking · time_off — visible-text locators, no testIDs"],
    [I.vial, "tests/", "Suites", "sanity · regression · per-Jira (PHIX-XXXXX) folders"],
    [I.gauge, "dashboard.py", "Control console", "Streamlit UI — pick suite & platform, live log stream, report link"],
    [I.mobile, "mobile_apk/", "Builds", "APK / IPA store — NRS Purple, PROD, teamadmin builds"],
    [I.chart, "reports/", "Output", "Self-contained HTML reports + Excel test-case workbooks"],
  ];
  const cols = 3, cardW = 3.85, cardH = 1.95, gx = 0.7, gyy = 2.0, hgap=0.27, vgap=0.3;
  for (let i=0;i<arch.length;i++){
    const [ic, name, tag, d] = arch[i];
    const col = i%cols, rowi = Math.floor(i/cols);
    const x = gx + col*(cardW+hgap), y = gyy + rowi*(cardH+vgap);
    card(s, x, y, cardW, cardH, C.card);
    s.addShape(p.shapes.RECTANGLE, { x, y, w:0.09, h:cardH, fill:{color:C.purple} });
    s.addImage({ data:ic, x:x+0.3, y:y+0.28, w:0.46, h:0.46 });
    s.addText(name, { x:x+0.92, y:y+0.24, w:cardW-1.1, h:0.4, fontFace:"Consolas", fontSize:17, bold:true, color:C.purple, align:"left", margin:0 });
    s.addText(tag, { x:x+0.92, y:y+0.66, w:cardW-1.1, h:0.32, fontFace:FONT_H, fontSize:12.5, bold:true, color:C.txt2, align:"left", margin:0 });
    s.addText(d, { x:x+0.3, y:y+1.08, w:cardW-0.55, h:0.75, fontFace:FONT_B, fontSize:12, color:C.txt2, align:"left", valign:"top", margin:0, lineSpacingMultiple:1.0 });
  }
  pageNum(s, 5);
  s.addNotes("Keep this brief unless the audience is technical. Standard page-object pattern. core/ is the engine — the driver factory, the self-healing element finder, the reporter. pages/ holds the page objects, all using visible-text locators because there are no testIDs. tests/ is split into sanity, regression, and a folder per Jira ticket. dashboard.py is the Streamlit control console we'll demo. mobile_apk/ stores the builds, and reports/ is the output. For a non-technical room, just say 'clean, modular, standard structure' and move on.");

  // ════════════════════════════════════════════════════════ SLIDE 6 — Self-healing
  s = p.addSlide(); bg(s, C.bg2);
  kicker(s, "The differentiator");
  title(s, "Self-healing element finder");
  s.addText("When a locator fails, the healer tries six strategies in order and stops at the first hit — so a changed label or missing accessibility id doesn't fail the test.",
    { x:0.7, y:1.85, w:5.3, h:1.5, fontFace:FONT_B, fontSize:15.5, color:C.txt2, align:"left", valign:"top", lineSpacingMultiple:1.15, margin:0 });
  card(s, 0.7, 3.5, 5.3, 3.25, C.card);
  s.addImage({ data:I.magic, x:1.0, y:3.78, w:0.5, h:0.5 });
  s.addText("Why no testIDs?", { x:1.65, y:3.8, w:4, h:0.45, fontFace:FONT_H, fontSize:16, bold:true, color:C.txt, align:"left", valign:"middle", margin:0 });
  s.addText([
    {text:"UzioMobile (React Native) ships ", options:{}},
    {text:"no testIDs", options:{bold:true, color:C.amberD}},
    {text:" — every element must be found by visible text. On Android, RN exposes labels via ", options:{}},
    {text:"@content-desc", options:{color:C.teal, fontFace:"Consolas"}},
    {text:", not @text — so every locator must check both.", options:{}},
  ], { x:1.0, y:4.4, w:4.7, h:1.55, fontFace:FONT_B, fontSize:13.5, color:C.txt2, align:"left", valign:"top", lineSpacingMultiple:1.2, margin:0 });
  s.addText("EVERY LOCATOR", { x:1.0, y:5.95, w:4.5, h:0.25, fontFace:FONT_H, fontSize:10.5, bold:true, color:C.txt3, charSpacing:2, align:"left", margin:0 });
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x:1.0, y:6.2, w:4.7, h:0.42, fill:{color:C.card2}, line:{color:C.line,width:1}, rectRadius:0.06 });
  s.addText("@text='X' or @content-desc='X'", { x:1.15, y:6.2, w:4.4, h:0.42, fontFace:"Consolas", fontSize:12.5, color:C.tealD, align:"left", valign:"middle", margin:0 });
  const strat = [
    ["S1","Exact","@text or @content-desc = 'X'", C.teal],
    ["S2","Case-insensitive","lower-cased comparison", C.teal],
    ["S3","Partial","contains(@text / @content-desc)", C.teal],
    ["S4","Accessibility id","find by ACCESSIBILITY_ID", C.blue],
    ["S5","Widget class","scan common widget classes", C.blue],
    ["S6","Page-source scan","raw page_source string search", C.amber],
  ];
  let sy = 1.85;
  for (let i=0;i<strat.length;i++){
    const [tag, name, d, col] = strat[i];
    const x=6.4, w=6.25, h=0.74;
    s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y:sy, w, h, fill:{color:C.card}, line:{color:C.line,width:1}, rectRadius:0.07, shadow:shadow() });
    s.addShape(p.shapes.OVAL, { x:x+0.18, y:sy+0.17, w:0.4, h:0.4, fill:{color:col} });
    s.addText(tag, { x:x+0.18, y:sy+0.17, w:0.4, h:0.4, fontFace:FONT_H, fontSize:12, bold:true, color:"FFFFFF", align:"center", valign:"middle", margin:0 });
    s.addText(name, { x:x+0.78, y:sy+0.08, w:2.4, h:0.58, fontFace:FONT_H, fontSize:14, bold:true, color:C.txt, align:"left", valign:"middle", margin:0 });
    s.addText(d, { x:x+3.0, y:sy+0.08, w:3.1, h:0.58, fontFace:"Consolas", fontSize:11.5, color:C.txt2, align:"left", valign:"middle", margin:0 });
    sy += h + 0.13;
  }
  pageNum(s, 6);
  s.addNotes("This is the slide to dwell on — it's what makes the framework durable. Most mobile suites break the moment a label changes; ours doesn't. The healer tries six strategies in order and stops at the first that works: exact match, case-insensitive, partial/contains, accessibility id, widget-class scan, and finally a raw page-source scan. The key context is the card on the left: UzioMobile has no testIDs at all, and React Native on Android exposes labels through content-desc rather than text — so every locator checks both. If you demo a heal live, this is the slide to return to afterward.");

  // ════════════════════════════════════════════════════════ SLIDE 7 — Cross-platform
  s = p.addSlide(); bg(s, C.bg);
  kicker(s, "Coverage");
  title(s, "Cross-platform, two run modes");
  const grid = [
    [I.android, "Android", "UiAutomator2", "Physical Samsung device, ADB-connected. 6/6 sanity green on the QA build.", C.teal],
    [I.apple, "iOS", "XCUITest", "Local simulator or BrowserStack via uploaded .ipa. Cross-platform locators ready.", C.txt2],
    [I.cloud, "BrowserStack", "Cloud devices", "Galaxy S23 / iPhone 15 on demand. No local setup — upload build, run, watch live.", C.blue],
    [I.mobile, "Local device", "Appium :4723", "Fast inner-loop on a plugged-in phone. Safe-back guards keep automation inside the app.", C.purple],
  ];
  const gW=5.95, gH=2.25, gX=0.7, gY=2.0, ghg=0.45, gvg=0.35;
  for (let i=0;i<grid.length;i++){
    const [ic, h, tag, d, col] = grid[i];
    const col_i=i%2, row_i=Math.floor(i/2);
    const x=gX+col_i*(gW+ghg), y=gY+row_i*(gH+gvg);
    card(s, x, y, gW, gH, C.card);
    s.addShape(p.shapes.OVAL, { x:x+0.35, y:y+0.38, w:0.85, h:0.85, fill:{color:C.card2}, line:{color:col,width:1.5} });
    s.addImage({ data:ic, x:x+0.55, y:y+0.58, w:0.45, h:0.45 });
    s.addText(h, { x:x+1.4, y:y+0.42, w:gW-1.6, h:0.45, fontFace:FONT_H, fontSize:21, bold:true, color:C.txt, align:"left", margin:0 });
    s.addText(tag, { x:x+1.4, y:y+0.88, w:gW-1.6, h:0.35, fontFace:"Consolas", fontSize:13, color:col, align:"left", margin:0 });
    s.addText(d, { x:x+0.4, y:y+1.4, w:gW-0.8, h:0.75, fontFace:FONT_B, fontSize:13, color:C.txt2, align:"left", valign:"top", margin:0, lineSpacingMultiple:1.1 });
  }
  pageNum(s, 7);
  s.addNotes("Same test code, four targets. Android runs through UiAutomator2 on a real Samsung — that's where we have 6/6 sanity green. iOS runs via XCUITest on a simulator or BrowserStack with an uploaded .ipa; the locators are already cross-platform. BrowserStack gives us Galaxy S23 or iPhone 15 on demand with zero local setup — great for the demo if no phone is handy. And local device is the fast inner loop. Mention the safe-back guards: the automation can never accidentally walk out of the app onto the launcher — that was a real bug we fixed and hard-coded against.");

  // ════════════════════════════════════════════════════════ SLIDE 8 — Reporting (real screenshot)
  s = p.addSlide(); bg(s, C.bg2);
  kicker(s, "The deliverable");
  title(s, "Reports the team actually opens");
  const rfeat = [
    [I.file, "Self-contained", "One HTML file — inline CSS, base64 screenshots. Opens by double-click, works offline."],
    [I.chart, "Visual summary", "Donut, pass-rate gauge, summary cards, status filter pills."],
    [I.sync, "Heal log inline", "Each test card expands to show its self-healing log and error message."],
    [I.mail, "Auto-shared", "Google Chat + email hooks fire on session teardown — team notified automatically."],
  ];
  let ry=2.0;
  for (const [ic,h,d] of rfeat){
    card(s, 0.7, ry, 5.0, 1.12, C.card);
    s.addImage({ data:ic, x:0.98, y:ry+0.33, w:0.44, h:0.44 });
    s.addText(h, { x:1.6, y:ry+0.14, w:3.95, h:0.4, fontFace:FONT_H, fontSize:15, bold:true, color:C.txt, align:"left", margin:0 });
    s.addText(d, { x:1.6, y:ry+0.52, w:3.95, h:0.55, fontFace:FONT_B, fontSize:11, color:C.txt2, align:"left", valign:"top", margin:0, lineSpacingMultiple:1.0 });
    ry += 1.24;
  }
  // real report screenshot panel
  const imgX=6.05, imgW=6.6, imgH=imgW/(2800/1260); // preserve aspect (≈2.97)
  card(s, imgX, 2.0, imgW, imgH+0.95, C.card);
  s.addText("Real run — NRS Purple full regression", { x:imgX+0.3, y:2.18, w:imgW-0.6, h:0.4, fontFace:FONT_H, fontSize:14, bold:true, color:C.txt, align:"left", margin:0 });
  s.addImage({ path:"C:/code/master/MobileAutoQA/demo/report_shot.png", x:imgX+0.25, y:2.65, w:imgW-0.5, h:imgH-0.5 });
  s.addText("78 tests · 65 passed · 83.3% pass rate · self-contained HTML, opened offline",
    { x:imgX+0.3, y:2.0+imgH+0.45, w:imgW-0.6, h:0.4, fontFace:FONT_B, fontSize:11.5, color:C.txt2, align:"left", valign:"middle", margin:0 });
  pageNum(s, 8);
  s.addNotes("This is a real report — the screenshot on the right is an actual run, not a mockup: NRS Purple full regression, 78 tests, 65 passed, 83.3% pass rate. The point on the left: it's a single self-contained HTML file. No server, no Allure, no Java — inline CSS and base64 screenshots, so it opens by double-click and works offline. Each test card expands to show its self-healing log and the error message, and on teardown it auto-posts to Google Chat and email so the team is notified without anyone doing anything. In the live demo, open the actual report so they can click into a test.");

  // ════════════════════════════════════════════════════════ SLIDE 9 — Coverage
  s = p.addSlide(); bg(s, C.bg);
  kicker(s, "What's covered");
  title(s, "Suites & coverage today");
  card(s, 0.7, 2.0, 6.4, 4.5, C.card);
  s.addText("Tests by suite", { x:1.0, y:2.2, w:5.8, h:0.4, fontFace:FONT_H, fontSize:15, bold:true, color:C.txt, align:"left", margin:0 });
  s.addChart(p.charts.BAR, [{ name:"Tests", labels:["Sanity","Regression","Per-Jira","Sanity cases (Excel)"], values:[6,8,15,43] }], {
    x:0.85, y:2.55, w:6.1, h:3.8, barDir:"bar",
    chartColors:[C.purple],
    catAxisLabelColor:C.txt2, catAxisLabelFontSize:12, catAxisLabelFontFace:FONT_B,
    valAxisLabelColor:C.txt3, valGridLine:{color:C.line, size:0.5}, catGridLine:{style:"none"},
    showValue:true, dataLabelPosition:"outEnd", dataLabelColor:C.txt, dataLabelFontSize:12, dataLabelFontBold:true,
    showLegend:false, chartArea:{fill:{color:C.card}},
  });
  const cov = [
    [I.bolt, "Sanity", "Smoke: launch, login, bottom-nav, clock in/out, logout. The /mobile-sanity orchestrator runs it end-to-end."],
    [I.shield, "Regression", "Core time-tracking flows — deeper than smoke, run via /mobile-regression."],
    [I.ticket, "Per-Jira", "PHIX-86688, 95866, 97864, 97935… each ticket gets its own generated suite + Excel cases."],
  ];
  let vy=2.0;
  for (const [ic,h,d] of cov){
    card(s, 7.45, vy, 5.2, 1.42, C.card);
    s.addImage({ data:ic, x:7.72, y:vy+0.27, w:0.42, h:0.42 });
    s.addText(h, { x:8.3, y:vy+0.18, w:4.1, h:0.38, fontFace:FONT_H, fontSize:15.5, bold:true, color:C.txt, align:"left", margin:0 });
    s.addText(d, { x:8.3, y:vy+0.58, w:4.15, h:0.78, fontFace:FONT_B, fontSize:11.5, color:C.txt2, align:"left", valign:"top", margin:0, lineSpacingMultiple:1.05 });
    vy += 1.54;
  }
  pageNum(s, 9);
  s.addNotes("Show the breadth. Sanity is the smoke suite — launch, login, navigation, clock in/out, logout — run end-to-end by the /mobile-sanity orchestrator. Regression goes deeper into the core time-tracking flows. Per-Jira is the powerful part: every ticket (86688, 95866, 97864, 97935 and more) gets its own generated suite and Excel test cases. The bar chart counts those, and note the 43 — that's the auto-generated sanity test-case workbook, which we'll show in the live demo.");

  // ════════════════════════════════════════════════════════ SLIDE 10 — Demo walkthrough
  s = p.addSlide(); bg(s, C.bg2);
  kicker(s, "Live now");
  title(s, "What we'll see in the demo");
  const steps = [
    [I.gauge, "Launch the dashboard", "streamlit run dashboard.py — pick suite, platform, run mode."],
    [I.play, "Run sanity on a real device", "Watch login → nav → clock in/out → logout on the phone, live."],
    [I.magic, "Trigger a self-heal", "Break a locator, re-run, watch a fallback strategy recover it."],
    [I.chart, "Open the HTML report", "Double-click the report — screenshots, donut, heal logs."],
    [I.list, "Show the Excel cases", "python -m scripts.gen_sanity_testcases — styled multi-tab workbook."],
  ];
  let yy=2.0;
  for (let i=0;i<steps.length;i++){
    const [ic,h,d]=steps[i];
    card(s, 0.7, yy, 11.95, 0.86, C.card);
    s.addShape(p.shapes.OVAL, { x:0.95, y:yy+0.19, w:0.48, h:0.48, fill:{color:C.purple} });
    s.addText(String(i+1), { x:0.95, y:yy+0.19, w:0.48, h:0.48, fontFace:FONT_H, fontSize:17, bold:true, color:"FFFFFF", align:"center", valign:"middle", margin:0 });
    s.addImage({ data:ic, x:1.7, y:yy+0.26, w:0.34, h:0.34 });
    s.addText(h, { x:2.25, y:yy+0.1, w:3.9, h:0.66, fontFace:FONT_H, fontSize:15.5, bold:true, color:C.txt, align:"left", valign:"middle", margin:0 });
    s.addText(d, { x:6.3, y:yy+0.1, w:6.1, h:0.66, fontFace:"Consolas", fontSize:11.5, color:C.txt2, align:"left", valign:"middle", margin:0 });
    yy += 0.98;
  }
  pageNum(s, 10);
  s.addNotes("This is your live-demo runsheet — keep it on screen as you switch to the machine. 1) Launch the Streamlit dashboard, pick suite and platform. 2) Run sanity on the plugged-in phone and narrate login → nav → clock in/out → logout. 3) The money moment: break a locator on purpose, re-run, and show a fallback strategy recovering it — then flip back to slide 6. 4) Double-click the generated HTML report and click into a test card. 5) Generate the Excel test cases. Pre-demo checklist: adb shows 'device', Appium on 4723, secrets.yaml present, and keep a pre-generated report open as a fallback.");

  // ════════════════════════════════════════════════════════ SLIDE 11 — Results
  s = p.addSlide(); bg(s, C.bg);
  kicker(s, "Impact");
  title(s, "Results so far");
  const big = [
    ["6/6", "sanity tests green", "on a physical Samsung device", C.teal],
    ["14/16", "navigation tests pass", "after self-healing fixes", C.purple],
    ["0", "app-exit / drift incidents", "since the safety guards landed", C.teal],
    ["5", "autonomous agents", "+ 2 suite orchestrators", C.purple],
    ["2", "platforms covered", "Android & iOS, cloud + local", C.blue],
    ["43", "sanity test cases", "auto-generated to Excel", C.amber],
  ];
  const bW=3.85, bH=1.95, bX=0.7, bY=2.0, bhg=0.27, bvg=0.3;
  for (let i=0;i<big.length;i++){
    const [num, lab, sub, col]=big[i];
    const c=i%3, r=Math.floor(i/3);
    const x=bX+c*(bW+bhg), y=bY+r*(bH+bvg);
    card(s, x, y, bW, bH, C.card);
    s.addText(num, { x:x+0.3, y:y+0.25, w:bW-0.6, h:0.85, fontFace:FONT_H, fontSize:46, bold:true, color:col, align:"left", margin:0 });
    s.addText(lab, { x:x+0.32, y:y+1.12, w:bW-0.6, h:0.4, fontFace:FONT_H, fontSize:15, bold:true, color:C.txt, align:"left", margin:0 });
    s.addText(sub, { x:x+0.32, y:y+1.5, w:bW-0.55, h:0.4, fontFace:FONT_B, fontSize:11.5, color:C.txt2, align:"left", margin:0 });
  }
  pageNum(s, 11);
  s.addNotes("Land the impact in numbers. 6/6 sanity green on a real device and 14/16 navigation tests passing — both real, both after the self-healing pass. Zero app-exit incidents since the safety guards: important because the automation once walked out of the app, and that class of bug is now impossible. Five agents plus two orchestrators is the architecture; two platforms, cloud and local, is the reach; and 43 auto-generated test cases shows the generation side pays off. Close by saying the framework is already running real regression today, not a prototype.");

  // ════════════════════════════════════════════════════════ SLIDE 12 — Thank you
  s = p.addSlide(); bg(s, C.bg);
  s.addShape(p.shapes.RECTANGLE, { x:0, y:0, w:PW, h:0.14, fill:{color:C.purple} });
  s.addShape(p.shapes.RECTANGLE, { x:0, y:PH-0.14, w:PW, h:0.14, fill:{color:C.teal} });
  s.addShape(p.shapes.OVAL, { x:PW/2-0.6, y:1.95, w:1.2, h:1.2, fill:{color:C.purpleF}, line:{color:C.purple,width:1.5} });
  s.addImage({ data:I.rocket, x:PW/2-0.32, y:2.23, w:0.64, h:0.64 });
  s.addText("Thank you", { x:0, y:3.35, w:PW, h:1.0, fontFace:FONT_H, fontSize:50, bold:true, color:C.txt, align:"center", margin:0 });
  s.addText("Questions & live walkthrough", { x:0, y:4.4, w:PW, h:0.5, fontFace:FONT_B, fontSize:20, color:C.txt2, align:"center", margin:0 });
  s.addText([
    { text:"Agentic Mobile App Automation", options:{ bold:true, color:C.purple } },
    { text:"   ·   Virat Saroha   ·   virat.saroha@uzio.com", options:{ color:C.txt2 } },
  ], { x:0, y:5.35, w:PW, h:0.4, fontFace:FONT_B, fontSize:15, align:"center", margin:0 });
  s.addNotes("Wrap up and invite questions. One-line recap: 'It takes a ticket, writes the tests, runs them on real devices, heals itself, and reports back — autonomously.' Then open the floor and offer to dig into any part live — the dashboard, a heal, the report, or the Excel output.");

  const out = "C:/code/master/MobileAutoQA/demo/MobileAutoQA_Demo.pptx";
  await p.writeFile({ fileName: out });
  console.log("WROTE " + out);
})();
