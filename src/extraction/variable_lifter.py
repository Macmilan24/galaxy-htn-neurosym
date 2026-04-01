from pydantic import BaseModel, Field, ConfigDict


class LisftedVariable(BaseModel):
    name: str
    produced_by_step: str
    produced_by_port: str
    consumed_by: list[dict] = Field(default_factory=list)

    @property
    def is_workflow_input(self):
        return self.produced_by_port == "output" and not self.consumed_by


class LiftedMethod(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    workflow_id: str
    workflow_name: str
    task_type: str

    variables: dict[tuple[str, str], LisftedVariable] = Field(default_factory=dict)
    subtasks: list["LiftedSubtask"] = Field(default_factory=list)
    required_inputs: list[LisftedVariable] = Field(default_factory=list)

    @property
    def variable_count(self):
        return len(self.variables)

    @property
    def all_variable_names(self):
        return sorted(set(v.name for v in self.variables.values()))


class LiftedSubtask(BaseModel):
    step_uid: str
    tool_name: str
    tool_full_id: str
    inputs: dict[str, str]
    outputs: dict[str, str]

    def __str__(self):
        ins = ", ".join(f"{k}={v}" for k, v in self.inputs.items())
        outs = ", ".join(f"{k}={v}" for k, v in self.outputs.items())
        return f"{self.tool_name}({ins}) -> ({outs})"


class VariableLifter:
    def lift(self, method) -> LiftedMethod:
        lifted = LiftedMethod(
            workflow_id=method.workflow_id,
            workflow_name=method.workflow_name,
            task_type=method.task_type,
        )

        # build lookup maps
        uid_to_step = {s.step_uid: s for s in method.steps}
        var_counter = 0

        step_output_ports = {}
        for edge in method.edges:
            if edge.source_step_uid not in step_output_ports:
                step_output_ports[edge.source_step_uid] = set()

            step_output_ports[edge.source_step_uid].add(edge.from_output_name)

        # mint variables for each
        for step_uid, ports in step_output_ports.items():
            for port in sorted(ports):
                step = uid_to_step.get(step_uid)
                var_name = f"?data_{var_counter}"
                var_counter += 1

                var = LisftedVariable(
                    name=var_name, produced_by_step=step_uid, produced_by_port=port
                )
                lifted.variables[(step_uid, port)] = var

        # build for each step, which variable feed into  which input ports
        step_input_bindings = {}
        for edge in method.edges:
            key = (edge.source_step_uid, edge.from_output_name)
            var = lifted.variables.get(key)
            if var:
                var.consumed_by.append(
                    {
                        "step_uid": edge.target_step_uid,
                        "input_port": edge.input_name,
                    }
                )

                if edge.target_step_uid not in step_input_bindings:
                    step_input_bindings[edge.target_step_uid] = {}
                step_input_bindings[edge.target_step_uid][edge.input_name] = var.name

        # build lifted subtask sequence
        step_output_bindings = {}  # step_uid -> {output_port: variable_name}
        for (step_uid, port), var in lifted.variables.items():
            if step_uid not in step_output_bindings:
                step_output_bindings[step_uid] = {}
            step_output_bindings[step_uid][port] = var.name

        for uid in method.topological_order:
            step = uid_to_step.get(uid)
            if not step or not step.is_tool:
                continue

            subtask = LiftedSubtask(
                step_uid=uid,
                tool_name=step.tool_name,
                tool_full_id=step.tool_full_id,
                inputs=step_input_bindings.get(uid, {}),
                outputs=step_output_bindings.get(uid, {}),
            )
            lifted.subtasks.append(subtask)

        # identify workflow level inputs
        for uid in method.topological_order:
            step = uid_to_step.get(uid)
            if step and step.is_data_input:
                for (s_uid, port), var in lifted.variables.items():
                    if s_uid == uid:
                        lifted.required_inputs.append(var)

        return lifted
