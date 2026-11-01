// Adds the ntfy notification (CT 106, http://<lan>.106) to Uptime Kuma and attaches it only to the
// Pi-hole DNS and HTTPS-with-DNS probes, so an internet outage sends one or two alerts instead of nine.
// Idempotent: the notification is matched by name and updated in place. Topic and token come from pve01
// (/root/ntfy/topic and /root/ntfy/token-uptime-kuma). Lives in CT 105 as /opt/uptime-kuma/kuma-ntfy.js.
// Run it from pve01, so the token is read from its file and never reaches the shell history:
//   pct exec 105 -- env NTFY_TOPIC="$(cat /root/ntfy/topic)" NTFY_TOKEN="$(cat /root/ntfy/token-uptime-kuma)" \
//     sh -c 'cd /opt/uptime-kuma/app && exec runuser -u kuma -- env NODE_PATH=/opt/uptime-kuma/app/node_modules node /opt/uptime-kuma/kuma-ntfy.js "$@"' sh [--test]
const { io } = require("socket.io-client");
const fs = require("fs");

const CREDENTIALS_FILE = "/opt/uptime-kuma/.admin";
const USER = "<admin-user>";
const NAME = "ntfy (CT 106)";
const PROBES = ["2 · Pi-hole DNS (<lan>.100)", "9 · HTTPS with DNS (google.com)"];
const { NTFY_TOPIC, NTFY_TOKEN } = process.env;
if (!NTFY_TOPIC || !NTFY_TOKEN) { console.error("NTFY_TOPIC and NTFY_TOKEN are required"); process.exit(2); }

const s = io("http://127.0.0.1:3001", { transports: ["websocket"], reconnection: false, timeout: 10000 });
const emit = (ev, ...args) => new Promise((ok, ko) => {
    const t = setTimeout(() => ko(new Error("no reply to " + ev)), 20000);
    s.emit(ev, ...args, (r) => { clearTimeout(t); ok(r); });
});
let monitorList = {};
let notificationList = [];
s.on("monitorList", (l) => { monitorList = l; });
s.on("notificationList", (l) => { notificationList = l; });

const notification = {
    name: NAME, type: "ntfy", isDefault: false, applyExisting: false,
    ntfyserverurl: "http://<lan>.106", ntfytopic: NTFY_TOPIC, ntfyPriority: 4,
    ntfyAuthenticationMethod: "accessToken", ntfyaccesstoken: NTFY_TOKEN,
};

(async () => {
    await new Promise((ok, ko) => { s.on("connect", ok); s.on("connect_error", ko); });
    const password = fs.readFileSync(CREDENTIALS_FILE, "utf8").match(/password: (\S+)/)[1];
    const login = await emit("login", { username: USER, password, token: "" });
    if (!login.ok) throw new Error("login: " + login.msg);
    await new Promise((ok) => setTimeout(ok, 1500));

    const existing = notificationList.find((n) => n.name === NAME);
    const saved = await emit("addNotification", notification, existing ? existing.id : null);
    if (!saved.ok) throw new Error("addNotification: " + saved.msg);
    const id = saved.id || (existing && existing.id);
    console.log((existing ? "notification updated" : "notification added") + ", id " + id);

    for (const name of PROBES) {
        const found = Object.values(monitorList).find((x) => x.name === name);
        if (!found) { console.log("MISSING probe:", name); continue; }
        const full = await emit("getMonitor", found.id);
        if (!full.ok) { console.log("FAILED getMonitor:", name, full.msg); continue; }
        const m = full.monitor;
        if (m.notificationIDList && m.notificationIDList[id]) { console.log("already attached:", name); continue; }
        m.notificationIDList = Object.assign({}, m.notificationIDList, { [id]: true });
        const edited = await emit("editMonitor", m);
        console.log(edited.ok ? "attached: " + name : "FAILED editMonitor: " + name + " " + edited.msg);
    }

    if (process.argv.includes("--test")) {
        const t = await emit("testNotification", notification);
        console.log("test notification:", t.ok ? "sent" : t.msg);
    }
    s.close();
    process.exit(0);
})().catch((e) => { console.error("ERROR", e.message); process.exit(1); });
