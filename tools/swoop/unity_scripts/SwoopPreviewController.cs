using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Playables;

public class SwoopPreviewController : MonoBehaviour {
    public Animator animOfficialRamjet;
    public Animator animSwoop;
    public AnimationClip swoopWingFlapClip;

    private Transform trRamjet;
    private Transform trSwoop;
    private SkinnedMeshRenderer smrRobotRamjet;
    private SkinnedMeshRenderer smrVehRamjet;
    private SkinnedMeshRenderer smrRobotSwoop;
    private SkinnedMeshRenderer smrVehSwoop;

    private bool isVehicleMode = false;
    private float flapTime = 0f;

    private void Start() {
        if (animOfficialRamjet == null) {
            var go = GameObject.Find("Ramjet_Official_Reference");
            if (go != null) animOfficialRamjet = go.GetComponent<Animator>();
        }
        if (animSwoop == null) {
            var go = GameObject.Find("Swoop_Candidate");
            if (go != null) animSwoop = go.GetComponent<Animator>();
        }
        if (animOfficialRamjet != null) {
            trRamjet = FindChildRecursive(animOfficialRamjet.transform, "transformed");
            foreach (var smr in animOfficialRamjet.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
                if (smr.name.Contains("_00")) smrRobotRamjet = smr;
                else if (smr.name.Contains("_01")) smrVehRamjet = smr;
            }
        }
        if (animSwoop != null) {
            trSwoop = FindChildRecursive(animSwoop.transform, "transformed");
            foreach (var smr in animSwoop.GetComponentsInChildren<SkinnedMeshRenderer>(true)) {
                if (smr.name.Contains("_00")) smrRobotSwoop = smr;
                else if (smr.name.Contains("_01")) smrVehSwoop = smr;
            }
        }
        Debug.Log("[SwoopPreviewController] Initialized (with Native 58-Frame Wing-Flap support).");
    }

    private void Update() {
        if (isVehicleMode && swoopWingFlapClip != null && trSwoop != null) {
            flapTime = (flapTime + Time.deltaTime) % Mathf.Max(0.1f, swoopWingFlapClip.length);
            swoopWingFlapClip.SampleAnimation(trSwoop.gameObject, flapTime);
        }
    }

    public void SetVehiclePreviewMode(bool vehicle) {
        isVehicleMode = vehicle;
        if (trRamjet != null) trRamjet.gameObject.SetActive(vehicle);
        if (trSwoop != null) trSwoop.gameObject.SetActive(vehicle);
        if (smrRobotRamjet != null) smrRobotRamjet.enabled = !vehicle;
        if (smrVehRamjet != null) { smrVehRamjet.gameObject.SetActive(vehicle); smrVehRamjet.enabled = vehicle; }
        if (smrRobotSwoop != null) smrRobotSwoop.enabled = !vehicle;
        if (smrVehSwoop != null) { smrVehSwoop.gameObject.SetActive(vehicle); smrVehSwoop.enabled = vehicle; }
    }

    private Transform FindChildRecursive(Transform parent, string name) {
        if (parent == null) return null;
        if (parent.name == name) return parent;
        for (int i = 0; i < parent.childCount; i++) {
            var found = FindChildRecursive(parent.GetChild(i), name);
            if (found != null) return found;
        }
        return null;
    }
}
