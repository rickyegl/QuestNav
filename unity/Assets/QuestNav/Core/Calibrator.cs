using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Google.Protobuf.Collections;
using Oculus.Interaction;
using Oculus.Interaction.Surfaces;
using QuestNav.Utils;
using TMPro;
using UnityEngine;
using UnityEngine.PlayerLoop;
using UnityEngine.UI;

public class Calibrator : MonoBehaviour
{
    // Start is called once before the first execution of Update after the MonoBehaviour is created

    [SerializeField]
    private GameObject testSphere;

    [SerializeField]
    private RayInteractor rightInteractor;

    [SerializeField]
    private PlaneSurface floor;

    [SerializeField]
    private GameObject indicatorDown;

    [SerializeField]
    private GameObject indicatorUp;

    [SerializeField]
    private TMP_Dropdown layoutSelector;

    [SerializeField]
    private GameObject buttonsList;

    [SerializeField]
    private GameObject buttonPrefab;

    [SerializeField]
    private TextAsset[] jsons;

    private TagData selectedTag;

    [SerializeField]
    private LineRenderer lineRenderer;
    private FieldLayoutData activeFieldLayoutData;
    public int activeFieldLayoutIndex;

    [SerializeField]
    private Button createFieldButton;

    [SerializeField]
    private TMP_InputField fieldNameText;

    private List<Field> fields;

    private Field activeField;
    public int activeFieldIndex;

    [SerializeField]
    private TMP_Dropdown fieldSelector;

    [SerializeField]
    private GameObject debugAprilTag;

    [SerializeField]
    private GameObject fieldObject;

    [SerializeField]
    private GameObject anchorsLocation;

    public int TrackedTag = 18;

    void Start()
    {
        layoutSelector.ClearOptions();

        for (int i = 0; i < jsons.Length; i++)
        {
            layoutSelector.options.Add(new TMP_Dropdown.OptionData(jsons[i].name));
        }

        loadFields();

        createFieldButton.onClick.AddListener(createFieldButtonClicked);
        layoutSelector.onValueChanged.AddListener(updateTagSelection);
        updateTagSelection(0);

        indicatorDown.SetActive(false);
        indicatorUp.SetActive(false);
        lineRenderer.enabled = false;

        SetSelectedTag(18);
        Debug.Log("Set active tag to: " + selectedTag.ID);

        //createFieldButtonClicked();

    }

    void loadFields()
    {
        Debug.Log("Loading fields from " + Application.persistentDataPath + "/userTagLayouts");
        fields = new List<Field>();
        if (!System.IO.Directory.Exists(Application.persistentDataPath + "/userTagLayouts"))
        {
            System.IO.Directory.CreateDirectory(Application.persistentDataPath + "/userTagLayouts");
        }
        string[] files = System.IO.Directory.GetFiles(Application.persistentDataPath + "/userTagLayouts", "*.json");
        foreach (string file in files)
        {
            string json = System.IO.File.ReadAllText(file);
            Field field = JsonUtility.FromJson<Field>(json);
            fields.Add(field);
        }
        fieldSelector.ClearOptions();
        Debug.Log("Found " + fields.Count + " fields in userTagLayouts");
        //fieldNameText.text = "vTest";
        for (int i = 0; i < fields.Count; i++)
        {
            fieldSelector.options.Add(new TMP_Dropdown.OptionData(fields[i].fieldName));
        }
        fieldSelector.onValueChanged.AddListener(setActiveField);
        setActiveField(0);
        if (fields.Count == 0)
        {
            activeField = new Field("Default Field", 0);
            saveActiveField();
            Debug.Log("No fields found, created default field: " + activeField.fieldName);
        }

        Debug.Log("Loaded " + fields.Count + " fields");
    }

    void setActiveField(int index)
    {
        // Guard against an invalid index from the dropdown.
        if (index < 0 || index >= fieldSelector.options.Count)
        {
            Debug.LogWarning($"setActiveField called with an invalid index: {index}.");
            activeField = null;
            return;
        }

        // Find the field by name and assign it directly to activeField.
        string fieldName = fieldSelector.options[index].text;
        activeField = fields.Find(f => f.fieldName == fieldName);

        // If the field was found, update UI. Otherwise, log a warning.
        if (activeField != null)
        {
            updateTagSelection(activeField.layoutIndex);
            showExistingTags();
            LoadFieldAnchors();
            activeFieldIndex = index;
        }
        else
        {
            Debug.LogWarning($"Field '{fieldName}' selected but not found in data list.");
        }
    }

