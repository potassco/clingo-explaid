## ToDos

### Important Features

`2023`

- [x] New CLI structure
  - different modes:
    - MUC
    - UNSAT-CONSTRAINTS
  - can be enabled through flags
- [x] Iterative Deltion for Multiple MUCs
  - variation of the QuickXplain algorithm : `SKIPPED`
- [x] Finish unsat-constraints implementation for the API

`2024 - JAN`

- [x] New option to enable verbose derivation output
  - `--show-decisions` with more fine grained `--decision-signature` option
- [x] Make `--show-decisions` its own mode
- [x] Give a warning in Transformer if control is not grounded yet
- [x] Documentation
  - [x] Proper README
  - [x] Docstrings for all API functions
  - [x] CLI documentation with examples
  - [x] Examples folder
    - [x] Sudoku
    - [x] Graph Coloring
    - [x] N-Queens
- [x] Error when calling `--muc` constants aren't properly kept:
  - The problem was in `AssumptionTransformer` where get_assumptions didn't
    have proper access to constants defined over the CL and the program
    constants
- [x] `AssumptionTransformer` doesn't work properly on included files
  - It actually did work fine

`2024 - FEB`

- [x] In `--show-decisions` hide INTERNAL when `--decision-signature` is active
- [x] cleanup `DecisionOrderPropagator` print functions
- [x] Features for `--unsat-constraints`
  - [x] File + Line (Clickable link)
- [x] Confusing Optimization prints during `--muc` when finding mucs in
  optimized Programs
- [x] File-Link test with space in filename
  - with `urllib.parsequote`
- [x] Write up why negated assumptions in MUC's are a problem
  - One which is currently not addressed by clingo-explaid
- [x] Remove minimization also from `--unsat-constaints` mode
- [x] Change file identification to use `clingo.ast.Location` instead of the
  subtring search and own built file tree
- [x] Add spaces around Link to make it clickable on MAC

`2024 - MAR`

- [x] Add way for `-a` to allow for signatures without variables (`test/0`)

### Extra Features

- [ ] `--unsat-constraints`:
  - [ ] Access comments in the same line as constraint
  - [ ] Currently, for multiline constraints a line number cannot be found
- [ ] Timeout
