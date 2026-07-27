function handle(Notes, cmd) {
  var note = noteById(Notes, cmd.note_id);
  return { plaintext: note.plaintext() };
}
