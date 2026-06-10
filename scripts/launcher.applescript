-- launcher.applescript — source for the "Meeting Transcriber" .app.
--
-- build-app.sh substitutes __REPO_ROOT__ with the absolute repo path at build
-- time. The app stays alive (on idle) so that quitting it (Cmd-Q / Dock Quit,
-- or logout) tears the server down via stop.sh.
--
-- launch.sh owns its own failure dialogs, so on run swallows shell errors.

property launchScript : "__REPO_ROOT__/scripts/launch.sh"
property stopScript : "__REPO_ROOT__/scripts/stop.sh"

on run
	try
		do shell script quoted form of launchScript
	on error
		-- launch.sh already showed a dialog on any failure path.
	end try
end run

on idle
	return 30
end idle

on quit
	try
		do shell script quoted form of stopScript
	end try
	continue quit
end quit
