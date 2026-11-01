// Sets up Uptime Kuma to monitor the home network: admin user, settings, probes and the public status page.
// Idempotent: probes are matched by name, so running it again only adds what is missing.
// Lives in CT 105 (uptime-kuma) as /opt/uptime-kuma/kuma-setup.js. Run it inside the CT with:
//   cd /opt/uptime-kuma/app && runuser -u kuma -- env NODE_PATH=/opt/uptime-kuma/app/node_modules node /opt/uptime-kuma/kuma-setup.js
const { io } = require("socket.io-client");
const crypto = require("crypto");
const fs = require("fs");

const CREDENTIALS_FILE = "/opt/uptime-kuma/.admin";
const USER = "<admin-user>";
const SLUG = "home";
const s = io("http://127.0.0.1:3001", { transports: ["websocket"], reconnection: false, timeout: 10000 });
const emit = (ev, ...args) => new Promise((ok, ko) => {
    const t = setTimeout(() => ko(new Error("no reply to " + ev)), 20000);
    s.emit(ev, ...args, (r) => { clearTimeout(t); ok(r); });
});
let monitorList = {};
s.on("monitorList", (l) => { monitorList = l; });

const base = {
    parent: null, method: "GET", interval: 20, retryInterval: 20, resendInterval: 0, maxretries: 1,
    notificationIDList: {}, ignoreTls: false, upsideDown: false, expiryNotification: false,
    maxredirects: 10, accepted_statuscodes: ["200-299"], dns_resolve_type: "A", dns_resolve_server: "",
    kafkaProducerBrokers: [], kafkaProducerSaslOptions: { mechanism: "None" }, rabbitmqNodes: [], conditions: [],
    active: true,
};
const ping = (name, host) => ({ ...base, type: "ping", name, hostname: host, timeout: 10, ping_count: 1, ping_numeric: true, packetSize: 56, ping_per_request_timeout: 2 });
const dns = (name, server) => ({ ...base, type: "dns", name, hostname: "google.com", dns_resolve_server: server, port: 53, timeout: 15 });
const http = (name, url) => ({ ...base, type: "http", name, url, timeout: 15 });

const MONITORS = [
    ["lan", ping("1 · Home router (<lan>.1)", "<lan>.1")],
    ["lan", dns("2 · Pi-hole DNS (<lan>.100)", "<lan>.100")],
    ["lan", dns("3 · Router DNS (<lan>.1)", "<lan>.1")],
    ["internet", ping("4 · ISP gateway (<isp-gateway>)", "<isp-gateway>")],
    ["internet", ping("5 · Internet: Cloudflare 1.1.1.1", "1.1.1.1")],
    ["internet", ping("6 · Internet: Google 8.8.8.8", "8.8.8.8")],
    ["internet", dns("7 · Google DNS direct", "8.8.8.8")],
    ["internet", http("8 · HTTPS without DNS (1.1.1.1)", "https://1.1.1.1/cdn-cgi/trace")],
    ["internet", http("9 · HTTPS with DNS (google.com)", "https://www.google.com/generate_204")],
];

const DESCRIPTION = [
    "When the internet goes down, check which probes turn red. All probes run from the Proxmox server, which is wired to the router.",
    "",
    "- **1 red** → the router is hung.",
    "- **1 up, 4–7 red** → the ISP gateway or the line behind it.",
    "- **Only 2 red** → Pi-hole.",
    "- **5–6 up, 8–9 red** → the router can't open new connections.",
    "- **Everything up, but the PC has no internet** → Wi-Fi.",
].join("\n");

(async () => {
    await new Promise((ok, ko) => { s.on("connect", ok); s.on("connect_error", ko); });
    const needSetup = await emit("needSetup");
    let password;
    if (needSetup) {
        password = crypto.randomBytes(18).toString("base64url");
        fs.writeFileSync(CREDENTIALS_FILE, "user: " + USER + "\npassword: " + password + "\n", { mode: 0o600 });
        const r = await emit("setup", USER, password);
        if (!r.ok) throw new Error("setup: " + r.msg);
        console.log("admin user created; credentials saved to " + CREDENTIALS_FILE);
    } else {
        password = fs.readFileSync(CREDENTIALS_FILE, "utf8").match(/password: (\S+)/)[1];
    }
    const login = await emit("login", { username: USER, password, token: "" });
    if (!login.ok) throw new Error("login: " + login.msg);
    await new Promise((ok) => setTimeout(ok, 1500));

    const current = await emit("getSettings");
    const settings = { ...current.data, checkUpdate: false, checkBeta: false, primaryBaseURL: "https://uptime-kuma.lan",
        serverTimezone: "<timezone>", keepDataPeriodDays: 180, searchEngineIndex: false, entryPage: "statusPage-" + SLUG };
    const saved = await emit("setSettings", settings, password);
    console.log("settings:", saved.ok ? "ok" : saved.msg);

    const ids = { lan: [], internet: [] };
    const existing = Object.values(monitorList);
    for (const [group, m] of MONITORS) {
        const found = existing.find((x) => x.name === m.name);
        if (found) { ids[group].push(found.id); console.log("exists:", m.name); continue; }
        const r = await emit("add", m);
        if (!r.ok) { console.log("FAILED", m.name, r.msg); continue; }
        ids[group].push(r.monitorID);
        console.log("added:", m.name, "id", r.monitorID);
    }

    const page = await emit("addStatusPage", "Home Network", SLUG);
    console.log("status page:", page.ok ? "created" : (/UNIQUE/.test(page.msg) ? "exists" : page.msg));
    const config = { slug: SLUG, title: "Home Network", description: DESCRIPTION, icon: "/icon.svg", theme: "auto",
        showTags: false, domainNameList: [], customCSS: "", showPoweredBy: false, showCertificateExpiry: false, autoRefreshInterval: 20,
        analyticsType: null, analyticsId: null, analyticsScriptUrl: null,
        footerText: "Router syslog: CT 105 (uptime-kuma), /var/log/router/router.log" };
    const groups = [
        { name: "LAN", monitorList: ids.lan.map((id) => ({ id })) },
        { name: "Internet", monitorList: ids.internet.map((id) => ({ id })) },
    ];
    const pageSaved = await emit("saveStatusPage", SLUG, config, "/icon.svg", groups);
    console.log("save status page:", pageSaved.ok ? "ok" : pageSaved.msg);
    s.close();
    process.exit(0);
})().catch((e) => { console.error("ERROR", e.message); process.exit(1); });