    void showExistingTags()
    {
        // Safety check to ensure we have an active field and layout data to work with.
        if (activeField == null || activeFieldLayoutData == null)
        {
            Debug.LogWarning("Cannot show existing tags because no active field or layout data is set.");
            return;
        }

        // Get all the Button components from the children of the buttonsList GameObject.
        // GetComponentsInChildren will find the Button on the child object itself.
        Button[] tagButtons = buttonsList.GetComponentsInChildren<Button>();

        // Ensure the number of buttons matches the number of tags in the current layout.
        if (tagButtons.Length != activeFieldLayoutData.tags.Count)
        {
            Debug.LogError("Mismatch between UI button count and layout tag count. Cannot update colors.");
            return;
        }
        Debug.Log($"Updating tag button colors for {tagButtons.Length} buttons based on active field '{activeField.fieldName}'.");
        // Loop through each button, which corresponds to a tag in the layout.
        for (int i = 0; i < tagButtons.Length; i++)
        {
            Button currentButton = tagButtons[i];
            TagData layoutTag = activeFieldLayoutData.tags[i]; // The tag this button represents.

            // Find the Image component to change its color.
            Image buttonImage = currentButton.GetComponent<Image>();
            if (buttonImage == null)
            {
                Debug.LogWarning($"Button for tag {layoutTag.ID} is missing an Image component.");
                continue;
            }

            // Check if a tag with the same ID exists in the saved list of the active field.
            bool tagExistsInField = activeField.tags.Exists(savedTag => savedTag.ID == layoutTag.ID);

            if (tagExistsInField)
            {
                // This tag has been saved for the current field, so color the button light green.
                buttonImage.color = new Color(0.6f, 0.9f, 0.6f, 1.0f);
            }
            else
            {
                // This tag does not exist in the current field, so keep its default color.
                // Since updateTagSelection recreates buttons from a prefab, we reset to white
                // to ensure a consistent default state.
                buttonImage.color = Color.white;
            }
        }
    }
    void createFieldButtonClicked()
    {
        Debug.Log("Creating field");
        //fieldSelector.ClearOptions();
        if (fieldNameText.text != "")
        {
            Boolean isFieldNameValid = true;
            String inputText = fieldNameText.text;
            foreach (Field iField in fields)
            {
                if (iField.fieldName == inputText)
                {
                    isFieldNameValid = false;
                    break;
                }
            }
            if (isFieldNameValid)
            {
                activeField = new Field(inputText, layoutSelector.value);
                saveActiveField();
            }
            else
            {
                Debug.LogWarning("Didn't create field, name " + fieldNameText.text + " already exists");
            }
        }
        else
        {
            Debug.LogWarning("Didn't create field, name is empty");
        }

    }

    void saveActiveField()
    {
        Debug.Log("Saving field to " + Application.persistentDataPath + "/userTagLayouts");
        if (activeField != null)
        {
            string json = JsonUtility.ToJson(activeField);
            System.IO.File.WriteAllText(Application.persistentDataPath + "/userTagLayouts/" + activeField.fieldName + ".json", json);
            print("Saved field to " + Application.persistentDataPath + "/userTagLayouts/" + activeField.fieldName + ".json");

            //fieldSelector.ClearOptions();
            for (int i = 0; i < fields.Count; i++)
            {
                if (fields[i].fieldName == activeField.fieldName)
                {
                    fields.RemoveAt(i);
                }
            }
            fields.Add(activeField);
            fieldSelector.options.Add(new TMP_Dropdown.OptionData(activeField.fieldName));
        }
        else { Debug.LogWarning("No active field to save"); }


    }

    void checkForRays()
    {
        SurfaceHit hit;
        floor.Raycast(rightInteractor.Ray, out hit, rightInteractor.MaxRayLength);

        Vector3 rayPose = hit.Point;

        testSphere.transform.position = rayPose;

        OVRInput.Button button = OVRInput.Button.PrimaryIndexTrigger;

        if (OVRInput.Get(button))
        {

        }

        if (OVRInput.GetDown(button))
        {
            indicatorUp.transform.position = rayPose;
            indicatorDown.SetActive(true);
            indicatorUp.SetActive(false);
            indicatorDown.transform.position = rayPose;
            lineRenderer.SetPosition(0, indicatorDown.transform.position);
        }
        else if (OVRInput.GetUp(button))
        {
            indicatorUp.transform.position = rayPose;
            indicatorUp.SetActive(true);
            lineRenderer.SetPosition(1, indicatorUp.transform.position);
            lineRenderer.enabled = true;
            saveActiveTagPosition();
        }
    }

