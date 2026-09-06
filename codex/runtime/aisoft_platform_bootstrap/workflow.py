"""Offline adoption decisions and versioned operation requests, never live apply."""
from __future__ import annotations

from .contract import ACTIONS, canonical, digest, document, require


def adoption_plan(manifest: dict, handoff_sha256: str, inventory: dict, target: dict) -> dict:
    document(manifest, "manifest")
    document(inventory, "inventory")
    document(target, "target")
    plan = {
        "contract_version": "platform-bootstrap-plan/v1", "source_sha": manifest["source_sha"],
        "handoff_sha256": handoff_sha256, "inventory_sha256": digest(canonical(inventory)),
        "target_sha256": digest(canonical(target)),
        "target_identity_sha256": target["target_identity_sha256"],
        "gitea_identity_sha256": target["gitea_identity_sha256"],
        "repository_identity_sha256": target["repository_identity_sha256"],
        "approval_reference": target["approval_reference"], "decision": "BLOCKED",
        "status": "BLOCKED", "reason": "UNKNOWN_STATE", "rollback": manifest["rollback"],
        "action_inputs": target["action_inputs"], "site_executor": target["site_executor"],
        "actions": [],
    }

    def blocked(reason: str, decision: str = "BLOCKED") -> dict:
        plan.update(reason=reason, decision=decision)
        return document(plan, "plan")

    if target["action_inputs"]["repo-bootstrap"]["staging_ref"] != "refs/heads/sync/platform-" + manifest["source_sha"]:
        return blocked("IDENTITY_MISMATCH")

    if inventory["target_identity_sha256"] != target["target_identity_sha256"] or (
        inventory["repository_identity_sha256"] is not None and
        inventory["repository_identity_sha256"] != target["repository_identity_sha256"]
    ):
        return blocked("IDENTITY_MISMATCH")
    if inventory["gitea_state"] == "unknown" or inventory["runner_state"] == "unknown" or \
            inventory["inbound_state"] == "unknown":
        return blocked("UNKNOWN_STATE")
    if inventory["ai_present"] or inventory["inbound_state"] == "timer" or (
        inventory["runner_state"] == "enabled" and inventory["runner_scope"] != "platform-only"
    ):
        return blocked("UNSAFE_HOST")
    absent = inventory["gitea_state"] == "absent"
    protection = inventory["protection"]
    if inventory["repository_identity_sha256"] is None and (
        any(protection[key] for key in ("direct_push_denied", "force_push_denied", "human_merge_only"))
        or protection["required_ci"]
    ):
        return blocked("INCONSISTENT_INVENTORY")
    if absent and (inventory["gitea_version"] is not None or inventory["gitea_identity_sha256"] is not None
                   or inventory["gitea_healthy"] or inventory["repository_identity_sha256"] is not None
                   or inventory["source_sha"] is not None or inventory["runner_state"] == "enabled"
                   or inventory["inbound_state"] != "disabled"):
        return blocked("INCONSISTENT_INVENTORY")
    if not absent and (inventory["gitea_version"] is None or inventory["gitea_identity_sha256"] is None
                       or not inventory["gitea_healthy"]):
        return blocked("UNKNOWN_STATE")
    if not absent and inventory["gitea_identity_sha256"] != target["gitea_identity_sha256"]:
        return blocked("IDENTITY_MISMATCH")
    if inventory["source_sha"] is not None and inventory["repository_identity_sha256"] is None:
        return blocked("INCONSISTENT_INVENTORY")
    if not absent and (inventory["gitea_version"] != target["gitea_version"] or
                       inventory["source_sha"] not in (None, manifest["source_sha"])):
        return blocked("VERSION_CHANGE", "controlled-upgrade")
    if inventory["rollback"] != manifest["rollback"]:
        return blocked("RECOVERY_MISSING")
    if absent:
        baseline = digest(canonical({"state": "uninstalled",
                                    "target_identity_sha256": target["target_identity_sha256"]}))
        if inventory["rollback"]["kind"] != "uninstalled" or inventory["rollback"]["identity_sha256"] != baseline:
            return blocked("RECOVERY_MISSING")
    elif inventory["rollback"]["kind"] != "snapshot" or not (
        inventory["backup_verified"] and inventory["restore_verified"]
    ) or inventory["rollback"]["source_sha"] != inventory["source_sha"]:
        return blocked("RECOVERY_MISSING")
    done = {
        "gitea-adoption": not absent,
        "repo-bootstrap": inventory["repository_identity_sha256"] == target["repository_identity_sha256"]
                          and inventory["source_sha"] == manifest["source_sha"],
        "protected-main": all(protection[key] for key in
                              ("direct_push_denied", "force_push_denied", "human_merge_only")),
        "required-ci": sorted(protection["required_ci"]) == sorted(target["required_ci"]),
        "runner": inventory["runner_state"] == "enabled" and inventory["runner_scope"] == "platform-only",
        "one-shot-inbound": inventory["inbound_state"] == "one-shot" and inventory["source_sha"] == manifest["source_sha"],
        # A canary is fresh evidence. It is never inferred from settings or skipped as a no-op.
        "canary": False,
    }
    plan.update(status="PLANNED", reason="READY",
                decision="first-install" if absent else (
                    "adopt" if all(done[action] for action in ACTIONS[:-1]) else "adopt-with-remediation"),
                actions=[{"action": action, "mode": "no-op" if done[action] else "change"}
                         for action in ACTIONS])
    return document(plan, "plan")


