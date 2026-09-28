# Contract provenance

The following authoritative files were copied byte-for-byte from `serda-dev/linguai-dataset-quality` at main commit `39c17b4b441b31112a1db6159380a9a034a1bef2`. Their text was compared against GitHub before inclusion here. SHA-256 fingerprints:

| Path | SHA-256 |
| --- | --- |
| `prompts/turkish_cpt_quality_teacher_v2.txt` | `6b71a4690559f7f9b01f489aae65872f222def15f9220b7311a9c70169ee3f68` |
| `prompts/teacher_user_v1.txt` | `4a937cf0e6b4a4337f2b1c7d2580ceaa7301429d8f28ca3eacc9aaa038283a8d` |
| `schemas/teacher_label_v1.schema.json` | `341c3979893adb38761fe74fad098383ce5aa3dfa417af20c297f58552d053a0` |
| `docs/requirements/TURKISH_CPT_DATA_QUALITY_SPEC_v1.md` | `14cdeb6b025aeb0ab33214ac9dff63dd9b55c30b710b83db0e04480b5bf0bcf2` |

The teacher system prompt is a strict versioned interface. A change requires a new prompt version, explicit review, a fresh provenance fingerprint and calibration; never edit v2 in place.
