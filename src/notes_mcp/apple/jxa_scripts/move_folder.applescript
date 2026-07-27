on run argv
    set srcId to item 1 of argv
    set destId to item 2 of argv
    tell application "Notes"
        set srcFolder to folder id srcId
        set destFolder to folder id destId
        move srcFolder to destFolder
    end tell
    return "ok"
end run
