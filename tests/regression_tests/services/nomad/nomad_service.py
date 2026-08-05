import json

API_URL = "http://localhost:4646/v1"
ALLOCATIONS_MARKER = "__ALLOCATIONS__"

SMOKE_JOB_HCL = """job "{job_id}" {{
  datacenters = ["*"]
  type        = "batch"

  group "smoke" {{
    count = {count}

    constraint {{
      distinct_hosts = true
    }}

    task "hello" {{
      driver = "raw_exec"

      config {{
        command = "/bin/sh"
        args    = ["-c", "echo nomad-regression-ok"]
      }}

      resources {{
        cpu    = 100
        memory = 64
      }}
    }}
  }}
}}
"""

RUN_JOB_COMMAND = """
cat > /tmp/{job_id}.nomad <<'NOMADHCL'
{job_hcl}
NOMADHCL
export NOMAD_TOKEN={token}
nomad job stop -purge {job_id} >/dev/null 2>&1 || true
nomad job run -detach /tmp/{job_id}.nomad 2>&1
for _ in $(seq 1 {attempts}); do
  ALLOCS=$(curl -s -H "X-Nomad-Token: $NOMAD_TOKEN" {api_url}/job/{job_id}/allocations)
  SETTLED=$(printf '%s' "$ALLOCS" | jq '[.[] | select(.ClientStatus=="complete" or .ClientStatus=="failed" or .ClientStatus=="lost")] | length')
  [ "$SETTLED" = "{count}" ] && break
  sleep 3
done
echo "{marker}"
printf '%s' "$ALLOCS"
"""


class NomadService:
    def __init__(self, remote_exec, token):
        self.remote_exec = remote_exec
        self.token = token

    def run_smoke_job(self, job_id: str, count: int, attempts: int = 40) -> dict:
        command = RUN_JOB_COMMAND.format(
            job_id=job_id,
            job_hcl=SMOKE_JOB_HCL.format(job_id=job_id, count=count),
            token=self.token,
            api_url=API_URL,
            attempts=attempts,
            count=count,
            marker=ALLOCATIONS_MARKER,
        )
        stdout, stderr, exit_code = self.remote_exec(command, timeout=300)
        if exit_code != 0 or ALLOCATIONS_MARKER not in stdout:
            raise RuntimeError(
                f"Running {job_id} failed (exit {exit_code}): {stderr or stdout}"
            )

        submit_output, _, allocations_json = stdout.partition(ALLOCATIONS_MARKER)
        allocations = json.loads(allocations_json)
        return {
            "job_id": job_id,
            "submit_output": submit_output,
            "node_ids": sorted({allocation["NodeID"] for allocation in allocations}),
            "client_statuses": sorted(
                allocation["ClientStatus"] for allocation in allocations
            ),
        }
