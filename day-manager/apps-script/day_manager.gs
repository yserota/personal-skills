/**
 * Day Manager — Google Apps Script
 *
 * Exports your Gmail and Google Calendar to a Google Drive folder each morning.
 * Google Drive for Desktop then syncs those files to your local machine,
 * where the Cursor skill can read them.
 *
 * SETUP (one time):
 *   1. Go to https://script.google.com → New project
 *   2. Paste this entire file, replacing any existing code
 *   3. Click Save (floppy disk icon), name the project "day-manager"
 *   4. Run the "setup" function once (select it in the dropdown → Run)
 *   5. Approve the permission prompt (Gmail + Calendar + Drive read/write)
 *   6. Done — runs automatically at 8am every day
 *
 * OUTPUT FILES (in Google Drive → day-manager → YYYY-MM-DD):
 *   gmail.txt      — recent email threads
 *   calendar.txt   — today's and tomorrow's calendar events
 */

// ── Config ────────────────────────────────────────────────────────────────────

var FOLDER_NAME          = "day-manager";   // Root folder name in Google Drive
var MAX_THREADS          = 50;              // Max Gmail threads to fetch
var HOURS_BACK           = 24;              // How many hours back to fetch Gmail
var TRIGGER_HOUR         = 8;              // Hour (0–23) to run the daily export
var GEMINI_WORK_DAYS_BACK = 3;             // How many work days back to fetch Gemini notes

// ── Entry points ──────────────────────────────────────────────────────────────

/**
 * Run this once to create the Drive folder and register the daily trigger.
 * Also runs exportAll() immediately so you can verify the output right away.
 */
function setup() {
  getOrCreateRootFolder();

  // Remove any existing triggers to avoid duplicates
  ScriptApp.getProjectTriggers().forEach(function(t) {
    ScriptApp.deleteTrigger(t);
  });

  // Daily trigger at TRIGGER_HOUR
  ScriptApp.newTrigger("exportAll")
    .timeBased()
    .everyDays(1)
    .atHour(TRIGGER_HOUR)
    .create();

  Logger.log("Setup complete. Daily trigger set for " + TRIGGER_HOUR + ":00.");

  // Run immediately to produce today's files
  exportAll();
}

/**
 * Main export — called daily by the trigger (or manually for testing).
 */
function exportAll() {
  var folder = getTodayFolder();
  exportGmail(folder);
  exportCalendar(folder);
  exportGeminiNotes(folder);
  Logger.log("Day Manager export complete for " + getTodayDateString() + ".");
}

// ── Drive helpers ─────────────────────────────────────────────────────────────

function getOrCreateRootFolder() {
  var folders = DriveApp.getFoldersByName(FOLDER_NAME);
  return folders.hasNext() ? folders.next() : DriveApp.createFolder(FOLDER_NAME);
}

function getTodayDateString() {
  return Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "yyyy-MM-dd");
}

function getTodayFolder() {
  var dateStr = getTodayDateString();
  var root    = getOrCreateRootFolder();
  var sub     = root.getFoldersByName(dateStr);
  return sub.hasNext() ? sub.next() : root.createFolder(dateStr);
}

/**
 * Write (or overwrite) a plain-text file in a Drive folder.
 */
function writeFile(folder, filename, content) {
  var existing = folder.getFilesByName(filename);
  while (existing.hasNext()) {
    existing.next().setTrashed(true);
  }
  folder.createFile(filename, content, MimeType.PLAIN_TEXT);
}

// ── Gmail export ──────────────────────────────────────────────────────────────