    // Update is called once per frame
    void Update()
    {
        if (selectedTag != null)
        {
            checkForRays();
        }
        if (poseMap.Count > 0)
        {
            if (poseMap.ContainsKey(TrackedTag))
            {
                //SetSelectedTag(TrackedTag);
                Pose originPose = getFieldOrigin(poseMap[TrackedTag], Conversions.FrcPoseToUnity(getTagFromId(TrackedTag).pose.translation.toVector3(), getTagFromId(TrackedTag).pose.rotation.toQuaternion()));
                setField(poseMap[TrackedTag], originPose);
            }
            else
            {
                int backupTagId = poseMap.Keys.First();
                //SetSelectedTag(backupTagId);
                Pose originPose = getFieldOrigin(poseMap[backupTagId], Conversions.FrcPoseToUnity(getTagFromId(backupTagId).pose.translation.toVector3(), getTagFromId(backupTagId).pose.rotation.toQuaternion()));
                setField(poseMap[backupTagId], originPose);
            }

        }

    }

    private List<OVRSpatialAnchor> _anchorInstances = new List<OVRSpatialAnchor>();
    private List<Guid> _anchorUuids = new List<Guid>();

    private async Task<Guid> SetupAnchorAsync(OVRSpatialAnchor anchor, bool saveAnchor)
    {
        // Keep checking for a valid and localized anchor state
        if (!await anchor.WhenLocalizedAsync())
        {
            Debug.LogError($"Unable to create anchor.");
            Destroy(anchor.gameObject);
            throw new InvalidOperationException("Anchor could not be localized.");
        }

        // Add the anchor to the list of all instances
        _anchorInstances.Add(anchor);

        // save the savable (green) anchors only
        if (saveAnchor && (await anchor.SaveAnchorAsync()).Success)
        {
            // Remember UUID so you can load the anchor later
            _anchorUuids.Add(anchor.Uuid);
            return anchor.Uuid;
        }
        throw new InvalidOperationException("Anchor could not be saved.");
    }

    private Dictionary<int, OVRSpatialAnchor.UnboundAnchor> _unboundAnchorMap = new Dictionary<int, OVRSpatialAnchor.UnboundAnchor>();
    private Dictionary<int, Pose> poseMap = new Dictionary<int, Pose>();

    public MapField<int, int> GetPoseMap()
    {
        MapField<int, int> map = new MapField<int, int>();
        foreach (var kvp in activeFieldLayoutData.tags)
        {
            int state = 0;
            int tagId = kvp.ID;
            if (poseMap.ContainsKey(tagId))
            {
                state = 1;
            }
            map.Add(tagId, state);
        }
        return map;
    }
    public async void LoadFieldAnchors()
    {
        List<Guid> guids = new List<Guid>();
        List<OVRSpatialAnchor.UnboundAnchor> unboundAnchors = new List<OVRSpatialAnchor.UnboundAnchor>();
        _unboundAnchorMap.Clear();
        if (activeField != null && activeField.tags.Count > 0)
        {
            activeField.tags.ForEach(tag =>
            {
                if (tag.anchorUuid != null && tag.anchorUuid != "")
                {
                    Guid anchorUuid = new Guid(tag.anchorUuid);
                    if (!_unboundAnchorMap.ContainsKey(tag.ID))
                    {
                        guids.Add(anchorUuid);
                    }
                }
                else
                {
                    Debug.LogWarning($"Tag {tag.ID} does not have a valid anchor UUID.");
                }
            });
            var result = await OVRSpatialAnchor.LoadUnboundAnchorsAsync(guids, unboundAnchors);
            if (result.Success)
            {
                foreach (var anchor in unboundAnchors)
                {
                    anchor.LocalizeAsync().ContinueWith(OnLocalized, anchor);
                }
            }
        }
        else
        {
            Debug.LogWarning("No active field or tags to load anchors for.");
            return;
        }

    }

