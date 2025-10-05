#!/usr/bin/env python3
import sys
import json
import traceback
import os

from agent_core import AgentCore


def send(obj):
    sys.stdout.write(json.dumps(obj, default=str) + "\n")
    sys.stdout.flush()


def bridge_emit(payload: dict):
    # All runtime step events flow through here
    send({"event": "step", **payload})


def main():
    send({"event": "bridge_ready", "pid": os.getpid()})

    # Pass the bridge emitter into the agent for live step streaming
    agent = AgentCore(event_cb=bridge_emit)

    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        try:
            msg = json.loads(raw)
            op = msg.get("op")
            req_id = msg.get("id")

            if op == "ping":
                send({"event": "pong", "id": req_id})
                continue

            if op == "run_goal":
                goal = msg.get("goal") or ""
                target = msg.get("target_app")
                max_iter = int(msg.get("max_iterations", 5))
                send({"event": "started", "id": req_id, "goal": goal, "target_app": target})
                result = agent.run_autonomous_loop(goal=goal, target_app=target, max_iterations=max_iter)
                send({"event": "finished", "id": req_id, "result": result})
                continue

            if op == "stop":
                send({"event": "stopping", "id": req_id})
                break

            send({"event": "error", "id": req_id, "error": f"Unknown op: {op}"})

        except Exception as e:
            send({"event": "error", "error": str(e), "trace": traceback.format_exc()})


if __name__ == "__main__":
    main()
