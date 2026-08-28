import os
import subprocess

desktop_dir = os.path.expanduser(r"~\Desktop")
target_vbs = r"C:\Users\Suresh\.gemini\antigravity-ide\scratch\nova-pro-assistant\ParuApp.vbs"
work_dir = r"C:\Users\Suresh\.gemini\antigravity-ide\scratch\nova-pro-assistant"

shortcuts = [
    os.path.join(desktop_dir, "Paru.lnk"),
    os.path.join(desktop_dir, "PARU AI - VantagePoint.lnk")
]

for s in shortcuts:
    vbs_content = f"""
Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "{s}"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "{target_vbs}"
oLink.WorkingDirectory = "{work_dir}"
oLink.Description = "Paru AI Desktop Assistant"
oLink.Save
"""
    vbs_path = os.path.join(os.environ.get("TEMP", "."), "make_paru_lnk.vbs")
    with open(vbs_path, "w", encoding="utf-8") as f:
        f.write(vbs_content)
    subprocess.run(["cscript", "//Nologo", vbs_path])
    print(f"Created: {s} -> {os.path.exists(s)}")