    private void OnLocalized(bool success, OVRSpatialAnchor.UnboundAnchor unboundAnchor)
    {
        if (!success)
        {
            Debug.LogError("Failed to localize unbound anchor with UUID: " + unboundAnchor.Uuid);
            return;
        }

        if (unboundAnchor.TryGetPose(out Pose pose))
        {
            //unboundAnchor.Uuid
            int tagId = getTagIdFromAnchorUuid(unboundAnchor.Uuid);
            poseMap[tagId] = pose;
            GameObject debugTag = Instantiate(debugAprilTag);
            debugTag.name = tagId.ToString();
            debugTag.transform.parent = anchorsLocation.transform;
            debugTag.transform.position = pose.position;
            debugTag.transform.rotation = pose.rotation;

        }
        else
        {
            Debug.LogError("Failed to get pose for unbound anchor with UUID: " + unboundAnchor.Uuid);
        }
    }

    private int getTagIdFromAnchorUuid(Guid anchorUuid)
    {
        // Find the tag ID associated with the given anchor UUID
        foreach (var tag in activeField.tags)
        {
            if (tag.anchorUuid == anchorUuid.ToString())
            {
                return tag.ID;
            }
        }
        return -1; // Return -1 if no matching tag is found
    }

    private void Awake()
    {

    }

    void updateTagSelection(int index)
    {
        foreach (Transform child in buttonsList.transform)
        {
            Destroy(child.gameObject);
        }
        activeFieldLayoutData = JsonUtility.FromJson<FieldLayoutData>(jsons[index].text);
        print("Showing " + activeFieldLayoutData.tags.Count + " tags");
        activeFieldLayoutIndex = index;
        for (int i = 0; i < activeFieldLayoutData.tags.Count; i++)
        {
            GameObject button = Instantiate(buttonPrefab, buttonsList.transform);
            button.SetActive(true);
            button.GetComponentInChildren<TMP_Text>().text = "Apriltag " + activeFieldLayoutData.tags[i].ID.ToString();
            TagData tagData = activeFieldLayoutData.tags[i];
            button.GetComponentInChildren<Button>().onClick.AddListener(() => OnTagButtonClicked(tagData));
        }
    }

    void OnTagButtonClicked(TagData tagData)
    {
        print("Tag ID: " + tagData.ID);
        selectedTag = tagData;
        TrackedTag = selectedTag.ID;

    }

    TagData getTagFromId(int id)
    {
        return activeFieldLayoutData.tags.Find(tag => tag.ID == id);
    }

    public void SetSelectedTag(int tagId)
    {
        // Find the tag in the active layout data
        selectedTag = activeFieldLayoutData.tags.Find(tag => tag.ID == tagId);
        TrackedTag = tagId;
        if (selectedTag != null)
        {
            //Debug.Log("Selected tag ID: " + selectedTag.ID);
            indicatorDown.SetActive(true);
            indicatorUp.SetActive(false);
            lineRenderer.enabled = false;
        }
        else
        {
            Debug.LogWarning("Tag with ID " + tagId + " not found in the active layout.");
        }
    }

