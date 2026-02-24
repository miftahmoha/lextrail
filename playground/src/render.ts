import { Network, Options } from "vis";
import { referNetwork } from './helpers';
import { DOM } from './interface'
import { initializeLayout, updateLayout } from './layout'
import {
    Optional, Undefinable, VisNet,
    Ts_Add, Ts_Mov, Ts_Del, Ts_Update, Ts_Network, Ts_Interface, Ts_State,
    Py_Data, Py_TrailLayer, Py_TrailState, Py_Graph,
} from './types'

// [NOTE] Needs to check the theme each time it is called.
export const VIS_MAIN_OPTIONS = (): Options => ({
    nodes: {
        shape: "dot",
        size: 20,
        color: {
            background: 'rgba(173, 216, 230, 1)',
            border: 'rgba(255, 255, 255, 0.5)',
        },
        font: {
            face: 'Space Mono',
            color: DOM.root.classList.contains('light-mode') ? '#000000' : '#ffffff',
            size: 14,
            strokeWidth: 0
        },
    },
    edges: {
        arrows: "to",
        color: {
            color: 'rgba(255, 255, 255, 0.2)',
            highlight: '#06b6d4'
        },
        width: 1.5
    },
    physics: {
        enabled: true,
        solver: "forceAtlas2Based",
        stabilization: {
            enabled: true,
            iterations: 1000,
            updateInterval: 25,
        },
    },
    layout: {
        randomSeed: 42
    },
});

export const VIS_SIDE_OPTIONS: Options = {
    nodes: {
        shape: "dot",
        size: 15,
        color: {
            background: 'rgba(173, 216, 230, 1)',
            border: 'rgba(255, 255, 255, 0.5)',
        },
        font: {
            face: 'Space Mono',
            color: DOM.root.classList.contains('light-mode') ? '#000000' : '#ffffff',
            size: 0,
            strokeWidth: 0
        },
    },
    edges: {
        arrows: "to",
        color: {
            color: 'rgba(255, 255, 255, 0.2)',
            highlight: '#06b6d4'
        },
        width: 1
    },
    layout: {
        randomSeed: 42
    },
};

function deleteSidebarItem(sidesContainer: HTMLElement, index: number): void {
    const sidebarItem = sidesContainer.children[index] as HTMLElement;
    if (!sidebarItem) {
        throw new Error(`Cannot delete non-existent sidebar item at index ${index}`);
    }

    // [NOTE] Need to delete the class to be able to trigger the animation in next frames.
    // [TODO] Buggy since it doesn't wait for the item removal, 
    // (1) Add an error when adding an existing sidebar item over an existing one, 
    // (2) Make the function wait for the animation to end.
    // sidebarItem.classList.add('sidebar-item-remove');
    // sidebarItem.addEventListener('animationend', () => {
    //     sidebarItem.remove();
    // }, { once: true });

    // Temporary fix.
    sidebarItem.remove();
}

// [NOTE] No need to reason about `frontDisplay` since it's going to be updated to the last item by `setActive`.
function deleteSideNetwork(sideNetworks: Network[], index: number): void {
    const sideNetwork = sideNetworks[index];

    if (!sideNetwork) {
        throw new Error(`Cannot delete non-existent network at index ${index}`);
    }

    sideNetwork.destroy();
    sideNetworks.splice(index, 1);
}

function delGraphs(delu: Ts_Del, interface_: Ts_Interface, network: Ts_Network): void {
    // Delete from highest to lowest index to avoid array index shifts.
    const indicesToDelete = Object.keys(delu)
        .map(Number)
        .sort((a, b) => b - a);

    for (const index of indicesToDelete) {
        deleteSidebarItem(interface_.sides, index);
        deleteSideNetwork(network.sides, index);
    }
}

function updateSidebarItem(
    sidebarItem: HTMLElement, index: number, graphData: Py_Graph, network: Ts_Network
): void {
    sidebarItem.classList.add('sidebar-item-new');

    // `2 * index + 1` since each thumbnail is precedeed by a header.
    const thumbnailItem = sidebarItem.children[1] as Optional<HTMLElement>;
    if (!thumbnailItem) {
        throw new Error(`Thumbnail item not found in sidebar item at index ${index}`);
    }

    // [TODO] Is `structuredClone` necessary?
    network.sides[index] = new Network(thumbnailItem, structuredClone(graphData), VIS_SIDE_OPTIONS);
}

