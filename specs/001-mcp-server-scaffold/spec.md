# Feature Specification: MCP Server Scaffold with Dummy list_folders Tool

**Feature Branch**: `001-mcp-server-scaffold`

**Created**: 2026-07-26

**Status**: Draft

**Input**: User description: "This is a python project. Build the basic scaffolding for this mcp server. Develop a dummy list_folders tool with its output stubbed for now. Update the readme file."

## Clarifications

### Session 2026-07-26

- Q: What fields and example values should the stubbed `list_folders` response include, beyond a folder name? → A: Name + id — e.g. `[{"id": "1", "name": "Notes"}, {"id": "2", "name": "Personal"}, {"id": "3", "name": "Work"}]`

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Runnable server scaffold (Priority: P1)

As a developer working on this project, I want a runnable Python MCP server
scaffold so that I have a working foundation to add real Apple Notes tools to
incrementally, instead of building the protocol plumbing from scratch each time.

**Why this priority**: Nothing else in this project can exist without a server
that starts and speaks the MCP protocol. This is the foundation every later
feature builds on.

**Independent Test**: Start the server process on its own and confirm it
initializes without error and correctly advertises itself as an MCP server
ready to accept a client connection.

**Acceptance Scenarios**:

1. **Given** the project is set up locally, **When** the server is started,
   **Then** it starts without error and is ready to accept an MCP client
   connection.
2. **Given** the server is running, **When** an MCP client asks for the list of
   available tools, **Then** the server responds with a tool list that
   includes `list_folders`.

---

### User Story 2 - Call the list_folders tool (Priority: P2)

As an MCP client (an AI agent or other tool caller), I want to call a
`list_folders` tool so that I can exercise the full request/response round
trip end-to-end, even though the data it returns is placeholder content until
real Apple Notes integration exists.

**Why this priority**: Proves the tool-call mechanism works correctly before
any real Notes integration is built, so future features can be added with
confidence the underlying plumbing is sound.

**Independent Test**: Call the `list_folders` tool through the running server
and confirm it returns a well-formed, consistent stub response.

**Acceptance Scenarios**:

1. **Given** the server is running, **When** `list_folders` is invoked with no
   arguments, **Then** it returns a successful response containing a stubbed
   list of folder entries (fixed placeholder data, not read from real Notes).
2. **Given** `list_folders` is invoked multiple times, **When** the responses
   are compared, **Then** they consistently match the same declared shape: a
   list of folder objects, each with an `id` and a `name`.

---

### User Story 3 - Discover and run the project via the README (Priority: P3)

As a new contributor, I want the README to explain what this project is and
how to run it, so that I can get the server running and verify it works
without asking someone else for help.

**Why this priority**: Lower priority than having a working server, but
required so the scaffold is actually usable by someone other than its author.

**Independent Test**: A person unfamiliar with the repository follows only
the README and successfully starts the server and calls `list_folders`.

**Acceptance Scenarios**:

1. **Given** a fresh clone of the repository, **When** a developer follows the
   README's setup steps, **Then** they can install dependencies and start the
   server successfully.
2. **Given** the server is running, **When** the developer follows the
   README's verification steps, **Then** they can confirm `list_folders`
   responds as expected.

---

### Edge Cases

- What happens when the server is started while another instance is already
  running?
- How does the system respond if `list_folders` is called with unexpected
  arguments, given it currently has no real filtering logic?
- What happens if an MCP client requests the tool list before server
  initialization has completed?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The project MUST provide a Python-based MCP server that can be
  started as a standalone local process.
- **FR-002**: The server MUST expose a list of its available tools to any
  connecting MCP client, and that list MUST include a tool named
  `list_folders`.
- **FR-003**: The `list_folders` tool MUST return a fixed, stubbed set of
  folder entries, each with an `id` and a `name` (e.g.,
  `[{"id": "1", "name": "Notes"}, {"id": "2", "name": "Personal"}, {"id": "3", "name": "Work"}]`).
  It MUST NOT read from, or connect to, real Apple Notes data at this stage.
- **FR-004**: The `list_folders` tool MUST succeed and return its stub
  response every time it is called with no input, with no side effects on any
  system state.
- **FR-005**: The README MUST describe what the project is, and MUST include
  concrete steps to install dependencies, start the server, and verify that
  `list_folders` responds correctly.
- **FR-006**: The scaffold MUST include an automated test that verifies
  `list_folders` returns its expected stubbed output.

### Key Entities

- **Folder (stub)**: A placeholder representation of an Apple Notes folder.
  Carries an `id` (stable identifier, distinct from the display name) and a
  `name`. Not yet backed by real Notes data — real folder attributes and
  behavior will be defined when actual Apple Notes integration is built, but
  the `id`/`name` split is chosen now so later tools can reference a folder by
  `id` without a breaking schema change.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can go from a fresh clone to a running MCP server in
  under 5 minutes by following the README alone.
- **SC-002**: 100% of `list_folders` calls made during normal operation return
  a valid, schema-consistent response with no errors.
- **SC-003**: A new contributor can verify the server and the `list_folders`
  tool work end-to-end using only the README, without reading the source code.

## Assumptions

- `list_folders` returns hardcoded, in-memory placeholder folders (each an
  `id` + `name` pair); it is not connected to real Apple Notes data yet — real
  integration is a separate, future feature.
- The server runs locally on the developer's machine using a standard local
  MCP transport (e.g., stdio), consistent with how local MCP servers are
  typically consumed by clients such as Claude Desktop or Claude Code. No
  network-exposed transport is in scope for this scaffold.
- No authentication or authorization is required at this stage, since the
  server runs locally under the developer's own account and does not yet
  touch real personal data.
- Per the project constitution's Test-First principle, "automated test" in
  FR-006 means a test that runs in the project's normal test suite, not a
  manual verification step.