function exportGmail(folder) {
  var tz      = Session.getScriptTimeZone();
  var cutoff  = new Date(Date.now() - HOURS_BACK * 3600 * 1000);
  var dateStr = Utilities.formatDate(cutoff, tz, "yyyy/MM/dd");
  var query   = "after:" + dateStr + " -category:promotions -category:social";

  var threads = GmailApp.search(query, 0, MAX_THREADS);
  var now     = Utilities.formatDate(new Date(), tz, "EEEE, MMMM d yyyy");

  var lines = [
    "GMAIL DIGEST — " + now,
    "Fetched: " + threads.length + " threads (last " + HOURS_BACK + "h, max " + MAX_THREADS + ")",
    repeat("=", 72),
    ""
  ];

  if (threads.length === 0) {
    lines.push("No emails found in the configured window.");
  }

  for (var i = 0; i < threads.length; i++) {
    var thread   = threads[i];
    var messages = thread.getMessages();
    var latest   = messages[messages.length - 1];

    var subject  = thread.getFirstMessageSubject() || "(no subject)";
    var from     = latest.getFrom();
    var date     = Utilities.formatDate(latest.getDate(), tz, "MMM d, HH:mm");
    var body     = latest.getPlainBody().replace(/\r\n/g, "\n").trim();
    var preview  = body.substring(0, 800);
    if (body.length > 800) preview += "\n[...truncated]";

    lines.push("[" + (i + 1) + "] " + subject);
    lines.push("    From:    " + from);
    lines.push("    Date:    " + date);
    if (messages.length > 1) {
      lines.push("    Thread:  " + messages.length + " messages");
    }
    lines.push("    ---");
    lines.push(preview);
    lines.push("");
    lines.push(repeat("-", 72));
    lines.push("");
  }

  writeFile(folder, "gmail.txt", lines.join("\n"));
  Logger.log("Gmail: exported " + threads.length + " threads → gmail.txt");
}

// ── Gemini Notes export ───────────────────────────────────────────────────────

/**
 * Exports meeting notes from emails labelled "Gemini" to gemini_notes.txt.
 * Gemini in Google Meet sends structured post-meeting summaries to this label.
 * If the label doesn't exist the file is written empty and a warning is logged.
 */
function exportGeminiNotes(folder) {
  var tz     = Session.getScriptTimeZone();
  var cutoff = getWorkDaysCutoff(GEMINI_WORK_DAYS_BACK);
  var now    = Utilities.formatDate(new Date(), tz, "EEEE, MMMM d yyyy");
  var cutoffStr = Utilities.formatDate(cutoff, tz, "EEE MMM d");

  var label = GmailApp.getUserLabelByName("Gemini");
  if (!label) {
    writeFile(folder, "gemini_notes.txt",
      "GEMINI MEETING NOTES — " + now + "\n" +
      "No 'Gemini' label found in this Gmail account.\n"
    );
    Logger.log("Gemini Notes: label not found — wrote empty gemini_notes.txt");
    return;
  }

  var threads = label.getThreads(0, MAX_THREADS);
  var recent  = threads.filter(function(t) {
    return t.getLastMessageDate() >= cutoff;
  });

  var lines = [
    "GEMINI MEETING NOTES — " + now,
    "Fetched: " + recent.length + " notes (last " + GEMINI_WORK_DAYS_BACK + " work days since " + cutoffStr + ", max " + MAX_THREADS + ")",
    repeat("=", 72),
    ""
  ];

  if (recent.length === 0) {
    lines.push("No Gemini meeting notes in the configured window.");
  }

  for (var i = 0; i < recent.length; i++) {
    var thread   = recent[i];
    var messages = thread.getMessages();
    var latest   = messages[messages.length - 1];

    var subject  = thread.getFirstMessageSubject() || "(no subject)";
    var date     = Utilities.formatDate(latest.getDate(), tz, "MMM d, HH:mm");
    var body     = latest.getPlainBody().replace(/\r\n/g, "\n").trim();

    // Gemini notes are long and structured — use a larger preview than regular email
    var preview = body.substring(0, 3000);
    if (body.length > 3000) preview += "\n[...truncated]";

    lines.push("[" + (i + 1) + "] " + subject);
    lines.push("    Date: " + date);
    lines.push("    ---");
    lines.push(preview);
    lines.push("");
    lines.push(repeat("-", 72));
    lines.push("");
  }

  writeFile(folder, "gemini_notes.txt", lines.join("\n"));
  Logger.log("Gemini Notes: exported " + recent.length + " notes → gemini_notes.txt");
}

