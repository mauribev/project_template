-- Export a .docx to PDF with Microsoft Word, so the layout check sees exactly
-- what Word renders. Called by verify_layout.py; not meant to be run by hand.
-- Arguments: the .docx path and the .pdf path, both inside Word's sandbox
-- container, where Word can read and write without asking for file access.
on run argv
    set inPath to item 1 of argv
    set outPath to item 2 of argv
    tell application "Microsoft Word"
        open (POSIX file inPath)
        set d to active document
        save as d file name outPath file format format PDF
        close d saving no
    end tell
end run
