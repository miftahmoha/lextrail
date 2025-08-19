import { Options } from "vis";
import { Network, VisNet, LTId, LTEdge, LTGraph, LTUpdate, LTData, LTNetwork, LTInterface, LTState, Optional } from './types'
import { referNetwork, moveNetwork } from './helpers';
import { DOM } from './interface'
import { initializeLayout, updateLayout } from './layout'

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
};

// Moves the highlight from a node A to a node B.
export function moveHighlight(network: Network, fromId: string, toId: string): void {
    // [TODO] Add a check that `fromNode` should be in a highlighted state if not null.
    const nodes = (network as VisNet).body.data.nodes;
    const fromNode = fromId ? nodes.get(fromId) : null;
    const toNode = toId ? nodes.get(toId) : null;

    if (!toNode) {
        throw new Error("Highlight sent to an invalid node.");
    }

    // Update `toNode` to highlighted state.
    nodes.update({
        id: toId,
        color: {
            background: '#06b6d4',
            border: '#06b6d4'
        },
        shadow: {
            enabled: true,
            color: '#06b6d4',
            size: 10,
            x: 0,
            y: 0
        },
    });

    // Reset `fromNode` to default color if it exists.
    if (fromId !== toId && fromNode) {
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
}

async function deleteSidebarItem(sidesContainer: HTMLElement, index: number): Promise<void> {
    const sidebarItem = sidesContainer.children[index] as HTMLElement;

    if (!sidebarItem) {
        throw new Error(`Cannot delete non-existent sidebar item at index ${index}`);
    }

    // [NOTE] Need to delete the class to be able to trigger the animation in next frames.
    // [NOTE] Buggy since it doesn't wait for the item removal, 
    // (1) Add an error when adding an existing sidebar item over an existing one, 
    // (2) Make the function wait for the animation to end.
    // sidebarItem.classList.add('sidebar-item-remove');
    // sidebarItem.addEventListener('animationend', () => {
    //     sidebarItem.remove();
    // }, { once: true });

    // Temporary fix.
    sidebarItem.remove();
}

// [NOTE] No need to reason about `frontDisplay` since it's going to be updated to the last item by `setActiveItems`.
async function deleteSideNetwork(sideNetworks: Network[], index: number): Promise<void> {
    const sideNetwork = sideNetworks[index];

    if (!sideNetwork) {
        throw new Error(`Cannot delete non-existent network at index ${index}`);
    }

    sideNetwork.destroy();
    sideNetworks.splice(index, 1);
}

function handleDeletions(
    deletions: Record<number, LTGraph>,
    interface_: LTInterface,
    network: LTNetwork,
): void {
    // Delete from highest to lowest index to avoid array index shifts.
    const indicesToDelete = Object.keys(deletions)
        .map(Number)
        .sort((a, b) => b - a);

    for (const index of indicesToDelete) {
        deleteSidebarItem(interface_.sides, index);
        deleteSideNetwork(network.sides, index);
    }
}

function updateSidebarItem(sidebarItem: HTMLElement, index: number, graphData: LTGraph,
    network: LTNetwork): void {
    sidebarItem.classList.add('sidebar-item-new');

    // `2 * index + 1` since each thumbnail is precedeed by a header.
    const thumbnailItem = sidebarItem.children[1] as Optional<HTMLElement>;
    if (!thumbnailItem) {
        throw new Error(`Thumbnail item not found in sidebar item at index ${index}`);
    }

    // [TODO] Is `structuredClone` necessary?
    network.sides[index] = new Network(thumbnailItem, structuredClone(graphData), VIS_SIDE_OPTIONS);
}

function createSidebarItem(sidebar: HTMLElement, indexIn: number, graphData: LTGraph,
    interface_: LTInterface, network: LTNetwork,): void {
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

    function setClickHandler(sidebar: HTMLElement, sidebarItem: HTMLElement, interface_: LTInterface,
        network: LTNetwork, indexIn: number): void {
        sidebarItem.onclick = () => {
            Array.from(sidebar.children).forEach(child => {
                child.classList.remove('active');
            });

            sidebarItem.classList.add('active');

            const frontItem = interface_.front as HTMLElement;

            // [TODO] Why this?
            // const VIS_MAIN_OPTIONS = {
            //     nodes: {
            //         font: {
            //             color: '#ff0000' // Red color
            //         }
            //     }
            // }
            network.front = moveNetwork(network.sides[indexIn], frontItem, VIS_MAIN_OPTIONS());

            // [NOTE] Need to remove the animation class in order to trigger it again.
            frontItem.classList.add('graph-fade');
            frontItem.addEventListener('animationend', () => {
                frontItem.classList.remove('graph-fade');
            });
        };

    }

    const indexOut = extractIndexOut(sidebar.id);
    const sidebarItem = createSidebarElement(indexIn, indexOut);

    sidebar.appendChild(sidebarItem);

    // Add a fading animation.
    sidebarItem.classList.add('graph-fade');

    setClickHandler(sidebar, sidebarItem, interface_, network, indexIn);

    // Associate the network to the sidebar item through the thumbnail.
    const thumbnail = sidebarItem.children[1] as HTMLElement;
    const sideNetwork = new Network(thumbnail, structuredClone(graphData), VIS_SIDE_OPTIONS);

    network.sides.push(sideNetwork);
}

function handleAdditions(
    additions: Record<number, LTGraph>,
    interface_: LTInterface,
    network: LTNetwork,
): void {
    for (const [key, graphData] of Object.entries(additions)) {
        const index = parseInt(key, 10);
        const sidebar = interface_.sides;

        const sidebarItem = sidebar.children[index] as Optional<HTMLElement>;
        if (sidebarItem) {
            updateSidebarItem(sidebarItem, index, graphData, network);
        } else {
            createSidebarItem(sidebar, index, graphData, interface_, network);
        }
    };
}

// Set the sidebar item with highest index as active.
function setActiveItem(interface_: LTInterface, network: LTNetwork, active: HTMLElement[]) {
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

async function handlePreviews(network: LTNetwork, previews: LTId[], delay: number) {
    const frontNetwork = network.front;
    if (!frontNetwork) {
        throw Error("Non-existant front network after `setActiveItem` call.")
    }

    const nodes = (frontNetwork as VisNet).body.data.nodes;

    // Highlight next possible nodes.
    const updateProperties = {
        color: {
            background: '#FFFFFF',
            border: '#FFFFFF',
        },
        shadow: {
            enabled: true,
            color: '#FFFFFF',
            size: 10,
            x: 0,
            y: 0,
        },
    };

    const updates = previews.map(id => ({
        id: id,
        ...updateProperties,
    }));

    nodes.update(updates);

    // A slight pause to notice the highlight of the preview nodes.
    await new Promise(resolve => setTimeout(resolve, delay / 2));

    // Revert back to default.
    const resetProperties = {
        color: {
            background: 'lightblue',
            border: 'rgba(255, 255, 255, 0.05)',
        },
        shadow: {
            enabled: false,
        },
    };

    const resets = previews.map(id => ({
        id: id,
        ...resetProperties,
    }));

    nodes.update(resets);
}

function handleMoves(moves: Record<number, LTEdge>, network: LTNetwork) {
    for (const [sindex, move] of Object.entries(moves)) {
        if (!move.to) continue;
        const index = Number(sindex);
        const sideNetwork = network.sides;
        moveHighlight(sideNetwork[index], move.from, move.to);
    }
}

export async function updateGraphs(state: LTState, updates: LTUpdate[], previews: LTId[]) {
    const promises = updates.map(async (update, i) => {
        handleDeletions(update.delu, state.interfaces[i], state.networks[i]);
        handleAdditions(update.addu, state.interfaces[i], state.networks[i]);
        setActiveItem(state.interfaces[i], state.networks[i], state.active[i]);
        // await handlePreviews(state.networks[i], previews, state.delay);
        handleMoves(update.movu, state.networks[i]);
    });

    await Promise.all(promises);
}

export function updateFrame(DOM: DOM, state: LTState, newData: LTData) {
    const newPreviews: LTId[][] = newData.previews.slice(state.frame);
    const newUpdates: LTUpdate[][] = newData.updates.slice(state.frame);

    for (let i = 0; i < newUpdates.length; i++) {
        const updates = newUpdates[i];

        const currLength = updates.length;
        const prevLength = state.networks.length;

        if (prevLength === 0) {
            initializeLayout(DOM, state, currLength);
        } else {
            // If `(currLength - prevLength) != 0` means either (1) we've got an ambiguity and we've 
            // got to render every possible graph, or (2) we've come from one and we've got to render the chosen graph.
            // If `(currLength - prevLength) == 0` means we've got a (chosen) subgraph of ambiguities
            // from the original graphs.
            updateLayout(DOM, state, prevLength, updates);
        }

        updateGraphs(state, updates, newPreviews[i]);
    }

    // Update state.
    state.response.data = newData;
    state.frame = newData.updates.length;

    DOM.display.frameCounter.textContent = `Frame ${state.frame}/${state.frame}`;

    // Update LLM response (fragmented strings allows simple transitions to previous frames).
    DOM.display.llmResponse.value = newData.response.slice(0, state.frame).join('') || "No response available";
}