// ── Calendar export ───────────────────────────────────────────────────────────

function exportCalendar(folder) {
  var tz        = Session.getScriptTimeZone();
  var todayStart = new Date();
  todayStart.setHours(0, 0, 0, 0);

  var dayAfterTomorrow = new Date(todayStart);
  dayAfterTomorrow.setDate(dayAfterTomorrow.getDate() + 2);

  var tomorrow = new Date(todayStart);
  tomorrow.setDate(tomorrow.getDate() + 1);

  var calendar   = CalendarApp.getDefaultCalendar();
  var allEvents  = calendar.getEvents(todayStart, dayAfterTomorrow);

  var todayEvents    = [];
  var tomorrowEvents = [];

  for (var i = 0; i < allEvents.length; i++) {
    var ev = allEvents[i];
    if (ev.getStartTime() < tomorrow) {
      todayEvents.push(ev);
    } else {
      tomorrowEvents.push(ev);
    }
  }

  var now         = Utilities.formatDate(new Date(), tz, "EEEE, MMMM d yyyy");
  var todayLabel  = Utilities.formatDate(todayStart, tz, "EEEE MMMM d");
  var tomorrowLabel = Utilities.formatDate(tomorrow, tz, "EEEE MMMM d");

  var lines = [
    "CALENDAR — " + now,
    "Fetched: " + allEvents.length + " events (today + tomorrow)",
    repeat("=", 72),
    "",
    "TODAY — " + todayLabel,
    repeat("-", 40)
  ];

  if (todayEvents.length > 0) {
    todayEvents.forEach(function(ev) { lines.push(formatEvent(ev, tz)); });
  } else {
    lines.push("  (no events)");
  }

  lines.push("");
  lines.push("TOMORROW — " + tomorrowLabel);
  lines.push(repeat("-", 40));

  if (tomorrowEvents.length > 0) {
    tomorrowEvents.forEach(function(ev) { lines.push(formatEvent(ev, tz)); });
  } else {
    lines.push("  (no events)");
  }

  lines.push("");
  writeFile(folder, "calendar.txt", lines.join("\n"));
  Logger.log("Calendar: exported " + allEvents.length + " events → calendar.txt");
}

function formatEvent(ev, tz) {
  var start    = Utilities.formatDate(ev.getStartTime(), tz, "HH:mm");
  var end      = Utilities.formatDate(ev.getEndTime(), tz, "HH:mm");
  var title    = ev.getTitle() || "(untitled)";
  var location = ev.getLocation() || "";
  var desc     = (ev.getDescription() || "").trim().split("\n")[0].substring(0, 200);
  var guests   = ev.getGuestList()
    .map(function(g) { return g.getName() || g.getEmail(); })
    .join(", ");

  var parts = ["  " + start + "\u2013" + end + "  " + title];
  if (location) parts.push("           Location:  " + location);
  if (guests)   parts.push("           Attendees: " + guests);
  if (desc)     parts.push("           Notes:     " + desc);
  return parts.join("\n");
}

// ── Utility ───────────────────────────────────────────────────────────────────

function repeat(char, n) {
  var s = "";
  for (var i = 0; i < n; i++) s += char;
  return s;
}

/**
 * Returns a Date set to midnight at the start of the work day that is
 * workDaysBack business days before today, skipping Saturdays and Sundays.
 * Examples (today = Monday): workDaysBack=3 → previous Wednesday.
 *           (today = Tuesday): workDaysBack=3 → previous Thursday.
 */
function getWorkDaysCutoff(workDaysBack) {
  var date = new Date();
  var counted = 0;
  while (counted < workDaysBack) {
    date.setDate(date.getDate() - 1);
    var dow = date.getDay(); // 0 = Sunday, 6 = Saturday
    if (dow !== 0 && dow !== 6) {
      counted++;
    }
  }
  date.setHours(0, 0, 0, 0);
  return date;
}