function createSidebarItem(
    sidebar: HTMLElement, indexIn: number, graphData: Py_Graph, interface_: Ts_Interface, network: Ts_Network, active: HTMLElement[]
): void {
    function extractIndexOut(id: string) {
        // [NOTE] Elements of an ambiguous sidebar have a suffix `_index` which specifies the index.
        const parts = id.split('_');
        if (parts.length < 2) {
            throw new Error(`Invalid ID format: ${id}`);
        }

        return parseInt(parts[1], 10);
    }

    function createSidebarElement(indexIn: number, indexOut: number): HTMLElement {
        const sidebarItem = document.createElement('div');
        sidebarItem.className = 'sidebar-item sidebar-item-new';
        sidebarItem.id = `sidebar-item-${indexIn}_${indexOut}`;

        const label = document.createElement('div');
        label.id = `label-${indexIn}_${indexOut}`;
        label.textContent = `Subgraph ${indexIn}`;

        const thumbnail = document.createElement('div');
        thumbnail.className = 'sidebar-thumbnail';
        thumbnail.id = `thumbnail-${indexIn}_${indexOut}`;

        sidebarItem.append(label, thumbnail);
        return sidebarItem;
    }

    function setClickHandler(
        indexIn: number, interface_: Ts_Interface, network: Ts_Network, active: HTMLElement[]
    ): void {
        const sidebarItems = interface_.sides.children;
        const sidebarItem = sidebarItems[indexIn] as HTMLElement;

        sidebarItem.onclick = () => {
            Array.from(sidebarItems).forEach(child => {
                child.classList.remove('active');
            });

            sidebarItem.classList.add('active');

            const frontItem = interface_.front as HTMLElement;
            network.front = referNetwork(network.sides[indexIn], frontItem, VIS_MAIN_OPTIONS());

            // [NOTE] Need to remove the animation class in order to trigger it again.
            frontItem.classList.add('graph-fade');
            frontItem.addEventListener('animationend', () => {
                frontItem.classList.remove('graph-fade');
            });

            active[0] = sidebarItem
        };

    }

    const indexOut = extractIndexOut(sidebar.id);
    const sidebarItem = createSidebarElement(indexIn, indexOut);

    sidebar.appendChild(sidebarItem);

    // Add a fading animation.
    sidebarItem.classList.add('graph-fade');

    setClickHandler(indexIn, interface_, network, active);

    // Associate the network to the sidebar item through the thumbnail.
    const thumbnail = sidebarItem.children[1] as HTMLElement;
    const sideNetwork = new Network(thumbnail, structuredClone(graphData), VIS_SIDE_OPTIONS);

    network.sides.push(sideNetwork);
}

function addGraphs(
    additions: Ts_Add, interface_: Ts_Interface, network: Ts_Network, active: HTMLElement[]
): void {
    for (const [key, graphData] of Object.entries(additions)) {
        const index = parseInt(key, 10);
        const sidebar = interface_.sides;

        const sidebarItem = sidebar.children[index] as Optional<HTMLElement>;
        if (sidebarItem) {
            updateSidebarItem(sidebarItem, index, graphData, network);
        } else {
            createSidebarItem(sidebar, index, graphData, interface_, network, active);
        }
    };
}

// Set the sidebar item with highest index as active.
function setActive(interface_: Ts_Interface, network: Ts_Network, active: HTMLElement[]) {
    const activeItem = [...interface_.sides.children].at(-1) as HTMLElement;

    const lastActiveItem = active[0];

    if (activeItem && lastActiveItem !== activeItem) {
        if (lastActiveItem) {
            lastActiveItem.classList.remove('active');
        }

        activeItem.classList.add('active');

        const lastNetwork = network.sides.at(-1);
        if (!lastNetwork) {
            throw Error(`Network data not found.`);
        }

        const frontItem = interface_.front;

        network.front = referNetwork(lastNetwork, (frontItem as HTMLElement), VIS_MAIN_OPTIONS());

        // [NOTE] Need to delete the class to be able to trigger the animation in next frames.
        frontItem.classList.add('graph-fade');
        frontItem.addEventListener('animationend', () => {
            frontItem.classList.remove('graph-fade');
        }, { once: true });
    };

    active[0] = activeItem;
}

export function moveHighlight(network: Network, fromId: Undefinable<string>, toId: string, kind: string): void {
    // [TODO] Add a check that `fromNode` should be in a highlighted state if not null.
    const nodes = (network as VisNet).body.data.nodes;

    const fromNode = fromId ? nodes.get(fromId) : null;
    if (fromNode && fromId !== toId) {
        nodes.update({
            id: fromId,
            color: {
                background: 'lightblue',
                border: 'rgba(255, 255, 255, 0.05)',
            },
            shadow: {
                enabled: false,
            },
        });
    }

    const color = kind == "SymbolKind.TERMINAL" ? '#06b6d4' : kind == "SymbolKind.END" ? '#f87171' : kind == "SymbolKind.REFERENCE" ? '#ebc2ce' : '#7fc1c6';

    const toNode = toId ? nodes.get(toId) : null;
    if (!toNode) {
        throw new Error("Highlight sent to an invalid node.");
    }
    else {
        nodes.update({
            id: toId,
            color: {
                background: color,
                border: color,
            },
            shadow: {
                enabled: true,
                color: color,
                size: 10,
                x: 0,
                y: 0
            },
        });
    }
}

