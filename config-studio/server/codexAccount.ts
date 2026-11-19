import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import type { IncomingMessage } from "node:http";
import { isIP } from "node:net";

export function localAccountRequest(req: IncomingMessage): boolean {
  const address = req.socket.remoteAddress || "";
  if (!["127.0.0.1", "::1", "::ffff:127.0.0.1"].includes(address)) return false;
  const host = req.headers.host || "";
  const hostname = host.startsWith("[") ? host.slice(1, host.indexOf("]")) : host.split(":")[0];
  if (hostname !== "localhost" && !(isIP(hostname) && ["127.0.0.1", "::1"].includes(hostname))) return false;
  if (req.headers["sec-fetch-site"] === "cross-site") return false;
  const origin = req.headers.origin;
  if (origin) {
    try {
      const parsed = new URL(origin);
      if (parsed.host !== host || !["http:", "https:"].includes(parsed.protocol)) return false;
    } catch { return false; }
  }
  return true;
}

export class PythonAccountBridge {
  private process: ChildProcessWithoutNullStreams | null = null;
  private sequence = 0;
  private buffer = "";
  private pending = new Map<number, { resolve: (value: unknown) => void; reject: (error: Error) => void; timer: ReturnType<typeof setTimeout> }>();
  constructor(private python: string, private root: string, private home: string, private executable: string, private provider: "codex_account" | "google_calendar" = "codex_account") {}

  private start() {
    if (this.process) return;
    const args = ["-m", `pixel_ops.data_sources.${this.provider}`, "--serve", "--home", this.home];
    if (this.provider === "codex_account") args.push("--executable", this.executable);
    const child = spawn(this.python, args, {
      cwd: this.root, windowsHide: true, env: { ...process.env, PYTHONUNBUFFERED: "1" },
    });
    this.process = child;
    child.stdout.on("data", (chunk: Buffer) => {
      this.buffer += chunk.toString();
      let newline: number;
      while ((newline = this.buffer.indexOf("\n")) >= 0) {
        const line = this.buffer.slice(0, newline);
        this.buffer = this.buffer.slice(newline + 1);
        try {
          const message = JSON.parse(line) as { id: number; result?: unknown; error?: string };
          const request = this.pending.get(message.id);
          if (request) {
            clearTimeout(request.timer);
            this.pending.delete(message.id);
            if (message.error) request.reject(new Error(message.error));
            else request.resolve(message.result);
          }
        } catch { /* Never expose arbitrary child output. */ }
      }
    });
    child.stderr.resume();
    child.on("error", () => this.close());
    child.on("exit", () => { if (this.process === child) this.close(); });
  }

  call(method: string, params: Record<string, unknown> = {}): Promise<unknown> {
    this.start();
    const id = ++this.sequence;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error("Account request timed out. Retry the connection."));
        this.close();
      }, 60_000);
      this.pending.set(id, { resolve, reject, timer });
      this.process!.stdin.write(JSON.stringify({ id, method, params }) + "\n");
    });
  }

  close() {
    const child = this.process;
    this.process = null;
    // EOF lets Python release its profile lock and terminate its Codex child.
    child?.stdin.end();
    if (child) {
      const timer = setTimeout(() => child.kill(), 5000);
      timer.unref();
      child.once("exit", () => clearTimeout(timer));
    }
    this.buffer = "";
    for (const request of this.pending.values()) {
      clearTimeout(request.timer);
      request.reject(new Error("Account bridge stopped. Retry the connection."));
    }
    this.pending.clear();
  }
}

export class CodexAccountBridge extends PythonAccountBridge {}
