# Meeting 41 B — human avatar assets

- `agent-girl.png` — human appearance for the AI seat (Sofia / girl reference)
- `agent-girl.mp4` — looping talking-head style visual used in the meeting stage

## Replace with your Desktop video

Copy your reference clip into this folder as `agent-girl.mp4`:

```powershell
copy "C:\Users\azureuser\Desktop\2026-08-03_01-01-17.mp4" org_platform\static\assets\avatar\agent-girl.mp4
```

Or upload from the Meeting 41 B room UI (**Upload avatar video**), or:

```bash
python tools/ingest_41b_avatar.py "C:/Users/azureuser/Desktop/2026-08-03_01-01-17.mp4"
```
