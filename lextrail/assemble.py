from collections import defaultdict, deque
from copy import copy
from dataclasses import dataclass, field
from uuid import UUID, uuid4
from typing import Deque, Optional

from lextrail.build import SymbolKind
from lextrail.guide import CFGGraph, TrailLayer, TrailFrame, build_cfg_graph
from lextrail.helpers import TrailError


@dataclass
class ASMNode:
    value: int
    id: UUID = field(default_factory=lambda: uuid4())

    def __hash__(self):
        return hash(self.id)


@dataclass
class ASMGraph:
    heads: list[ASMNode]
    edges: dict[ASMNode, set[ASMNode]]
    tails: list[ASMNode]

    def new() -> "ASMGraph":
        return ASMGraph(heads=[], edges=defaultdict(list), tails=[])


@dataclass
class ASMStep:
    accumulator: list[int]
    node: Optional[ASMNode]

    @classmethod
    def new(cls) -> "ASMStep":
        return ASMStep(accumulator=[], node=None)


@dataclass
class ASMToken:
    value: Deque[int]

    @classmethod
    def new(cls) -> "ASMToken":
        return ASMToken(deque())

    @classmethod
    def from_str(cls, s: str) -> "ASMToken":
        return cls(deque(s.encode("utf-8")))

    def end(self) -> bool:
        return not self.value


@dataclass
class ASMFrame:
    layers: list["TrailLayer"]
    step: ASMStep
    token: ASMToken

    @classmethod
    def new(cls, cfg: str) -> "ASMFrame":
        return ASMFrame(
            layers=TrailFrame.new(cfg), step=ASMStep.new(), token=ASMToken.new()
        )


@dataclass
class ASMProposal:
    frame: ASMFrame
    value: str


type ASMRefs = dict[str, list[int]]


@dataclass
class ASMState:
    proposals: list[ASMProposal]
    backrefs: ASMRefs

    @classmethod
    def new(cls) -> "ASMState":
        return ASMState(proposals=[], backrefs=defaultdict(list))


@dataclass
class ASMSchema:
    cfg: CFGGraph
    asm: ASMGraph


@dataclass
class ASM:
    schema: ASMSchema
    state: ASMState


def build_asm_graph(alphabet: list[str]):
    graph: ASMNode = ASMGraph.new()
    node: Optional[ASMNode] = None

    tokens = [symbol.encode("utf-8") for symbol in alphabet]

    for token in tokens:
        for i, byte in enumerate(token):
            candidates = graph.heads if i == 0 else graph.edges[node] if node else []
            found = next((node for node in candidates if node.value == byte), None)

            if found:
                node = found
            else:
                new_node = ASMNode(byte)
                candidates.append(new_node)
                node = new_node

        if node not in graph.tails:
            graph.tails.append(node)

    return graph


def asm_cfg(cfg: str, alphabet: list[str]) -> ASM:
    return ASM(
        schema=ASMSchema(cfg=build_cfg_graph(cfg), asm=build_asm_graph(alphabet)),
        state=ASMState.new(),
    )


def asm_exp(exp: str, alphabet: list[str]) -> ASM:
    return ASM(
        schema=ASMSchema(
            cfg=build_cfg_graph(f"start: {exp}"), asm=build_asm_graph(alphabet)
        ),
        state=ASMState.new(),
    )


def asm_rex(rex: str, alphabet: list[str]) -> ASM:
    return ASM(
        schema=ASMSchema(
            cfg=build_cfg_graph(f"start: /{rex}/"), asm=build_asm_graph(alphabet)
        ),
        state=ASMState.new(),
    )


def assemble(graph: ASMGraph, frame: ASMFrame) -> list[ASMProposal]:
    proposals: list[ASMProposal] = []

    token, step = frame.token, frame.step
    bytes, node = token.value, step.node

    successors = graph.edges[node] if node else graph.heads

    while bytes:
        found = next(
            (successor for successor in successors if successor.value == bytes[0]), None
        )

        if found:
            # Update token.
            byte = bytes.popleft()

            step.node = found
            step.accumulator.append(byte)

            if found in graph.tails:
                final_layers = [copy(layer) for layer in frame.layers]

                # Reset the step for the next run.
                final_step = ASMStep.new()
                final_token = ASMToken(value=deque(bytes))

                final_frame = ASMFrame(
                    layers=final_layers, step=final_step, token=final_token
                )
                final_value = bytearray(step.accumulator).decode("utf-8")

                proposals.append(
                    ASMProposal(
                        frame=final_frame,
                        value=final_value,
                    )
                )

            successors = graph.edges[found]
        else:
            break

    return proposals