    async void saveActiveTagPosition()
    {

        // 1. Determine the measured world pose of the AprilTag
        Transform definiteTransform = new GameObject().transform; // Temporary for calculation
        definiteTransform.position = (indicatorDown.transform.position + indicatorUp.transform.position) / 2f;

        // This orients definiteTransform's local Z along (indicatorUp - indicatorDown)
        // and its local Y along world up.
        definiteTransform.rotation = Quaternion.LookRotation(indicatorUp.transform.position - indicatorDown.transform.position, Vector3.up);

        // This +90 degree rotation implies that the (indicatorUp - indicatorDown) direction
        // corresponds to the tag's local X-axis (or -X), and you're rotating it
        // so that the tag's conceptual "forward" (what JSON considers Z-forward) aligns.
        // Ensure this correctly reflects your tag's physical orientation vs. JSON definition.
        definiteTransform.rotation = Quaternion.Euler(definiteTransform.rotation.eulerAngles.x, definiteTransform.rotation.eulerAngles.y + 90f, 0f);

        // These are the *actual measured* world coordinates of the tag
        Vector3 tagWorldPosition = definiteTransform.position;
        Quaternion tagWorldRotation = definiteTransform.rotation;

        Destroy(definiteTransform.gameObject); // Clean up the temporary GameObject

        // 2. Update the debug visualizer (optional, but good for verification)


        // DO NOT DO THIS - IT USES JSON Z AS WORLD Y, WHICH IS WRONG HERE.
        // debugAprilTag.transform.position = new Vector3(debugAprilTag.transform.position.x, (float)selectedTag.pose.translation.z, debugAprilTag.transform.position.z);


        // 3. Get the tag's pose in Field Coordinates (from JSON, converted to Unity's system)
        // JSON X -> Unity X
        // JSON Z (elevation in JSON) -> Unity Y
        // JSON Y (depth/forward in JSON's XY plane) -> Unity Z
        Vector3 tagPositionInFieldCoords = Conversions.FrcTranslationToUnity(selectedTag.pose.translation.toVector3());//getActiveTagPositionInFieldCoords();
        debugAprilTag.transform.position = tagWorldPosition;
        debugAprilTag.transform.position = new Vector3(debugAprilTag.transform.position.x, tagPositionInFieldCoords.y, debugAprilTag.transform.position.z);
        debugAprilTag.transform.rotation = tagWorldRotation;
        foreach (Transform child in debugAprilTag.transform)
        {
            child.gameObject.SetActive(false);
        }
        foreach (Transform child in anchorsLocation.transform)
        {
            if (child.name == selectedTag.ID.ToString())
            {
                Destroy(child.gameObject);
            }
        }

        definiteTransform.transform.position = new Vector3(definiteTransform.transform.position.x, tagPositionInFieldCoords.y, definiteTransform.transform.position.z);
        //Pose fieldOrigin = getFieldOrigin(definiteTransform.transform.GetPose(),new Pose(tagPositionInFieldCoords, Conversions.FrcQuaternionToUnity(selectedTag.pose.rotation.toQuaternion())));
        //setField(definiteTransform.transform.GetPose(), fieldOrigin);
        poseMap[TrackedTag] = definiteTransform.transform.GetPose();
        Debug.Log("Creating anchor at position: " + definiteTransform.transform.position + " with rotation: " + definiteTransform.transform.rotation);
        Guid guid = await CreateAnchorAt(definiteTransform.transform.GetPose());
        //sout if every object in the if below is null
        Debug.Log("Active field: " + activeField.fieldName);
        Debug.Log("Selected tag ID: " + selectedTag.ID);
        Debug.Log("activeField.tags.Count: " + activeField.tags.Count);

        if (activeField.tags.Find(t => t.ID == selectedTag.ID) != null)
        {
            activeField.tags.Remove(activeField.tags.Find(t => t.ID == selectedTag.ID));
            Debug.LogWarning("Tag with ID " + selectedTag.ID + " already exists in the field. Replacing it.");
        }
        Debug.Log("Adding tag with ID " + selectedTag.ID + " to the field with anchor UUID: " + guid.ToString());
        activeField.tags.Add(new TagData
        {
            ID = selectedTag.ID,
            anchorUuid = guid.ToString(),
        });

        saveActiveField();

    }

    Pose getFieldOrigin(Pose worldPose, Pose tagUnityPose)
    {
        //Debug.Log("World Rotation: " + worldPose.rotation.eulerAngles.y + " Tag Rotation: " + tagUnityPose.rotation.eulerAngles.y);
        Quaternion fieldOriginWorldRotation = worldPose.rotation * Quaternion.Inverse(tagUnityPose.rotation);
        Vector3 fieldOriginWorldPosition = worldPose.position - (fieldOriginWorldRotation * tagUnityPose.position);
        return new Pose(fieldOriginWorldPosition, fieldOriginWorldRotation);
    }

    void setField(Pose worldPose, Pose originPose)
    {
        // 5. Apply to the fieldObject

        fieldObject.transform.position = originPose.position;
        fieldObject.transform.rotation = originPose.rotation;
        //Debug.Log("Set field position to: " + vrCameraRoot.transform.position + " and rotation to: " + vrCameraRoot.transform.rotation);
    }

    async Task<Guid> CreateAnchorAt(Pose saveLocation)
    {
        GameObject anchorObject = Instantiate(debugAprilTag);

        anchorObject.transform.parent = anchorsLocation.transform;
        anchorObject.transform.position = saveLocation.position;
        anchorObject.transform.rotation = saveLocation.rotation;
        anchorObject.AddComponent<OVRSpatialAnchor>();
        OVRSpatialAnchor anchor = anchorObject.GetComponent<OVRSpatialAnchor>();
        anchor.enabled = true;
        Guid guid = await SetupAnchorAsync(anchor, true);
        Debug.Log("Created anchor with UUID: " + guid);
        return guid;
    }