def operation_request(plan: dict, action: str, direction: str, *, dry_run: bool) -> dict:
    document(plan, "plan")
    require(plan["status"] == "PLANNED" and plan["reason"] == "READY", "ADOPTION_BLOCKED")
    require(action in ACTIONS and direction in ("apply", "rollback"), "ACTION_INVALID")
    require([entry["action"] for entry in plan["actions"]] == ACTIONS, "PLAN_INVALID")
    # #270 defines the action protocol. B1/B2 must bind and validate the site executor.
    # An approval reference alone can never enable a shell/API/installer here.
    require(dry_run, "SITE_EXECUTOR_NOT_BOUND")
    mode = next(entry["mode"] for entry in plan["actions"] if entry["action"] == action)
    return document({"contract_version": "platform-bootstrap-request/v1",
        "plan_sha256": digest(canonical(plan)), "source_sha": plan["source_sha"],
        "target_identity_sha256": plan["target_identity_sha256"],
        "gitea_identity_sha256": plan["gitea_identity_sha256"],
        "repository_identity_sha256": plan["repository_identity_sha256"],
        "approval_reference": plan["approval_reference"], "action": action,
        "direction": direction, "mode": mode, "rollback": plan["rollback"],
        "exact_inputs": plan["action_inputs"][action], "site_executor": plan["site_executor"],
        "predecessor_actions": ACTIONS[:ACTIONS.index(action)],
        "status": "DRY_RUN", "execution": "NOT RUN"}, "request")


def readback(request: dict, observation: dict) -> dict:
    document(request, "request")
    document(observation, "observation")
    require(observation["request_sha256"] == digest(canonical(request)), "IDENTITY_MISMATCH")
    for field in ("target_identity_sha256", "gitea_identity_sha256", "repository_identity_sha256"):
        require(observation[field] == request[field], "IDENTITY_MISMATCH")
    expected_source = request["source_sha"] if request["direction"] == "apply" else request["rollback"]["source_sha"]
    require(observation["source_sha"] == expected_source, "IDENTITY_MISMATCH")
    checks = {"identity", "no-op", "deliberate-failure", "recovery"}
    checks.add("negative-permission")
    if request["action"] in ("required-ci", "canary"):
        checks.add("required-ci")
    if request["action"] == "canary" and request["direction"] == "apply":
        checks.update(("human-merge", "provenance"))
        require(observation["result"] != "PASS" or observation["company_merge_sha"] is not None,
                "EVIDENCE_INCOMPLETE")
    if observation["result"] == "PASS":
        require(checks <= set(observation["checks"]), "EVIDENCE_INCOMPLETE")
    return {"status": observation["result"], "validation_scope": "declared-observation-only",
            "evidence_layer": observation["evidence_layer"], "execution": "NOT RUN",
            "request_sha256": digest(canonical(request)),
            "observation_sha256": digest(canonical(observation))}
