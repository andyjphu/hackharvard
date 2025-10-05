// pythonAgent.js
import { spawn } from "node:child_process";
import path from "node:path";
import readline from "node:readline";
import { EventEmitter } from "node:events";

export class PythonAgent extends EventEmitter {
  constructor({ pythonBin = process.env.PYTHON_BIN || "python3", bridgePath, env = {} } = {}) {
    super();
    this.pythonBin = pythonBin;
    this.bridgePath = bridgePath;
    this.env = { ...process.env, ...env };
    this.proc = null;
    this.pending = new Map(); // id -> {resolve, reject}
    this._counter = 0;
  }

  start() {
    if (this.proc) return;
    this.proc = spawn(this.pythonBin, ["-u", this.bridgePath], {
      env: this.env,
      stdio: ["pipe", "pipe", "pipe"],
    });

    const rl = readline.createInterface({ input: this.proc.stdout });
    rl.on("line", (line) => {
      let msg;
      try { msg = JSON.parse(line); } catch { return; }
      // Forward all events
      this.emit("event", msg);

      if (msg.event === "finished" && msg.id) {
        const pending = this.pending.get(msg.id);
        if (pending) {
          this.pending.delete(msg.id);
          pending.resolve(msg.result);
        }
      } else if (msg.event === "error" && msg.id) {
        const pending = this.pending.get(msg.id);
        if (pending) {
          this.pending.delete(msg.id);
          pending.reject(new Error(msg.error || "Unknown Python error"));
        }
      }
    });

    this.proc.stderr.on("data", (buf) => {
      this.emit("stderr", buf.toString());
    });

    this.proc.on("exit", (code, sig) => {
      this.emit("exit", { code, sig });
      // Fail all pendings
      for (const [, p] of this.pending) p.reject(new Error("Python exited"));
      this.pending.clear();
      this.proc = null;
    });
  }

  stop() {
    try {
      this.sendRaw({ op: "stop", id: this._nextId() });
    } catch {}
    if (this.proc) this.proc.kill("SIGTERM");
  }

  _nextId() {
    this._counter += 1;
    return `req_${Date.now()}_${this._counter}`;
  }

  sendRaw(msg) {
    if (!this.proc) throw new Error("Python not started");
    this.proc.stdin.write(JSON.stringify(msg) + "\n");
  }

  runGoal({ goal, target_app = null, max_iterations = 5 }) {
    if (!this.proc) this.start();
    const id = this._nextId();
    const payload = { op: "run_goal", id, goal, target_app, max_iterations };
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.sendRaw(payload);
    });
  }
}
