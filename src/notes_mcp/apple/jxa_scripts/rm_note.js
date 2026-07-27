function handle(Notes, cmd) {
  var note = noteById(Notes, cmd.identifier);
  Notes.delete(note);
  return null;
}
