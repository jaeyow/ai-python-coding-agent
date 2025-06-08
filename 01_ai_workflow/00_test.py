from burr.core import ApplicationBuilder, State, action, Application

@action(reads=[], writes=[])
def step_1(state: State, word: str) -> State:
    print(f"Step 1: {word}")
    return state


@action(reads=[], writes=[])
def step_2(state: State, word: str) -> State:
    print(f"Step 2: {word}")
    return state


@action(reads=[], writes=[])
def step_3(state: State, word: str) -> State:
    print(f"Step 3: {word}")
    return state


@action(reads=[], writes=[])
def step_4(state: State, word: str) -> State:
    print(f"Step 4: {word}")
    return state


@action(reads=[], writes=[])
def step_5(state: State, word: str) -> State:
    print(f"Step 5: {word}")
    return state


def application() -> Application:
    return (
        ApplicationBuilder()
        .with_actions(
            step_1,
            step_2,
            step_3,
            step_4,
            step_5,
        )
        .with_transitions(
            ("step_1", "step_2"),
            ("step_2", "step_3"),
            ("step_3", "step_4"),
            ("step_4", "step_5"),
        )
        .with_entrypoint("step_1")
        .build()
    )


if __name__ == "__main__":
  for word in ["red", "green", "blue"]:
    app = application()
    app.visualize(
        include_conditions=True,
        include_state=True,
        format="png",
        output_file_path="00_test",
    )

    app.run(halt_after=["step_5"], inputs={"word": word})
    print(f"Finished with {word}")