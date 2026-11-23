import sys, json, time, statistics
from pathlib import Path

# ─── make project root importable no matter where we launch from ───
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from langchain_core.messages import HumanMessage
from agents.user_agent import user_graph

# ─── dataset path is relative to THIS file, not cwd ───
DATASET = Path(__file__).parent / "datasets" / "user_eval.jsonl"
RESULTS = Path(__file__).parent / "results.json"

DATA = [json.loads(l) for l in DATASET.read_text(encoding="utf-8").splitlines() if l.strip()]

def called_tools(messages):
    out = []
    for m in messages:
        if getattr(m, "tool_calls", None):
            out += [tc["name"] for tc in m.tool_calls]
    return out

def run():
    results, latencies = [], []
    for i, case in enumerate(DATA):
        tid = f"eval-{i}-{time.time_ns()}"
        t0 = time.time()
        res = user_graph.invoke(
            {"messages": [HumanMessage(content=case["input"])]},
            config={"configurable": {"thread_id": tid}}
        )
        latencies.append(time.time() - t0)
        used = called_tools(res["messages"])

        if case.get("expect_no_tool"):
            passed = len(used) == 0
        else:
            passed = case["expect_tool"] in used

        results.append({"input": case["input"], "expected": case.get("expect_tool"),
                        "used": used, "passed": passed})

    acc = sum(r["passed"] for r in results) / len(results) * 100
    report = {
        "tool_call_accuracy": round(acc, 1),
        "n_cases": len(results),
        "avg_latency_sec": round(statistics.mean(latencies), 2),
        "p95_latency_sec": round(sorted(latencies)[int(0.95*len(latencies))], 2),
        "results": results,
    }
    print(json.dumps({k: v for k, v in report.items() if k != "results"}, indent=2))
    with open("evals/results.json", "w") as f:
        json.dump(report, f, indent=2)

if __name__ == "__main__":
    run()