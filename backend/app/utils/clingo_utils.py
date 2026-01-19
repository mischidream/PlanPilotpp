import clingo

def solve_abstract_lp(lp_path, horizon):
    ctl = clingo.Control([
        "-c", f"horizon={horizon}"
    ])

    ctl.load(lp_path)

    ctl.ground([("base", [])])

    atoms = []

    def on_model(model):
        nonlocal atoms
        atoms = model.symbols(shown=True)

    result = ctl.solve(on_model=on_model)

    return atoms

import clingo

def read_occurs_abs_lp(file_path):
    ctl = clingo.Control()
    ctl.load(file_path)

    # Force showing occurs_abstract atoms
    ctl.add("base", [], "#show occurs_abstract/2.")
    ctl.ground([("base", [])])

    atoms = []

    def on_model(model):
        nonlocal atoms
        atoms = model.symbols(shown=True)

    ctl.solve(on_model=on_model)
    return atoms


def write_occurs_abs_lp(atoms, output_path):
    lines = []

    for atom in atoms:
        if atom.name == "occurs":
            # occurs(action(...),T) → occurs_abstract(action(...),T)
            action = atom.arguments[0]
            time = atom.arguments[1]
            lines.append(f"occurs_abstract({action},{time}).")

        elif atom.name == "occurs_abstract":
            # already abstract (just in case)
            lines.append(f"{atom}.")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))


def create_map_lp(atoms, output_path, concrete_hangars):
    # concrete_hangars = ["hangar1", "hangar2"]
    lines = []

    for atom in atoms:
        if atom.name != "occurs_abstract":
            continue

        action_term = atom.arguments[0]
        time = atom.arguments[1]

        tuple_term = action_term.arguments[0]
        hangar_index = _find_hangarabs_index(action_term)

        # CASE 1: action uses hangarabs → choice rule
        if hangar_index is not None:
            choices = []

            for hangar in concrete_hangars:
                new_args = _replace_arg(tuple_term.arguments, hangar_index, hangar)
                new_tuple = clingo.Function("", new_args)
                new_action = clingo.Function("action", [new_tuple])
                choices.append(f"occurs({new_action},{time})")

            choice_body = "; ".join(choices)
            lines.append(
                f"1 {{ {choice_body} }} 1 :- occurs_abstract({action_term},{time})."
            )

        # CASE 2: no hangarabs → direct rewrite
        else:
            lines.append(
                f"occurs({action_term},{time}) :- occurs_abstract({action_term},{time})."
            )

    with open(output_path, "w") as f:
        f.write("\n".join(lines))


def solve_concrete_lp_with_mapping(output_c_lp, occurs_abs_lp, map_lp, horizon):
    ctl = clingo.Control(["-c", f"horizon={horizon}"])
    ctl.load(output_c_lp)
    ctl.load(occurs_abs_lp)
    ctl.load(map_lp)

    ctl.ground([("base", [])])

    plans = []

    def on_model(model):
        plans.append(model.symbols(shown=True))

    result = ctl.solve(on_model=on_model)
    print("Concrete plan SAT:", result)
    return plans

def _replace_arg(args, index, new_value):
    new_args = list(args)
    new_args[index] = clingo.String(new_value)
    return new_args

def _find_hangarabs_index(action_term):
    # TODO: maybe not only for the first action in the timestep
    tuple_term = action_term.arguments[0]
    for i, arg in enumerate(tuple_term.arguments):
        if arg.type == clingo.SymbolType.String and arg.string == "hangarabs":
            return i
    return None