def asm_run(asm_s: ASM):
    schema, state = asm_s.schema, asm_s.state

    cfg, asm = schema.cfg, schema.asm
    proposals, backrefs = state.proposals, state.backrefs

    # === Backreferences ===
    for proposal in proposals:
        node, value = proposal.frame.layers[-1].node, proposal.value

        for tag in node.tags:
            backrefs[tag] += value

    frames = (
        [proposal.frame for proposal in proposals] if proposals else [ASMFrame.new(cfg)]
    )

    state.proposals.clear()

    while frames:
        frame = frames.pop()
        checkpoint = frame.layers[-1]
        graph, node = checkpoint.graph, checkpoint.node

        if node:
            successors = graph.edges[node] if frame.token.end() else [node]
        else:
            successors = graph.heads

        if not successors:
            frame.layers.pop()

            if frame.layers:
                frames.append(frame)

            continue

        for successor in successors:
            if successor.kind == SymbolKind.TERMINAL:
                next_layers = [copy(layer) for layer in frame.layers]
                next_layers[-1].node = successor

                step, token = frame.step, frame.token
                next_step, next_token = (
                    ASMStep(accumulator=step.accumulator[:], node=step.node),
                    (
                        ASMToken.from_str(successor.content)
                        if token.end()
                        else ASMToken(value=deque(token.value))
                    ),
                )

                next_frame = ASMFrame(
                    layers=next_layers, step=next_step, token=next_token
                )

                proposals = assemble(asm, next_frame)
                state.proposals.extend(proposals)

                if next_token.end():
                    frames.append(next_frame)
            elif successor.kind == SymbolKind.VARIABLE:
                next_layers = [copy(layer) for layer in frame.layers]
                next_layers[-1].node = successor

                # Reaching a `VARIABLE` means adding a layer to the stack.
                next_value = successor.content
                next_layer = TrailLayer(graph=cfg[next_value], node=None)
                next_layers.append(next_layer)

                next_frame = ASMFrame(
                    layers=next_layers, step=copy(frame.step), token=copy(frame.token)
                )

                # Push it to be processed.
                frames.append(next_frame)
            elif successor.kind == SymbolKind.REFERENCE:
                next_layers = [copy(layer) for layer in frame.layers]
                next_layers[-1].node = successor

                step, token = frame.step, frame.token
                next_step, next_token = (
                    ASMStep(accumulator=step.accumulator[:], node=step.node),
                    (
                        ASMToken(value=backrefs[successor.content])
                        if token.end()
                        else ASMToken(value=token.value[:])
                    ),
                )

                next_frame = ASMFrame(
                    layers=next_layers, step=next_step, token=next_token
                )

                proposals = assemble(asm, next_frame)
                state.proposals.extend(proposals)

                if next_token.end():
                    frames.append(next_frame)
            elif successor.kind == SymbolKind.END:
                if frame.step == ASMStep.new():
                    next_layers = [copy(layer) for layer in frame.layers]
                    next_layers[-1].node = successor

                    next_frame = ASMFrame(
                        layers=next_layers, step=ASMStep.new(), token=ASMToken.new()
                    )

                    state.proposals.append(ASMProposal(frame=next_frame, value=""))
            else:
                raise TrailError("Symbol of kind `{successor.kind}` is not supported.")


def get_next_tokens(asm: ASM, token: str):
    state = asm.state

    current = state.proposals
    state.proposals = [proposal for proposal in current if proposal.value == token]

    if current and not state.proposals:
        raise TrailError(f"`{token}` has no previous state.")

    asm_run(asm)

    return [proposal.value for proposal in state.proposals]