    /// <summary>
    /// Given a tagId and the current real-world headset pose (2D on floor + yaw),
    /// compute the real-world pose of the tag using the known field-layout pose,
    /// create an anchor there, and save it to the active field.
    /// 
    /// headsetWorldPose: the headset/world pose when the tag was observed. If you only have 2D+Yaw,
    /// provide position.y=0 and rotation=(0,yaw,0). We will align the tag's world Y to the tag's field Y height.
    /// </summary>
    public async Task<bool> CalibrateTagFromHeadset2DAsync(Pose headsetWorldPose)
    {
        if (activeFieldLayoutData == null)
        {
            Debug.LogWarning("No activeFieldLayoutData set.");
            return false;
        }
        if (activeField == null)
        {
            Debug.LogWarning("No active field selected.");
            return false;
        }
        if (selectedTag == null)
        {
            Debug.LogWarning("No active tag selected. Please select a tag first.");
            return false;
        }


        int tagId = selectedTag.ID;

        // Tag pose in field coordinates (Unity)
        Vector3 tagPosField = Conversions.FrcTranslationToUnity(selectedTag.pose.translation.toVector3());
        Quaternion tagRotField = Conversions.FrcQuaternionToUnity(selectedTag.pose.rotation.toQuaternion());
        Pose tagFieldPose = new Pose(tagPosField, tagRotField);

        // Use provided 2D+Yaw headset pose as the measured tag world pose.
        Vector3 headsetPosWorld = headsetWorldPose.position;
        Quaternion headsetRotWorld = headsetWorldPose.rotation;

        Pose measuredTagWorldPose = new Pose(headsetPosWorld, headsetRotWorld);

        // Align the measured tag world Y to the tag's field Y
        measuredTagWorldPose.position = new Vector3(
            measuredTagWorldPose.position.x,
            tagPosField.y,
            measuredTagWorldPose.position.z
        );

        // Debug visualization
        if (debugAprilTag != null)
        {
            debugAprilTag.transform.position = measuredTagWorldPose.position;
            debugAprilTag.transform.rotation = measuredTagWorldPose.rotation;
            foreach (Transform c in debugAprilTag.transform) c.gameObject.SetActive(false);
        }

        // Save pose
        poseMap[tagId] = measuredTagWorldPose;

        try
        {
            Guid guid = await CreateAnchorAt(measuredTagWorldPose);

            // Replace existing entry for this tag in the field
            var existing = activeField.tags.Find(t => t.ID == tagId);
            if (existing != null) activeField.tags.Remove(existing);

            activeField.tags.Add(new TagData
            {
                ID = tagId,
                anchorUuid = guid.ToString(),
            });

            saveActiveField();
            TrackedTag = tagId;
            return true;
        }
        catch (Exception e)
        {
            Debug.LogError($"Failed to create/save anchor for tag {tagId}: {e}");
            return false;
        }

    }
}








[System.Serializable]
public class QuaternionData
{
    public double W;
    public double X;
    public double Y;
    public double Z;
}

[System.Serializable]
public class RotationData
{
    public QuaternionData quaternion;
    public Quaternion toQuaternion()
    {
        return new Quaternion(
            (float)quaternion.X,
            (float)quaternion.Y,
            (float)quaternion.Z,
            (float)quaternion.W
        );
    }
}

[System.Serializable]
public class TranslationData
{
    public double x;
    public double y;
    public double z;

    public Vector3 toVector3()
    {
        return new Vector3(
            (float)x,
            (float)y,
            (float)z
        );
    }
}

[System.Serializable]
public class PoseData
{
    public TranslationData translation;
    public RotationData rotation;
}

[System.Serializable]
public class TagData
{
    public int ID;
    public PoseData pose;
    public String anchorUuid;
}

[System.Serializable]
public class FieldData
{
    public double length;
    public double width;
}

[System.Serializable]
public class FieldLayoutData
{
    public List<TagData> tags; // Use List for JSON arrays
    public FieldData field;
}

[System.Serializable] // This attribute is crucial for JsonUtility
public class Field
{
    public string fieldName;
    public List<TagData> tags;
    public int layoutIndex;
    public Field(string fieldName, int layoutIndex)
    {
        this.fieldName = fieldName;
        tags = new List<TagData>();
        this.layoutIndex = layoutIndex;
    }

}