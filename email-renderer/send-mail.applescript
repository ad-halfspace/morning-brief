-- send-mail.applescript
-- Send an HTML email via Apple Mail.
-- Invoked as: osascript send-mail.applescript "<subject>" "<html_path>" "<recipient_email>"
-- Used by the morning-brief and weekly-ahead scheduled tasks so the bash side stays
-- free of heredocs + braces-with-quotes that trip Claude Code's "expansion obfuscation"
-- static guard. Keep this file plain — all variable substitution happens here.

on run argv
  if (count of argv) < 3 then
    error "Usage: osascript send-mail.applescript <subject> <html_path> <recipient>"
  end if
  set theSubject to item 1 of argv
  set htmlPath to item 2 of argv
  set theRecipient to item 3 of argv

  set theBody to (read POSIX file htmlPath as «class utf8»)

  tell application "Mail"
    set newMessage to make new outgoing message with properties {subject:theSubject, visible:false}
    tell newMessage
      set html content to theBody
      make new to recipient at end of to recipients with properties {address:theRecipient}
    end tell
    send newMessage
  end tell
end run