function moveGraphs(moves: Ts_Mov, network: Ts_Network) {
    for (const [sindex, move] of Object.entries(moves)) {
        if (!move.to) continue;
        const index = Number(sindex);
        const sideNetwork = network.sides;
        moveHighlight(sideNetwork[index], move?.from?.id, move?.to?.id, move?.to?.kind);
    }
}

export async function updateGraphs(state: Ts_State, updates: Ts_Update[]) {
    const promises = updates.map(async (update, i) => {
        delGraphs(update.delu, state.interfaces[i], state.networks[i]);
        addGraphs(update.addu, state.interfaces[i], state.networks[i], state.active[i]);
        // Sets the active item on the front display.
        setActive(state.interfaces[i], state.networks[i], state.active[i]);
        moveGraphs(update.movu, state.networks[i]);
    });

    await Promise.all(promises);
}

export function createUpdate(prevStates: Py_TrailLayer[], currStates: Py_TrailLayer[]): Ts_Update {
    let addu: Ts_Add = {};
    let movu: Ts_Mov = {};
    let delu: Ts_Del = {};

    const min_len = Math.min(prevStates?.length || 0, currStates.length);

    // === MOVE ===
    for (let i = 0; i < min_len; i++) {
        const [prevState, currState] = [prevStates[i], currStates[i]];

        if (JSON.stringify(prevState) !== JSON.stringify(currState)) {
            if (JSON.stringify(prevState.graph) === JSON.stringify(currState.graph)) {
                if (!prevState.state || !currState.state)
                    throw Error(`Invalid states for either ${prevState} or ${currState}.`);

                movu[i] = { "from": prevState.state, "to": currState.state };
            }
            else {
                delu[i] = prevState.graph;
                addu[i] = currState.graph;

                if (!currState.state)
                    throw Error(`Invalid state for ${currState}.`);

                movu[i] = { "from": null, "to": currState.state };
            }
        }
        else {
            if (!prevState.state || !currState.state)
                throw Error(`Invalid states for either ${prevState} or ${currState}.`);

            movu[i] = { "from": prevState.state, "to": currState.state };
        }
    }

    // === DEL ===
    if ((prevStates?.length || 0) > currStates.length) {
        for (let i = min_len; i < prevStates.length; i++) {
            const prevState = prevStates[i];

            delu[i] = prevState.graph;

            if (!prevState.state) {
                throw Error(`Invalid state for ${prevState}.`);
            }

            movu[i] = { "from": prevState.state, "to": null };
        }
    }

    // === ADD ===
    if ((prevStates?.length || 0) < currStates.length) {
        for (let i = min_len; i < currStates.length; i++) {
            const currState = currStates[i];

            addu[i] = currState.graph;

            if (!currState.state) {
                throw Error(`Invalid state for ${currState}.`);
            }

            movu[i] = { "from": null, "to": currState.state };
        }
    }

    return { "addu": addu, "movu": movu, "delu": delu };
}

export async function updateFrame(DOM: DOM, state: Ts_State, recvData: Py_Data) {
    const results: Py_TrailState[][] = recvData.results;

    const prevResults = results[state.frame - 1];
    const nextResults = results[results.length - 1];

    // [NOTE] If there is an increase of states within an ambiguous node, updates from the FIRST
    // current node to the rest of nodes are created.
    const updates = nextResults.map((nextStates, i) =>
        createUpdate(prevResults?.[i] ?? prevResults?.[0], nextStates)
    );

    const nextLength = updates.length;
    const currLength = state.networks.length;

    if (currLength === 0) {
        initializeLayout(DOM, state, nextLength);
    } else {
        // If `(currLength - prevLength) != 0` means either (1) we've got an ambiguity and we've 
        // got to render every possible graph, or (2) we've come from one and we've got to render
        // the chosen graph.
        // If `(currLength - prevLength) == 0` means we've got a (chosen) subgraph of ambiguities
        // from the original graphs.
        updateLayout(DOM, state, nextLength);
    }

    updateGraphs(state, updates);

    // Update state.
    state.response.data = recvData;
    state.frame = recvData.results.length;

    DOM.display.frameCounter.textContent = `Frame ${state.frame}/${state.frame}`;

    // Fragmented strings allow simple transitions to previous frames.
    DOM.display.llmResponse.value = recvData.response.slice(0, state.frame).join('') || "No response available";
}